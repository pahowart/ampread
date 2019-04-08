#!/usr/bin/env python3
#
# Author Paul Howarth
# Sample program for Raspberry Pi V2 using SCT-013 current sensors and
# an ads1015 analog 2 digital converter to monitor individual house panel circuit current.
# The sensor output is then uploaded to influxdb.
#
# Please note that there is only basic error checking implemented.
#
# This code is free to use, copy or distribute.
#
# Acknowledgements to adafruit for sample python scripts as well as
# the ebook Raspberry Pi: Measure, Record, Explore by Malcolm Maclean
# This script is intentionally over commented to help out other newbie's like me.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re
import sys
import datetime
import time
import Adafruit_ADS1x15
import math
import holidays
import socket
from influxdb import InfluxDBClient

# Create first ADS1015 ADC instance.
adc1 = Adafruit_ADS1x15.ADS1015(address=0x48, busnum=1)

# Create a second ADS1015 ADC instance if are using a second ADC.
adc2 = Adafruit_ADS1x15.ADS1115(address=0x49, busnum=1)

GAIN_A = 4         # see ads1015/1115 documentation for potential values.
GAIN_B = 4
samples = 200      # increase or decrease # of samples taken from ads1015
places = int(2)    # set rounding 
time_elapsed = (0)

# Define holidays country as Canada (Ontario is default Province)
ca_holidays = holidays.Canada()

# start loop to find current and utility voltage and then upload to influxdb
while True:

    try:
        # reset variables
        count = int(0)
        data = [0] * 4
        maxValue = [0] * 4
        IrmsA = [0] * 4
        ampsA = [0] * 4
        voltage = float(0)
        kilowatts = float(0)
        
        # start timer to use in kWh calculations
        start_time = time.time()

        # since we are measuring an AC circuit the output of SCT-013 will be a sinewave.
        # in order to calculate amps from sinewave we will need to get the peak voltage
        # from each input and use root mean square formula (RMS)
        # this loop will take 200 samples from each input and give you the highest (peak)
        # voltage from each port on the first ads1015.
        while count < samples:
            count += 1
            # nested loop to find highest sensor values from samples
            for i in range(0, 4):

                # read input A0 through A3 from adc1 as absolute value
                data[i] = abs(adc1.read_adc(i, gain=GAIN_A))

                # see if you have a new maxValue
                if data[i] > maxValue[i]:
                    maxValue[i] = data[i]

            # convert maxValue sensor outputs to amps
            # I used a sct-013 that is calibrated for 1000mV output @ 30A. Usually has 30A/1V printed on it.
            for i in range(0, 4):
                IrmsA[i] = float(maxValue[i] / float(2047) * 30)
                IrmsA[i] = round(IrmsA[i], places)
                ampsA[i] = IrmsA[i] / math.sqrt(2)  # RMS formula to get current reading to match what an ammeter shows.
                ampsA[i] = round(ampsA[i], places)

        # assign range values to variables used for io adafruit upload.
        ampsA0 = ampsA[0]
        ampsA1 = ampsA[1]
        ampsA2 = ampsA[2]
        ampsA3 = ampsA[3]

        # reset variables before reading adc2
        count = int(0)
        data = [0] * 4
        maxValue = [0] * 4
        IrmsB = [0] * 4
        ampsB = [0] * 4

        # this loop will take 200 samples from each input and give you the highest (peak)
        # voltage from each port on the second ads1015.
        while count < samples:
            count += 1
            # nested loop to find highest sensor values from samples
            for i in range(0, 4):

                # read input A0 through A3 from adc2 as absolute value
                data[i] = abs(adc2.read_adc(i, gain=GAIN_B))

                # see if you have a new maxValue
                if data[i] > maxValue[i]:
                    maxValue[i] = data[i]

            # convert maxValue sensor outputs to amps
            # I used a sct-013 that is calibrated for 1000mV output @ 30A. Usually has 30A/1V printed on it.
            for i in range(0, 4):
                IrmsB[i] = float(maxValue[i] / float(22000) * 30)
                IrmsB[i] = round(IrmsB[i], places)
                ampsB[i] = IrmsB[i] / math.sqrt(2)  # RMS formula to get current reading to match what an ammeter shows.
                ampsB[i] = round(ampsB[i], places)

        # assign range values to variables for upload to influxdb
        ampsB0 = ampsB[0]
        ampsB1 = ampsB[1]
        ampsB2 = ampsB[2]
        ampsB3 = ampsB[3]



    except KeyboardInterrupt:
        print('You cancelled the operation.')
        sys.exit()
        
    # This section pulls status information from a UPS using a NUT Server
    # The most important value is the Utility Voltage which is variable LINEV
    # Other variables are captured to display UPS info in separate Grafana dashboard
    
    # NUT server ip, port number
    HOST = ('192.168.10.1') 
    PORT = 3493
    
    # Open socket with remote host
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # Send command
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(b'LIST VAR 9180\n')
    time.sleep(.25)
    data = s.recv(2048)
    utf8 = data.decode('utf-8')
    #print (utf8) # uncomment to see raw output from UPS
    s.close()

    values = re.findall(r'"(.*?)"', utf8) # find values using regex
    
    #print(values) # uncomment to see regex output
    
    # split results we want from "values" into individual variables for upload to influxdb
    try:
        BCHG = float(values[0])
        TIMELEFT = round(float(values[2])/60,2)
        UPSMODEL = (values[5])
        LINEV = float(values[19])
        LOAD = float(values[42])
        SERVER = (values[50])
        STATUS = (values[51])
    
    except:
        try:
            # shift values during power outage due to additional status line that is output
            LINEV = float(values[20])
            LOAD = float(values[43])
            SERVER = (values[51])
            STATUS = (values[52])
        
        except:
            BCHG = float(100.0)
            TIMELEFT = round(float(300.0)/60,2)
            UPSMODEL = ('Script Error')
            LINEV = float(120.0)
            LOAD = float(50.0)
            SERVER = ('Script Error')
            STATUS = ('Script Error')


    # Calculate total AMPS from all sensors and convert to kilowatts
    kilowatts = round((ampsA0 + ampsA1 + ampsA2 + ampsA3 + ampsB0 + ampsB1 + ampsB2 + ampsB3) * LINEV/1000,places)

    # Get current month, day, hour for rate schedule calculations
    date = datetime.date.today()
    month = datetime.date.today().month
    day = datetime.date.today().day
    weekday = datetime.datetime.today().weekday()
    hour = datetime.datetime.now().time()

    # Assign pricing to TOU time range by summer and winter
    # Determine if summer or winter time of use schedule is in effect.
    # Time of Use kwh electricity pricing for Ontario as of Jan 2019.
    rate_01 = 0.065
    rate_02 = 0.094
    rate_03 = 0.132

    # These are the time ranges for time of use in Ontario as of Jan 2019.
    # Winter Time of Use tou_01 Schedule 7am to 11am
    # Winter Time of Use tou_02 Schedule 11am to 5pm
    # Winter Time of Use tou_03 Schedule 5pm to 7pm
    # Winter Time of Use tou_04 Schedule 7pm to 7am
    # Weekends and Holidays are always tou_04
    if 5 <= month < 11:
        tou_01 = rate_02 
        tou_02 = rate_03
        tou_03 = rate_02
        tou_04 = rate_01
        schedule = 'Summer'
    else:
        tou_01 = rate_03
        tou_02 = rate_02
        tou_03 = rate_03
        tou_04 = rate_01
        schedule = 'Winter'

    # Default rate is tou_04
    rate = tou_04

    # Check for tou_01 time range
    start = datetime.time(7, 00)
    end = datetime.time(11, 00)
    if start <= hour <= end:
        rate = tou_01

    # Check for tou_02 time range
    start = datetime.time(11, 00)
    end = datetime.time(17, 00)
    if start <= hour <= end:
        rate = tou_02

    # Check for tou_03 time range
    start = datetime.time(17, 00)
    end = datetime.time(19, 00)
    if start <= hour <= end:
        rate = tou_03

    # In Ontario, weekends and holidays are always offpeak.
    # Check to see if it is a weekend
    if date.today().weekday() in range(6,7):
        rate = tou_04

    # Check to see if it is a holiday.
    if date in ca_holidays:
        rate = tou_04
        
    # determine time of use string "tag" for influxdb
    tou = str('null')
    if rate == rate_01:
        tou = 'offpeak'
    elif rate == rate_02:
        tou = 'midpeak'
    else:
        tou = 'onpeak'
        
    # convert kilowatts to kilowatts / hour (kWh)
    kwh = round((kilowatts * time_elapsed)/3600,8)
    
    # Calculate estimated cost / hour assuming current usage is maintained for an hour
    cph = round((kilowatts * rate),places)

    # iso = datetime.datetime.now()
    iso = datetime.datetime.utcnow().isoformat() + 'Z'

    # write all ampere readings to database
    json_amps = [
        {
            "measurement": "current",
            "tags": {
                "tou_schedule": schedule,
                "tou": tou
            },
            "time": iso,
            "fields": {
                "ampsA0": ampsA[0],
                "ampsA1": ampsA[1],
                "ampsA2": ampsA[2],
                "ampsA3": ampsA[3],
                "ampsB0": ampsB[0],
                "ampsB1": ampsB[1],
                "ampsB2": ampsB[2],
                "ampsB3": ampsB[3],
            }
        }
    ]
    # Change the client IP address and user/password to match your instance of influxdb
    # Note that I have no user or password, place them in the quotes '' after port number
    # retries=0 means infinate attempts.
    client = InfluxDBClient('192.168.10.13', 8086, '', '', 'ampread', timeout=60,retries=3)
    try:
        client.create_database('ampread')
        client.write_points(json_amps)
    except ConnectionError:
        print('influxdb server not responding')
        continue

    # write voltage, rate, kW, kWh, and cost/hr to influx
    json_misc = [
        {
            "measurement": "voltage",
            "tags": {
                "tou_schedule": schedule,
                "tou": tou
            },
            "time": iso,
            "fields": {
                "voltage": LINEV,
                "rate": rate,
                "cph": cph,
                "kwh": kwh,
                "schedule": schedule,
                "kilowatts": kilowatts,
            }
        }
    ]

    client = InfluxDBClient('192.168.10.13', 8086, '', '', 'ampread', timeout=60,retries=3)
    try:
        client.create_database('ampread')
        client.write_points(json_misc)
    except ConnectionError:
        print('influxdb server not responding')
        continue
    
    # Prepare UPS values in JSON format for upload to Influxdb
    json_ups = [
        {
            "measurement": "apcaccess",
            "tags": {
                "status": STATUS,
                "upsmodel": UPSMODEL,
                "server": SERVER
            },
            #"time": iso, # Commented out, causing influxdb to not write data points
            "fields": {
                "LINEV": LINEV,
                "LOAD": LOAD,
                "BCHG": BCHG,
                "TIMELEFT": TIMELEFT,
            }
        }
    ]
    
    
    #print(values)    # uncomment for testing if values update
    
    # write values to influxdb
    client = InfluxDBClient('192.168.10.13', 8086, '', '', 'ups_stats', timeout=60,retries=3)
    try:
        client.create_database('ups_stats')
        client.write_points(json_ups)
    except ConnectionError:
        print('influxdb server not responding')
        continue

    # Wait before repeating loop
    time.sleep(20)
    time_elapsed = time.time() - start_time
    
    

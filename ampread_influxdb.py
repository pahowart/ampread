# Author Paul Howarth
# Sample program for Raspberry Pi V2 using SCT-013 current sensors and
# an adafruit ads1015 AD converter to monitor individual house panel circuit current.
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

# !/usr/bin/env python

import time
import sys
import datetime
import Adafruit_ADS1x15
import math
import holidays
from influxdb import InfluxDBClient

# Load urllib to scrape AC Mains voltage reading from APCUPSD CGI webmon page.
# There are other methods to get your utility voltage
# I just happen to have an apc ups with apcupsd already.
# If you use this method you will need to update urlStr with your apcupsd webmon url.
import urllib

urlStr = "http://192.168.10.200/cgi-bin/apcupsd/upsstats.cgi?"

# Create first ADS1015 ADC instance.
adc1 = Adafruit_ADS1x15.ADS1015(address=0x48, busnum=1)

# Create a second ADS1015 ADC instance if are using a second ADC.
adc2 = Adafruit_ADS1x15.ADS1115(address=0x49, busnum=1)

GAIN_A = 4  # see ads1015/1115 documentation for potential values.
GAIN_B = 4
samples = 200  # change this value to increase or decrease the number of samples taken
places = int(2)

# Define holidays country as Canada
ca_holidays = holidays.Canada()

# start loop to find current and utility voltage and then upload to io.adafruit sensor dashboard
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

        # since we are measuring an AC circuit the output of SCT-013 will be a sinwave.
        # in order to calculate amps from sinwave we will need to get the peak voltage
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

        # assign range values to variables used for io adafruit upload.
        ampsB0 = ampsB[0]
        ampsB1 = ampsB[1]
        ampsB2 = ampsB[2]
        ampsB3 = ampsB[3]



    except KeyboardInterrupt:
        print('You cancelled the operation.')
        sys.exit()

    # Scrape AC Mains voltage from apcupsd webmon
    # This works for apcupsd ver: 3.14.12 , but may break in other releases if page layout changes.
    # It would be better to use a parser, but that is beyond my pay grade at this point.
    fileObj = urllib.urlopen(urlStr)
    for line in fileObj:
        if 'Utility Voltage:' in line:
            startIndex = line.find(':') + 2
            endIndex = line.find(' VAC', startIndex)
            utility = line[startIndex:endIndex]
            voltage = float(utility)

    # Calculate total from all sensors and convert to kilowatts
    kilowatts = ((ampsA0 + ampsA1 + ampsA2 + ampsA3 + ampsB0 + ampsB1 + ampsB2 + ampsB3) * voltage) / 1000
    kilowatts = round(kilowatts, places)

    # Get current month, day, hour for rate schedule calculations
    date = datetime.date.today()
    month = datetime.date.today().month
    day = datetime.date.today().day
    weekday = datetime.datetime.today().weekday()
    hour = datetime.datetime.now().time()

    # Assign pricing to TOU time range by summer and winter
    # Determine if summer or winter time of use schedule is in effect.
    # Time of Use kwh electricity pricing for Ontario as of May 2018.
    offpeak = float(0.065)
    midpeak = float(0.094)
    onpeak = float(0.132)

    # These are the time ranges for time of use in Ontario as of May 2018.
    # Winter Time of Use tou_01 Schedule 7am to 11am
    # Winter Time of Use tou_02 Schedule 11am to 5pm
    # Winter Time of Use tou_03 Schedule 5pm to 7pm
    # Winter Time of Use tou_04 Schedule 7pm to 7am
    # Weekends and Holidays are always tou_04

    if 5 <= month < 11:
        tou_01 = midpeak
        tou_02 = onpeak
        tou_03 = midpeak
        tou_04 = offpeak
        schedule = "Summer"
    else:
        tou_01 = onpeak
        tou_02 = midpeak
        tou_03 = onpeak
        tou_04 = offpeak
        schedule = "Winter"

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

    # In Ontario weekends and holidays are always offpeak.
    # Check to see if it is a weekend
    if weekday == 0 or weekday >= 5:
        rate = tou_04

    # Check to see if it is a holiday.
    if date in ca_holidays:
        rate = tou_04

    # Calculate current cost per hour
    cph = float(kilowatts * rate)
    cph = round(cph, places)

    # iso = datetime.datetime.now()
    iso = datetime.datetime.utcnow().isoformat() + 'Z'

    # write all current readings to database
    # there are two separate rights to the database: one for current, and one for other misc.
    json_body = [
        {
            "measurement": "current",
            "tags": {
                "schedule": schedule,
                "rate": rate,
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

    client = InfluxDBClient('172.20.0.2', 8086, 'root', 'root', 'ampread')
    try:
        client.create_database('ampread')
        client.write_points(json_body)
    except ConnectionError:
        print('influxdb server not responding')
        break

    # write voltage and rate to database
    json_body = [
        {
            "measurement": "voltage",
            "tags": {
                "schedule": schedule,
                "rate": rate
            },
            "time": iso,
            "fields": {
                "voltage": voltage,
                "rate": rate,
                "cph": cph,
                "schedule": schedule,
                "kilowatts": kilowatts,
            }
        }
    ]
# Change the client IP address and user/password to match your instance of influxdb
    client = InfluxDBClient('172.20.0.2', 8086, 'root', 'root', 'ampread')
    try:
        client.create_database('ampread')
        client.write_points(json_body)
    except ConnectionError:
        print('influxdb server not responding')
        break
    # result = client.query('select value from voltage;')
    # print("Result: {0}".format(result))

# Wait before repeating loop
time.sleep(20)

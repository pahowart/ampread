# Author Paul Howarth
# Sample program for Raspberry Pi V2 using SCT-013 current sensors and
# an adafruit ads1015 AD converter to monitor individual house panel circuit current.
# The sensor output is then uploaded to io adafruit dashboard.
#
# Working dashboard can be seen here https://io.adafruit.com/shammie_hands/current-meter
#
# Please note that there is only basic error checking implemented. That means that if there is
# an issue with the adafruit io site this python script may error out. If you want to
# avoid this I suggest that you use upstart to restart this python script if it
# errors out.
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

import time
import datetime
import Adafruit_ADS1x15
import math

# Load urllib to scrape voltage reading from APCUPSD CGI webmon page.
# There are other methods to get your utility voltage
# I just happen to have an apc ups with apcupsd already.
# If you use this method you will need to update urlStr with your apcupsd webmon url.
import urllib
urlStr = "http://192.168.10.62/cgi-bin/apcupsd/upsstats.cgi?host=192.168.10.200&temp=C"

# This section of code is used to pull the io adafruit key from
# /etc/adafruitio.conf so it isn't exposed when distributing this code.
# to use this method your adafruitio.conf should look like the following
# [client_key]
# key = your key without quotes
import ConfigParser
config = ConfigParser.ConfigParser()
config.read("/etc/adafruitio.conf")
key = config.get("client_key", "key")

# Import adafruit io library and create instance of REST client in order to use adafruit io website.
from Adafruit_IO import Client, Data

# Create an ADS1015 ADC (12-bit) instance.
adc = Adafruit_ADS1x15.ADS1015()
GAIN = 4   # see ads1015/1115 documentation for potential values.
samples = 200  # change this value to increase or decrease the number of samples taken
places = int(2)

# Time of Use kwh electricity pricing for Ontario as of Aug 2016.
offpeak = float(0.087)
midpeak = float(0.132)
onpeak = float(0.180)

# start loop to find current and utility voltage and then upload to io.adafruit sensor dashboard
while True:
    # login to adafruit io using config file for credentials.
    # you can input your client key directly here instead of using a config file.
    # change aio = key to aio = Client('your_key_here'). Single quotes required around your key.
    try:
        aio = Client('{}'.format(key))
    except:
        print "aio login failed"
        continue

    # reset variables
    count = int(0)
    data = [0]*4
    maxValue = [0]*4
    Irms = [0]*4
    amps = [0]*4
    voltage = float(0)
    kilowatts = float(0)

    # since we are measuring an AC circuit the output of SCT-013 will be a sinwave.
    # in order to calculate amps from sinwave we will need to get the peak voltage
    # from each input and use root mean square formula (RMS)
    # this loop will take 200 samples from each input and give you the highest (peak)
    # voltage from each port on the ads1015.
    while count < samples:
        count += 1
        # nested loop to find highest sensor values from samples
        for i in range(0, 4):

            # read input A0 thru A3 from adc as absolute value
            data[i] = abs(adc.read_adc(i, gain=GAIN))

            # see if you have a new maxValue
            if data[i] > maxValue[i]:
                maxValue[i] = data[i]

        # convert maxValue sensor outputs to amps
        # I used a sct-013 that is calibrated for 1000mV output @ 30A. Usually has 30A/1V printed on it.
        for i in range(0, 4):
            Irms[i] = float(maxValue[i] / float(2047) * 30)
            Irms[i] = round(Irms[i], places)
            amps[i] = Irms[i] / math.sqrt(2)  # RMS formula to get current reading to match what an ammeter shows.
            amps[i] = round(amps[i], places)

    # assign range values to variables used for io adafruit upload.
    ampsA0 = amps[0]
    ampsA1 = amps[1]
    ampsA2 = amps[2]
    ampsA3 = amps[3]
    
    # Send a data item with value ampsA0 to the 'A0' feed
    # Assumes you have set up adafruit feed named A0 already on the io adafruit site.
    data = Data(value=ampsA0)
    try:
        aio.create_data('A0', data)
    except:
        print "A0 data upload failed"
        continue


    # Send a data item with value ampsA1 to the 'A1' feed
    # Assumes you have set up adafruit feed named A1 already on the io adafruit site.
    data = Data(value=ampsA1)
    try:
        aio.create_data('A1', data)
    except:
        print "A1 data upload failed"
        continue

         
    # placeholder for future sensors on ads1015 port A2/3

    # Scrape voltage from apcupsd webmon and send to adafruit.io
    # This works for apcupsd ver: 3.14.12 , but may break in other releases if page layout changes.
    # It would be better to use a parser, but that is beyond my pay grade at this point.
    fileObj = urllib.urlopen(urlStr)
    for line in fileObj:
        if 'Utility Voltage:' in line:
            startIndex = line.find(':') + 2
            endIndex = line.find(' VAC', startIndex)
            utility = line[startIndex:endIndex]
            voltage = float(utility)
            data = Data(value=voltage)
            try:
                aio.create_data('voltage', data)
            except:
                print "Voltage data upload failed"
                continue

    # Calculate total from all sensors kilowatts
    # I only have 2 sensors for now and therefore I have intentionally left out ampsA2 and ampsA3
    kilowatts = ((ampsA0 + ampsA1) * voltage) / 1000
    kilowatts = round(kilowatts, places)

    # Send data to the 'kilowatts' io adafruit feed.
    # Assumes you have set up adafruit feed named kilowatts already on the io adafruit site.
    data = Data(value=kilowatts)
    try:
        aio.create_data('kilowatts', data)
    except:
        print "kilowatts data upload failed"
        continue

    # Get current month, day, hour for rate schedule calculations
    month = datetime.date.today().month
    day = datetime.datetime.today().weekday()
    hour = datetime.datetime.now().time()

    # These are the time ranges for time of use in Ontario as of Aug 2016.
    # Winter Time of Use tou_01 Schedule 7am to 11am
    # Winter Time of Use tou_02 Schedule 11am to 5pm
    # Winter Time of Use tou_03 Schedule 5pm to 7pm
    # Winter Time of Use tou_04 Schedule 7pm to 7am

    # Assign pricing to TOU time range by summer and winter
    # Determine if summer or winter schedule is in effect.
    if 4 < month > 10:
        tou_01 = midpeak
        tou_02 = onpeak
        tou_03 = midpeak
        tou_04 = offpeak
        data = Data(value="Summer")
    else:
        tou_01 = onpeak
        tou_02 = midpeak
        tou_03 = onpeak
        tou_04 = offpeak
        data = Data(value="Winter")

    # Update adafruit with schedule.
    # This was added to confirm if I was getting correct TOU pricing from loop above, but is not necessary.
    # I left it in as a visual reminder on my adafruit dashboard to change laundry schedules etc
    # between summer and winter.

    try:
        aio.create_data('schedule', data)
    except:
        print "Schedule data upload failed"
        continue

    # Default rate is tou_04
    rate = tou_04

    # Check for tou_01 time range
    start = datetime.time(7, 00)
    end = datetime.time(11, 00)
    if start <= hour <= end:
        rate = tou_01

    # Check for tou_03 time range
    start = datetime.time(17, 00)
    end = datetime.time(19, 00)
    if start <= hour <= end:
        rate = tou_03

    # Check for tou_02 time range
    start = datetime.time(11, 00)
    end = datetime.time(17, 00)
    if start <= hour <= end:
        rate = tou_02

    # In Ontario weekends and holidays are always offpeak.
    # Check to see if it is a weekend
    # now = datetime.datetime.date(now)
    # print now
    if day == 0 or day >= 5:
        rate = tou_04

    # Place holder to add in a holiday calendar check and force offpeak if true.

    # Calculate current cost / hour
    kwh = float(kilowatts * rate)
    kwh = round(kwh, places)

    # Send a data item with value kwh in feed cost-per-hour
    data = Data(value=kwh)
    try:
        aio.create_data('cost-per-hour', data)
    except:
        print "Cost / Hour data upload failed"
        continue

    # Wait before repeating loop
    time.sleep(10)

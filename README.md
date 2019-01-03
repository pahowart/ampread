# ampread
Raspberry PI python script to read SCT-013 current sensors and upload to either io.adafruit or a local influxdb

I found lots of arduino projects for energy monitoring but I wanted something for the Raspberry Pi. This python code will take current and voltage readings and then calculate total kilowatts and current cost/kwh based on Ontario time of use pricing.

This project uses:

1. Raspberry Pi Model 2B, but should work on any model.

2. ADS1015 Analog Digital converter. I like this unit as it has a GAIN function built in.
 
3. SCT-013 Split winding current sensor. This is the type that is calibrated to output 1V for 30A.
 
4. APC UPS with apcupsd and multimon running to get utility AC voltage

6. InfluxDB with grafana to display dashboard

There are 2 versions: ampread_python2 (Tested on Python 2.7) and ampread_python3 (Tested on Python 3.5)
  
For the grafana dashboard you can use my docker container here: https://hub.docker.com/r/pahowart/influxdb-grafana/

You can import my grafana ampread dashboard using the "grafana ampread dashboard.json" file.

I used this project to teach myself python and therefore may not have followed all of the correct conventions. Sometimes I did things that could have been done with fewer steps in order to help myself keep track of what needed to be done.


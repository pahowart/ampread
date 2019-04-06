# ampread
Raspberry PI python script to read SCT-013 current sensors and upload to either io.adafruit or a local influxdb

I found lots of arduino projects for energy monitoring but I wanted something for the Raspberry Pi. This python code will take current and voltage readings and then calculate total kilowatts and current cost/kwh based on Ontario time of use pricing.

This project uses:

1. Raspberry Pi Model 2B, but should work on any model.

2. ADS1015 Analog Digital converter. I like this unit as it has a GAIN function built in.
 
3. SCT-013 Split winding current sensor. This is the type that is calibrated to output 1V for 30A.
 
4. UPS with APCUPSD or NUT support and network information server running to grab utility AC voltage

6. InfluxDB with grafana to display dashboard

There are 3 versions: 

1. ampread_python2 (Tested on Python 2.7 but no longer developed and 
2. ampread_python3b (Tested on Python 3.7 with APCUPSD UPS, no longer developed)
3. ampread_python3d (Tested with Python 3.7 with UPS and NUT server. current version I use)

You can import my grafana ampread dashboard using the "grafana ampread dashboard.json" file.

You will also find separate files for UPS monitoring in my other projects. 


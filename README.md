# ampread
raspi python script to read sct-013 current sensors and upload to either io.adafruit or a local influxdb

I found lots of arduino projects for energy monitoring but I wanted something for the Raspberry Pi. This python code will take current and voltage readings and then calculate total kilowatts and current cost/kwh based on Ontario time of use pricing.

This project uses:

1. Raspberry Pi Model 2B, but should work on any model.

2. ADS1015 Analog Digital converter. I like this unit as it has a GAIN function built in.
 
3. SCT-013 Split winding current sensor. This is the type that is calibrated to output 1V for 30A.
 
4. APC UPS with apcupsd and multimon running to get utility AC voltage
 
5. io.adafruit account to display sensor data or an instance of influxDB

So far there are three versions:

  i) adafruit_io with no exception handling and 
  
  ii) adafruit_io_v1d with basic exception handling and holiday schedule implemented.
  
  iii) apmread_influxdb - use with innfluxdb and grafana for graphic readout.
  
 
I have no idea how to use github correctly for version control etc. Figuring that out is for another day.

I used this project to teach myself python and therefore my not have followed all of the correct conventions. Sometimes I did things that could have been done with fewer steps in order to help myself keep track of what needed to be done.


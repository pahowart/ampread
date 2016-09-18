# ampread
raspi python script to read sct-013 current sensors and upload to io.adafruit

I found lots of arduino projects for energy monitoring but I wanted something for the Raspberry Pi.

This project uses:

1. Raspberry Pi Model 2B, but should work on any model.

2. ADS1015 Analog Digital convertor. I like this unit as it has a GAIN function built in.
 
3. SCT-013 Split winding current sensor. This is the type that is calibrated to output 1V for 30A.
 
4. io.adafruit account to display sensor data.

So far there are two versions:
  adafruit_io with no exception handling and 
  
  adafruit_iov1a with basic exception handling. 
  
I have no idea how to use github correctly for version control etc. Figuring that out is for another day.

I used this project to teach myself python and therefore my not have followed all of the correct conventions. Sometimes I did things that could have been done with fewer steps in order to help myself keep track of what needed to be done.

Eventually I will be expanding this code to include dumping the data to a remote sql database and as well as scaling it out to more sensors.

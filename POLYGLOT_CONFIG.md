## Configuration and setup

 From <https://sourceforge.net/p/raspberry-gpio-python/wiki/BasicUsage/>

>Multiple Temperature Sensors DS18B20 (tested) placed on the 2 wire bus on RPi - Vcc Pin1, GND Pin8, Data Pin7 - 4.7K Ohm resistor from pin7 to pin 1 - only one resistor is needed if multiple sensors are used 

>Use custom config parameters to name sensors in node server/ISY (not implemented yet).  Perform ls /sys/bus/w1/devices.  Devices are named 28-xxxxxxxxxxx - use this xxxxxxxxxxxx to identify sensor and add coresponding name as user config 

#### For more pinout information:
- <https://www.raspberrypi.org/documentation/usage/gpio/>
- <https://pinout.xyz/pinout/wiringpi>

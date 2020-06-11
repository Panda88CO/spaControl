#!/usr/bin/env python3

import polyinterface
import sys
import json
import RPi.GPIO as GPIO
import os
import glob
import time
import datetime
import queue
import os,subprocess
from subprocess import call
from w1thermsensor import W1ThermSensor


LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super().__init__(polyglot)
        LOGGER.info('_init_')
        self.name = 'Rpi Temp Sensors'
        self.address = 'rpitemp'
        self.primary = self.address
        try:
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
        except:
            LOGGER.info('modprobe OS calls not successful')


    def start(self):
        LOGGER.info('start - Temp Sensor controller')
        try:
            self.mySensors = W1ThermSensor()
            self.nbrSensors = len(self.mySensors.get_available_sensors())
            LOGGER.info( str(self.nbrSensors) + ' Sensors detected')
            self.discover()  
        except:
            LOGGER.info('ERROR initializing w1thermSensors ')
            #self.stop()
        self.updateInfo()

    def stop(self):
        #W1ThermSensor.get_available_sensors()
        LOGGER.info('stop - Cleaning up Temp Sensors')


    def shortPoll(self):
        LOGGER.info('shortPoll')
        for node in self.nodes:
            self.nodes[node].updateInfo()
            self.nodes[node].reportDrivers()
            
    def longPoll(self):
        LOGGER.info('longPoll')
        for node in self.nodes:
            self.nodes[node].updateInfo()
            self.nodes[node].reportDrivers()
            self.nodes[node].update24Hqueue()

    def update24Hqueue (self):
         LOGGER.info('Update24H queue')
         pass

    def updateInfo(self):
        LOGGER.info('Update Info')
        pass

    def query(self, command=None):
        LOGGER.info('querry Info')
        for node in self.nodes:
            self.nodes[node].updateInfo()
            self.nodes[node].reportDrivers()

    def discover(self, command=None):
        LOGGER.info('discover')
        count = 0
        for mySensor in self.mySensors.get_available_sensors():
            count = count+1
            currentSensor = mySensor.id.lower()
            LOGGER.debug(currentSensor)
            address = 'rpitemp'+str(count)
            #self.tempName = None
            #self.check_params()
            if currentSensor in self.polyConfig['customParams']:
               LOGGER.info('A customParams name for sensor detected')
               name = self.polyConfig['customParams'][currentSensor]
            else:
               LOGGER.debug('Default Naming')
               name = 'Sensor'+str(count)
            
            LOGGER.info( address + name + currentSensor)
            if not address in self.nodes:
               self.addNode(TEMPsensor(self, self.address, address, name, currentSensor))

    def check_params(self, command=None):
        # Looking for custom defined names - allowing sensor detection order to change and not affect ISY
        LOGGER.info('Getting Sensor Names from custom Params' )
        #i = 0 
        #for mySensor in W1ThermSensor.get_available_sensors():     
        #    i = i+1
        #    if mySensor.id in self.polyConfig['customParams']:
        #       LOGGER.info('A customParams for name for sensor detected')
        #       self.name[i] = self.polyConfig['customParams'][mySensor.id]
        #    else:
        #       self.name[i] = 'TempSensor'+str(i) 
        #       LOGGER.info('Default Sensor Name added' + self.name[i])

    id = 'RPITEMP'
    commands = {'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class TEMPsensor(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sensorID):
        super().__init__(controller, primary, address, name)
        LOGGER.info('TempSensor init' + sensorID)
        self.sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensorID )
        self.startTime = datetime.datetime.now()
        self.tempC = self.sensor.get_temperature(W1ThermSensor.DEGREES_C)
        self.tempMinC24H = self.tempC
        self.tempMaxC24H = self.tempC    
        self.queue24H = []

        LOGGER.info(sensorID + ' initialized')


    def start(self):
        LOGGER.info('TempSensor start')
        self.currentTime = datetime.datetime.now()
        self.tempC = self.sensor.get_temperature(W1ThermSensor.DEGREES_C)
        self.tempMinC24H = self.tempC
        self.tempMaxC24H = self.tempC
        self.updateInfo()
        LOGGER.info(str(self.tempC) + ' TempSensor Reading')
        return True

    def stop(self):
        LOGGER.info('STOP - Cleaning up Temp Sensors')
        #self.sensor = None



    def update24Hqueue (self):
        timeDiff = self.currentTime - self.startTime
        if timeDiff.days <= 1:
            self.queue24H.append(self.tempC)
            if self.tempC < self.tempMinC24H:
                self.tempMinC24H = self.tempC 
                LOGGER.debug('24H temp table updated Min')
            elif self.tempC > self.tempMaxC24H:
                self.tempMaxC24H = self.tempC 
                LOGGER.debug('24H temp table updated Max')
        else:
            self.queue24H.put(self.tempC)
            temp = self.queue24H.pop()
            if ((temp == self.tempMaxC24H) or (temp == self.tempMaxC24H)):
                self.tempMaxC24H = max(self.queue24H)
                self.tempMinC24H = min(self.queue24H)
                LOGGER.debug('24H temp table updated')
        pass

    def updateInfo(self):
        LOGGER.info('TempSensor updateInfo')
        self.currentTime = datetime.datetime.now()
        self.setDriver('GV0', round(float(self.tempC),1))
        self.setDriver('GV1', round(float(self.tempMinC24H),1))
        self.setDriver('GV2', round(float(self.tempMaxC24H),1))
        self.setDriver('GV3', round(self.tempC*9/5+32.0, 1))
        self.setDriver('GV4', round(self.tempMinC24H*9.0/5+32.0, 1))
        self.setDriver('GV5', round(self.tempMaxC24H*9.0/5+32.0, 1))
        self.setDriver('GV6', int(self.currentTime.strftime("%m")))
        self.setDriver('GV7', int(self.currentTime.strftime("%d")))
        self.setDriver('GV8', int(self.currentTime.strftime("%Y")))
        self.setDriver('GV9', int(self.currentTime.strftime("%H")))
        self.setDriver('GV10',int(self.currentTime.strftime("%M")))
        self.setDriver('ST', 1)
        return True                                                    
        
    def updateTemp(self, command):
        LOGGER.info('TempSensor updateTemp')
        self.tempC = self.sensor.get_temperature(W1ThermSensor.DEGREES_C)
        self.tempMinC24H = self.tempC
        self.tempMaxC24H = self.tempC
        return True

    
    def query(self, command=None):
        LOGGER.info('TempSensor querry')
        self.updateInfo()
        self.reportDrivers()

    drivers = [{'driver': 'GV0', 'value': 0, 'uom': 4},
               {'driver': 'GV1', 'value': 0, 'uom': 4},
               {'driver': 'GV2', 'value': 0, 'uom': 4},
               {'driver': 'GV3', 'value': 0, 'uom': 17},
               {'driver': 'GV4', 'value': 0, 'uom': 17},
               {'driver': 'GV5', 'value': 0, 'uom': 17},              
               {'driver': 'GV6', 'value': 0, 'uom': 47},               
               {'driver': 'GV7', 'value': 0, 'uom': 9},
               {'driver': 'GV8', 'value': 0, 'uom': 77},              
               {'driver': 'GV9', 'value': 0, 'uom': 20},              
               {'driver': 'GV10', 'value': 0, 'uom': 44},
               {'driver': 'ST', 'value': 0, 'uom': 2}              
              ]
    id = 'TEMPSENSOR'
    
    commands = { 'UPDATE': updateTemp }



if __name__ == "__main__":
#    signal.signal(signal.SIGTERM, signal_term_handler)
    try:
        LOGGER.info('Starting Server COE')
        polyglot = polyinterface.Interface('Temp_Sensors')
        
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

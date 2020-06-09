#!/usr/bin/env python3

import polyinterface
import sys
import RPi.GPIO as GPIO
import os
import glob
import time
import datetime
import os,subprocess
from subprocess import call
from w1thermsensor import W1ThermSensor

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super().__init__(polyglot)
        self.name = 'RPi_Temp_Sensors'
        self.address = 'rpitemp'
        self.primary = self.address
        
    def start(self):
        LOGGER.info('Started Temp Sensor controller')
        mySensors = W1ThermSensor()
        if len(W1ThermSensor.get_available_sensors()) == 0:
           LOGGER.debug( 'No sensors detected')
        else:
           self.nbrSensors = len(W1ThermSensor.get_available_sensors())
           LOGGER.debug( int(self.nbrSensors) + ' Sensors detected')
        self.check_params()
        self.discover()

    def stop(self):
        LOGGER.debug('Cleaning up Temp Sensors')

    def shortPoll(self):
        for node in self.nodes:
            self.nodes[node].updateInfo()
            
    def updateInfo(self):
        LOGGER.debug('Update Info')
        pass

    def query(self, command=None):
        LOGGER.debug('querry Info')
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, command=None):
        LOGGER.debug('discover')
        #for i  in W1ThermSensor.get_available_sensors():
        #    address = 'sensor'+str(i)
        #    name = self.name[i]
        #    sensorID = i.id
        #    if not address in self.nodes:
        #      self.addNode(TEMPsensor(self, self.address, address, name, sensorID))

    def check_params(self, command=None):
        # Looking for custom defined names - allowing sensor detection order to change and not affect ISY
        LOGGER.debug('Getting Sensor Names from custom Params' ) 
        #for mySensor in W1ThermSensor.get_available_sensors():     
        #    if mySensor.id in self.polyConfig['customParams']:
        #       LOGGER.debug('A customParams for name for sensor detected')
        #       self.name[i] = self.polyConfig['customParams'][mySensor.id]
        #    else:
        #       self.name[i] = 'TempSensor'+str(i) 
        #       LOGGER.debug('Default Sensor Name added')

    id = 'RPITEMP'
    commands = {'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class TEMPsensor(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sonsorIDSensor):
        super().__init__(controller, primary, address, name)
        LOGGER.debug('TempSensor init')
        #self.pinid = pinid

    def start(self):
        LOGGER.debug('TempSensor start')
        self.startTime = datetime.datetime.now()
        self.tempMinC24H = 0
        self.tempMaxC24H = 0
        self.updateInfo()
        return True

    def updateInfo(self):
        LOGGER.debug('TempSensor updateInfo')
        #self.currentTime
        #self.setDriver('GV0', self.temp)
        #self.setDriver('GV1', tempMinC24H )
        #self.setDriver('GV2', tempMaxC24H )
        #self.setDriver('GV3', round(self.temp*9/5+32.0, 1))
        #self.setDriver('GV4', round(self.tempMinC24H*9.0/5+32.0, 1))
        #self.setDriver('GV5', round(self.tempMaxC24H*9.0/5+32.0, 1))
        #self.setDriver('GV6', self.debounce_time)
        #self.setDriver('GV7', self.debounce_time)
        #self.setDriver('GV8', self.debounce_time)
        #self.setDriver('GV9', self.debounce_time)
        #self.setDriver('GV10', self.debounce_time)
        return True                                                    
        
    def updateTemp(self, command):
        LOGGER.debug('TempSensor updateTemp')
        #self.temp = 0
        return True

    
    def query(self, command=None):
        LOGGER.debug('TempSensor querry')
        #self.updateInfo()
        #self.reportDrivers()

    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2},
               {'driver': 'GV0', 'value': 0, 'uom': 4},
               {'driver': 'GV1', 'value': 0, 'uom': 4},
               {'driver': 'GV2', 'value': 0, 'uom': 4},
               {'driver': 'GV3', 'value': 0, 'uom': 17},
               {'driver': 'GV4', 'value': 0, 'uom': 17},
               {'driver': 'GV5', 'value': 0, 'uom': 17},              
               {'driver': 'GV6', 'value': 0, 'uom': 77},               
               {'driver': 'GV7', 'value': 0, 'uom': 47},
               {'driver': 'GV8', 'value': 0, 'uom': 9},              
               {'driver': 'GV9', 'value': 0, 'uom': 20},              
               {'driver': 'GV10', 'value': 0, 'uom': 44},              
              ]
    id = 'TEMPSENSOR'
    
    commands = { 'UPDATE': updateTemp }



if __name__ == "__main__":
#    signal.signal(signal.SIGTERM, signal_term_handler)
    try:
        LOGGER.info('Starting Server  COE')
        polyglot = polyinterface.Interface('TEMP_SENSORS')
        
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

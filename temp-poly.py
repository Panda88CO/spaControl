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
        self.name = 'RPi Temp Sensors'
        self.address = 'rpitemp'
        self.primary = self.address
        
    def start(self):
        LOGGER.info('Started Temp Sensor controller')
        mySensors = W1ThermSensor()
        if mySensors:
           LOGGER.info('No sensors detected')
        else:
           self.nbrSensors = len(W1ThermSensor.get_available_sensors())
        self.check_params()
        LOGGER.debug(GPIO.RPI_INFO)
        self.discover()
        LOGGER.debug(GPIO.RPI_INFO)

    def stop(self):
        LOGGER.debug('Cleaning up Temp Sensors')

    def shortPoll(self):
        for node in self.nodes:
            self.nodes[node].updateInfo()
            
    def updateInfo(self):
        pass

    def query(self, command=None):
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, command=None):
        for i  in W1ThermSensor.get_available_sensors():
            address = 'sensor'+str(i)
            name = self.name[i]
            sensorID = i.id
            if not address in self.nodes:
               self.addNode(TEMPsensor(self, self.address, address, name, sensorID))

    def check_params(self, command=None):
        # Looking for custom defined names - allowing sensor detection order to change and not affect ISY
        LOGGER.debug('Getting Sensor Names from custom Params' ) 
        for mySensor in W1ThermSensor.get_available_sensors():     
            if mySensor.id in self.polyConfig['customParams']:
               LOGGER.debug('A customParams for name for sensor detected')
               self.name[i] = self.polyConfig['customParams'][mySensor.id]
            else:
               self.name[i] = 'TempSensor'+str(i) 
               LOGGER.debug('Default Sensor Name added')

    id = 'RPI_TEMP'
    commands = {'DISCOVER': discover}
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class TEMPsensor(polyinterface.Node):
    def __init__(self, controller, primary, address, name, sonsorIDSensor):
        super().__init__(controller, primary, address, name)
        self.pinid = pinid

    def start(self):
        self.startTime = datetime.datetime.now()
        self.tempMinC24H = 0
        self.tempMaxC24H = 0
        self.updateInfo()
        return True

    def updateInfo(self):
        self.currentTime
        self.setDriver('GV0', self.temp)
        self.setDriver('GV1', tempMinC24H )
        self.setDriver('GV2', tempMaxC24H )
        self.setDriver('GV3', round(self.temp*9/5+32.0, 1))
        self.setDriver('GV4', round(self.tempMinC24H*9.0/5+32.0, 1))
        self.setDriver('GV5', round(self.tempMaxC24H*9.0/5+32.0, 1))
        self.setDriver('GV6', self.debounce_time)
        self.setDriver('GV7', self.debounce_time)
        self.setDriver('GV8', self.debounce_time)
        self.setDriver('GV9', self.debounce_time)
        self.setDriver('GV10', self.debounce_time)
        return True                                                    
        
    def updateTemp(self, command):
        self.temp = 0
        return True

    def setMode(self, command):
        cmd = command.get('cmd')
        if self.callback_set:
            LOGGER.debug('Removing all callback')
            GPIO.remove_event_detect(self.pinid)
            self.callback_set = False
            self.setDriver('GV4', 0)
        if self.pwm is not None:
            LOGGER.debug('Stopping PIN {} PWM'.format(self.pinid))
            self.pwm.stop()
            self.pwm = None
        if cmd in ['SET_INPUT', 'PULLUP', 'PULLDOWN']:
            self.mode = 1  # Input
            self.setDriver('GV0', ISY_MODES[self.mode])
            if cmd == 'PULLUP':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(self.pinid, GPIO.BOTH, callback=self._callback, bouncetime=self.debounce_time)
                self.callback_set = True
                self.setDriver('GV4', 1)
                self.st = True
            elif cmd == 'PULLDOWN':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.add_event_detect(self.pinid, GPIO.BOTH, callback=self._callback, bouncetime=self.debounce_time)
                self.callback_set = True
                self.setDriver('GV4', 1)
                self.st = False
            else:
                GPIO.setup(self.pinid, GPIO.IN)
                GPIO.add_event_detect(self.pinid, GPIO.BOTH, callback=self._callback, bouncetime=self.debounce_time)
                self.callback_set = True
                self.setDriver('GV4', 1)
        elif cmd in ['SET_INPUTS', 'PULLUPS', 'PULLDOWNS']:
            self.mode = 1  # Input
            self.setDriver('GV0', ISY_MODES[self.mode])
            if cmd == 'PULLUPS':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.st = True
            elif cmd == 'PULLDOWNS':
                GPIO.setup(self.pinid, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                self.st = False
            else:
                GPIO.setup(self.pinid, GPIO.IN)
        elif cmd in ['DON', 'DOF']:
            if self.mode != 0 or self.setup is False:  # Output
                self.mode = 0
                self.setDriver('GV0', ISY_MODES[self.mode])
                GPIO.setup(self.pinid, GPIO.OUT)
            if cmd == 'DON':
                GPIO.output(self.pinid, GPIO.HIGH)
                self.st = True
            else:
                GPIO.output(self.pinid, GPIO.LOW)
                self.st = False
        else:
            LOGGER.error('setMode: Unrecognized command {}'.format(cmd))
            return False
        self.setup = True
        self._reportSt()
        return True

    def startPWM(self, command):
        if self.callback_set:
            LOGGER.debug('Removing all callback')
            GPIO.remove_event_detect(self.pinid)
            self.callback_set = False
            self.setDriver('GV4', 0)
        query = command.get('query')
        self.pwm_dc = float(query.get('D.uom51'))
        self.pwm_freq = int(query.get('F.uom90'))
        self.setDriver('GV1', self.pwm_dc)
        self.setDriver('GV2', self.pwm_freq)
        self._pwm()
        return True

    def setPWM(self, command):
        if self.callback_set:
            LOGGER.debug('Removing all callback')
            GPIO.remove_event_detect(self.pinid)
            self.callback_set = False
        cmd = command.get('cmd')
        if self.pwm is None:
            LOGGER.info('Pin {} is not in PWM mode'.format(self.pinid))
        if cmd == 'SET_DC':
            self.pwm_dc = float(command.get('value'))
            self.setDriver('GV1', self.pwm_dc)
            if self.pwm is not None:
                self.pwm.ChangeDutyCycle(self.pwm_dc)
        elif cmd == 'SET_FREQ':
            self.pwm_freq = int(command.get('value'))
            self.setDriver('GV2', self.pwm_freq)
            if self.pwm is not None:
                self.pwm.ChangeFrequency(self.pwm_freq)
        elif cmd == 'PWM':
            self._pwm()
        else:
            LOGGER.error('setPWM: Unrecognized command {}'.format(cmd))
            return False
        return True

    def setDebounce(self, command):
        cmd = command.get('cmd')
        self.debounce_time = int(command.get('value'))
        self.setDriver('GV3', self.debounce_time)
        if self.callback_set:
            LOGGER.warning('Debounce time will change next time callback is set')

    def _reportSt(self):
        if self.pwm is not None:
            self.setDriver('ST', 4)  # PWM
        elif self.mode in [0, 1] and self.setup:
            if GPIO.input(self.pinid):
                self.setDriver('ST', 2)  # High
                if self.st is False:
                    self.reportCmd('DON')
                    self.st = True
            else:
                self.setDriver('ST', 1)  # Low
                if self.st is True:
                    self.reportCmd('DOF')
                    self.st = False
        else:
            self.setDriver('ST', 3)  # N/A

    def _reportCb(self):
        if GPIO.input(self.pinid):
            LOGGER.debug('Callback - High')
            self.reportCmd('DON')
            self.setDriver('ST', 2)  # High
            self.st = True
        else:
            LOGGER.debug('Callback - Low')
            self.reportCmd('DOF')
            self.setDriver('ST', 1)  # Low
            self.st = False

    def _pwm(self):
        LOGGER.info('Starting PIN {} PWM DC {} at {} Hz'.format(self.pinid, self.pwm_dc, self.pwm_freq))
        if self.pwm is not None:
            ''' PWM has already started '''
            self.pwm.ChangeFrequency(self.pwm_freq)
            self.pwm.ChangeDutyCycle(self.pwm_dc)
            return True
        if self.mode not in [0, 43] or self.setup is False:
            GPIO.setup(self.pinid, GPIO.OUT)
        self.mode = 43
        self.setDriver('GV0', ISY_MODES[self.mode])
        self.pwm = GPIO.PWM(self.pinid, self.pwm_freq)
        self.pwm.start(self.pwm_dc)
        self.st = False
        self._reportSt()
        return True

    def query(self, command=None):
        self.updateInfo()
        self.reportDrivers()

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
    id = 'TEMP_SENSOR'
    
    commands = { 'UPDATE': updateTemp }

#def signal_term_handler(signal, frame):
#    LOGGER.warning('Got SIGTERM, exiting...')
#    GPIO.cleanup()
#    sys.exit(0)


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

#-------------------------------------------------------------------------------
# Name:        ModSlaveSim
# Purpose:
#
# Author:      elbar
#
# Created:     26/03/2012
# Copyright:   (c) elbar 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from PyQt5 import QtCore
#repeated timer
import RepeatTimer as rt
import random
#modbus toolkit
import modbus_tk.defines as cst
import modbus_tk.modbus_tcp as modbus_tcp
import modbus_tk.modbus_rtu as modbus_rtu
from modbus_tk.hooks import install_hook
#serial communication
import serial
#data model
from ModSlaveMBDataModel import ModSlaveMBDataModel
#add logging capability
import logging

#Hooks
SERVER_HOOKS = ("modbus.Server.before_handle_request", "modbus.Server.after_handle_request")

#-------------------------------------------------------------------------------
def ModSvrFactory(args):
    """ modFactory : rtu or tcp server holding several slaves """

    logger = logging.getLogger("modbus_tk")

    _svr = None

    if args[0]=='-tcp':
        logger.info("Build TCP Server - {0}:{1}".format(args[2],args[1]))
        try :
            # remove extra zeros from ip addr
            _ip = args[2]
            _ip = _ip.split('.')
            _ip = str(int(_ip[0])) + "." + str(int(_ip[1])) + "." + str(int(_ip[2])) + "." + str(int(_ip[3]))
            _svr = modbus_tcp.TcpServer(int(args[1]), _ip)
        except Exception as err:
            logger.error("Error while building TCP Server : {0}".format(err))
    elif args[0]=='-rtu':
        logger.info("Build RTU Server - Port: {0}, Baudrate: {1}, Bytesize: {2}, Parity: {3}, Stopbits : {4}"
                    .format(args[1],args[2],args[3],args[4],args[5]))
        try:
            _svr = modbus_rtu.RtuServer(serial.Serial(port=args[1],
                                                        baudrate=int(args[2]),
                                                        bytesize=int(args[3]),
                                                        parity=args[4],
                                                        stopbits=float(args[5]),
                                                        xonxoff=0))
        except Exception as err:
            logger.error("Error while building RTU Server : {0}".format(err))
    else:
        logger.error("Wrong arguments")

    return _svr
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
class ModSlave(QtCore.QObject):
    """ modbus slave """

    def __init__(self, modSvr, slaveAddress, timeIntervalSim, sim_min = 0, sim_max= 65535,
                    start_addr_coils = 0 ,no_coils = 10,
                    start_addr_dis_inputs = 0, no_dis_inputs = 10,
                    start_addr_input_regs = 0, no_input_regs = 10,
                    start_addr_hold_regs = 0, no_hold_regs = 10,):
        super(ModSlave,self).__init__()
        self._sim_interval = timeIntervalSim
        self._sim_min = sim_min
        self._sim_max = sim_max
        self._start_addr_coils = start_addr_coils
        self._no_coils = no_coils
        self._start_addr_dis_inputs = start_addr_dis_inputs
        self._no_dis_inputs = no_dis_inputs
        self._start_addr_input_regs = start_addr_input_regs
        self._no_input_regs = no_input_regs
        self._start_addr_hold_regs = start_addr_hold_regs
        self._no_hold_regs = no_hold_regs
        self._logger = logging.getLogger("modbus_tk")
        # data models
        self.coils_data_model = ModSlaveMBDataModel(start_addr_coils, no_coils, 0)
        self.coils_data_model.update_data.connect(self.set_coils_data)
        self.dis_inputs_data_model = ModSlaveMBDataModel(start_addr_dis_inputs, no_dis_inputs, 0)
        self.dis_inputs_data_model.update_data.connect(self.set_dis_inputs_data)
        self.input_regs_data_model = ModSlaveMBDataModel(start_addr_input_regs, no_input_regs, 0)
        self.input_regs_data_model.update_data.connect(self.set_input_regs_data)
        self.hold_regs_data_model = ModSlaveMBDataModel(start_addr_hold_regs, no_hold_regs, 0)
        self.hold_regs_data_model.update_data.connect(self.set_hold_regs_data)
        #install hooks
        install_hook(SERVER_HOOKS[1], self._update)

        try:
            #add slave
            self.slave= modSvr.add_slave(slaveAddress)
            #add blocks
            self.slave.add_block('0', cst.COILS , start_addr_coils, no_coils)
            self.slave.add_block('1', cst.DISCRETE_INPUTS, start_addr_dis_inputs, no_dis_inputs)
            self.slave.add_block('3', cst.ANALOG_INPUTS , start_addr_input_regs, no_input_regs)
            self.slave.add_block('4', cst.HOLDING_REGISTERS, start_addr_hold_regs, no_hold_regs)
            #create timer -> repeat timer
            self._sim_timer=rt.RepeatTimer(timeIntervalSim,self._blockValues,0)
        except Exception as err:
            self._logger.error("Slave Init Error : {0}".format(err))

        #update data
        self._blockValues()

    def start_sim(self):
        self._logger.info("Slave sim timer started")
        self._sim_timer.start()

    def stop_sim(self):
        self._logger.info("Slave sim timer stopped")
        self._sim_timer.cancel()

    def _update(self, data):
        '''update mbdata on receiving'''
        #update model data
        self.coils_data_model.update_model(self.get_coils_data())
        self.hold_regs_data_model.update_model(self.get_hold_regs_data())

    def _blockValues(self):
        #simulate then update
        #coils
        if (self.coils_data_model.sim):
            block0 = []  # coils
            for i in range(0,self._no_coils):
                block0.append(random.randrange(0,2,1))
            self.set_coils_data(block0)
        #discrete inputs
        if (self.dis_inputs_data_model.sim):
            block1 = []  # discrete inputs
            for i in range(0,self._no_dis_inputs):
                block1.append(random.randrange(0,2,1))
            self.set_dis_inputs_data(block1)
        #input registers
        if (self.input_regs_data_model.sim):
            block3 = []  # input registers
            for i in range(0,self._no_input_regs):
                block3.append(random.randrange(self._sim_min,self._sim_max,1))
            self.set_input_regs_data(block3)
        #holding registers
        if (self.hold_regs_data_model.sim):
            block4 = []  # holding registers
            for i in range(0,self._no_hold_regs):
                block4.append(random.randrange(self._sim_min,self._sim_max,1))
            self.set_hold_regs_data(block4)
        #update model data
        self.coils_data_model.update_model(self.get_coils_data())
        self.dis_inputs_data_model.update_model(self.get_dis_inputs_data())
        self.input_regs_data_model.update_model(self.get_input_regs_data())
        self.hold_regs_data_model.update_model(self.get_hold_regs_data())

    def get_coils_data(self):
        return self.slave.get_values('0', self._start_addr_coils, self._no_coils)

    def set_coils_data(self, data):
        self.slave.set_values('0', self._start_addr_coils, data)

    def get_dis_inputs_data(self):
        return self.slave.get_values('1', self._start_addr_dis_inputs, self._no_dis_inputs)

    def set_dis_inputs_data(self, data):
        self.slave.set_values('1', self._start_addr_dis_inputs, data)

    def get_input_regs_data(self):
        return self.slave.get_values('3', self._start_addr_input_regs, self._no_input_regs)

    def set_input_regs_data(self, data):
        self.slave.set_values('3', self._start_addr_input_regs, data)

    def get_hold_regs_data(self):
        return self.slave.get_values('4', self._start_addr_hold_regs, self._no_hold_regs)

    def set_hold_regs_data(self, data):
        self.slave.set_values('4', self._start_addr_hold_regs, data)

#-------------------------------------------------------------------------------

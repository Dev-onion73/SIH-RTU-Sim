#-------------------------------------------------------------------------------
# Name:        ModSlaveSettingsRTU
# Purpose:
#
# Author:      ElBar
#
# Created:     17/04/2012
# Copyright:   (c) ElBar 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from PyQt5 import QtGui,QtCore,QtWidgets
from Ui_settingsModbusRTU import Ui_SettingsModbusRTU
import os

import Utils
#add logging capability
import logging

#-------------------------------------------------------------------------------
class ModSlaveSettingsRTUWindow(QtWidgets.QDialog):
    """ Class wrapper for RTU settings ui """

    def __init__(self):
        super(ModSlaveSettingsRTUWindow,self).__init__()
        #init value
        if os.name == 'nt':  # windows
            self.rtu_dev = 'COM'
        else:  # linux?
            self.rtu_dev = '/dev/ttyS'
        self.rtu_port = 1
        self.baud_rate = 9600
        self.byte_size = 8
        self.parity = 'None'
        self.stop_bits = '1'
        self._logger = logging.getLogger("modbus_tk")
        self.setupUI()

    def setupUI(self):
        #create window from ui
        self.ui=Ui_SettingsModbusRTU()
        self.ui.setupUi(self)
        if os.name == 'nt':  # windows
            self.ui.cmbDev.setEnabled(False)
            self.ui.cmbPort.setMinimum(1)
        else: # linux?
            self.ui.cmbDev.setEnabled(True)
            self.ui.cmbPort.setMinimum(0)
        #set init values
        self._set_values()
        #signals-slots
        self.accepted.connect(self._OK_pressed)
        self.rejected.connect(self._cancel_pressed)

    def _set_values(self):
        """set param values to ui"""
        self._logger.info("Set param values to UI")
        self.ui.cmbDev.setEditText(self.rtu_dev)
        self.ui.cmbPort.setValue(self.rtu_port)
        self.ui.cmbBaud.setCurrentIndex(self.ui.cmbBaud.findText(str(self.baud_rate)))
        self.ui.cmbDataBits.setCurrentIndex(self.ui.cmbDataBits.findText(str(self.byte_size)))
        self.ui.cmbParity.setCurrentIndex(self.ui.cmbParity.findText(self.parity))
        self.ui.cmbStopBits.setCurrentIndex(self.ui.cmbStopBits.findText(str(self.stop_bits)))

    def _get_values(self):
        """get param values from ui"""
        self._logger.info("Get param values from UI")
        self.rtu_dev = self.ui.cmbDev.currentText()
        self.rtu_port = self.ui.cmbPort.value()
        self.baud_rate = self.ui.cmbBaud.currentText()
        self.byte_size = self.ui.cmbDataBits.currentText()
        self.parity = self.ui.cmbParity.currentText()
        self.stop_bits = self.ui.cmbStopBits.currentText()

    def _OK_pressed(self):
        """new values are accepted"""
        self._get_values()

    def _cancel_pressed(self):
        """new values are rejected"""
        self._set_values()

    def showEvent(self,QShowEvent):
        """set values for controls"""
        self._set_values()

#-------------------------------------------------------------------------------
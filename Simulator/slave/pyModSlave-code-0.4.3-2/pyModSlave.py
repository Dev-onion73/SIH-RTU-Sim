#-------------------------------------------------------------------------------
# Name:        pyModSlaveQt
# Purpose:
#
# Author:      ElBar
#
# Created:     29/02/2012
# Copyright:   (c) ElBar 2012
# Licence:     <your licence>
# Logging Levels
# CRITICAL : 50
# ERROR : 40
# WARNING : 30
# INFO : 20
# DEBUG : 10
# NOTSET : 0
#
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import sys
import os
import subprocess
import webbrowser
from PyQt5 import QtGui,QtWidgets
import logging # add logging capability
import configparser # config file parser

from Ui_mainwindow import Ui_MainWindow
from ModSlaveAbout import ModSlaveAboutWindow
from ModSlaveSettingsRTU import ModSlaveSettingsRTUWindow
from ModSlaveSettingsTCP import ModSlaveSettingsTCPWindow
from ModSlaveSettings import ModSlaveSettingsWindow
from ModSlaveMBData import ModSlaveMBData
from ModSlaveMBDataModel import ModSlaveMBDataModel
from ModSlaveBusMonitor import ModSlaveBusMonitorWindow

#modbus toolkit
import modbus_tk
import ModFactory as modFactory
import Utils

#-------------------------------------------------------------------------------
class ModSlaveMainWindow(QtWidgets.QMainWindow):
    """ Class wrapper for main window ui """

    def __init__(self):
        super(ModSlaveMainWindow,self).__init__()
        #init
        self.svr = None # Server hosting one or more slaves
        self._svr_args = []
        self.slv = None # Slave
        self._coils = 10
        self._coils_start_addr = 0
        self._inputs = 10
        self._inputs_start_addr = 0
        self._input_regs = 10
        self._input_regs_start_addr = 0
        self._hold_regs = 10
        self._hold_regs_start_addr = 0
        self._time_interval = 2000 # interval for simulation in msec
        self._modbus_mode = 1 # 1:RTU, 2:TCP
        self._modbus_slave_ID = 1
        self._logging_level = 30 # warning level
        self._params_file_name = 'pyModSlave.ini'
        self._logger = logging.getLogger("modbus_tk")
        self._logger.setLevel(0) # start with no logging
        self._setupUI()

    def _setupUI(self):
        #create window from ui
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        #setup toolbar
        self.ui.mainToolBar.addAction(self.ui.actionLoad_Session)
        self.ui.mainToolBar.addAction(self.ui.actionSave_Session)
        self.ui.mainToolBar.addAction(self.ui.actionConnect)
        self.ui.mainToolBar.addAction(self.ui.actionReset_Counters)
        self.ui.mainToolBar.addSeparator()
        self.ui.mainToolBar.addAction(self.ui.actionLog)
        self.ui.mainToolBar.addAction(self.ui.actionBus_Monitor)
        self.ui.mainToolBar.addAction(self.ui.actionHeaders)
        self.ui.mainToolBar.addSeparator()
        self.ui.mainToolBar.addAction(self.ui.actionSerial_RTU)
        self.ui.mainToolBar.addAction(self.ui.actionTCP)
        self.ui.mainToolBar.addAction(self.ui.actionSettings)
        self.ui.mainToolBar.addSeparator()
        self.ui.mainToolBar.addAction(self.ui.actionModbus_Manual)
        self.ui.mainToolBar.addAction(self.ui.actionAbout)
        self.ui.mainToolBar.addAction(self.ui.actionExit)
        #setup status bar
        pm = QtGui.QPixmap()
        self.status_ind = QtWidgets.QLabel(self.ui.centralWidget)
        self.status_ind.setFixedSize(16,16)
        self.status_ind.setPixmap(QtGui.QPixmap(':/img/bullet-red-16.png'))
        self.status_text = QtWidgets.QLabel(self.ui.centralWidget)
        self.status_packet_text = QtWidgets.QLabel(self.ui.centralWidget)
        self.status_packet_text.setStyleSheet("QLabel {color:blue;}")
        self.status_error_text = QtWidgets.QLabel(self.ui.centralWidget)
        self.status_error_text.setStyleSheet("QLabel {color:red;}")
        self.ui.statusBar.addWidget(self.status_ind)
        self.ui.statusBar.addWidget(self.status_text, 14)
        self.ui.statusBar.addWidget(self.status_packet_text, 14)
        self.ui.statusBar.addWidget(self.status_error_text, 14)
        #setup ui dialogs
        self._about_dlg = ModSlaveAboutWindow()
        self._settingsRTU_dlg = ModSlaveSettingsRTUWindow()
        self._settingsTCP_dlg = ModSlaveSettingsTCPWindow()
        self._settings_dlg = ModSlaveSettingsWindow()
        self._bus_monitor_dlg = ModSlaveBusMonitorWindow(self)
        #setup data controller
        self._mbdata_ctrl = ModSlaveMBData(self.ui)
        #signals-slots
        self.ui.actionLoad_Session.triggered.connect(self._load_session)
        self.ui.actionSave_Session.triggered.connect(self._save_session)
        self.ui.actionAbout.triggered.connect(self._about_dlg.show)
        self.ui.actionSerial_RTU.triggered.connect(self._settings_RTU_show)
        self.ui.actionTCP.triggered.connect(self._settings_TCP_show)
        self.ui.actionSettings.triggered.connect(self._settings_show)
        self.ui.actionBus_Monitor.triggered.connect(self._bus_monitor_show)
        self.ui.actionReset_Counters.triggered.connect(self._reset_counters)
        self.ui.actionLog.triggered.connect(self._open_log_file)
        self.ui.actionHeaders.triggered.connect(self._showHeaders)
        self.ui.actionModbus_Manual.triggered.connect(self._open_modbus_manual)
        self.ui.actionConnect.triggered.connect(self._start_stop)
        self.ui.cmbModbusMode.currentIndexChanged.connect(self._update_status_bar)
        self.ui.spInterval.valueChanged.connect(self._spInterval_value_changed)
        self._bus_monitor_dlg.update_counters.connect(self._update_counters)
        self.ui.cmbModbusMode.currentIndexChanged.connect(self._update_modbus_mode)
        #show window
        self._update_status_bar()
        self.show()

    def _settings_RTU_show(self):
        """open RTU settings dialog"""
        self._settingsRTU_dlg.ui.cmbPort.setEnabled(self.svr == None)
        self._settingsRTU_dlg.ui.cmbDev.setEnabled(self.svr == None)
        self._settingsRTU_dlg.ui.cmbBaud.setEnabled(self.svr == None)
        self._settingsRTU_dlg.ui.cmbDataBits.setEnabled(self.svr == None)
        self._settingsRTU_dlg.ui.cmbParity.setEnabled(self.svr == None)
        self._settingsRTU_dlg.ui.cmbStopBits.setEnabled(self.svr == None)
        self._settingsRTU_dlg.exec_()
        self._update_status_bar()

    def _settings_TCP_show(self):
        """open TCP settings dialog"""
        self._settingsTCP_dlg.ui.leIP.setEnabled(self.svr == None)
        self._settingsTCP_dlg.ui.leTCPPort.setEnabled(self.svr == None)
        self._settingsTCP_dlg.exec_()
        self._update_status_bar()

    def _settings_show(self):
        """open general settings dialog"""
        self._settings_dlg.ui.sbMaxNoOfBusMonitorLines.setEnabled(self.svr == None)
        self._settings_dlg.ui.sbSimMin.setEnabled(self.svr == None)
        self._settings_dlg.ui.sbSimMax.setEnabled(self.svr == None)
        self._settings_dlg.exec_()
        self._bus_monitor_dlg.set_max_no_of_bus_monitor_lines(self._settings_dlg.max_no_of_bus_monitor_lines)
        self._update_status_bar()

    def _mbdata_show(self):
        """coils data dialog"""
        self._mbdata_dlg.show()

    def _bus_monitor_show(self):
        """coils data dialog"""
        self._bus_monitor_dlg.svr = self.svr
        self._bus_monitor_dlg.move(self.x() + self.width() + 20, self.y())
        self._bus_monitor_dlg.show()

    def _spInterval_value_changed(self,value):
        """sim interval value changed"""
        self._time_interval = value

    def _update_status_bar(self):
        """update status bar"""
        if (self.ui.cmbModbusMode.currentText() == "TCP"):#TCP server
            msg = "TCP : {0}:{1}".format(self._settingsTCP_dlg.tcp_ip,
                                        self._settingsTCP_dlg.tcp_port)
        elif (self.ui.cmbModbusMode.currentText() == "RTU"):#RTU server
            msg = "RTU : {0}, {1}, {2}, {3}, {4}".format(self._settingsRTU_dlg.rtu_port,
                                                    self._settingsRTU_dlg.baud_rate,
                                                    self._settingsRTU_dlg.byte_size,
                                                    self._settingsRTU_dlg.stop_bits,
                                                    self._settingsRTU_dlg.parity)
        self.status_text.setText(msg)
        if (self.svr != None):#server is running
            self.status_ind.setPixmap(QtGui.QPixmap(':/img/bullet-green-16.png'))
        else:#server is stopped
            self.status_ind.setPixmap(QtGui.QPixmap(':/img/bullet-red-16.png'))
        self._update_counters()

    def _update_counters(self):
        """update packets - errors counters"""
        self.status_packet_text.setText('Packets : %d' % self._bus_monitor_dlg.packets)
        self.status_error_text.setText('Erros : %d' % self._bus_monitor_dlg.errors)

    def _showHeaders(self, value):
        """show/hide headers"""
        if (value):#show
            self.ui.tvCoilsData.horizontalHeader().show()
            self.ui.tvCoilsData.verticalHeader().show()
            self.ui.tvDiscreteInputsData.horizontalHeader().show()
            self.ui.tvDiscreteInputsData.verticalHeader().show()
            self.ui.tvInputRegistersData.horizontalHeader().show()
            self.ui.tvInputRegistersData.verticalHeader().show()
            self.ui.tvHoldingRegistersData.horizontalHeader().show()
            self.ui.tvHoldingRegistersData.verticalHeader().show()
        else:#hide
            self.ui.tvCoilsData.horizontalHeader().hide()
            self.ui.tvCoilsData.verticalHeader().hide()
            self.ui.tvDiscreteInputsData.horizontalHeader().hide()
            self.ui.tvDiscreteInputsData.verticalHeader().hide()
            self.ui.tvInputRegistersData.horizontalHeader().hide()
            self.ui.tvInputRegistersData.verticalHeader().hide()
            self.ui.tvHoldingRegistersData.horizontalHeader().hide()
            self.ui.tvHoldingRegistersData.verticalHeader().hide()

    def _update_ui(self):
        """update enable-disable status of ui components"""
        if (self.ui.actionConnect.isChecked()):#start
            self.ui.actionLoad_Session.setEnabled(False)
            self.ui.actionSave_Session.setEnabled(False)
            self.ui.cmbModbusMode.setEnabled(False)
            self.ui.sbSlaveID.setEnabled(False)
            self.ui.spInterval.setEnabled(False)
            self.ui.sbNoOfCoils.setEnabled(False)
            self.ui.sbCoilsStartAddr.setEnabled(False)
            self.ui.sbNoOfDigInputs.setEnabled(False)
            self.ui.sbDigInputsstartAddr.setEnabled(False)
            self.ui.sbNoOfHoldingRegs.setEnabled(False)
            self.ui.sbHoldingRegsStartAddr.setEnabled(False)
            self.ui.sbNoOfInputRegs.setEnabled(False)
            self.ui.sbInputRegsStartAddr.setEnabled(False)
        else:#stop
            self.ui.actionLoad_Session.setEnabled(True)
            self.ui.actionSave_Session.setEnabled(True)
            self.ui.cmbModbusMode.setEnabled(True)
            self.ui.sbSlaveID.setEnabled(True)
            self.ui.spInterval.setEnabled(True)
            self.ui.sbNoOfCoils.setEnabled(True)
            self.ui.sbCoilsStartAddr.setEnabled(True)
            self.ui.sbNoOfDigInputs.setEnabled(True)
            self.ui.sbDigInputsstartAddr.setEnabled(True)
            self.ui.sbNoOfHoldingRegs.setEnabled(True)
            self.ui.sbHoldingRegsStartAddr.setEnabled(True)
            self.ui.sbNoOfInputRegs.setEnabled(True)
            self.ui.sbInputRegsStartAddr.setEnabled(True)
            _empty_model = self.coils_data_model = ModSlaveMBDataModel(0, 0, 0)
            self._mbdata_ctrl.set_data_models(_empty_model,_empty_model,_empty_model,_empty_model)

    def _start_stop(self):
        """start - stop server and slave"""
        self._reset_counters()
        del self._svr_args[:]#clear params
        svr_hooks = []
        if (self.ui.actionConnect.isChecked()):#start
            if (self.ui.cmbModbusMode.currentText() == "TCP"): # TCP server params
                self._logger.info("Starting TCP server")
                self._svr_args.append("-tcp")
                self._svr_args.append(self._settingsTCP_dlg.tcp_port)
                self._svr_args.append(self._settingsTCP_dlg.tcp_ip)
            elif (self.ui.cmbModbusMode.currentText() == "RTU"): # RTU server params
                self._logger.info("Starting RTU server")
                self._svr_args.append("-rtu")
                if os.name == 'nt': #windows
                    self._svr_args.append("COM" + str(self._settingsRTU_dlg.rtu_port))
                else: #linux?
                    self._svr_args.append(self._settingsRTU_dlg.rtu_dev + str(self._settingsRTU_dlg.rtu_port))
                self._svr_args.append(self._settingsRTU_dlg.baud_rate)
                self._svr_args.append(self._settingsRTU_dlg.byte_size)
                self._svr_args.append(self._settingsRTU_dlg.parity[0])
                self._svr_args.append(self._settingsRTU_dlg.stop_bits)
            if (len(self._svr_args) > 0): # check for valid no of parameters
                self.svr = modFactory.ModSvrFactory(self._svr_args)
                if (self.svr == None):#fail to build server
                    self._logger.error("Fail to start server")
                    Utils.errorMessageBox("Fail to start server")
                    self.ui.actionConnect.setChecked(False)
                else:
                    self.svr.start()
                    self.slv = modFactory.ModSlave(self.svr, self.ui.sbSlaveID.value(),
                                                   self.ui.spInterval.value() / 1000.0, 
                                                   self._settings_dlg.sim_min, self._settings_dlg.sim_max,
                                                   self.ui.sbCoilsStartAddr.value(), self.ui.sbNoOfCoils.value(),
                                                   self.ui.sbDigInputsstartAddr.value(), self.ui.sbNoOfDigInputs.value(),
                                                   self.ui.sbInputRegsStartAddr.value(), self.ui.sbNoOfInputRegs.value(),
                                                   self.ui.sbHoldingRegsStartAddr.value(), self.ui.sbNoOfHoldingRegs.value())
                    if (self.slv == None):#fail to build slave
                        self._logger.error("Fail to start slave")
                        Utils.errorMessageBox("Fail to start slave")
                        self.svr.stop()
                        self.svr = None
                        self.ui.actionConnect.setChecked(False)
                    else:
                        self._mbdata_ctrl.set_data_models(self.slv.coils_data_model,
                                                         self.slv.dis_inputs_data_model,
                                                         self.slv.input_regs_data_model,
                                                         self.slv.hold_regs_data_model)
                        self.slv.start_sim()
        else:#stop
            self._logger.info("Stop server")
            self.slv.stop_sim()
            self.svr.stop()
            self.slv = None
            self.svr = None
        #update user interface
        self._update_ui()
        self._update_status_bar()

    def _load_params(self, fname):
        self._logger.info("Load params")
        config_tcp_defaut = {'TCP_Port':'502', 'TCP_IP':'127.000.000.001'}
        if os.name == 'nt':  # windows
            config_rtu_defaut = {'RTU_Dev':'COM', 'RTU_Port':'0', 'Baud':'9600', 'DataBits':'8', 'StopBits':'1', 'Parity':'None'}
        else:  # linux?
            config_rtu_defaut = {'RTU_Dev': '/dev/ttyS', 'RTU_Port': '0', 'Baud': '9600', 'DataBits': '8', 'StopBits': '1', 'Parity': 'None'}
        config_var_defaut = {'Coils':'10', 'CoilsStartAddr':'0', 'DisInputs':'10', 'DisInputsStartAddr':'0',
                             'InputRegs':'10', 'InputRegsStartAddr':'0','HoldRegs':'10', 'HoldRegsStartAddr':'0',
                             'TimeInterval':'1000', 'MaxNoOfBusMonitorLines':'50', 'ModbusMode':'1', 'ModbusSlaveID':'1',
                             'LoggingLevel':'30', 'SimMin':'0', 'SimMax':'65535'}
        config_default = {}
        config_default.update(config_tcp_defaut)
        config_default.update(config_rtu_defaut)
        config_default.update(config_var_defaut)
        config = configparser.ConfigParser(config_default)
        if not(config.read(fname)):#if file does not exist exit
            self._logger.error("Parameters file does not exist")
            return
        #TCP Settings
        self._settingsTCP_dlg.tcp_port = config.getint('TCP', 'TCP_Port')
        self._settingsTCP_dlg.tcp_ip = config.get('TCP', 'TCP_IP')
        #RTU Settings
        self._settingsRTU_dlg.rtu_dev = config.get('RTU', 'RTU_Dev')
        self._settingsRTU_dlg.rtu_port = config.getint('RTU', 'RTU_Port')
        self._settingsRTU_dlg.baud_rate = config.getint('RTU', 'Baud')
        self._settingsRTU_dlg.byte_size = config.getint('RTU', 'DataBits')
        self._settingsRTU_dlg.stop_bits = config.get('RTU', 'StopBits')
        self._settingsRTU_dlg.parity = config.get('RTU', 'Parity')
        #Var Settings
        self._coils = config.getint('Var', 'Coils')
        self._coils_start_addr = config.getint('Var', 'CoilsStartAddr')
        self._inputs = config.getint('Var', 'DisInputs')
        self._inputs_start_addr = config.getint('Var', 'DisInputsStartAddr')
        self._input_regs = config.getint('Var', 'InputRegs')
        self._input_regs_start_addr = config.getint('Var', 'InputRegsStartAddr')
        self._hold_regs = config.getint('Var', 'HoldRegs')
        self._hold_regs_start_addr = config.getint('Var', 'HoldRegsStartAddr')
        self._time_interval = config.getint('Var', 'TimeInterval')
        self._settings_dlg.max_no_of_bus_monitor_lines = config.getint('Var', 'MaxNoOfBusMonitorLines')
        self._settings_dlg.sim_min = config.getint('Var', 'SimMin')
        self._settings_dlg.sim_max = config.getint('Var', 'SimMax')
        self._bus_monitor_dlg.set_max_no_of_bus_monitor_lines(self._settings_dlg.max_no_of_bus_monitor_lines)
        self._modbus_mode = config.getint('Var', 'ModbusMode')
        self._modbus_slave_ID = config.getint('Var', 'ModbusSlaveID')
        self._logging_level = config.getint('Var', 'LoggingLevel')
        self._logger.setLevel(self._logging_level)
        #update ui
        self.ui.sbNoOfCoils.setValue(self._coils)
        self.ui.sbCoilsStartAddr.setValue(self._coils_start_addr)
        self.ui.sbNoOfDigInputs.setValue(self._inputs)
        self.ui.sbDigInputsstartAddr.setValue(self._inputs_start_addr)
        self.ui.sbNoOfHoldingRegs.setValue(self._hold_regs)
        self.ui.sbHoldingRegsStartAddr.setValue(self._hold_regs_start_addr)
        self.ui.sbNoOfInputRegs.setValue(self._input_regs)
        self.ui.sbInputRegsStartAddr.setValue(self._input_regs_start_addr)
        self.ui.spInterval.setValue(self._time_interval)
        self.ui.cmbModbusMode.setCurrentIndex(self._modbus_mode)
        self.ui.sbSlaveID.setValue(self._modbus_slave_ID)

    def _save_params(self, fname):
        self._logger.info("Save params")
        #update params from ui
        self._coils = self.ui.sbNoOfCoils.value()
        self._coils_start_addr = self.ui.sbCoilsStartAddr.value()
        self._inputs = self.ui.sbNoOfDigInputs.value()
        self._inputs_start_addr = self.ui.sbDigInputsstartAddr.value()
        self._hold_regs = self.ui.sbNoOfHoldingRegs.value()
        self._hold_regs_start_addr = self.ui.sbHoldingRegsStartAddr.value()
        self._input_regs = self.ui.sbNoOfInputRegs.value()
        self._input_regs_start_addr = self.ui.sbInputRegsStartAddr.value()
        self._modbus_mode = self.ui.cmbModbusMode.currentIndex()
        self._modbus_slave_ID = self.ui.sbSlaveID.value()
        config = configparser.ConfigParser()
        #TCP Settings
        config.add_section('TCP')
        config.set('TCP','TCP_Port',str(self._settingsTCP_dlg.tcp_port))
        config.set('TCP','TCP_IP',self._settingsTCP_dlg.tcp_ip)
        #RTU Settings
        config.add_section('RTU')
        config.set('RTU','RTU_Dev', self._settingsRTU_dlg.rtu_dev)
        config.set('RTU','RTU_Port',str(self._settingsRTU_dlg.rtu_port))
        config.set('RTU','Baud',str(self._settingsRTU_dlg.baud_rate))
        config.set('RTU','DataBits',str(self._settingsRTU_dlg.byte_size))
        config.set('RTU','StopBits',str(self._settingsRTU_dlg.stop_bits))
        config.set('RTU','Parity',self._settingsRTU_dlg.parity)
        #Var Settings
        config.add_section('Var')
        config.set('Var','Coils',str(self._coils))
        config.set('Var','CoilsStartAddr',str(self._coils_start_addr))
        config.set('Var','DisInputs',str(self._inputs))
        config.set('Var','DisInputsStartAddr', str(self._inputs_start_addr))
        config.set('Var','InputRegs',str(self._input_regs))
        config.set('Var','InputRegsStartAddr', str(self._input_regs_start_addr))
        config.set('Var','HoldRegs',str(self._hold_regs))
        config.set('Var','HoldRegsStartAddr', str(self._hold_regs_start_addr))
        config.set('Var','TimeInterval', str(self._time_interval))
        config.set('Var','MaxNoOfBusMonitorLines', str(self._settings_dlg.max_no_of_bus_monitor_lines))
        config.set('Var','SimMin', str(self._settings_dlg.sim_min))
        config.set('Var','SimMax', str(self._settings_dlg.sim_max))
        config.set('Var','ModbusMode', str(self._modbus_mode))
        config.set('Var','ModbusSlaveID', str(self._modbus_slave_ID))
        config.set('Var','LoggingLevel', str(self._logging_level))
        #Save Settings
        config_file = open(fname, 'w')
        config.write(config_file)

    def _load_session(self):
        cwd = os.getcwd()
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Load Session file", cwd, "Session Files (*.ses);;All Files (*.*)")
        if (file_path[0] != ''):
            self._logger.info("Load session : " + file_path[0])
            self._load_params(os.path.abspath(file_path[0]))

    def _save_session(self):
        cwd = os.getcwd()
        file_path = QtWidgets.QFileDialog.getSaveFileName(self, "Save Session file", cwd, "Session Files (*.ses)")
        if (file_path[0] != ''):
            self._logger.info("Save session : " + file_path[0])
            self._save_params(os.path.abspath(file_path[0]))

    def _reset_counters(self):
        self._bus_monitor_dlg.reset_counters()

    def _update_modbus_mode(self, index):
        if (index == 0):# RTU
            self.ui.lblSlave.setText('Slave Addr')
            #self.ui.sbSlaveID.setVisible(True)
        elif (index == 1):# TCP
            self.ui.lblSlave.setText('Unit ID')
            #self.ui.sbSlaveID.setVisible(False)

    def _open_log_file(self):
        """open application log"""
        if (not os.path.exists('pyModSlave.log')):
            msg = "File 'pyModSlave.log' does not exist"
            self._logger.error(msg)
            Utils.errorMessageBox(msg)
            return
        try:
            subprocess.Popen(['notepad.exe', 'pyModSlave.log'])
        except WindowsError as we:
            msg = "Windows Error No %i - %s" % we.args
            self._logger.error(msg)
            Utils.errorMessageBox(msg)

    def _open_modbus_manual(self):
        """open modbus manual"""
        if (not os.path.exists('ManModbus\index.html')):
            msg = "Modbus Manual is missing"
            self._logger.error(msg)
            Utils.errorMessageBox(msg)
            return
        try:
            webbrowser.open_new_tab('ManModbus\index.html')
        except WindowsError as we:
            msg = "Cannot open Modbus Manual %i - %s" % we.args
            self._logger.error(msg)
            Utils.errorMessageBox(msg)

    def showEvent(self,QShowEvent):
        """set values for controls"""
        self._load_params(self._params_file_name)
        self._update_status_bar()

    def closeEvent(self,QCloseEvent):
        """window is closing"""
        self._save_params(self._params_file_name)

#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
def suppress_qt_warnings():
    os.environ["QT_DEVICE_PIXEL_RATIO"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCREEN_SCALE_FACTORS"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"

def main():
    #qt dpi warnings
    suppress_qt_warnings()
    #logger
    logger = modbus_tk.utils.create_logger("console")
    Utils.set_up_logger_file(logger,'pyModSlave.log')
    #create qt application
    app=QtWidgets.QApplication(sys.argv)
    #load main window
    window=ModSlaveMainWindow()
    #application loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------
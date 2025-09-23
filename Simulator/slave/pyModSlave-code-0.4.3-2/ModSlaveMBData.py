#-------------------------------------------------------------------------------
# Name:        ModSlaveMBData
# Purpose:
#
# Author:      elbar
#
# Created:     28/08/2012
# Copyright:   (c) elbar 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from PyQt5 import QtGui,QtCore,QtWidgets
from ModSlaveMBDataItemDelegate import ModSlaveMBDataItemDelegate

#add logging capability
import logging

#-------------------------------------------------------------------------------
class ModSlaveMBData(QtCore.QObject):
    """ Class wrapper for modbus data """

    def __init__(self, ui):
        super(ModSlaveMBData, self).__init__()
        #data models
        self.coils = None
        self.dis_inputs = None
        self.input_regs = None
        self.hold_regs = None
        self._logger = logging.getLogger("modbus_tk")
        #setup UI
        self.ui = ui
        self.setupUI()

    def setupUI(self):
        #signals-slots
        self.ui.chkSimCoils.stateChanged.connect(self._sim_coils_changed)
        self.ui.chkSimDisInputs.stateChanged.connect(self._sim_dis_inputs_changed)
        self.ui.chkSimInputRegs.stateChanged.connect(self._sim_input_regs_changed)
        self.ui.chkSimHoldRegs.stateChanged.connect(self._sim_hold_regs_changed)
        self.ui.cmbInputRegsType.currentIndexChanged.connect(self._input_regs_data_type_changed)
        self.ui.cmbHoldRegsType.currentIndexChanged.connect(self._hold_regs_data_type_changed)
        self.ui.pbResetDO.clicked.connect(self._reset_DO)
        self.ui.pbResetDI.clicked.connect(self._reset_DI)
        self.ui.pbResetAO.clicked.connect(self._reset_AO)
        self.ui.pbResetAI.clicked.connect(self._reset_AI)
        #read only table views
        self.ui.tvCoilsData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.tvDiscreteInputsData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.tvHoldingRegistersData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.tvInputRegistersData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        #item delegates
        self.ui.tvCoilsData.setItemDelegate(ModSlaveMBDataItemDelegate(True))
        self.ui.tvDiscreteInputsData.setItemDelegate(ModSlaveMBDataItemDelegate(True))
        self.ui.tvHoldingRegistersData.setItemDelegate(ModSlaveMBDataItemDelegate(False))
        self.ui.tvInputRegistersData.setItemDelegate(ModSlaveMBDataItemDelegate(False))

    def set_data_models(self, coils, dis_inputs, input_regs, hold_regs):
        self.coils = coils
        self.dis_inputs = dis_inputs
        self.input_regs = input_regs
        self.hold_regs = hold_regs
        #table views models
        #coils
        self.ui.tvCoilsData.setModel(self.coils.model)
        self.coils.update_view.connect(self._models_data_changed)
        self.ui.tvCoilsData.itemDelegate().update_item.connect(self.coils.update_item)
        self._sim_coils_changed()
        #discrete inputs
        self.ui.tvDiscreteInputsData.setModel(self.dis_inputs.model)
        self.dis_inputs.update_view.connect(self._models_data_changed)
        self.ui.tvDiscreteInputsData.itemDelegate().update_item.connect(self.dis_inputs.update_item)
        self._sim_dis_inputs_changed()
        #input regs
        self.ui.tvInputRegistersData.setModel(self.input_regs.model)
        self.input_regs.update_view.connect(self._models_data_changed)
        self.input_regs.set_data_type(self.ui.cmbInputRegsType.currentIndex())
        self.ui.tvInputRegistersData.itemDelegate().update_item.connect(self.input_regs.update_item)
        self._sim_input_regs_changed()
        #holding regs
        self.ui.tvHoldingRegistersData.setModel(self.hold_regs.model)
        self.hold_regs.update_view.connect(self._models_data_changed)
        self.hold_regs.set_data_type(self.ui.cmbHoldRegsType.currentIndex())
        self.ui.tvHoldingRegistersData.itemDelegate().update_item.connect(self.hold_regs.update_item)
        self._sim_hold_regs_changed()
        #update table views
        self._models_data_changed()

    def _sim_coils_changed(self):
        self._logger.info("Sim Coils : " + str(self.ui.chkSimCoils.isChecked()))
        self.coils.sim = self.ui.chkSimCoils.isChecked()
        self.ui.pbResetDO.setDisabled(self.coils.sim)
        if (self.coils.sim):
            self.ui.tvCoilsData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        else:
            self.ui.tvCoilsData.setEditTriggers(QtWidgets.QAbstractItemView.AnyKeyPressed)

    def _sim_dis_inputs_changed(self):
        self._logger.info("Sim Digital Inputs : " + str(self.ui.chkSimDisInputs.isChecked()))
        self.dis_inputs.sim = self.ui.chkSimDisInputs.isChecked()
        self.ui.pbResetDI.setDisabled(self.dis_inputs.sim)
        if (self.dis_inputs.sim):
            self.ui.tvDiscreteInputsData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        else:
            self.ui.tvDiscreteInputsData.setEditTriggers(QtWidgets.QAbstractItemView.AnyKeyPressed)

    def _sim_input_regs_changed(self):
        self._logger.info("Sim Input Regs : " + str(self.ui.chkSimInputRegs.isChecked()))
        self.input_regs.sim = self.ui.chkSimInputRegs.isChecked()
        self.ui.pbResetAI.setDisabled(self.input_regs.sim)
        if (self.input_regs.sim):
            self.ui.tvInputRegistersData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        else:
            self.ui.tvInputRegistersData.setEditTriggers(QtWidgets.QAbstractItemView.AnyKeyPressed)

    def _sim_hold_regs_changed(self):
        self._logger.info("Sim Holding Regs : " + str(self.ui.chkSimHoldRegs.isChecked()))
        self.hold_regs.sim = self.ui.chkSimHoldRegs.isChecked()
        self.ui.pbResetAO.setDisabled(self.hold_regs.sim)
        if (self.hold_regs.sim):
            self.ui.tvHoldingRegistersData.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        else:
            self.ui.tvHoldingRegistersData.setEditTriggers(QtWidgets.QAbstractItemView.AnyKeyPressed)

    def _models_data_changed(self):
        self.ui.tvCoilsData.viewport().update()
        self.ui.tvCoilsData.resizeColumnsToContents()
        self.ui.tvDiscreteInputsData.viewport().update()
        self.ui.tvDiscreteInputsData.resizeColumnsToContents()
        self.ui.tvInputRegistersData.viewport().update()
        self.ui.tvInputRegistersData.resizeColumnsToContents()
        self.ui.tvHoldingRegistersData.viewport().update()
        self.ui.tvHoldingRegistersData.resizeColumnsToContents()

    def _input_regs_data_type_changed(self):
        self._logger.info("Input Regs Data Type Changed")
        if (self.input_regs):
            self.input_regs.set_data_type(self.ui.cmbInputRegsType.currentIndex())
            (self.ui.tvInputRegistersData.itemDelegate()).set_data_type(self.ui.cmbInputRegsType.currentIndex())

    def _hold_regs_data_type_changed(self):
        self._logger.info("Holding Regs Data Type Changed")
        if (self.hold_regs):
            self.hold_regs.set_data_type(self.ui.cmbHoldRegsType.currentIndex())
            (self.ui.tvHoldingRegistersData.itemDelegate()).set_data_type(self.ui.cmbHoldRegsType.currentIndex())

    def _reset_DO(self):
        self._logger.info("Reset DO")
        self.coils.reset_data()

    def _reset_DI(self):
        self._logger.info("Reset DI")
        self.dis_inputs.reset_data()

    def _reset_AO(self):
        self._logger.info("Reset AO")
        self.hold_regs.reset_data()

    def _reset_AI(self):
        self._logger.info("Reset AI")
        self.input_regs.reset_data()

#-------------------------------------------------------------------------------
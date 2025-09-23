#-------------------------------------------------------------------------------
# Name:        ModSlaveMBDataModel
# Purpose:
#
# Author:      elbar
#
# Created:     29/08/2012
# Copyright:   (c) elbar 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from PyQt5 import QtGui,QtCore,QtWidgets

#-------------------------------------------------------------------------------
class ModSlaveMBDataModel(QtCore.QObject):
    """ Modbus data model """
    # setup signals
    update_view = QtCore.pyqtSignal()
    update_data = QtCore.pyqtSignal(list)

    def __init__(self, start_addr = 0, no_of_items = 10, data_type = 0):#data type > 0 : decimal, 1 : hex
        super(ModSlaveMBDataModel,self).__init__()
        self._start_addr = start_addr
        self._no_of_items = no_of_items
        self._offset = start_addr % 10
        self._no_of_model_items = ((self._offset + self._no_of_items - 1) // 10 + 1) * 10
        self.model = QtGui.QStandardItemModel(self._no_of_model_items / 10, 10)
        self.model.setHorizontalHeaderLabels(("00","01","02","03","04","05","06","07","08","09"))
        self.model.setVerticalHeaderLabels(["%02d"%(x*10) for x in range((no_of_items - 1) // 10 + 1)])
        self._data = None
        self._data_type = data_type
        # simulate values
        self.sim = False

    def update_model(self, data):
        self._data = data
        for i in range(0, self._no_of_model_items):
            row = i //10
            col = i % 10
            idx = self.model.index(row, col, QtCore.QModelIndex())
            if (i >= (self._offset + self._no_of_items) or i < self._offset):#not used cells
                self.model.setData(idx, "x", QtCore.Qt.DisplayRole)
                self.model.setData(idx, QtGui.QBrush(QtCore.Qt.red), QtCore.Qt.ForegroundRole)
                self.model.setData(idx, QtGui.QBrush(QtCore.Qt.lightGray), QtCore.Qt.BackgroundRole)
                item = self.model.itemFromIndex(idx)
                item.setEditable(False)
            else:
                self.model.setData(idx, "ADDRESS : {0}".format(i + self._start_addr - self._offset), QtCore.Qt.ToolTipRole)
                if (not self._data):#no data
                    self.model.setData(idx, 0, QtCore.Qt.DisplayRole)
                elif (self._data_type == 0):#decimal
                    self.model.setData(idx, self._data[i - self._offset], QtCore.Qt.DisplayRole)
                else:#hex
                    self.model.setData(idx,"%X"%self._data[i - self._offset], QtCore.Qt.DisplayRole)
        # emit SIGNAL for updating UI
        self.update_view.emit()

    def set_data_type(self, dt):
        self._data_type = dt
        self.update_model(self._data)

    def reset_data(self):
        _new_data = []
        for i in range(0, self._no_of_model_items):
            row = i //10
            col = i % 10
            if (i >= self._offset and i < (self._offset + self._no_of_items)):
                 idx = self.model.index(row, col, QtCore.QModelIndex())
                 self.model.setData(idx, 0, QtCore.Qt.DisplayRole)
                 self.model.setData(idx, "ADDRESS : {0}".format(i + self._start_addr - self._offset), QtCore.Qt.ToolTipRole)
                 _new_data.append(0)
        # emit SIGNAL for updating UI
        self.update_view.emit()
        self.update_data.emit(_new_data)
        self.update_model(_new_data)

    def update_item(self):
        _new_data = []
        for i in range(0, self._no_of_model_items):
            row = i //10
            col = i % 10
            if (i >= self._offset and i < (self._offset + self._no_of_items)):
                 idx = self.model.index(row, col, QtCore.QModelIndex())
                 value = str(self.model.data(idx, QtCore.Qt.EditRole))
            try:
                if (self._data_type == 0): # decimal
                     _new_data.append(int(value, 10))
                elif(self._data_type == 1): #hex
                    _new_data.append(int(value, 16))
            except Exception:
                _new_data.append(0)
        # emit SIGNAL for updating UI
        self.update_view.emit()
        self.update_data.emit(_new_data)
        self.update_model(_new_data)
#-------------------------------------------------------------------------------
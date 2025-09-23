# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\python\pyModSlave\ui\settingsmodbustcp.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SettingsModbusTCP(object):
    def setupUi(self, SettingsModbusTCP):
        SettingsModbusTCP.setObjectName("SettingsModbusTCP")
        SettingsModbusTCP.resize(240, 110)
        SettingsModbusTCP.setMinimumSize(QtCore.QSize(240, 110))
        SettingsModbusTCP.setMaximumSize(QtCore.QSize(240, 160))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/img/network-16.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        SettingsModbusTCP.setWindowIcon(icon)
        SettingsModbusTCP.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(SettingsModbusTCP)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.leTCPPort = QtWidgets.QLineEdit(SettingsModbusTCP)
        self.leTCPPort.setObjectName("leTCPPort")
        self.gridLayout.addWidget(self.leTCPPort, 1, 1, 1, 1)
        self.lblTCPPort = QtWidgets.QLabel(SettingsModbusTCP)
        self.lblTCPPort.setObjectName("lblTCPPort")
        self.gridLayout.addWidget(self.lblTCPPort, 1, 0, 1, 1)
        self.lblIP = QtWidgets.QLabel(SettingsModbusTCP)
        self.lblIP.setObjectName("lblIP")
        self.gridLayout.addWidget(self.lblIP, 0, 0, 1, 1)
        self.leIP = QtWidgets.QLineEdit(SettingsModbusTCP)
        self.leIP.setObjectName("leIP")
        self.gridLayout.addWidget(self.leIP, 0, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(SettingsModbusTCP)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.lblTCPPort.setBuddy(self.leTCPPort)

        self.retranslateUi(SettingsModbusTCP)
        self.buttonBox.accepted.connect(SettingsModbusTCP.accept)
        self.buttonBox.rejected.connect(SettingsModbusTCP.reject)
        QtCore.QMetaObject.connectSlotsByName(SettingsModbusTCP)

    def retranslateUi(self, SettingsModbusTCP):
        _translate = QtCore.QCoreApplication.translate
        SettingsModbusTCP.setWindowTitle(_translate("SettingsModbusTCP", "Modbus TCP Settings"))
        self.leTCPPort.setText(_translate("SettingsModbusTCP", "502"))
        self.lblTCPPort.setText(_translate("SettingsModbusTCP", "TCP Port"))
        self.lblIP.setText(_translate("SettingsModbusTCP", "IP"))
        self.leIP.setInputMask(_translate("SettingsModbusTCP", "999.999.999.999;_"))

import pyModSlaveQt_rc

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'settings.ui'
#
# Created by: PyQt5 UI code generator 5.14.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.resize(240, 132)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Settings.sizePolicy().hasHeightForWidth())
        Settings.setSizePolicy(sizePolicy)
        Settings.setMinimumSize(QtCore.QSize(240, 132))
        Settings.setMaximumSize(QtCore.QSize(240, 192))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/img/options-16.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Settings.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(Settings)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lblMaxNoOfBusMonitorLines = QtWidgets.QLabel(Settings)
        self.lblMaxNoOfBusMonitorLines.setObjectName("lblMaxNoOfBusMonitorLines")
        self.gridLayout.addWidget(self.lblMaxNoOfBusMonitorLines, 0, 1, 1, 1)
        self.sbMaxNoOfBusMonitorLines = QtWidgets.QSpinBox(Settings)
        self.sbMaxNoOfBusMonitorLines.setMaximum(100)
        self.sbMaxNoOfBusMonitorLines.setProperty("value", 50)
        self.sbMaxNoOfBusMonitorLines.setObjectName("sbMaxNoOfBusMonitorLines")
        self.gridLayout.addWidget(self.sbMaxNoOfBusMonitorLines, 0, 2, 1, 1)
        self.lblSimMin = QtWidgets.QLabel(Settings)
        self.lblSimMin.setObjectName("lblSimMin")
        self.gridLayout.addWidget(self.lblSimMin, 1, 1, 1, 1)
        self.lblSimmax = QtWidgets.QLabel(Settings)
        self.lblSimmax.setObjectName("lblSimmax")
        self.gridLayout.addWidget(self.lblSimmax, 2, 1, 1, 1)
        self.sbSimMin = QtWidgets.QSpinBox(Settings)
        self.sbSimMin.setMaximum(65535)
        self.sbSimMin.setObjectName("sbSimMin")
        self.gridLayout.addWidget(self.sbSimMin, 1, 2, 1, 1)
        self.sbSimMax = QtWidgets.QSpinBox(Settings)
        self.sbSimMax.setMaximum(65535)
        self.sbSimMax.setObjectName("sbSimMax")
        self.gridLayout.addWidget(self.sbSimMax, 2, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(Settings)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Settings)
        self.buttonBox.accepted.connect(Settings.accept)
        self.buttonBox.rejected.connect(Settings.reject)
        QtCore.QMetaObject.connectSlotsByName(Settings)

    def retranslateUi(self, Settings):
        _translate = QtCore.QCoreApplication.translate
        Settings.setWindowTitle(_translate("Settings", "Settings"))
        self.lblMaxNoOfBusMonitorLines.setText(_translate("Settings", "Max No of Bus Monitor Lines"))
        self.lblSimMin.setText(_translate("Settings", "Simulation Min Value"))
        self.lblSimmax.setText(_translate("Settings", "Simulation Max Value"))
import pyModSlaveQt_rc

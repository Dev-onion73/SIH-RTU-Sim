# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\about.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_About(object):
    def setupUi(self, About):
        About.setObjectName("About")
        About.resize(400, 96)
        About.setMinimumSize(QtCore.QSize(400, 96))
        About.setMaximumSize(QtCore.QSize(400, 150))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/img/info16.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        About.setWindowIcon(icon)
        About.setModal(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(About)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblVersion = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.lblVersion.setFont(font)
        self.lblVersion.setAlignment(QtCore.Qt.AlignCenter)
        self.lblVersion.setObjectName("lblVersion")
        self.verticalLayout.addWidget(self.lblVersion)
        self.lblLibVer = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblLibVer.setFont(font)
        self.lblLibVer.setAlignment(QtCore.Qt.AlignCenter)
        self.lblLibVer.setObjectName("lblLibVer")
        self.verticalLayout.addWidget(self.lblLibVer)
        self.lblURL = QtWidgets.QLabel(About)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblURL.setFont(font)
        self.lblURL.setAlignment(QtCore.Qt.AlignCenter)
        self.lblURL.setOpenExternalLinks(True)
        self.lblURL.setObjectName("lblURL")
        self.verticalLayout.addWidget(self.lblURL)

        self.retranslateUi(About)
        QtCore.QMetaObject.connectSlotsByName(About)

    def retranslateUi(self, About):
        _translate = QtCore.QCoreApplication.translate
        About.setWindowTitle(_translate("About", "About"))
        self.lblVersion.setText(_translate("About", "pyModSlave"))
        self.lblLibVer.setText(_translate("About", "modbus_tk lib"))
        self.lblURL.setText(_translate("About", "http://"))
import pyModSlaveQt_rc

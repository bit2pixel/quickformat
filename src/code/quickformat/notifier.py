#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSize, SIGNAL, QThread

from PyKDE4.kdecore import i18n

from notifier_backend import PAbstractBox
from notifier_backend import OUT, TOPCENTER, MIDCENTER, CURRENT, OUT
from notifier_backend import QProgressIndicator

class Notifier(PAbstractBox):

    def __init__(self, parent):
        PAbstractBox.__init__(self, parent)

        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName("verticalLayout")

        spacerItem = QtGui.QSpacerItem(20, 139, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(10)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)

        self.icon = QtGui.QLabel(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(32)
        sizePolicy.setVerticalStretch(32)
        sizePolicy.setHeightForWidth(self.icon.sizePolicy().hasHeightForWidth())
        self.icon.setSizePolicy(sizePolicy)
        self.icon.setMinimumSize(QtCore.QSize(32, 32))
        self.icon.setMaximumSize(QtCore.QSize(32, 32))
        self.icon.setText("")
        self.icon.setPixmap(QtGui.QPixmap(":/images/images/dialog-ok-apply.png"))
        self.icon.setAlignment(QtCore.Qt.AlignCenter)
        self.icon.setObjectName("icon")
        self.horizontalLayout_2.addWidget(self.icon)


        self.busy = QProgressIndicator(self, "white")
        self.busy.setFixedSize(30, 30)
        self.horizontalLayout_2.addWidget(self.busy)

        self.label = QtGui.QLabel(self)
        self.label.setMinimumHeight(30)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setWordWrap(False)
        self.label.setIndent(0)

        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)

        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)

        self.okButton = QtGui.QPushButton(self)
        self.okButton.setStyleSheet("color: #222222")
        self.okButton.setObjectName("okButton")
        self.okButton.setText(i18n("OK"))
        self.okButton.hide()

        self.horizontalLayout.addWidget(self.okButton)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem4)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem5 = QtGui.QSpacerItem(20, 138, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem5)

        self._animation = 2
        self._duration = 500

        self.okButton.clicked.connect(self.hideBox)

    def hideBox(self):
        self.animate(start=MIDCENTER, stop=TOPCENTER, direction=OUT)
        self.okButton.hide()

    def setMessage(self, message, button, indicator, icon=False, wait=False):
        self.adjustSize()
        self.label.adjustSize()

        if message == '':
            self.label.hide()
        else:
            if icon:
                self.icon.show()
            else:
                self.icon.hide()

            if button:
                self.okButton.show()
            else:
                self.okButton.hide()

            if indicator:
                self.busy.show()
            else:
                self.busy.hide()

            self.label.setText(message)
            self.label.setAlignment(QtCore.Qt.AlignVCenter)
            self.label.adjustSize()
        self.adjustSize()

    def setIcon(self, icon=None):
        if not icon:
            self.icon.hide()
        else:
            self.icon.setPixmap(icon.pixmap(22, 22))
            self.icon.show()
        self.adjustSize()

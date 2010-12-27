#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSize, SIGNAL, QThread

from PyKDE4.kdecore import i18n
from PyKDE4.solid import Solid

from subprocess import Popen, PIPE, STDOUT, call
from time import time

from quickformat.ui_quickformat import Ui_QuickFormat
from quickformat.diskTools import DiskTools

from quickformat.ui_volumeitem import Ui_VolumeItem

from pds.thread import PThread
from pds.gui import PMessageBox, OUT, TOPCENTER, MIDCENTER, CURRENT, OUT

import sys, os

volumeList = {'':''}

fileSystems = { "Ext4":"ext4",
                "Ext3":"ext3",
                "Ext2":"ext2",
                "FAT32":"vfat",
                "NTFS":"ntfs-3g",
                }

class VolumeItem(Ui_VolumeItem, QtGui.QWidget):
    def __init__(self, name, path, label, format, icon, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.name.setText(name)
        self.label.setText(label)
        self.path.setText(path)
        self.format.setText("(%s)" % format)
        self.icon.setPixmap(icon)

class QuickFormat(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)

        self.ui = Ui_QuickFormat()
        self.ui.setupUi(self)

        self.__init_signals__()
        self.__set_custom_widgets__()
        self.__process_args__()

        self.generate_volume_list()
        self.generate_file_system_list()

        self.volume_to_format_path = ""
        self.volume_to_format_type = ""
        self.volume_to_format_label = ""

        self.__initial_selection__()

        self.pds_messagebox = PMessageBox(self)
        self.pds_messagebox.enableOverlay()

        self.pds_messagebox.busy.busy()
        self.pds_messagebox.setStyleSheet("color:white")

    def __initial_selection__(self):
        self.ui.volumeName.setCurrentIndex(0)
        self.set_info()
        print self.volume_to_format_path, self.volume_to_format_type, self.volume_to_format_label

    def __set_custom_widgets__(self):
        self.ui.listWidget = QtGui.QListWidget(self)
        self.ui.volumeName.setModel(self.ui.listWidget.model())
        self.ui.volumeName.setView(self.ui.listWidget)

    def __process_args__(self):
        self.volumePathArg = ""

        if len(sys.argv) == 2:
            self.volumePathArg = sys.argv[1]

    def __init_signals__(self):
        self.connect(self.ui.volumeName, SIGNAL("activated(int)"), self.set_info)
        self.connect(self.ui.btn_format, SIGNAL("clicked()"), self.format_disk)

        self.connect(self.ui.btn_cancel, SIGNAL("clicked()"), self.close)

    def hide_pds_messagebox(self):
        self.pds_messagebox.animate(start=MIDCENTER, stop=TOPCENTER, direction=OUT)

    def format_disk(self):
        self.formatter = Formatter(self.volume_to_format_path, fileSystems[str(self.ui.fileSystem.currentText())], self.ui.volumeLabel.text())
        print "========================"
        print self.volume_to_format_path, self.volume_to_format_type, self.volume_to_format_label
        print "========================"
        self.connect(self.formatter, SIGNAL("format_started()"), self.format_started)
        self.connect(self.formatter, SIGNAL("format_successful()"), self.format_successful)
        self.connect(self.formatter, SIGNAL("format_failed()"), self.format_failed)
        self.formatter.start()

    def format_started(self):
        self.pds_messagebox.setMessage("Please wait while formatting...")
        self.pds_messagebox.animate(start=TOPCENTER, stop=MIDCENTER)

    def format_successful(self):
        self.ui.btn_cancel.setText("Close")
        self.pds_messagebox.setMessage("Format completed successfully.")
        self.pds_messagebox.animate(start=TOPCENTER, stop=MIDCENTER)
        # close message after 2 seconds
        QtCore.QTimer.singleShot(2000, self.hide_pds_messagebox)

    def format_failed(self):
        self.ui.btn_cancel.setText("Close")
        self.pds_messagebox.setMessage("Device is in use. Please try again")
        self.pds_messagebox.animate(start=TOPCENTER, stop=MIDCENTER)
        # close message after 2 seconds
        QtCore.QTimer.singleShot(2000, self.hide_pds_messagebox)



    def find_key(self, dic, val):
        """return the key of dictionary dic given the value"""
        return [k for k, v in dic.iteritems() if v == val][0]

    def generate_volume_list(self):
        selectedIndex = 0
        currentIndex = 0

        volumeList.clear()

        volumes = self.get_volumes()

        for volume in volumes:
            self.add_volume_to_list(volume)

            """
            if volumePath == self.volumePathArg:
                selectedIndex = currentIndex

            # append volumeList
            volumeList[currentIndex] = volumePath
            currentIndex += 1
            """
        # select the appropriate volume from list
        self.ui.volumeName.setCurrentIndex(selectedIndex)

    def generate_file_system_list(self):
        # Temporary sapce for file system list
        self.tempFileSystems = []

        # Get file system list
        for fs in fileSystems:
            self.tempFileSystems.append(fs)

        # Sort file system list
        self.tempFileSystems.sort()
        self.sortedFileSystems = self.tempFileSystems

        # Display file system list in combobox
        for fs in self.sortedFileSystems:
            self.ui.fileSystem.addItem(fs)

    def set_info(self):
        """ Displays the selected volume info on main screen """
        currentIndex = self.ui.volumeName.currentIndex()
        item = self.ui.listWidget.item(currentIndex)
        volumeItem = self.ui.listWidget.itemWidget(item)

        label = volumeItem.label.text()
        path = volumeItem.path.text()
        icon = volumeItem.icon.pixmap()
        fileSystem = str(volumeItem.format.text()).strip("()")

        # find fileSystem index from list
        fsIndex = self.ui.fileSystem.findText(self.find_key(fileSystems, fileSystem))

        # select fileSystem type
        self.ui.fileSystem.setCurrentIndex(fsIndex)

        self.ui.volumeLabel.setText(label)
        self.ui.icon.setPixmap(icon)

        self.volume_to_format_path = path
        self.volume_to_format_type = fileSystem
        self.volume_to_format_label = label


    def filter_file_system(self, fileSystem):
        print fileSystem
        if fileSystem!="" \
                and not str(fileSystem).startswith("iso") \
                and not str(fileSystem).startswith("swap"):
            return True

    def get_volumes(self):
        volumes = []

        # Get volumes
        for volume in Solid.Device.listFromType(Solid.StorageDrive.StorageVolume):
            # Apply filter
            if self.filter_file_system(self.get_volume_file_system(volume)):
                volumes.append(volume)
        return volumes

    def get_volume_icon(self, icon):
        iconPath = ":/images/images/" + str(icon) + ".png"
        return QtGui.QPixmap(iconPath)

    def get_volume_name(self, volume):
        return volume.product()

    def get_volume_path(self, volume):
        return volume.asDeviceInterface(Solid.Block.Block).device()

    def get_volume_file_system(self, volume):
        return volume.asDeviceInterface(Solid.StorageVolume.StorageVolume).fsType()

    def get_disk_name(self, volume):
        """ returns the disk name that the volume resides on """
        return "%s %s" % (volume.parent().vendor(), volume.parent().product())

    def prepare_selection_text(self, diskName, volumePath, volumeName):
        if volumeName != "":
            return "%s (%s)" % (volumeName, volumePath)

        return "%s (%s)" % (diskName, volumePath)

    def add_volume_to_list(self, volume):
        volumeInfo = {}
        volumeInfo["disk_name"] = self.get_disk_name(volume)
        volumeInfo["volume_name"] = self.get_volume_name(volume)
        volumeInfo["volume_path"] = self.get_volume_path(volume)
        volumeInfo["volume_file_system"] = self.get_volume_file_system(volume)
        volumeInfo["volume_icon"] = self.get_volume_icon(volume.icon())

        # Create custom widget
        widget = VolumeItem(volumeInfo["disk_name"], volumeInfo["volume_path"], volumeInfo["volume_name"], volumeInfo["volume_file_system"], volumeInfo["volume_icon"], self.ui.listWidget)

        # Create list widget item
        # First parameter is the text shown on the combobox when a selection is made
        selectionText = self.prepare_selection_text(volumeInfo["disk_name"], volumeInfo["volume_path"], volumeInfo["volume_name"])
        item = QtGui.QListWidgetItem(selectionText, self.ui.listWidget)

        # Set the list widget item's interior to our custom widget and append to list
        # list widget item <-> custom widget
        self.ui.listWidget.setItemWidget(item, widget)

        item.setSizeHint(QSize(200,70))

class Formatter(QThread):
    def __init__(self, volume_to_format_path, volume_to_format_type, volume_to_format_label):
        QThread.__init__(self)

        self.volumeToFormat = str(volume_to_format_path)
        self.fs = str(volume_to_format_type)
        self.volumeLabel = str(volume_to_format_label)

        self.diskTools = DiskTools()

        print "=========================="
        print self.volumeToFormat, self.fs, self.volumeLabel
        print "=========================="

    def run(self):

        self.emit(SIGNAL("format_started()"))

        self.formatted = self.format_disk()

        try:
            self.diskTools.refreshPartitionTable(self.volumeToFormat[:8])
        except:
            print "ERROR: Cannot refresh partition"

        if self.formatted==False:
            self.emit(SIGNAL("format_failed()"))
        else:
            self.emit(SIGNAL("format_successful()"))

    def is_device_mounted(self, volumePath):
        for mountPoint in self.diskTools.mountList():
            if self.volumeToFormat == mountPoint[0]:
                return True

    def format_disk(self):
        # If device is mounted then unmount
        if self.is_device_mounted(self.volumeToFormat) == True:
            try:
                self.diskTools.umount(str(self.volumeToFormat))
            except:
                return False

        # If NTFS is selected then activate quick format
        if self.fs == "ntfs-3g":
            self.fs = "ntfs"
            self.quickOption = " -Q "
        else:
            self.quickOption = ""


        # If volume label empty
        if self.volumeLabel == "":
            self.volumeLabel = "My Disk"

        # If VFAT then labeling parameter changes
        if self.fs == "vfat":
            self.labelingCommand = "-n"
        else:
            self.labelingCommand = "-L"


        # Command to execute
        command = "mkfs -t " + self.fs + self.quickOption + " " + self.labelingCommand + " '" + self.volumeLabel + "' " + self.volumeToFormat
        print command

        # Execute
        proc = Popen(command, shell = True, stdout = PIPE,)

        # If theres an error then emmit error signal
        output = proc.communicate()[0]

        ### TODO:
        ### if output contains these words emmit signal
        ### errorWords = ["error", "Error", "cannot", "Cannot"] ...

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    quick_format = QuickFormat()
    quick_format.show()

    app.exec_()




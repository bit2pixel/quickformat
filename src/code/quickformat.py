#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSize, SIGNAL, QThread

from PyKDE4 import kdeui
from PyKDE4.kdecore import i18n
from PyKDE4.solid import Solid
from PyKDE4.kdecore import KCmdLineArgs

from quickformat.ui_quickformat import Ui_QuickFormat
from quickformat.formatter import Formatter

from quickformat.notifier import Notifier

from quickformat.about import aboutData
from quickformat.ui_volumeitem import Ui_VolumeItem

from pds.thread import PThread
from pds.gui import OUT, MIDCENTER, MIDCENTER, CURRENT, OUT

import sys, os

import dbus

VOLUME_LIST = {'':''}

FILE_SYSTEMS = {"Ext4":"ext4",
                "Ext3":"ext3",
                "Ext2":"ext2",
                "FAT32":"vfat",
                "NTFS":"ntfs-3g",
                }
ACCEPTED_BUSSES = [Solid.StorageDrive.Usb,
                   Solid.StorageDrive.Ieee1394, # Firewire
                   Solid.StorageDrive.Platform] # Card Readers

ACCEPTED_DRIVE_TYPES = [Solid.StorageDrive.HardDisk,
                        Solid.StorageDrive.Floppy,
                        Solid.StorageDrive.CompactFlash,
                        Solid.StorageDrive.MemoryStick,
                        Solid.StorageDrive.SmartMedia,
                        Solid.StorageDrive.SdMmc,
                        Solid.StorageDrive.Xd]

class Volume():
    def __init__(self, volume):
        self.volume = volume

        self.icon = self.get_volume_icon()
        self.name = self.get_volume_name()
        self.path = self.get_volume_path()
        self.file_system = self.get_volume_file_system()
        self.size = self.get_volume_size()

        self.device_type = self.get_device_type()
        self.device_bus = self.get_device_bus()
        self.device_path = self.get_device_path()
        self.device_name = self.get_device_name()

    def has_accepted_bus(self):
        """ controls if the device is appropriate for formatting """
        if self.device_bus in ACCEPTED_BUSSES:
            print "BUS = %s" % self.device_bus
            return True

    def has_accepted_drivetype(self):
       if self.device_type in ACCEPTED_DRIVE_TYPES:
            return True


    # Get Device Information

    def get_device_type(self):
        """ returns the bus of the device """
        try:
            return self.volume.parent().asDeviceInterface(Solid.StorageDrive.StorageDrive).driveType()
        except:
            pass

    def get_device_bus(self):
        """ returns the bus of the device """
        try:
            return self.volume.parent().asDeviceInterface(Solid.StorageDrive.StorageDrive).bus()
        except:
            pass

    def get_device_path(self):
        try:
            return self.volume.parent().asDeviceInterface(Solid.Block.Block).device()
        except:
            return self.path

    def get_device_name(self):
        """ returns the device name that the volume resides on """
        return "%s %s" % (self.volume.parent().vendor(), self.volume.parent().product())


    # Get Volume Information

    def get_volume_icon(self):
        icon = str(self.volume.icon())
        iconPath = ":/images/images/" + icon + ".png"
        return QtGui.QPixmap(iconPath)

    def get_volume_name(self):
        return self.volume.product()

    def get_volume_path(self):
        return self.volume.asDeviceInterface(Solid.Block.Block).device()

    def get_volume_file_system(self):
        return self.volume.asDeviceInterface(Solid.StorageVolume.StorageVolume).fsType()

    def get_volume_size(self):
        return self.volume.asDeviceInterface(Solid.StorageVolume.StorageVolume).size()


class VolumeUiItem(Ui_VolumeItem, QtGui.QWidget):
    def __init__(self, name, path, label, format, icon, size, device, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.device.hide()
        self.name.setText(name)
        self.label.setText(label)
        self.path.setText(path)
        self.device.setText(device)

        size_human = self.size_to_human(size)

        self.size.setText(size_human)
        self.format.setText("(%s)" % format)
        self.icon.setPixmap(icon)

    def size_to_human(self, size):
        size = size / 1024.0 ** 2

        if size >= 1000 and size < 100000:
            size = str("%.2f" % (size / 1024.0)) + " GB"
        elif size > 100000:
            size = str(int(size / 1024)) + " GB"
        else:
            size = str(int(size)) + " MB"

        return size


class QuickFormat(QtGui.QWidget):
    def __init__(self, parent = None, args = None):
        QtGui.QWidget.__init__(self, parent)
        self.__sysargs = args

        self.ui = Ui_QuickFormat()
        self.ui.setupUi(self)

        self.first_run = True

        # Initial selection is the first partition found (see next comment)
        self.initial_selection = 0

        # If a partition path is given as argument, intial selection becomes the parition given
        self.__process_args__()

        # Connect Qt Signals
        self.__init_signals__()

        # Initialize custom widgets such as the new combobox
        self.__set_custom_widgets__()

        # Initialize the fancy notification widget (Derrived from PDS by Gokmen Goksel)
        self.__init_notifier__()

        self.show_volume_list()
        self.generate_file_system_list()

        self.volume_to_format_path = ""
        self.volume_to_format_type = ""
        self.volume_to_format_label = ""
        self.volume_to_format_device = ""

        self.__make_initial_selection__(self.initial_selection)

        self.refreshing_devices = False
        self.formatting = False

        # Monitor USB ports for any new devices
        notifier = Solid.DeviceNotifier().instance()
        self.connect(notifier, SIGNAL("deviceAdded(const QString&)"), self.slot_refresh_volume_list)
        self.connect(notifier, SIGNAL("deviceRemoved(const QString&)"), self.slot_refresh_volume_list)

    def __make_initial_selection__(self, index):
        self.ui.volumeName.setCurrentIndex(index)
        self.set_info()
        print self.volume_to_format_path, self.volume_to_format_type, self.volume_to_format_label

    def __init_notifier__(self):
        self.pds_messagebox = Notifier(self)
        self.pds_messagebox.enableOverlay()

        self.pds_messagebox.busy.busy()
        self.pds_messagebox.setStyleSheet("color:white")

        self.pds_messagebox.adjustSize()
        self.pds_messagebox.label.adjustSize()

    def __set_custom_widgets__(self):
        self.ui.listWidget = QtGui.QListWidget(self)
        self.ui.volumeName.setModel(self.ui.listWidget.model())
        self.ui.volumeName.setView(self.ui.listWidget)

    def __process_args__(self):
        self.volumePathArg = ""
        if len(self.__sysargs) == 2:
            if not self.__sysargs[1].startswith("-"):
                self.volumePathArg = self.__sysargs[1]

    def __init_signals__(self):
        self.connect(self.ui.volumeName, SIGNAL("activated(int)"), self.set_info)
        self.connect(self.ui.btn_format, SIGNAL("clicked()"), self.format_device)
        self.connect(self.ui.btn_cancel, SIGNAL("clicked()"), self.close)

    def filter_file_system(self, volume):
        if volume.has_accepted_bus() and volume.has_accepted_drivetype():
            return True

    def get_volumes(self):
        volumes = []

        # Get volumes
        for v in Solid.Device.listFromType(Solid.StorageDrive.StorageVolume):
            # Apply filter
            volume = Volume(v)
            if self.filter_file_system(volume):
                volumes.append(volume)
        return volumes

    def show_volume_list(self):
        self.ui.listWidget.clear()
        self.ui.volumeName.hidePopup()
        selectedIndex = 0
        currentIndex = 0

        VOLUME_LIST.clear()

        volumes = self.get_volumes()

        if not volumes:
            self.no_device_notification()
        else:
            for volume in volumes:
                self.add_volume_to_list(volume)

            # select the appropriate volume from list
            self.ui.volumeName.setCurrentIndex(selectedIndex)
        self.first_run = False

    def format_device(self):
        self.formatter = Formatter(self.volume_to_format_path,
                                   FILE_SYSTEMS[str(self.ui.fileSystem.currentText())],
                                   self.ui.volumeLabel.text(), self.volume_to_format_device)
        self.connect(self.formatter, SIGNAL("format_started()"), self.slot_format_started)
        self.connect(self.formatter, SIGNAL("format_successful()"), self.slot_format_successful)
        self.connect(self.formatter, SIGNAL("format_failed()"), self.format_failed)
        self.formatter.start()

    def slot_format_started(self):
        self.formatting = True
        self.pds_messagebox.setMessage(i18n("Please wait while formatting..."), button=False, indicator=True)
        self.pds_messagebox.animate(start=MIDCENTER, stop=MIDCENTER)

    def slot_format_successful(self):
        self.formatting = False
        self.pds_messagebox.setMessage(i18n("Format completed successfully."), button=True, indicator=False, icon=True)
        self.pds_messagebox.animate(start=MIDCENTER, stop=MIDCENTER)
        self.refresh_volume_list(notify=False)

    def format_failed(self):
        self.formatting = False
        self.pds_messagebox.setMessage(i18n("Device is in use. Please try again."), button=True, indicator=True)
        self.pds_messagebox.animate(start=MIDCENTER, stop=MIDCENTER)

    def no_device_notification(self):
        if self.first_run:
            msgBox = QtGui.QMessageBox(1, i18n("QuickFormat"), i18n("There aren't any removable devices."))
            msgBox.exec_()
            sys.exit()
        else:
            self.formatting = False
            self.pds_messagebox.setMessage(i18n("There aren't any removable devices."), button=False, indicator=False, icon=True)
            self.pds_messagebox.animate(start=MIDCENTER, stop=MIDCENTER)

    def refresh_volume_list(self, notify=True):
        if notify:
            self.notify_refreshing_device_list()
            if not self.formatting:
                QtCore.QTimer.singleShot(2000, self.hide_pds_messagebox)

        self.show_volume_list()
        self.refreshing_devices = False

    def notify_refreshing_device_list(self):
        if not self.refreshing_devices and not self.formatting:
            self.refreshing_devices == True
            self.pds_messagebox.setMessage(i18n("Loading devices..."), button=False, indicator=True)
            self.pds_messagebox.animate(start=MIDCENTER, stop=MIDCENTER)

    def slot_refresh_volume_list(self, device):
        print device
        #FIX doesnt work if hal is used in system
        if str(device).find("UDisks")>=0:
            self.refresh_volume_list()

    def hide_pds_messagebox(self):
        self.pds_messagebox.animate(start=MIDCENTER, stop=MIDCENTER, direction=OUT)

    def generate_file_system_list(self):
        self.ui.fileSystem.clear()

        # Temporary sapce for file system list
        self.tempFileSystems = []

        # Get file system list
        for fs in FILE_SYSTEMS:
            self.tempFileSystems.append(fs)

        # Sort file system list
        self.tempFileSystems.sort()
        self.sortedFileSystems = self.tempFileSystems

        # Display file system list in combobox
        for fs in self.sortedFileSystems:
            self.ui.fileSystem.addItem(fs)

    def __find_key(self, dic, val):
        """return the key of a value of a dictionary"""
        return [k for k, v in dic.iteritems() if v == val][0]

    def set_info(self):
        """ Displays the selected volume info on main screen """
        currentIndex = self.ui.volumeName.currentIndex()
        item = self.ui.listWidget.item(currentIndex)
        volumeItem = self.ui.listWidget.itemWidget(item)

        label = volumeItem.label.text()
        path = volumeItem.path.text()
        icon = volumeItem.icon.pixmap()
        size = volumeItem.size.text()
        device = volumeItem.device.text()
        fileSystem = str(volumeItem.format.text()).strip("()")

        try:
            # find fileSystem index from list
            fsIndex = self.ui.fileSystem.findText(self.__find_key(FILE_SYSTEMS, fileSystem))

            # select fileSystem type
            self.ui.fileSystem.setCurrentIndex(fsIndex)
        except:
            print "File system not found"

        self.ui.volumeLabel.setText(label)
        self.ui.icon.setPixmap(icon)

        self.volume_to_format_path = path
        self.volume_to_format_type = fileSystem
        self.volume_to_format_label = label
        self.volume_to_format_device = device


    def prepare_selection_text(self, deviceName, volumePath, volumeName):
        if volumeName != "":
            return "%s - %s" % (volumeName, volumePath)

        return "%s - %s" % (deviceName, volumePath)

    def add_volume_to_list(self, volume):

        # Create custom widget
        widget = VolumeUiItem(volume.device_name,
                              volume.path,
                              volume.name,
                              volume.file_system,
                              volume.icon,
                              volume.size,
                              volume.device_path,
                              self.ui.listWidget)

        # Create list widget item
        # First parameter is the text shown on the combobox when a selection is made
        selectionText = self.prepare_selection_text(volume.device_name, volume.path, volume.name)
        item = QtGui.QListWidgetItem(selectionText, self.ui.listWidget)

        # Set the list widget item's interior to our custom widget and append to list
        # list widget item <-> custom widget
        self.ui.listWidget.setItemWidget(item, widget)

        item.setSizeHint(QSize(200,70))

        if volume.path == self.volumePathArg:
            self.initial_selection = self.ui.listWidget.count() - 1


    """
    for v in Solid.Device.listFromType(Solid.StorageVolume.StorageVolume):
        try:
            str(v.asDeviceInterface(Solid.Block.Block).device()), str(v.product()), str(v.vendor()), v.parent().asDeviceInterface(Solid.StorageDrive.StorageDrive).driveType(), v.asDeviceInterface(Solid.StorageVolume.StorageVolume).fsType()
        except:
            pass
    """
if __name__ == "__main__":
    args = []
    if len(sys.argv) >= 2:
        if not sys.argv[1].startswith("-"):
            args = sys.argv
            sys.argv = [sys.argv[0]]

    # DBUS MainLoop
    if not dbus.get_default_main_loop():
        from dbus.mainloop.qt import DBusQtMainLoop
        DBusQtMainLoop(set_as_default = True)

    KCmdLineArgs.init(sys.argv, aboutData)
    app = kdeui.KApplication()

    quick_format = QuickFormat(args = args)
    quick_format.show()

    app.exec_()

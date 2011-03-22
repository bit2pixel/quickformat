#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSize, SIGNAL, QThread
from quickformat.disktools import DiskTools
from subprocess import Popen, PIPE, STDOUT, call

import parted

class Formatter(QThread):
    def __init__(self, volume_to_format_path, volume_to_format_type, volume_to_format_label, volume_to_format_disk):
        QThread.__init__(self)

        self.volumeToFormat = str(volume_to_format_path)
        self.fs = str(volume_to_format_type)
        self.volumeLabel = str(volume_to_format_label)
        self.disk = str(volume_to_format_disk)

        self.diskTools = DiskTools()

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

        # If NTFS is selected then activate quick formating option
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
            self.flag = "fat32"
        else:
            self.labelingCommand = "-L"
            self.flag = self.fs

        # Change Device Flags With Parted Module
        print "DISK %s" % self.disk
        parted_device = parted.Device(self.disk)
        parted_disk = parted.Disk(parted_device)

        parted_partition = parted_disk.getPartitionByPath(self.volumeToFormat)

        parted_partition.fileSystem =  parted.fileSystemType[self.flag]

        # Commit Changes
        parted_disk.commit()
        parted_device.close()

        # udev trigger

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



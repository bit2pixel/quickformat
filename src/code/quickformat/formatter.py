#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSize, SIGNAL, QThread
from quickformat.disktools import *
from subprocess import Popen, PIPE, STDOUT, call

import parted

class Formatter(QThread):
    #def __init__(self, volume_to_format_path, volume_to_format_type, volume_to_format_label, volume_to_format_disk):
    def __init__(self):
        QThread.__init__(self)

        # Volume to format
        self.volume = None

        # Formatting status
        self.formatting = False

    def run(self):
        # Send signal for notification
        self.formatting = True
        self.emit(SIGNAL("format_started()"))

        self.formatted = self.format_disk()

        try:
            #refreshPartitionTable(volume.path[:8])
            refreshPartitionTable(self.volume.device_path)
        except:
            print "ERROR: Cannot refresh partition"

        self.formatting = False

        if self.formatted == False:
            self.emit(SIGNAL("format_failed()"))
        else:
            self.emit(SIGNAL("format_successful()"))

    def set_volume_to_format(self, volume):
        self.volume = volume
        print self.volume

    def is_device_mounted(self):
        for mountPoint in getMounted():
            if self.volume.path == mountPoint[0]:
                return True

    def format_disk(self):
        # If device is mounted then unmount

        if self.is_device_mounted() == True:
            try:
                umount(str(self.volume.path))
            except:
                return False

        # If NTFS is selected then activate quick formating option
        if self.volume.file_system == "ntfs-3g":
            self.volume.file_system = "ntfs"
            self.quickOption = " -Q "
        else:
            self.quickOption = ""

        # If volume label empty
        if self.volume.name == "":
            self.volume.name = "My Disk"

        self.flag = ""

        # If VFAT then labeling parameter changes
        if self.volume.file_system == "vfat":
            self.labelingCommand = "-n"
            self.flag = "fat32"
        else:
            self.labelingCommand = "-L"
            self.flag = self.volume.file_system

        # Change Device Flags With Parted Module
        print "---------------"
        print "DISK %s" % self.volume.device_path

        try:
            print "TRYING TO REMOVE FLAGS"
            parted_device = parted.Device(self.volume.device_path)
            #parted_device = parted.Device("/dev/sdh")
            parted_disk = parted.Disk(parted_device)

            parted_partition = parted_disk.getPartitionByPath(self.volume.path)

            print "---------------"
            print self.volume.path
            print "---------------"


            parted_partition.fileSystem = parted.fileSystemType[self.flag]

            # Get possible flags
            parted_flags = parted.partitionFlag.values()

            # Remove any Flags
            flags_found = parted_partition.getFlagsAsString().split(", ")

            if len(flags_found) == 0:
                for flag in flags_found:
                    parted_partition.unsetFlag(parted_flags.index(flag) + 1)

            # Commit Changes
            parted_disk.commit()
        except:
            print "NO FLAG WRITTEN"
        # udev trigger

        # Command to execute
        command = "mkfs -t " + self.volume.file_system + self.quickOption + " " + self.labelingCommand + " '" + self.volume.name + "' " + self.volume.path
        print "---------------"
        print command
        print "---------------"

        # Execute
        proc = Popen(command, shell = True, stdout = PIPE,)

        # If theres an error then emmit error signal
        output = proc.communicate()[0]
        print "---------------"
        print output
        print "---------------"

        ### TODO:
        ### if output contains these words emmit signal
        ### errorWords = ["error", "Error", "cannot", "Cannot"] ...



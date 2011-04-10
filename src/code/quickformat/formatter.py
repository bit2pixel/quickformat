#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QSize, SIGNAL, QThread
from quickformat.disktools import *
from subprocess import Popen, PIPE, STDOUT, call

import parted

class Formatter(QThread):
    def __init__(self):
        QThread.__init__(self)

        # Volume to format
        self.volume = None

        # Volumes current or new file system
        self.new_file_system = None

        # Volumes current or new file system
        self.new_label = None

        # Formatting status
        self.formatting = False

    def run(self):
        # Send signal for notification
        self.formatting = True
        self.emit(SIGNAL("format_started()"))

        self.formatted = self.format_disk()

        if self.formatted == True:
            try:
                refreshPartitionTable(self.volume.device_path)
            except:
                print "ERROR: Cannot refresh partition table"

            self.emit(SIGNAL("format_successful()"))
        else:
            self.emit(SIGNAL("format_failed()"))

        self.formatting = False


    def set_volume_to_format(self, volume, file_system, label):
        self.volume = volume
        self.new_file_system = file_system
        self.new_label = label

    def is_device_mounted(self):
        for mountPoint in getMounted():
            if self.volume.path == mountPoint[0]:
                return True

    def _remove_volume_flags(self):
        try:
            print "---------------"
            print "TRYING TO REMOVE FLAGS of %s" % self.volume.device_path

            parted_device = parted.Device(self.volume.device_path)
            parted_disk = parted.Disk(parted_device)

            parted_partition = parted_disk.getPartitionByPath(self.volume.path)
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
        except Exception as e:
            print "FAILED TO REMOVE FLAGS \n", e.message

    def format_disk(self):
        # If device is mounted then unmount

        if self.is_device_mounted() == True:
            try:
                umount(str(self.volume.path))
            except:
                return False

        # If NTFS is selected then activate quick formating option
        if self.new_file_system == "ntfs-3g":
            self.new_file_system = "ntfs"
            self.quickOption = "-Q"
        else:
            self.quickOption = ""

        # If volume label empty
        if self.new_label == "":
            self.new_label = "My Disk"

        self.flag = ""

        # If VFAT then labeling parameter changes
        if self.new_file_system == "vfat":
            self.labelingCommand = "-n"
            self.flag = "fat32"
        else:
            self.labelingCommand = "-L"
            self.flag = self.new_file_system

        # udev trigger here??

        # Command to execute
        command = "mkfs -t %s %s %s '%s' %s -v" % (self.new_file_system, self.quickOption, self.labelingCommand, self.new_label, self.volume.path)
        print "---------------"
        print "COMMAND: %s" % command
        print "---------------"

        # Execute
        proc = Popen(command, shell = True, stdout = PIPE,)

        # If theres an error then emmit error signal
        output = proc.communicate()[0]
        print "---------------"
        print "OUTPUT: %s" % output
        print "RETURN: %s" % proc.returncode
        print "---------------"

        ### TODO:
        ### if output contains these words emmit signal
        ### errorWords = ["error", "Error", "cannot", "Cannot"] ...

        # If format succeeded, remove parition flags
        if proc.returncode == 0:
            # Change Device Flags With Parted Module
            self._remove_volume_flags()

            return True

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2009 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

# Comar
import comar

class DiskTools:
    def __init__(self):
        self.link = comar.Link()
        self.link.setLocale()
        #self.link.useAgent()
        self.package = self.getMainPackage()

    def listenSignals(self, func):
        self.link.listenSignals("Disk.Manager", func)

    def getPackages(self):
        """
            List of packages that provide Disk.Manager model
        """
        return list(self.link.User.Manager)

    def getMainPackage(self):
        """
            Package that's selected by system.
            For now, it's hardcoded. This value should be given by COMAR.
        """
        packages = self.getPackages()
        if not len(packages):
            return None
        return "mudur"

    def deviceList(self, func=None):
        if func:
            self.link.Disk.Manager[self.package].getDevices(async=func)
        else:
            return self.link.Disk.Manager[self.package].getDevices()

    def partitionList(self, device, func=None):
        if func:
            self.link.Disk.Manager[self.package].getDeviceParts(device, async=func)
        else:
            return self.link.Disk.Manager[self.package].getDeviceParts(device)

    def entryList(self, func=None):
        if func:
            self.link.Disk.Manager[self.package].listEntries(async=func)
        else:
            return self.link.Disk.Manager[self.package].listEntries()

    def mountList(self, func=None):
        if func:
            self.link.Disk.Manager[self.package].getMounted(async=func)
        else:
            return self.link.Disk.Manager[self.package].getMounted()

    def getEntry(self, entry):
        path, fsType, fs_options = self.link.Disk.Manager[self.package].getEntry(entry)
        options = []
        for key, val in fs_options.iteritems():
            if len(val):
                options.append("%s=%s" % (key, val))
            else:
                options.append("%s" % key)
        options = ",".join(options)
        return unicode(path), unicode(fsType), options

    def removeEntry(self, entry):
        return self.link.Disk.Manager[self.package].removeEntry(entry)

    def addEntry(self, device, path, fsType, fs_options):
        if isinstance(fs_options, basestring):
            options = {}
            for opt in fs_options.split(","):
                if "=" in opt:
                    key, val = opt.split("=", 1)
                    options[key] = val
                else:
                    options[opt] = ""
            fs_options = options
        return self.link.Disk.Manager[self.package].addEntry(device, path, fsType, fs_options)

    def getDeviceByLabel(self, label):
        return unicode(self.link.Disk.Manager[self.package].getDeviceByLabel(label))

    def mount(self, device, path):
        print "mount"
        self.link.Disk.Manager[self.package].mount(device, path)

    def umount(self, device):
        print "unmount"
        self.link.Disk.Manager[self.package].umount(device)

    def refreshPartitionTable(self, device):
        self.link.Disk.Manager[self.package].refreshPartitionTable(device)

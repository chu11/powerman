#!/usr/bin/env python
####################################################################
# $Id$
# by Andrew C. Uselton <uselton2@llnl.gov> 
# Copyright (C) 2000 Regents of the University of California
# See ./DISCLAIMER
####################################################################

import sys
import commands
import string
import getopt
import os
import time

def usage(msg):
    print "usage:", sys.argv[0], "[-a] [-c conf] [-f fan] [-l ldir] [-q] [-w node,...] [on | off | reset]"
    print "-a       = on/off/reset all nodes"
    print "-c conf  = configuration file (default: <ldir>/etc/bogus.conf)"
    print "-f fan   = fanout for parallelism (default: 256 where implemented)"
    print "-l ldir  = powerman lirary directory (default: /usr/lib/powerman)"
    print "-q       = be quiet about any errors that may have occurred"
    print "-w nodes = comma separated list of nodes"
    print "-w -     = read nodes from stdin, one per line"
    print "on       = turn on nodes (the default)"
    print "off      = turn off nodes"
    print "reset    = reset nodes"
    print msg
    sys.exit(0)

def init(f):
    "Read in the contents of the configuration file"
    # Ignore lines with a leading "#".  Ignore lines lacking 2 tokens.
    # The first token names the node and the second provides the MAC
    # address.  Set up the "macs" dictionary, indexed by node name,
    # to provide the MAC addresses.  
    macs = {}
    line = f.readline()
    while (line):
        tokens = string.split(line)
        line = f.readline()
	if(len(tokens) < 2):
            continue
        if (tokens[0][0] == '#'): continue
        macs[tokens[0]] = tokens[1]
    return macs

# Check for level of permision and restrict activities for non-root users

stat, uid = commands.getstatusoutput('/usr/bin/id -u')
if (stat == 0):
    if (uid != '0'):
        if (verbose):
            sys.stderr.write( "etherwake: You must be root to run this\n")
        sys.exit(1)
else:
    if (verbose):
        sys.stderr.write( "etherwake: error attempting to determin id -u\n")
    sys.exit(1)

# initialize globals
powermandir = '/usr/lib/powerman/'
config_file = 'etc/etherwake.conf'
verbose     = 1
names       = []
com         = 1
all         = 0
bitmap      = 0
fanout      = 256

# Look for environment variables and set globals

try:
    test = os.environ['POWERMANDIR']
    if (os.path.isdir(test)):
        powermandir = test
except KeyError:
    pass

# Parse the command line, check for sanity, and set globals

try:
    opts, args = getopt.getopt(sys.argv[1:], 'abc:f:l:qw:')
except getopt.error:
    usage("Error processing options\n")


if(not opts):
    usage("provide a list of nodes")

for opt in opts:
    op, val = opt
    if (op == '-a'):
        all = 1
    elif (op == '-c'):
        config_file = val
    elif (op == '-f'):
        fanout = val
    elif (op == '-l'):
        powermandir  = val
    elif (op == '-q'):
        verbose = 0
    elif (op == '-w'):
        if (val == '-'):
            name = sys.stdin.readline()
            while (name):
                if (name[-1:] == '\n'):
                    name = name[:-1]
                names.append(name)
                name = sys.stdin.readline()
        else:
            names = string.split(val, ',')
    else:
        usage("Unrecognized option " + op + "\n")
        
try:
    if (args and args[0]):
        if (args[0] == 'off'):
            com = 0
        elif (args[0] == 'on'):
            com = 1
        elif (args[0] == 'reset'):
            com = 2
        else:
            if (verbose):
                sys.stderr.write("etherwake: " + args[0] + " is not a recognized command\n");
            sys.exit(1)
except TypeError:
    if (verbose):
        sys.stderr.write("etherwake: " + args + " should be a list with one element\n")
    sys.exit(1)

if (powermandir):
    if (powermandir[-1] != '/'):
        powermandir = powermandir + '/'
    if(os.path.isdir(powermandir)):
        sys.path.append(powermandir)
        config_file = powermandir + config_file
    else:
        if (verbose):
            sys.stderr.write("etherwake: Couldn\'t find library directory: " + powermandir + "\n")
        sys.exit(1)
else:
    if (verbose):
        sys.stderr.write("etherwake: Couldn\'t find library directory: " + powermandir + "\n")
    sys.exit(1)

etherwake = powermandir + 'lib/ether-wake'
if (not etherwake or not os.path.isfile(etherwake)):
    if (verbose):
        sys.stderr.write("etherwake: Couldn\'t find the utility: " + etherwake + "\n")
    sys.exit(1)
    
try:
    f = open(config_file, 'r')
    macs = init(f)
    f.close()
except IOError :
    if (verbose):
        sys.stderr.write("etherwake: Couldn\'t find configuration file: " + config_file + "\n")
    sys.exit(1)
    
# Carry out the action.  Note that an etherwake is always sent
# (two for reset), so a higher level utility needs to be resposible
# for checking the state of the nodes beofre being sent.  This will
# attempt to send to every valid node, even if some of those named
# are not legitimate targets, but it will only send to known
# legitimate targets, i.e. extra names in the list won't cause it
# to fail, but it won't send to them.  
if(all):
    for mac in macs:
        os.system(etherwake + ' ' + mac)
        # It might be nice to schedule this rather than block for it.
        # I.e. fork and detatch.
        if (com == 2):
            time.sleep(5)
            os.system(etherwake + ' ' + mac)
    sys.exit(0)
else:
    for name in names:
        try:
            mac = macs[name]
            os.system(etherwake + ' ' + mac)
            if (com == 2):
                time.sleep(5)
                os.system(etherwake + ' ' + mac)
        except KeyError:
            pass
sys.exit(0)


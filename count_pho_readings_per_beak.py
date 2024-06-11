# MsgOut - 16 bit value
# EngConsole - raw values ?
# Group0Data - raw value?

# Only care about channels 0,3,7

import os
import sys
import getopt
import numpy as np
import csv

#--------------------------------------------------------------------------------------------#

def parseGroup0Data(infilename):
    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open %s." % infilename)
        sys.exit(1)

    err = 0

    line = fileIn.readline()

    while "DAC_PHO" not in line:
        line = fileIn.readline()

    ch = 0

    while line:
        if "BEAK" in line and "Beak Error" not in line:
            if ch != 9:
                err = 1
                return err, line
            ch = 0
        else:
            if "ADC_PHO" in line:
                ch += 1
        line = fileIn.readline()
    
    return err, ""


            
#--------------------------------------------------------------------------------------------#

def usage():
    print("extract_beak_offset_stats.py -i <rotor name> [-o]")
    print(" -i <test name> Full prefix name of rotor")
    print(" -o Flag to indicate output file should be created")
    sys.exit(0)

argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:o")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
test_name = ""
CREATE_OUTPUT_FILE = False
     
for o, a in opts:
    if o == "-i":
        test_name = a
    elif o == "-o":
        CREATE_OUTPUT_FILE = True

if test_name == "":
    usage()

test_name = test_name.replace("Exports", "Reports")
test_path = os.path.abspath(test_name)
base_name = os.path.basename(test_name)


## --- Group0Data raw values --- ##
infilename = test_path + "_Group0Data.txt"
err, line = parseGroup0Data(infilename)

if err:
    print("FAIL: %s" % infilename)
    print("  %s" % line)
else:
    print("OK: %s" % infilename)

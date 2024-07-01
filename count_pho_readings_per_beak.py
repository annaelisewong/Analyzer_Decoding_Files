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

    ADC_read_data = [] # [beak timestamp, last ADC reading-first ADC reading, num ADC readings]
    beak_t = 0
    startADC_t = 0
    currADC_t = 0
    ADC_count = 0

    line = fileIn.readline()

    while line:

        line = [l.strip() for l in line.split()]

        if "BEAK" in line and "Beak Error" not in line:
            ADC_read_data.append([beak_t, (currADC_t - startADC_t) * 1000000, ADC_count])

            beak_t = float(line[1])
            startADC_t = 0
            currADC_t = 0
            ADC_count = 0

        elif "ADC_PHO" in line:
            if ADC_count == 0:
                startADC_t = float(line[1])
            else:
                currADC_t = float(line[1])
            ADC_count += 1
        
        elif "DAC_PHO" in line:
            startADC_t = 0.000055 # Arbitrary number for me to flag that this isn't an ADC_PHO
            currADC_t = 0

        line = fileIn.readline()
            
    return ADC_read_data

#--------------------------------------------------------------------------------------------#

def parseBeakTimingOutData(infilename):
    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open %s." % infilename)
        sys.exit(1)

    hold_time_data = [] # [beak timestamp, hold time length]

    line = fileIn.readline()

    while line:
        if "Done" in line:
            break
        if "BEAK" in line:
            line = [l.strip() for l in line.split()]
            hold_time_data.append([float(line[1]), 0])
        line = fileIn.readline()

    while "Global Cuvette Delay" not in line:
        line = fileIn.readline()

    for _ in range(4):
        line = fileIn.readline()

    idx = 0
    while "Timing Stats" not in line and line:
        line = [l.strip() for l in line.split()]
        if len(line) < 11:
            continue
        hold_time_data[idx][1] = float(line[5]) - float(line[4]) # Cycle time - Integration time
        idx += 1
        line = fileIn.readline()
        
    return hold_time_data
#--------------------------------------------------------------------------------------------#

def usage():
    print("count_pho_readings_per_beak.py -i <rotor name> [-o]")
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
ADC_read_data = parseGroup0Data(infilename)

infilename = test_path + "_BeakTimingOut.txt"
hold_time_data = parseBeakTimingOutData(infilename)

# Filter to remove any timestamp values < 0
i = 0
for h in hold_time_data:
    if h[0] <= 0:
        i+= 1
for _ in range(i):
    del hold_time_data[0]

i = 0
for a in ADC_read_data:
    if a[0] <= 0:
        i+= 1

for _ in range(i):
    del ADC_read_data[0]

# print("Beak Time  # ADC  Hold T  ADC dT  Status")
# print("---------  -----  ------  ------  ------")
# for adc, hold in zip(ADC_read_data, hold_time_data):
#     if adc[0] != hold[0]:
#         print("Beak Timestamps do not align.")
#         print(adc[0], hold[0])
#         break

#     if adc[1] == -55:
#         continue

#     status = "OK"

#     # Compare ADC time delta with hold time
#     if hold[1] <= adc[1]:
#         print("ADC readings not contained within hold time bounds.")
#         status = "FAIL"
    
#     if adc[2] != 10:
#         print("Didn't have 10 ADC readings")
#         status = "FAIL"
    
#     print("%9.4f   %2d    %6.2f  %6.2f   %3s" % (adc[0], adc[2], hold[1], adc[1], status))

if CREATE_OUTPUT_FILE:
    fileOut = open(test_path + "_PhoPerBeakOut.txt", 'wt')

    print("\nOutput file: %s" % (test_path + "_PhoPerBeakOut.txt"))

    fileOut.write("Rotor name: %s\n\n" % base_name)

    fileOut.write("Beak Time  # ADC  Hold T  ADC dT  Status\n")
    fileOut.write("---------  -----  ------  ------  ------\n")
    for adc, hold in zip(ADC_read_data, hold_time_data):
        if adc[0] != hold[0]:
            fileOut.write("Beak Timestamps do not align.")
            fileOut.write(adc[0], hold[0])
            break

        if adc[1] == -55:
            continue

        status = "OK"

        # Compare ADC time delta with hold time
        if hold[1] <= adc[1]:
            fileOut.write("ADC readings not contained within hold time bounds.\n")
            status = "FAIL"
        
        if adc[2] != 10:
            fileOut.write("Didn't have 10 ADC readings.\n")
            status = "FAIL"
        
        fileOut.write("%9.4f   %2d    %6.2f  %6.2f   %3s\n" % (adc[0], adc[2], hold[1], adc[1], status))

    fileOut.close()

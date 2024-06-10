# MsgOut - 16 bit value
# EngConsole - raw values ?
# Group0Data - raw value?

# Only care about channels 0,3,7

import os
import sys
import getopt
import numpy as np
import csv

# Print the output with the DAC value (extract from filename)

BITMASK_FFFF0000 = 4294901760
BITMASK_FFFF = 65535

#--------------------------------------------------------------------------------------------#

def parseMsgOut(infilename):
    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open %s." % infilename)
        sys.exit(1)

    line = fileIn.readline()
    
    while "Summary" not in line:
        line = fileIn.readline()

    channel_data = []

    while line:
        vals = []
        if "Photometric Data" in line:
            line = [l.strip('}') for l in line.split()]
            if len(line) < 20:
                continue
            for i in range(10, 20):
                vals.append(int(line[i]))
            channel_data.append(vals)
        line = fileIn.readline()

    if len(channel_data) < 10:
        print("Not enough photonic readings.")

    fileIn.close()

    return channel_data

#--------------------------------------------------------------------------------------------#

def parseEngConsole(infilename):
    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open %s." % infilename)
        sys.exit(1)

    line = fileIn.readline()

    while "cuvette calibration success" not in line:
        line = fileIn.readline()

    signed_data = [] # 32 bit values
    converted_signed_data = [] # 32 bit values
    raw_vals = []
    converted_vals = []

    while line:
        if "ADC" in line:
            line = [l.strip(':') for l in line.split()]
            raw_vals.append(int(line[3]))
            converted_vals.append(int(line[4]))
            
            if int(line[1]) == 9:
                signed_data.append(raw_vals)
                converted_signed_data.append(converted_vals)
                raw_vals = []
                converted_vals = []

        line = fileIn.readline()

    if len(signed_data) < 10 or len(converted_signed_data) < 10:
        print("Not enough photonic readings.")

    fileIn.close()

    return signed_data, converted_signed_data

#--------------------------------------------------------------------------------------------#

def parseGroup0Data(infilename):
    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open %s." % infilename)
        sys.exit(1)

    line = fileIn.readline()

    while "DAC_PHO" not in line:
        line = fileIn.readline()

    raw_data = []
    vals = []

    while line:
        if "BEAK" in line and "Beak Error" not in line:
            if len(vals) > 0:
                raw_data.append(vals)
            vals = []
        else:
            if "ADC_PHO" in line:
                line = [l.strip() for l in line.split()]
                vals.append(int(line[11]))
        line = fileIn.readline()
    
    if len(vals) > 0:
        raw_data.append(vals)

    if len(raw_data) < 10:
        print("Group0Data: Not enough photonic readings.")
    
    fileIn.close()

    return raw_data

#--------------------------------------------------------------------------------------------#

def convert32BitTo16Bit(val):
    val >>= 8 # shift by 8 bits
    val += 410
    val <<= 1
    val &= BITMASK_FFFF
    return val
            
#--------------------------------------------------------------------------------------------#

def usage():
    print("extract_beak_offset_stats.py -i <test name> [-b] [-o]")
    print(" -i <test name> Full prefix name of rotor")
    print(" -b Flag to indicate test was a baseline")
    print(" -o Flag to indicate output file should be created")
    sys.exit(0)

argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:ob")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
test_name = ""
BASELINE_TEST = False
CREATE_OUTPUT_FILE = False
     
for o, a in opts:
    if o == "-i":
        test_name = a
    elif o == "-o":
        CREATE_OUTPUT_FILE = True
    elif o == "-b":
        BASELINE_TEST = True

if test_name == "":
    usage()

test_name = test_name.replace("Exports", "Reports")
test_path = os.path.abspath(test_name)
base_name = os.path.basename(test_name)

outfilename = test_name + "_ResultsOut.csv"

fileOut = open(outfilename, 'wt')
writer = csv.writer(fileOut, delimiter = ',', quotechar='"')

## --- MsgOut 16 bit values --- ##
infilename = test_path + "_MsgOut.txt"
pho_data_16bit = parseMsgOut(infilename)

# Verify that the data is 16 bits
for pho_data in pho_data_16bit:
    ch = 0
    for p in pho_data:
        if p & BITMASK_FFFF0000 > 0:
            print("CH%d [Error]: %s greater than 16 bits" % (ch, bin(p)))
        ch += 1

## --- EngConsole 16 bit values --- ##
infilename = os.path.dirname(test_path).replace("Reports", "EngConsoleOutputs") + "\\EngConsole_" + base_name + ".txt"
signed_data, converted_signed_data = parseEngConsole(infilename) # signed_data = raw value >> 8, converted_signed_data = (signed_data + 410) * 2

# Verify that the data is 16 bits
for s_data in signed_data:
    ch = 0
    for s in s_data:
        if s < 0:
            if len(bin(s)) > 19: # 19 = -0b + 16 bits
                print("CH%d [Error]: %s greater than 16 bits" % (ch, bin(s)))
        elif s & BITMASK_FFFF0000 > 0:
            print("CH%d [Error]: %s greater than 16 bits" % (ch, bin(s)))
        ch += 1

for cs_data in converted_signed_data:
    ch = 0
    for cs in cs_data:
        if cs < 0:
            if len(bin(cs)) > 19: # 19 = -0b + 16 bits
                print("CH%d [Error]: %s greater than 16 bits" % (ch, bin(cs)))
        elif cs & BITMASK_FFFF0000 > 0:
            print("CH%d [Error]: %s greater than 16 bits" % (ch, bin(cs)))
        ch += 1

## --- Group0Data raw values --- ##
infilename = test_path + "_Group0Data.txt"
raw_pho_data = parseGroup0Data(infilename)

## --- Process the data --- ##
# 1. Make sure the raw data can be converted to match the processed data
# 2. Make sure the putty console and msg out file values match

ch0_raw_data_32bit = []
ch3_raw_data_32bit = []
ch7_raw_data_32bit = []

ch0_proc_data_16bit = []
ch3_proc_data_16bit = []
ch7_proc_data_16bit = []

if BASELINE_TEST:
    ch1_raw_data_32bit = []
    ch2_raw_data_32bit = []
    ch4_raw_data_32bit = []
    ch5_raw_data_32bit = []
    ch6_raw_data_32bit = []
    ch8_raw_data_32bit = []
    ch9_raw_data_32bit = []

    ch1_proc_data_16bit = []
    ch2_proc_data_16bit = []
    ch4_proc_data_16bit = []
    ch5_proc_data_16bit = []
    ch6_proc_data_16bit = []
    ch8_proc_data_16bit = []
    ch9_proc_data_16bit = []

# 1. Make sure the PuTTy and MsgOut data matches
    # mo = msgout, ec=engconsole
for vals_mo, vals_ec in zip(pho_data_16bit, converted_signed_data):
    if vals_mo[0] != vals_ec[0]:
        print("Error: [CH0] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[0], vals_ec[0]))
        sys.exit(1)
    else:
        ch0_proc_data_16bit.append(vals_mo[0])
    if vals_mo[3] != vals_ec[3]:
        print("Error: [CH3] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[3], vals_ec[3]))
        sys.exit(1)
    else:
        ch3_proc_data_16bit.append(vals_mo[3])
    if vals_mo[7] != vals_ec[7]:
        print("Error: [CH7] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[7], vals_ec[7]))
        sys.exit(1)
    else:
        ch7_proc_data_16bit.append(vals_mo[7])
    
    if BASELINE_TEST:
        if vals_mo[1] != vals_ec[1]:
            print("Error: [CH1] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[1], vals_ec[1]))
            sys.exit(1)
        else:
            ch1_proc_data_16bit.append(vals_mo[1])
        if vals_mo[2] != vals_ec[2]:
            print("Error: [CH2] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[2], vals_ec[2]))
            sys.exit(1)
        else:
            ch2_proc_data_16bit.append(vals_mo[2])
        if vals_mo[4] != vals_ec[4]:
            print("Error: [CH4] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[4], vals_ec[4]))
            sys.exit(1)
        else:
            ch4_proc_data_16bit.append(vals_mo[4])
        if vals_mo[5] != vals_ec[5]:
            print("Error: [CH5] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[5], vals_ec[5]))
            sys.exit(1)
        else:
            ch5_proc_data_16bit.append(vals_mo[5])
        if vals_mo[6] != vals_ec[6]:
            print("Error: [CH6] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[6], vals_ec[6]))
            sys.exit(1)
        else:
            ch6_proc_data_16bit.append(vals_mo[6])
        if vals_mo[8] != vals_ec[8]:
            print("Error: [CH8] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[8], vals_ec[8]))
            sys.exit(1)
        else:
            ch8_proc_data_16bit.append(vals_mo[8])
        if vals_mo[9] != vals_ec[9]:
            print("Error: [CH9] Values don't match: MsgOut val=%d, EngConsole val=%d" % (vals_mo[9], vals_ec[9]))
            sys.exit(1)
        else:
            ch9_proc_data_16bit.append(vals_mo[9])
        

# 2. Extract the raw values
for vals in raw_pho_data:
    ch0_raw_data_32bit.append(vals[0])
    ch3_raw_data_32bit.append(vals[3])
    ch7_raw_data_32bit.append(vals[7])

    if BASELINE_TEST:
        ch1_raw_data_32bit.append(vals[1])
        ch2_raw_data_32bit.append(vals[2])
        ch4_raw_data_32bit.append(vals[4])
        ch5_raw_data_32bit.append(vals[5])
        ch6_raw_data_32bit.append(vals[6])
        ch8_raw_data_32bit.append(vals[8])
        ch9_raw_data_32bit.append(vals[9])
    
# 3. Verify the actual 16 bit numbers match the converted raw values
for raw_vals, proc_vals in zip(ch0_raw_data_32bit, ch0_proc_data_16bit):
    conv_raw_vals = convert32BitTo16Bit(raw_vals)
    if conv_raw_vals != proc_vals:
        print("Error: [CH0] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))

for raw_vals, proc_vals in zip(ch3_raw_data_32bit, ch3_proc_data_16bit):
    conv_raw_vals = convert32BitTo16Bit(raw_vals)
    if conv_raw_vals != proc_vals:
        print("Error: [CH3] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))

for raw_vals, proc_vals in zip(ch7_raw_data_32bit, ch7_proc_data_16bit):
    conv_raw_vals = convert32BitTo16Bit(raw_vals)
    if conv_raw_vals != proc_vals:
        print("Error: [CH7] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))

if BASELINE_TEST:
    for raw_vals, proc_vals in zip(ch1_raw_data_32bit, ch1_proc_data_16bit):
        conv_raw_vals = convert32BitTo16Bit(raw_vals)
        if conv_raw_vals != proc_vals:
            print("Error: [CH1] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))
    for raw_vals, proc_vals in zip(ch2_raw_data_32bit, ch2_proc_data_16bit):
        conv_raw_vals = convert32BitTo16Bit(raw_vals)
        if conv_raw_vals != proc_vals:
            print("Error: [CH1] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))
    for raw_vals, proc_vals in zip(ch4_raw_data_32bit, ch4_proc_data_16bit):
        conv_raw_vals = convert32BitTo16Bit(raw_vals)
        if conv_raw_vals != proc_vals:
            print("Error: [CH1] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))
    for raw_vals, proc_vals in zip(ch5_raw_data_32bit, ch5_proc_data_16bit):
        conv_raw_vals = convert32BitTo16Bit(raw_vals)
        if conv_raw_vals != proc_vals:
            print("Error: [CH1] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))
    for raw_vals, proc_vals in zip(ch6_raw_data_32bit, ch6_proc_data_16bit):
        conv_raw_vals = convert32BitTo16Bit(raw_vals)
        if conv_raw_vals != proc_vals:
            print("Error: [CH1] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))
    for raw_vals, proc_vals in zip(ch8_raw_data_32bit, ch8_proc_data_16bit):
        conv_raw_vals = convert32BitTo16Bit(raw_vals)
        if conv_raw_vals != proc_vals:
            print("Error: [CH1] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))
    for raw_vals, proc_vals in zip(ch9_raw_data_32bit, ch9_proc_data_16bit):
        conv_raw_vals = convert32BitTo16Bit(raw_vals)
        if conv_raw_vals != proc_vals:
            print("Error: [CH1] Expected value (%d) does not match actual value (%d)" % (conv_raw_vals, proc_vals))

# 4. Find the statistics for the values
ch0_raw_avg = np.mean(ch0_raw_data_32bit)
ch0_raw_std = np.std(ch0_raw_data_32bit)

ch0_proc_avg = np.mean(ch0_proc_data_16bit)
ch0_proc_std = np.std(ch0_proc_data_16bit)

ch3_raw_avg = np.mean(ch3_raw_data_32bit)
ch3_raw_std = np.std(ch3_raw_data_32bit)

ch3_proc_avg = np.mean(ch3_proc_data_16bit)
ch3_proc_std = np.std(ch3_proc_data_16bit)

ch7_raw_avg = np.mean(ch7_raw_data_32bit)
ch7_raw_std = np.std(ch7_raw_data_32bit)

ch7_proc_avg = np.mean(ch7_proc_data_16bit)
ch7_proc_std = np.std(ch7_proc_data_16bit)

if BASELINE_TEST:
    ch1_raw_avg = np.mean(ch1_raw_data_32bit)
    ch1_raw_std = np.std(ch1_raw_data_32bit)

    ch1_proc_avg = np.mean(ch1_proc_data_16bit)
    ch1_proc_std = np.std(ch1_proc_data_16bit)

    ch2_raw_avg = np.mean(ch2_raw_data_32bit)
    ch2_raw_std = np.std(ch2_raw_data_32bit)

    ch2_proc_avg = np.mean(ch2_proc_data_16bit)
    ch2_proc_std = np.std(ch2_proc_data_16bit)

    ch4_raw_avg = np.mean(ch4_raw_data_32bit)
    ch4_raw_std = np.std(ch4_raw_data_32bit)

    ch4_proc_avg = np.mean(ch4_proc_data_16bit)
    ch4_proc_std = np.std(ch4_proc_data_16bit)

    ch5_raw_avg = np.mean(ch5_raw_data_32bit)
    ch5_raw_std = np.std(ch5_raw_data_32bit)

    ch5_proc_avg = np.mean(ch5_proc_data_16bit)
    ch5_proc_std = np.std(ch5_proc_data_16bit)

    ch6_raw_avg = np.mean(ch6_raw_data_32bit)
    ch6_raw_std = np.std(ch6_raw_data_32bit)

    ch6_proc_avg = np.mean(ch6_proc_data_16bit)
    ch6_proc_std = np.std(ch6_proc_data_16bit)

    ch8_raw_avg = np.mean(ch8_raw_data_32bit)
    ch8_raw_std = np.std(ch8_raw_data_32bit)

    ch8_proc_avg = np.mean(ch8_proc_data_16bit)
    ch8_proc_std = np.std(ch8_proc_data_16bit)

    ch9_raw_avg = np.mean(ch9_raw_data_32bit)
    ch9_raw_std = np.std(ch9_raw_data_32bit)

    ch9_proc_avg = np.mean(ch9_proc_data_16bit)
    ch9_proc_std = np.std(ch9_proc_data_16bit)

    print("\n     CH0 32-bit  CH0 16-bit  CH1 32-bit  CH1 16-bit  CH2 32-bit  CH2 16-bit  CH3 32-bit  CH3 16-bit  CH4 32-bit  CH4 16-bit  CH5 32-bit  CH5 16-bit  CH6 32-bit  CH6 16-bit  CH7 32-bit  CH7 16-bit  CH8 32-bit  CH8 16-bit  CH9 32-bit  CH9 16-bit")
    print("     ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------")
    for i in range(10):
        print(" (%d) %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d" % \
              (i, ch0_raw_data_32bit[i], ch0_proc_data_16bit[i], ch1_raw_data_32bit[i], ch1_proc_data_16bit[i], ch2_raw_data_32bit[i], ch2_proc_data_16bit[i], \
               ch3_raw_data_32bit[i], ch3_proc_data_16bit[i], ch4_raw_data_32bit[i], ch4_proc_data_16bit[i], ch5_raw_data_32bit[i], ch5_proc_data_16bit[i], \
                ch6_raw_data_32bit[i], ch6_proc_data_16bit[i], ch7_raw_data_32bit[i], ch7_proc_data_16bit[i], ch8_raw_data_32bit[i], ch8_proc_data_16bit[i], ch9_raw_data_32bit[i], ch9_proc_data_16bit[i]))
    print("     ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------  ----------")
    print("AVG: %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d" % \
          (ch0_raw_avg, ch0_proc_avg, ch1_raw_avg, ch1_proc_avg, ch2_raw_avg, ch2_proc_avg, ch3_raw_avg, ch3_proc_avg, ch4_raw_avg, ch4_proc_avg,\
           ch5_raw_avg, ch5_proc_avg, ch6_raw_avg, ch6_proc_avg, ch7_raw_avg, ch7_proc_avg, ch8_raw_avg, ch8_proc_avg, ch9_raw_avg, ch9_proc_avg))
    print("STD: %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d  %10d" % \
          (ch0_raw_std, ch0_proc_std, ch1_raw_std, ch1_proc_std, ch2_raw_std, ch2_proc_std, ch3_raw_std, ch3_proc_std, ch4_raw_std, ch4_proc_std,\
           ch5_raw_std, ch5_proc_std, ch6_raw_std, ch6_proc_std, ch7_raw_std, ch7_proc_std, ch8_raw_std, ch8_proc_std, ch9_raw_std, ch9_proc_std))
    
    with open(outfilename,'wt', newline='') as myfile:
        wrtr = csv.writer(myfile, delimiter=',', quotechar='"')
        rows = []
        rows.append(["","CH0 32-bit", "CH0 16-bit","CH1 32-bit", "CH1 16-bit","CH2 32-bit", "CH2 16-bit", "CH3 32-bit", "CH3 16-bit", "CH4 32-bit", "CH4 16-bit",\
                     "CH5 32-bit", "CH5 16-bit", "CH6 32-bit", "CH6 16-bit", "CH7 32-bit", "CH7 16-bit", "CH8 32-bit", "CH8 16-bit", "CH9 32-bit", "CH9 16-bit"])
        for i in range(10):
            rows.append([i, ch0_raw_data_32bit[i], ch0_proc_data_16bit[i], \
                         ch1_raw_data_32bit[i], ch1_proc_data_16bit[i], \
                         ch2_raw_data_32bit[i], ch2_proc_data_16bit[i], \
                         ch3_raw_data_32bit[i], ch3_proc_data_16bit[i], \
                         ch4_raw_data_32bit[i], ch4_proc_data_16bit[i], \
                         ch5_raw_data_32bit[i], ch5_proc_data_16bit[i], \
                         ch6_raw_data_32bit[i], ch6_proc_data_16bit[i], \
                         ch7_raw_data_32bit[i], ch7_proc_data_16bit[i], \
                         ch8_raw_data_32bit[i], ch8_proc_data_16bit[i], \
                         ch9_raw_data_32bit[i], ch9_proc_data_16bit[i]])

        rows.append(["AVG:", ch0_raw_avg, ch0_proc_avg, ch1_raw_avg, ch1_proc_avg, ch2_raw_avg, ch2_proc_avg, ch3_raw_avg, ch3_proc_avg, ch4_raw_avg, ch4_proc_avg,\
           ch5_raw_avg, ch5_proc_avg, ch6_raw_avg, ch6_proc_avg, ch7_raw_avg, ch7_proc_avg, ch8_raw_avg, ch8_proc_avg, ch9_raw_avg, ch9_proc_avg])
        rows.append(["STD:", ch0_raw_std, ch0_proc_std, ch1_raw_std, ch1_proc_std, ch2_raw_std, ch2_proc_std, ch3_raw_std, ch3_proc_std, ch4_raw_std, ch4_proc_std,\
           ch5_raw_std, ch5_proc_std, ch6_raw_std, ch6_proc_std, ch7_raw_std, ch7_proc_std, ch8_raw_std, ch8_proc_std, ch9_raw_std, ch9_proc_std])

        for row in rows:
            wrtr.writerow(row)

    sys.exit(0)


print("\n     CH0 32-bit  CH0 16-bit  CH3 32-bit  CH3 16-bit  CH7 32-bit  CH7 16-bit")
print("     ----------  ----------  ----------  ----------  ----------  ----------")
for i in range(10):
    print(" (%d) %10d  %10d  %10d  %10d  %10d  %10d" % (i, ch0_raw_data_32bit[i], ch0_proc_data_16bit[i], ch3_raw_data_32bit[i], ch3_proc_data_16bit[i], ch7_raw_data_32bit[i], ch7_proc_data_16bit[i]))
print("     ----------  ----------  ----------  ----------  ----------  ----------")
print("AVG: %10d  %10d  %10d  %10d  %10d  %10d" % (ch0_raw_avg, ch0_proc_avg, ch3_raw_avg, ch3_proc_avg, ch7_raw_avg, ch7_proc_avg))
print("STD: %10d  %10d  %10d  %10d  %10d  %10d" % (ch0_raw_std, ch0_proc_std, ch3_raw_std, ch3_proc_std, ch7_raw_std, ch7_proc_std))

with open(outfilename,'wt', newline='') as myfile:
    wrtr = csv.writer(myfile, delimiter=',', quotechar='"')
    rows = []
    rows.append(["","CH0 32-bit", "CH0 16-bit", "CH3 32-bit", "CH3 16-bit", "CH7 32-bit", "CH7 16-bit"])
    for i in range(10):
        rows.append([i, ch0_raw_data_32bit[i], ch0_proc_data_16bit[i], ch3_raw_data_32bit[i], ch3_proc_data_16bit[i], ch7_raw_data_32bit[i], ch7_proc_data_16bit[i]])

    rows.append(["AVG:", ch0_raw_avg, ch0_proc_avg, ch3_raw_avg, ch3_proc_avg, ch7_raw_avg, ch7_proc_avg])
    rows.append(["STD:", ch0_raw_std, ch0_proc_std, ch3_raw_std, ch3_proc_std, ch7_raw_std, ch7_proc_std])

    for row in rows:
        wrtr.writerow(row)
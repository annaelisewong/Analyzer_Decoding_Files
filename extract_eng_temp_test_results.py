import os
import getopt
import sys
import numpy as np
import csv

# Open the Group1Data file and extract the values
# Open the Trace file and extract those temperature values

# Using the special RIS file to get exactly 10 temperature readings

# Average out those 10 temperature readings for the average value
# Average out all of the trace output readings for the raw average value

# Parse the command line options

#--------------------------------------------------------------------------------------------#

def parseGroup1Data(infilename):
    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open %s" % infilename)
        sys.exit(1)

    # Sensor data
    top = []
    bot = []
    rtr = []
    # amb = []

    # NOTE: not currently collecting timestamps for these readings since we are just averaging them out

    line = fileIn.readline()

    while line:
        line = [l.strip() for l in line.split()]

        if len(line) < 1:
            line = fileIn.readline()
            continue

        if "TOP_TEMP" in line:
            top.append(int(line[-2]))
        elif "BOT_TEMP" in line:
            bot.append(int(line[-2]))
        elif "RTR_TEMP" in line:
            rtr.append(int(line[-2]))
        # elif line[0] == "Temp":
        #     amb.append(float(line[4]))

        line = fileIn.readline()

    fileIn.close()

    return top, bot, rtr

#--------------------------------------------------------------------------------------------#

def parseTraceOutput(infilename):
    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open %s" % infilename)
        sys.exit(1)

    # Sensor data
    top = []
    bot = []
    rtr = []
    # amb = []

    # NOTE: not currently collecting timestamps for these readings since we are just averaging them out

    line = fileIn.readline()

    while line:

        line = [l.strip(':') for l in line.split()]

        if len(line) < 5 or "PuTTY" in line:
            line = fileIn.readline()
            continue

        top.append(int(line[9]))
        bot.append(int(line[-1]))
        rtr.append(int(line[7]))
        # amb.append(int(line[5]))

        line = fileIn.readline()

    fileIn.close()

    return top, bot, rtr

#--------------------------------------------------------------------------------------------#

def findTempAverages(temps):
    return np.mean(temps)

#--------------------------------------------------------------------------------------------#

def usage():
    pass

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
test_dir  = os.path.dirname(test_path)

outfilename = test_name + "_ResultsOut.csv"

## --- Group 1 Data --- ##
infilename = test_path + "_Group1Data.txt"
g1_top, g1_bot, g1_rtr = parseGroup1Data(infilename)

## --- Trace Data --- ##
infilename = test_dir.replace("Reports", "EngConsoleOutputs\\Trace_") + base_name + ".txt"
trace_top, trace_bot, trace_rtr = parseTraceOutput(infilename)

print("Group 1 Averages:")
print("  TOP: %d" % np.mean(g1_top))
print("  BOT: %d" % np.mean(g1_bot))
print("  RTR: %d" % np.mean(g1_rtr))

print("Trace Averages:")
print("  TOP: %d" % np.mean(trace_top))
print("  BOT: %d" % np.mean(trace_bot))
print("  RTR: %d" % np.mean(trace_rtr))

if CREATE_OUTPUT_FILE:
    with open(outfilename,'wt', newline='') as fileOut:
        writer = csv.writer(fileOut, delimiter=',', quotechar='"')
        rows = []
        rows.append(["Group 1 Engine Temperature Data:"])
        rows.append(["Rotor", "Top Plate", "Bottom Plate"])
        for rtr, top, bot in zip(g1_rtr, g1_top, g1_bot):
            rows.append([rtr, top, bot])

        rows.append(["Trace Raw Engine Temperature Data:"])
        rows.append(["Rotor", "Top Plate", "Bottom Plate"])
        for rtr, top, bot in zip(trace_rtr, trace_top, trace_bot):
            rows.append([rtr, top, bot])

        for row in rows:
            writer.writerow(row)


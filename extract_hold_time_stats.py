import sys
import os
import numpy as np
import getopt

def usage():
    print("extract_hold_time_stats.py -r <rotor name> [-o]")
    print(" -r <rotor name> Full prefix name of rotor")
    print(" -o Flag to indicate output file should be created")
    sys.exit(0)

argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:o")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
CREATE_OUTPUT_FILE = False
     
for o, a in opts:
    if o == "-r":
        rotor_name = a
    elif o == "-o":
        CREATE_OUTPUT_FILE = True

if rotor_name == "":
    usage()

infilename = rotor_name + "_BeakTimingOut.txt"

print("Hold Time Stats\n")

all_holdTime = []

if infilename == "":
    print("No file name detected.")
    sys.exit(1)

print("\nFile Name: %s\n" % infilename)

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open input file %s" % (infilename))
    sys.exit(1)

line = fileIn.readline()

while "Global Cuvette Delay" not in line:
    line = fileIn.readline()

## Workaround to get past the next 3 lines
for i in range(3):
    line = fileIn.readline()

holdTime = []
## Collect values

while line:
    line = fileIn.readline()
    if len(line) < 11:
        break
    line = [l.strip() for l in line.split()]
    holdTime.append( float(line[5]) - float(line[4]) )

## Find statistics
avg = np.mean(holdTime)
min = np.min(holdTime)
max = np.max(holdTime)
std = np.std(holdTime)

print("     Hold Time")
print("     ---------")
print("Min  %9.3f" % (min))
print("Max  %9.3f" % (max))
print("Avg  %9.3f" % (avg))
print("Std  %9.3f" % (std))

if CREATE_OUTPUT_FILE:
    outfilename = rotor_name + "_HoldTimeStatsOut.txt"
    fileOut = open(outfilename, 'wt')

    fileOut.write("Hold Time Stats\n\n")
    fileOut.write("File Name: %s\n\n" % infilename)

    fileOut.write("     Hold Time")
    fileOut.write("     ---------")
    fileOut.write("Min  %9.3f" % (min))
    fileOut.write("Max  %9.3f" % (max))
    fileOut.write("Avg  %9.3f" % (avg))
    fileOut.write("Std  %9.3f" % (std))

    fileOut.close()


all_holdTime += holdTime


# avg = np.mean(all_holdTime)
# min = np.min(all_holdTime)
# max = np.max(all_holdTime)
# std = np.std(all_holdTime)

# print("\nCombined Statistics\n")

# print("     Hold Time")
# print("     ---------")
# print("Min  %9.3f" % (min))
# print("Max  %9.3f" % (max))
# print("Avg  %9.3f" % (avg))
# print("Std  %9.3f" % (std))

# fileOut.write("     Hold Time")
# fileOut.write("     ---------")
# fileOut.write("Min  %9.3f" % (min))
# fileOut.write("Max  %9.3f" % (max))
# fileOut.write("Avg  %9.3f" % (avg))
# fileOut.write("Std  %9.3f" % (std))
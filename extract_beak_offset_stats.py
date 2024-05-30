import sys
import numpy as np
import getopt

# This debug variable allows the initialization beak signal glitch that occurs to be 
# "filtered" out to avoid the skewing of data. The "filter" simply ignores any
# beak signals that occur before 0s (CAM UP).
AEW_DEBUG = 1

def usage():
    print("extract_beak_offset_stats.py -r <rotor name> [-o]")
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

rotor_name = rotor_name.replace("Exports", "Reports")

infilename = rotor_name + "_BeakTimingOut.txt"

print("Beak Error Stats\n")

all_beakError = []
all_beakErrorPercent = []


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
line = fileIn.readline() # Get passed the File: etc. line

## Collect beak times
beakErrorTime = []
while "Done" not in line:
    line = [l.strip() for l in line.split()]
    beakErrorTime.append(float(line[1]))
    line = fileIn.readline()

while "Global Cuvette Delay" not in line:
    line = fileIn.readline()

line = [l.strip() for l in line.split()]
gcd = int(line[4])

## Workaround to get past the next 3 lines
for i in range(3):
    line = fileIn.readline()

beakError = []
beakErrorPercent = []

## Collect values

while line:
    line = fileIn.readline()
    if len(line) < 11:
        break
    line = [l.strip() for l in line.split()]
    beakError.append(float(line[7]))
    beakErrorPercent.append(float(line[8]))

## "Filter" the list to remove any beak values that occur before 0s
if AEW_DEBUG:
    temp = np.min(beakErrorTime)
    temp_idx = beakErrorTime.index(temp)
    del beakError[temp_idx]
    del beakErrorPercent[temp_idx]


## Find statistics
beakError_avg = np.mean(beakError)
beakError_min = np.min(beakError)
beakError_max = np.max(beakError)
beakError_std = np.std(beakError)

beakErrorPercent_avg = np.mean(beakErrorPercent)
beakErrorPercent_min = np.min(beakErrorPercent)
beakErrorPercent_max = np.max(beakErrorPercent)
beakErrorPercent_std = np.std(beakErrorPercent)

print("     Beak Error  % Error")
print("     ----------  -------")
print("Min  %10.3f %8.3f" % (beakError_min, beakErrorPercent_min))
print("Max  %10.3f %8.3f" % (beakError_max, beakErrorPercent_max))
print("Avg  %10.3f %8.3f" % (beakError_avg, beakErrorPercent_avg))
print("Std  %10.3f %8.3f" % (beakError_std, beakErrorPercent_std))

if CREATE_OUTPUT_FILE:
    outfilename = rotor_name.replace("Exports", "Reports") + "_BeakOffsetStatsOut.txt"
    fileOut = open(outfilename, 'wt')

    fileOut.write("Beak Error Stats\n\n")
    fileOut.write("File Name: %s\n\n" % infilename)


    fileOut.write("     Beak Error  % Error\n")
    fileOut.write("     ----------  -------\n")
    fileOut.write("Min  %10.3f %8.3f\n" % (beakError_min, beakErrorPercent_min))
    fileOut.write("Max  %10.3f %8.3f\n" % (beakError_max, beakErrorPercent_max))
    fileOut.write("Avg  %10.3f %8.3f\n" % (beakError_avg, beakErrorPercent_avg))
    fileOut.write("Std  %10.3f %8.3f\n" % (beakError_std, beakErrorPercent_std))


all_beakError += beakError
all_beakErrorPercent += beakErrorPercent

# beakError_avg = np.mean(all_beakError)
# beakError_min = np.min(all_beakError)
# beakError_max = np.max(all_beakError)
# beakError_std = np.std(all_beakError)

# beakErrorPercent_avg = np.mean(all_beakErrorPercent)
# beakErrorPercent_min = np.min(all_beakErrorPercent)
# beakErrorPercent_max = np.max(all_beakErrorPercent)
# beakErrorPercent_std = np.std(all_beakErrorPercent)

# print("\nCombined Statistics\n")

# print("     Beak Error  % Error")
# print("     ----------  -------")
# print("Min  %10.3f %8.3f" % (beakError_min, beakErrorPercent_min))
# print("Max  %10.3f %8.3f" % (beakError_max, beakErrorPercent_max))
# print("Avg  %10.3f %8.3f" % (beakError_avg, beakErrorPercent_avg))
# print("Std  %10.3f %8.3f" % (beakError_std, beakErrorPercent_std))

# fileOut.write("Combined Statistics\n")
# fileOut.write("     Beak Error  % Error\n")
# fileOut.write("     ----------  -------\n")
# fileOut.write("Min  %10.3f %8.3f\n" % (beakError_min, beakErrorPercent_min))
# fileOut.write("Max  %10.3f %8.3f\n" % (beakError_max, beakErrorPercent_max))
# fileOut.write("Avg  %10.3f %8.3f\n" % (beakError_avg, beakErrorPercent_avg))
# fileOut.write("Std  %10.3f %8.3f\n" % (beakError_std, beakErrorPercent_std))
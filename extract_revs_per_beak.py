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

all_beakError = []
all_beakErrorPercent = []


if infilename == "":
    print("No file name detected.")
    sys.exit(1)

# print("\nFile Name: %s\n" % infilename)

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open input file %s" % (infilename))
    sys.exit(1)

line = fileIn.readline()
line = fileIn.readline() # Get passed the File: etc. line

## Collect beak times
beakTime = []
cuvNum = []
flashIdx = []
rotationCt = []
while "Done" not in line and line:
    line = [l.strip() for l in line.split()]
    beakTime.append(float(line[1]))
    cuvNum.append(int(line[4]))
    flashIdx.append(int(line[-1][:-3]))
    rotationCt.append([int(line[-1][:-3]), int(line[-1][-2:])])     # XX:YY --> [XX, YY]
    line = fileIn.readline()


## "Filter" the list to remove any beak values that occur before 0s
if AEW_DEBUG:
    temp = np.min(beakTime)
    temp_idx = beakTime.index(temp)
    del beakTime[temp_idx]
    del cuvNum[temp_idx]
    del rotationCt[temp_idx]


prevCuv = cuvNum[0]        # This value isn't possible, just using it as a placeholder for now
prevT = beakTime[0]
# prevFlash = flashIdx[0]
prevRotCt = (rotationCt[0][0] * 30) + rotationCt[0][1]
deltaT = 0.0
revT = 0.04012       # 40 ms between beak flashes = 1 revolution, although this may vary
TOTAL_CUVETTES = 30

outfilename = rotor_name + "_BeakRevStatsOut.txt"

fileOut = open(outfilename, 'wt')
fileOut.write("File: %s\n\n" % infilename)
fileOut.write("Exp Cuv  Cuv #  Timestamp  DeltaT  Rev Count  Status\n")
fileOut.write("-------  -----  ---------  ------  ---------  ------\n")

for cuv, t, rC in zip(cuvNum[1:], beakTime[1:], rotationCt[1:]):
    deltaT = t-prevT
    rotCt = (rC[0] * 30) + rC[1]
    deltaRotCt = rotCt - prevRotCt
    formatted_deltaRotC = "%d:%d" % (int(deltaRotCt/30), deltaRotCt%30)

    # Looking at number of cuvettes between beak flashes of same cuvette
    if cuv == prevCuv:
        if cuv != rC[1]:
            # Error, we should always be looking at the correct cuvette
            fileOut.write("%7d  %5d  %9.4f  %6.3f  %9s  FAILED: expected cuvette != actual cuvette\n" % (cuv, rC[1], t, deltaT, formatted_deltaRotC))   # expected cuvette, actual cuvette, time, number rotations
        else:
            # We are looking at the correct cuvette
            if deltaRotCt != TOTAL_CUVETTES:
                # Error, there should be exactly one rotation between beak flashes of the same cuvette
                fileOut.write("%7d  %5d  %9.4f  %6.3f  %9s  FAILED: unexpected cuvette count\n" % (cuv, rC[1], t, deltaT, formatted_deltaRotC))
            else:
                fileOut.write("%7d  %5d  %9.4f  %6.3f  %9s  PASSED\n" % (cuv, rC[1], t, deltaT, formatted_deltaRotC))

    # Looking at number of cuvettes between beak flashes of different cuvettes
    else:
        if cuv != rC[1]:
            # Error, we should always be looking at the correct cuvette
            fileOut.write("\n%7d  %5d  %9.4f  %6.3f  %9s  FAILED: expected cuvette != actual cuvette\n" % (cuv, rC[1], t, deltaT, formatted_deltaRotC))
        else:
            if deltaRotCt <= TOTAL_CUVETTES:
                # Error, a full rotation between different cuvettes did not happen
                fileOut.write("\n%7d  %5d  %9.4f  %6.3f  %9s  FAILED: expected >1 rotations between changing cuvettes\n" % (cuv, rC[1], t, deltaT, formatted_deltaRotC))
            else:
                fileOut.write("\n%7d  %5d  %9.4f  %6.3f  %9s  PASSED\n" % (cuv, rC[1], t, deltaT, formatted_deltaRotC))
    
    prevT = t
    prevCuv = cuv
    prevRotCt = rotCt

### PRINT TO THE OUTPUT FILE IN GOOD FORMAT IF OUTPUT FILE REQUESTED, OTHERWISE PRINT?
### HOW TO DO IN AN EFFICIENT WAY
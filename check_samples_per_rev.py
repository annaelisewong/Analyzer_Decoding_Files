import os
import sys
import numpy as np
import getopt

def usage():
    print("check_samples_per_rev.py -r <rotor name> [-o]")
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

infilename = rotor_name + "_Group0Data.txt"

print("Sample Time Stats: %s" % infilename)

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

sampleTimes = []

while line:
    line = fileIn.readline()
    if "BEAK" in line:
        line = [l.strip() for l in line.split()]
        sampleTimes.append(float(line[6]))
    
timePerSample = []
for i in range(len(sampleTimes)-1):
    timePerSample.append( (sampleTimes[i+1] - sampleTimes[i]) >= 0.04 ) # Make sure an entire revolution has occurred

onePerRev = np.all(timePerSample)

print("    One sample/rev: %r" % onePerRev)

if CREATE_OUTPUT_FILE:
    outfilename = rotor_name + "_SamplesPerRevOut.txt"
    fileOut = open(outfilename, 'wt')

    fileOut.write("Sample Time Stats: %s\n\n" % infilename)
    fileOut.write("One sample per revolution: %r" % onePerRev)
    fileOut.close()

fileIn.close()

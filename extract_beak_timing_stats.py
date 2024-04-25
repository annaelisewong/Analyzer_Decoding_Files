import sys
import getopt

def usage():
    print("extract_beak_timing_stats.py -r <rotor name> [-o]")
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

if infilename == "":
    print("No file name detected.")
    sys.exit(1)

print("\nBeakTimingOut file: %s" % (infilename))

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open input file %s" % (infilename))
    sys.exit(1)

line = fileIn.readline()

while "Timing Stats" not in line:
    line = fileIn.readline()

if CREATE_OUTPUT_FILE:
    outfilename = rotor_name + "_BeakTimingStatsOut.txt"
    fileOut = open(outfilename, 'wt')
    fileOut.write("File Name: %s\n\n" % infilename)

while line:
    if CREATE_OUTPUT_FILE:
        fileOut.write(line)
    print(line.strip())
    line = fileIn.readline()


fileIn.close()

if CREATE_OUTPUT_FILE:
    fileOut.close()
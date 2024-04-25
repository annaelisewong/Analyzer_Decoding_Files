import getopt
import sys

def usage():
    print("extract_spectra_gains.py -r <rotor name> [-o]")
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

infilename = rotor_name + "_MsgOut.txt"

if infilename == "":
    print("No file name detected.")
    sys.exit(1)

print("\nFile Name: %s" % infilename)

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open file %s" % infilename)
    sys.exit(1)

line = fileIn.readline()

while "Summary" not in line:
    line = fileIn.readline()

for _ in range(4):
    line = fileIn.readline()

c_count = 0

if CREATE_OUTPUT_FILE:
    outfilename = rotor_name + "_SpectraGainsOut.txt"
    fileOut = open(outfilename, 'wt')
    fileOut.write("File Name: %s\n" % infilename)

while line:
    line = fileIn.readline()
    if "[C ]" in line:
        c_count += 1
    if c_count >= 2:
        line = [l.strip('}') for l in line.split()]
        print("Spectra gain: %d %d %d %d %d %d %d %d %d %d" % (int(line[9]), int(line[10]), int(line[11]), int(line[12]), int(line[13]), \
                                                                int(line[14]), int(line[15]), int(line[16]), int(line[17]), int(line[18])))
        if CREATE_OUTPUT_FILE:
            fileOut.write("Spectra gain: %d %d %d %d %d %d %d %d %d %d\n\n" % (int(line[9]), int(line[10]), int(line[11]), int(line[12]), int(line[13]), \
                                                                            int(line[14]), int(line[15]), int(line[16]), int(line[17]), int(line[18])))
        break

fileIn.close()
if CREATE_OUTPUT_FILE:
    fileOut.close()
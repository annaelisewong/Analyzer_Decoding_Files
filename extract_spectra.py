import sys
import getopt

def usage():
    print("extract_spectra.py -r <rotor name> [-o]")
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

if infilename == "":
    print("No file name detected.")
    sys.exit(1)

print("\nFile Name: %s\n" % infilename)

if CREATE_OUTPUT_FILE:
    outfilename = rotor_name + "_LightSpectraOut.txt"
    fileOut = open(outfilename, 'wt')
    fileOut.write("File Name: %s\n\n" % infilename)

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open input file %s" % (infilename))
    sys.exit(1)

line = fileIn.readline()
while "BEAK" not in line:
    line = fileIn.readline()
    if "BEAK" in line:
        line = [l.strip() for l in line.split()]
        if int(line[4]) != 0: 
            # Make sure that we are looking at cuvette 0, and not any odd beak glitch readings before this
            line = fileIn.readline()
            continue
        if float(line[1]) < 0:
            line = fileIn.readline()
            continue

line = fileIn.readline()

spectra = []
while "ADC_PHO" in line:
    line = [l.strip() for l in line.split()]
    if line[7] in spectra:
        print("%s is a repeat light spectra. Please review.")
        if CREATE_OUTPUT_FILE:
            fileOut.write("%s is a repeat light spectra. Please review.")
        continue
    spectra.append(line[7])
    line = fileIn.readline()

if len(spectra) != 10:
    print("Expected 10 light spectra, got %d. Please review." % len(spectra))
    if CREATE_OUTPUT_FILE:
        fileOut.write("Expected 10 light spectra, got %d. Please review." % len(spectra))
    sys.exit(1)

for i, s in enumerate(spectra):
    print("%2d: %s" %(i + 1, s))
    if CREATE_OUTPUT_FILE:
        fileOut.write("%2d: %s\n" %(i + 1, s))

fileIn.close()
if CREATE_OUTPUT_FILE:
    fileOut.close()
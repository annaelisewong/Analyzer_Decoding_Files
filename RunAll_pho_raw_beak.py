import sys
import os
import math
import subprocess
import getopt

def usage():
    print("RunAll_pho_raw_beak.py [-g GCD]")
    print(" -g [optional] GCD value")

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "g:")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
gcd = ""
     
for o, a in opts:
    if o == "-g":
        gcd = a

if gcd == "":
    argc = len(sys.argv)
    if argc == 1:
        file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_MsgOut" in filename]
    if argc > 2:
        print("Too many arguments.")
        sys.exit(0)
    elif argc == 2:
        file_list = [sys.argv[1]]

    outfilename0 = "gcd_values.csv"
    if os.path.exists(outfilename0):
        fileOut = open(outfilename0, 'wt')
    else:
        fileOut = open(outfilename0, 'a')

    outfilename1 = "files_missing_gcd.txt"
    if os.path.exists(outfilename1):
        noGcdFileOut = open(outfilename1, 'wt')
    else:
        noGcdFileOut = open(outfilename1, 'a')

    total_files = 0

## Part 1: Extract the GCD values for each file

    for infilename in file_list:

        if infilename == "":
            print("No file name detected.")
            continue #sys.exit(1)
        
        try:
            fileIn = open(infilename, 'rt')
        except:
            print("Could not open input file %s" % (infilename))
            continue #sys.exit(1)
        
        try:
            numGcdInstances = lambda file, s: open(file, 'rt').read().count(s)
            gcd_total = numGcdInstances(infilename, "gcd")
            if gcd_total == 0:
                print("\tNo instances of 'gcd' in file. Moving on.\n")
                noGcdFileOut.write("%s\n" %infilename)
                continue
        except:
            print("Could not open input file %s\n" % infilename)
            continue #sys.exit(1)

        line = fileIn.readline()

        total_files += 1

        while "gcd" not in line:
            line = fileIn.readline()

        line = [l.strip() for l in line.split()]
        # NOTE: 2 options for rounding the value: (1) using the floor of the float value, or (2) rounding the float value up or down respective to the dec value
        gcd = math.floor(int(line[7]) * 1.6)
        datafilename = os.path.splitext(infilename)[0].replace("MsgOut", "Group0") + ".csv"
        datafilename = datafilename.replace("Reports", "Exports")
        fileOut.write(f"{datafilename}, {gcd}\n")

        fileIn.close()

    fileOut.close()
    noGcdFileOut.close()

    ## Part 2: Beak Timings

    infilename = "gcd_values.csv"
    fileIn = open(infilename, 'rt')

    file_count = 1
    line = fileIn.readline()

    while line:
        line = line.split()
        if len(line) > 0:
            datafile = line[0].strip(",")
            gcd = line[1]
            outfilename = os.path.splitext(datafile)[0].replace("Group0", "BeakTimingOut") + ".txt"
            outfilename = outfilename.replace("Exports", "Reports")
            print("  (%d/%d) Running: pho_beak_raw.py for %s" % (file_count, total_files, datafile))
            fileOut = open(outfilename, 'wt')
            p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\pho_raw_beak.py", "-i", datafile, "-g", gcd], stdout=fileOut)
            p.wait()
            fileOut.close()
            line = fileIn.readline()
        file_count += 1
        
else:
    ## Part 2: Beak Timings
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_Group0.csv" in filename]
    file_count = 1
    for file in file_list:
        outfilename = os.path.splitext(file)[0].replace("Group0", "BeakTimingOut") + ".txt"
        outfilename = outfilename.replace("Exports", "Reports")
        print("  (%d/%d) Running: pho_beak_raw.py for %s" % (file_count, len(file_list), file))
        fileOut = open(outfilename, 'wt')
        p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\pho_raw_beak.py", "-i", file, "-g", gcd], stdout=fileOut)
        p.wait()
        fileOut.close()
        file_count += 1
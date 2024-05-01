import os
import sys
import getopt
import numpy as np

# BeakTimingStatsOut - integration time
# BeakOffsetStatsOut - offset (exp t btwn beak trig & ref cuv falling edge vs. actual t)
# HoldTimeStatsOut   - hold time
# PhaseStatsOut (?)  - motor nominal RPM
# TempStatsOut       - min/max temps ?
# TempStatsOut       - temp at each state of assay?

#-----------------------------------------------------------------------------------------------------------------------------------------#

def usage():
    print("compare_stats.py -i <file suffix> [-o]")
    print(" -i <file suffix> Suffix of the desired file group")
    print("    Accepted suffixes:")
    print("      BeakTimingStatsOut")
    print("      BeakOffsetStatsOut")
    print(" -o Flag to indicate output file should be created")
    sys.exit(0)

#-----------------------------------------------------------------------------------------------------------------------------------------#

argc = len(sys.argv)
if argc < 2:
    print("not enough args")
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:o")
except getopt.error:
    print("getopt error")
    usage()
    sys.exit(2)
    
# Process options
suffix = ""
CREATE_OUTPUT_FILE = False
     
for o, a in opts:
    if o == "-i":
        suffix = a
    elif o == "-o":
        CREATE_OUTPUT_FILE = True

if suffix == "":
    print("no suffix")
    usage()

## BeakTimingOut
if suffix == "BeakTimingStatsOut":
    # Find all files in the directory with BeakTimingOut suffix
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if suffix in filename]

    # Create variables
    all_beakDelay = []
    all_beakInteg = []

    # Parse each file
    for infilename in file_list:
        if "All_BeakTimingStatsOut.txt" in infilename:
            continue

        try:
            fileIn = open(infilename, 'rt')
        except:
            print("Could not open input file %s" % (infilename))
            sys.exit(1)

        line = fileIn.readline()

        while "Mean" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        all_beakDelay.append(float(line[1]))
        all_beakInteg.append(float(line[2]))

        continue

    print("\nAll Beak Timing Statistics")
    print("  Beak Delay nominal value: %5.3f" % np.mean(all_beakDelay))
    print("  Beak Integ nominal value: %5.3f" % np.mean(all_beakInteg))

    if CREATE_OUTPUT_FILE:
        outfilename = "All_BeakTimingStatsOut.txt"
        try:
            fileOut = open(outfilename, 'wt')
            print("\nOutput file created: %s" % outfilename)
        except:
            print("Could not open output file %s" % outfilename)
            sys.exit(1)
        
        fileOut.write("All Beak Timing Statistics\n")
        fileOut.write("  Beak Delay nominal value: %5.3f\n" % np.mean(all_beakDelay))
        fileOut.write("  Beak Integ nominal value: %5.3f" % np.mean(all_beakInteg))

## BeakOffsetStatsOut
elif suffix == "BeakOffsetStatsOut":
    # Find all files in the directory with BeakTimingOut suffix
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if suffix in filename]

    # Create variables
    all_beakOffset = []

    # Parse each file
    for infilename in file_list:
        if "All_BeakOffsetStatsOut.txt" in infilename:
            continue

        try:
            fileIn = open(infilename, 'rt')
        except:
            print("Could not open input file %s" % (infilename))
            sys.exit(1)

        line = fileIn.readline()

        while "Avg" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        all_beakOffset.append(float(line[1]))

        continue

    print("\nAll Beak Offset Statistics")
    print("  Beak Offset nominal value: %5.3f" % np.mean(all_beakOffset))

    if CREATE_OUTPUT_FILE:
        outfilename = "All_BeakOffsetStatsOut.txt"
        try:
            fileOut = open(outfilename, 'wt')
            print("\nOutput file created: %s" % outfilename)
        except:
            print("Could not open output file %s" % outfilename)
            sys.exit(1)
        
        fileOut.write("All Beak Offset Statistics\n")
        fileOut.write("  Beak Offset nominal value: %5.3f\n" % np.mean(all_beakOffset))

elif suffix == "HoldTimeStatsOut":
    # Find all files in the directory with BeakTimingOut suffix
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if suffix in filename]

    # Create variables
    all_holdTime = []

    # Parse each file
    for infilename in file_list:
        if "All_HoldTimeStatsOut.txt" in infilename:
            continue

        try:
            fileIn = open(infilename, 'rt')
        except:
            print("Could not open input file %s" % (infilename))
            sys.exit(1)

        line = fileIn.readline()

        while "Avg" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        all_holdTime.append(float(line[1]))

        continue

    print("\nAll Hold Time Statistics")
    print("  Hold Time nominal value: %5.3f" % np.mean(all_holdTime))

    if CREATE_OUTPUT_FILE:
        outfilename = "All_HoldTimeStatsOut.txt"
        try:
            fileOut = open(outfilename, 'wt')
            print("\nOutput file created: %s" % outfilename)
        except:
            print("Could not open output file %s" % outfilename)
            sys.exit(1)
        
        fileOut.write("All Beak Offset Statistics\n")
        fileOut.write("  Beak Offset nominal value: %5.3f\n" % np.mean(all_holdTime))

elif suffix == "TempStatsOut":
    # Find all files in the directory with BeakTimingOut suffix
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if suffix in filename]

    # Create variables
    phases = ['Warming', 'Barcode Read', 'Transition', 'Separate', 'Transition', 'Prime S1/S2', 'Transition', 'Unnamed', 'Transition', 'Read Check 1', 'Transition', 'Move to Mix Chamber', 'Mix Sample', \
            'Transition', 'Read Check 2', 'Transition', 'Prime S3', 'Transition', 'Distribute Chemistries', 'Transition', 'Read Check 3', 'Transition', 'Mix Chemistries', 'Transition', 'Read']
    all_rotorTemps = [[], #  0: Warming
                      [], #  1: Barcode Read
                      [], #  2: Separate
                      [], #  3: Prime S1/S2
                      [], #  4: Unnamed
                      [], #  5: Read Check 1
                      [], #  6: Move to Mix Chamber
                      [], #  7: Mix Sample
                      [], #  8: Read Check 2
                      [], #  9: Prime S3
                      [], # 10: Distribute Chemistries
                      [], # 11: Read Check 3
                      [], # 12: Mix Chemistries
                      []] # 13: Read
    phase_count = 0

    # Parse each file
    for infilename in file_list:
        if "All_TempStatsOut.txt" in infilename:
            continue

        try:
            fileIn = open(infilename, 'rt')
        except:
            print("Could not open input file %s" % (infilename))
            sys.exit(1)

        line = fileIn.readline()

        for phase in phases:
            line = fileIn.readline()
            if phase == "Transition":
                continue

            while phase not in line:
                line = fileIn.readline()
            
            while "Rotor Temps" not in line:
                line = fileIn.readline()

            line = fileIn.readline()
            if "No temperature readings" in line:
                line = fileIn.readline()
                phase_count += 1
                continue
            
            while "Avg:" not in line:
                line = fileIn.readline()

            line = [l.strip() for l in line.split()]

            all_rotorTemps[phase_count].append(float(line[1]))

            phase_count += 1
            if phase_count > 13:
                continue

        phase_count = 0 
        continue

    print("\nAll Rotor Temp Nominal Values")
    for phase in phases:
        if phase == "Transition":
            continue

        if len(all_rotorTemps[phase_count]) == 0:
            print("  %22s: No temperature readings." % phase)
            phase_count += 1
            continue

        print("  %22s: %5.3f" % (phase, np.mean(all_rotorTemps[phase_count])))
        phase_count += 1

    if CREATE_OUTPUT_FILE:
        outfilename = "All_TempStatsOut.txt"
        try:
            fileOut = open(outfilename, 'wt')
            print("\nOutput file created: %s" % outfilename)
        except:
            print("Could not open output file %s" % outfilename)
            sys.exit(1)

        phase_count = 0
        
        fileOut.write("\nAll Rotor Temp Nominal Values\n")
        for phase in phases:
            if phase == "Transition":
                continue

            if len(all_rotorTemps[phase_count]) == 0:
                fileOut.write("  %22s: No temperature readings.\n" % phase)
                phase_count += 1
                continue

            fileOut.write("  %22s: %5.3f\n" % (phase, np.mean(all_rotorTemps[phase_count])))
            phase_count += 1

elif suffix == "PhaseStatsOut":
    pass

else:
    print("Couldn't match suffix to file.")
    usage()
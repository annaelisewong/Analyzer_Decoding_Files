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
    print("      HoldTimeStatsOut")
    print("      TempStatsOut")
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
    file_count = 0
    # Create variables
    min_beakDelay = []
    max_beakDelay = []
    avg_beakDelay = []
    std_beakDelay = []
    min_beakInteg = []
    max_beakInteg = []
    avg_beakInteg = []
    std_beakInteg = []

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

        while "Min" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        min_beakDelay.append(float(line[1]))
        min_beakInteg.append(float(line[2]))

        while "Max" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        max_beakDelay.append(float(line[1]))
        max_beakInteg.append(float(line[2]))

        while "Mean" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        avg_beakDelay.append(float(line[1]))
        avg_beakInteg.append(float(line[2]))

        while "Stdev" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        std_beakDelay.append(float(line[1]))
        std_beakInteg.append(float(line[2]))

        file_count += 1

        continue

    print("Num files: %d" % file_count)
    print("\nAll Beak Timing Statistics")
    print("Beak Delay")
    print("  min: %5.3f" % np.min(min_beakDelay))
    print("  max: %5.3f" % np.max(max_beakDelay))
    print("  avg: %5.3f" % np.mean(avg_beakDelay))
    print("  std: %5.3f\n" % np.std(std_beakDelay))
    print("Beak Integ")
    print("  min: %5.3f" % np.min(min_beakInteg))
    print("  max: %5.3f" % np.max(max_beakInteg))
    print("  avg: %5.3f" % np.mean(avg_beakInteg))
    print("  std: %5.3f" % np.std(std_beakInteg))


    if CREATE_OUTPUT_FILE:
        outfilename = "All_BeakTimingStatsOut.txt"
        try:
            fileOut = open(outfilename, 'wt')
            print("\nOutput file created: %s" % outfilename)
        except:
            print("Could not open output file %s" % outfilename)
            sys.exit(1)
        
        fileOut.write("All Beak Timing Statistics\n")
        fileOut.write("Beak Delay\n")
        fileOut.write("  min: %5.3f\n" % np.min(min_beakDelay))
        fileOut.write("  max: %5.3f\n" % np.max(max_beakDelay))
        fileOut.write("  avg: %5.3f\n" % np.mean(avg_beakDelay))
        fileOut.write("  std: %5.3f\n\n" % np.std(std_beakDelay))
        
        fileOut.write("Beak Integ\n")
        fileOut.write("  min: %5.3f\n" % np.min(min_beakInteg))
        fileOut.write("  max: %5.3f\n" % np.max(max_beakInteg))
        fileOut.write("  avg: %5.3f\n" % np.mean(avg_beakInteg))
        fileOut.write("  std: %5.3f\n" % np.std(std_beakInteg))

## BeakOffsetStatsOut
elif suffix == "BeakOffsetStatsOut":
    # Find all files in the directory with BeakTimingOut suffix
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if suffix in filename]
    file_count = 0
    # Create variables
    min_beakOffset = []
    max_beakOffset = []
    avg_beakOffset = []
    std_beakOffset = []

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

        while "Min" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        min_beakOffset.append(float(line[1]))

        while "Max" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        max_beakOffset.append(float(line[1]))

        while "Avg" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        avg_beakOffset.append(float(line[1]))

        while "Std" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        std_beakOffset.append(float(line[1]))

        file_count += 1
        continue
    
    print("Num files: %d" % file_count)
    print("\nAll Beak Offset Statistics")
    print("  min: %5.3f" % np.min(min_beakOffset))
    print("  max: %5.3f" % np.max(max_beakOffset))
    print("  avg: %5.3f" % np.mean(avg_beakOffset))
    print("  std: %5.3f" % np.std(std_beakOffset))

    if CREATE_OUTPUT_FILE:
        outfilename = "All_BeakOffsetStatsOut.txt"
        try:
            fileOut = open(outfilename, 'wt')
            print("\nOutput file created: %s" % outfilename)
        except:
            print("Could not open output file %s" % outfilename)
            sys.exit(1)
        
        fileOut.write("All Beak Offset Statistics\n")
        fileOut.write("  min\n: %5.3f" % np.min(min_beakOffset))
        fileOut.write("  max\n: %5.3f" % np.max(max_beakOffset))
        fileOut.write("  avg\n: %5.3f" % np.mean(avg_beakOffset))
        fileOut.write("  std\n: %5.3f" % np.std(std_beakOffset))

## HoldTimeStatsOut
elif suffix == "HoldTimeStatsOut":
    # Find all files in the directory with BeakTimingOut suffix
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if suffix in filename]

    file_count = 0
    # Create variables
    min_holdTime = []
    max_holdTime = []
    avg_holdTime = []
    std_holdTime = []

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

        while "Min" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        min_holdTime.append(float(line[1]))

        while "Max" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        max_holdTime.append(float(line[1]))

        while "Avg" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        avg_holdTime.append(float(line[1]))

        while "Std" not in line:
            line = fileIn.readline()
        
        line = [l.strip() for l in line.split()]

        std_holdTime.append(float(line[1]))

        file_count += 1

        continue

    print("Num files: %d" % file_count)

    print("\nAll Hold Time Statistics")
    print("  min: %5.3f" % np.min(min_holdTime))
    print("  max: %5.3f" % np.max(max_holdTime))
    print("  avg: %5.3f" % np.mean(avg_holdTime))
    print("  std: %5.3f" % np.std(std_holdTime))

    if CREATE_OUTPUT_FILE:
        outfilename = "All_HoldTimeStatsOut.txt"
        try:
            fileOut = open(outfilename, 'wt')
            print("\nOutput file created: %s" % outfilename)
        except:
            print("Could not open output file %s" % outfilename)
            sys.exit(1)
        
        fileOut.write("All Beak Hold Statistics\n")
        fileOut.write("  min\n: %5.3f" % np.min(min_holdTime))
        fileOut.write("  max\n: %5.3f" % np.max(max_holdTime))
        fileOut.write("  avg\n: %5.3f" % np.mean(avg_holdTime))
        fileOut.write("  std\n: %5.3f" % np.std(std_holdTime))

## TempStatsOut
elif suffix == "TempStatsOut":
    # Find all files in the directory with BeakTimingOut suffix
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if suffix in filename]

    # Create variables
    phases = ['Warming', 'Barcode Read', 'Transition', 'Separate', 'Transition', 'Prime S1/S2', 'Transition', 'Unnamed', 'Transition', 'Read Check 1', 'Transition', 'Move to Mix Chamber', 'Mix Sample', \
            'Transition', 'Read Check 2', 'Transition', 'Prime S3', 'Transition', 'Distribute Chemistries', 'Transition', 'Read Check 3', 'Transition', 'Mix Chemistries', 'Transition', 'Read']
    avg_rotorTemps = [[], #  0: Warming
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
    min_rotorTemps = [[], #  0: Warming
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
    max_rotorTemps = [[], #  0: Warming
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
    std_rotorTemps = [[], #  0: Warming
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

        if "Lipid" in infilename or "NFC" in infilename:
            continue

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

            while "Min" not in line:
                line = fileIn.readline()
            
            line = [l.strip() for l in line.split()]
            min_rotorTemps[phase_count].append(float(line[1]))

            while "Max" not in line:
                line = fileIn.readline()
            
            line = [l.strip() for l in line.split()]
            max_rotorTemps[phase_count].append(float(line[1]))
            
            while "Avg:" not in line:
                line = fileIn.readline()

            line = [l.strip() for l in line.split()]
            avg_rotorTemps[phase_count].append(float(line[1]))

            while "Std:" not in line:
                line = fileIn.readline()

            line = [l.strip() for l in line.split()]
            std_rotorTemps[phase_count].append(float(line[1]))

            phase_count += 1
            if phase_count > 13:
                continue

        phase_count = 0 
        continue

    print("\nAll Rotor Temp Nominal Values\n")
    print("        Phase Name          Min      Max      Avg      Std  ")
    print("  ----------------------  -------  -------  -------  -------")

    for phase in phases:
        if phase == "Transition":
            continue
        if len(avg_rotorTemps[phase_count]) == 0:
            print("  %22s     -        -        -        -\n" % phase.upper())
            phase_count += 1
            continue
        print("  %22s   %6.3f   %6.3f   %6.3f   %6.3f\n" % (phase.upper(), np.mean(min_rotorTemps[phase_count]), np.mean(max_rotorTemps[phase_count]), np.mean(avg_rotorTemps[phase_count]), np.mean(std_rotorTemps[phase_count])))
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
        
        fileOut.write("\nAll Rotor Temp Nominal Values\n\n")
        fileOut.write("        Phase Name          Min      Max      Avg      Std  \n")
        fileOut.write("  ----------------------  -------  -------  -------  -------\n")

        for phase in phases:
            if phase == "Transition":
                continue
            if len(avg_rotorTemps[phase_count]) == 0:
                fileOut.write("  %22s     -        -        -        -\n" % phase.upper())
                phase_count += 1
                continue
            fileOut.write("  %22s   %6.3f   %6.3f   %6.3f   %6.3f\n" % (phase.upper(), np.mean(min_rotorTemps[phase_count]), np.mean(max_rotorTemps[phase_count]), np.mean(avg_rotorTemps[phase_count]), np.mean(std_rotorTemps[phase_count])))
            phase_count += 1

elif suffix == "PhaseStatsOut":
    pass

else:
    print("Couldn't match suffix to file.")
    usage()
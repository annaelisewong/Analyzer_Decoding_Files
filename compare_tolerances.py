import os
import sys
import getopt

"""
Files to check:
1. BeakTimingStatsOut.txt
2. BeakOffsetStatsOut.txt
3. HoldTimeStatsOut.txt
4. TempStatsOut.txt ?
"""

def usage():
    print("extract_beak_offset_stats.py -r <rotor name> -t <tolerances CSV")
    print(" -r <rotor name> Full prefix name of rotor")
    print(" -t <tolerances CSV> CSV file with tolerances")
    sys.exit(0)

#--------------------------------------------------------------------------------------------#

def getTolerances(infilename):

    try:
        fileIn = open(infilename, "rt")
    except:
        print("Could not open tolerances file: %s" % infilename)
        sys.exit(1)

    # [Tolerance Name, min, max, expVal]
    beakTimingTol   = ["BeakTiming", 0.0, 0.0, 0.0]
    integTimingTol  = ["IntegrationTiming", 0.0, 0.0, 0.0]
    offsetTimingTol = ["OffsetTiming", 0.0, 0.0, 0.0]
    holdTimingTol   = ["HoldTiming", 0.0, 0.0, 0.0]

    line = fileIn.readline()

    while line:
        if "BeakTiming" in line:
            line = [l.strip() for l in line.split(',')]
            beakTimingTol[1] = float(line[1])
            beakTimingTol[2] = float(line[2])
            beakTimingTol[3] = float(line[3])
        elif "IntegrationTiming" in line:
            line = [l.strip() for l in line.split(',')]
            integTimingTol[1] = float(line[1])
            integTimingTol[2] = float(line[2])
            integTimingTol[3] = float(line[3])
        elif "OffsetTiming" in line:
            line = [l.strip() for l in line.split(',')]
            offsetTimingTol[1] = float(line[1])
            offsetTimingTol[2] = float(line[2])
            offsetTimingTol[3] = float(line[3])
        elif "HoldTiming" in line:
            line = [l.strip() for l in line.split(',')]
            holdTimingTol[1] = float(line[1])
            holdTimingTol[2] = float(line[2])
            holdTimingTol[3] = float(line[3])

        line = fileIn.readline()

    return [beakTimingTol, integTimingTol, offsetTimingTol, holdTimingTol]

#--------------------------------------------------------------------------------------------#

def compareTolerances(toleranceName, tolerances, values):
    for tol in tolerances:
        if toleranceName == tol[0]:
            # Start the comparison
            fileOut.write("  " + toleranceName + "\n")
            # Minimum value
            if values[0] < tol[1]:
                fileOut.write("    Minimum value:\tFAIL\n")
                fileOut.write("      * Min=%f\n      * Act=%f\n" % (tol[1], values[0]))
            else:
                fileOut.write("    Minimum value:\tOK\n")
            # Maximum value
            if values[1] > tol[2]:
                fileOut.write("    Maximum value:\tFAIL\n")
                fileOut.write("      * Max=%f\n      * Act=%f\n" % (tol[2], values[1]))
            else:
                fileOut.write("    Maximum value:\tOK\n")
            # Average value
            fileOut.write("    Target value:\t%f\n" % tol[3])
            fileOut.write("    Average value:\t%f\n" % values[2])
            fileOut.write("    Offset from target:\t%f\n\n" % (values[2] - tol[3]))

    return

#--------------------------------------------------------------------------------------------#

def beakTimingStatsOut(infilename):
    try:
        fileIn = open(infilename, "rt")
    except:
        print("Could not open %s." % infilename)
        return
    
    # [min, max, avg]
    beakDelayT = [0.0, 0.0, 0.0]
    integT = [0.0, 0.0, 0.0]
    
    lines = fileIn.readlines()

    for line in lines[1:]:
        if "Min" in line:
            line = [l.strip() for l in line.split()]
            beakDelayT[0] = float(line[1])
            integT[0] = float(line[2])

        elif "Max" in line:
            line = [l.strip() for l in line.split()]
            beakDelayT[1] = float(line[1])
            integT[1] = float(line[2])

        elif "Mean" in line:
            line = [l.strip() for l in line.split()]
            beakDelayT[2] = float(line[1])
            integT[2] = float(line[2])

    return beakDelayT, integT

#--------------------------------------------------------------------------------------------#

def beakOffsetStatsOut(infilename):
    try:
        fileIn = open(infilename, "rt")
    except:
        print("Could not open %s." % infilename)
        return
    
    # [min, max, avg]
    beakOffsetT = [0.0, 0.0, 0.0]
    
    lines = fileIn.readlines()

    for line in lines[1:]:
        if "Min" in line:
            line = [l.strip() for l in line.split()]
            beakOffsetT[0] = float(line[1])

        elif "Max" in line:
            line = [l.strip() for l in line.split()]
            beakOffsetT[1] = float(line[1])

        elif "Avg" in line:
            line = [l.strip() for l in line.split()]
            beakOffsetT[2] = float(line[1])

    return beakOffsetT

#--------------------------------------------------------------------------------------------#

def holdTimeStatsOut(infilename):
    try:
        fileIn = open(infilename, "rt")
    except:
        print("Could not open %s." % infilename)
        return
    
    # [min, max, avg]
    holdT = [0.0, 0.0, 0.0]
    
    lines = fileIn.readlines()

    for line in lines[1:]:
        if "Min" in line:
            line = [l.strip() for l in line.split()]
            holdT[0] = float(line[1])

        elif "Max" in line:
            line = [l.strip() for l in line.split()]
            holdT[1] = float(line[1])

        elif "Avg" in line:
            line = [l.strip() for l in line.split()]
            holdT[2] = float(line[1])

    return holdT

#--------------------------------------------------------------------------------------------#

argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:t:")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
infilename = ""
for o, a in opts:
    if o == "-r":
        rotor_name = a
    if o == "-t":
        infilename = a

if rotor_name == "" or infilename == "":
    usage()

rotor_name = rotor_name.replace("Exports", "Reports")
outfilename = "ToleranceComparisonOut.txt"
fileOut = open(outfilename, "a")

fileOut.write("Rotor Name: %s\n\n" % os.path.basename(rotor_name))

## GET TOLERANCES ##
tolerances = getTolerances(infilename)

## BEAK TIMING STATS ##
infilename = rotor_name + "_BeakTimingStatsOut.txt"
beakDelayT, integT = beakTimingStatsOut(infilename)

## BEAK OFFSET STATS ##
infilename = rotor_name + "_BeakOffsetStatsOut.txt"
beakOffsetT = beakOffsetStatsOut(infilename)

## HOLD TIME STATS ##
infilename = rotor_name + "_HoldTimeStatsOut.txt"
holdT = holdTimeStatsOut(infilename)

## COMPARE TOLERANCES
compareTolerances("BeakTiming", tolerances, beakDelayT)
compareTolerances("IntegrationTiming", tolerances, integT)
compareTolerances("OffsetTiming", tolerances, beakOffsetT)
compareTolerances("HoldTiming", tolerances, holdT)

fileOut.write("---------------------------------------------------\n\n")

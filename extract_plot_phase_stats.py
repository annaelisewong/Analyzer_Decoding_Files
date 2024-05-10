import sys
import subprocess

from enum import Enum
import sys
import getopt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
import matplotlib.ticker as ticker
from scipy import signal
import struct

# This is obsolete now, but keeping for some of the deprecated functions
Phase = Enum('Phase', ['INIT','BARCODE', 'TRAN2SEPARATE', 'SEPARATE', 'TRAN2PRIMES1S2', 'PRIMES1S2', 'READCHECK1', 'TRAN2MIXCHAMBER', 'MIXCHAMBER', 'MIX1',  \
                       'READCHECK2', 'TRAN2PRIMES3', 'PRIMES3', 'TRAN2DISTRIBUTECHEMS', 'DISTRIBUTECHEMS', 'TRAN2READCHECK3', 'READCHECK3', 'TRAN2MIX2', 'MIX2', 'READ', 'END'])

#-----------------------------------------------------------------------------------------------------------------------------------------#

def usage():
    print("extract_plot_phase_stats.py -r <rotor_name> [-p] [-s]")
    print(" -r <rotor name> Full prefix name of rotor")
    print(" -p Flag to indicate that an output plot should be generated")
    print(" -s Flag to indicate that an output plot should be generated and saved")

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseRISReadable()
@brief           Parse through RIS_Readable text file and extracts data for instructed RPM, and instructed durations of time
@param fileIn:   Open RIS_Readable text file
@return risRPM:  Array containing instructed RPM values
@return risdT:   Array containing time durations for each RPM instruction
@return risAccl: Array containing acceleration values between RPM instructions
'''

def parseRISReadable(fileIn):
    line = fileIn.readline()
    while "Summary Full" not in line:
        line = fileIn.readline()

    for _ in range(2):
        line = fileIn.readline()

    # risInstructions = [] # array for holding [time, RPM, direction, loops] information for easier use
    risRPM = []
    risdT = [] # only have the instructed duration, don't have the actual timestamps
    risAccl = []
    speedChecked = False
    while line:
        line = fileIn.readline()
        line = line.replace("'", "")
        line = line.replace("RPM", "")
        line = [l.strip() for l in line.split()]

        if len(line) < 1:
            continue

        if "NO_CHANGE" in line[3]:
            if "WAIT_MSG_C" in line[10] and len(risRPM) > 0:
                risRPM.append(risRPM[-1])
                risdT.append(risdT[-1])
                risAccl.append(risdT[-1]) # ?
            continue
        elif "HIGH_SPEED" in line[3]:
            line[3] = 0 # TODO: Update this value. not sure what it should be
        elif "LOW_SPEED" in line[3]:
            line[3] = 0 # TODO: Update this value, not sure what it should be
        elif "SPEED_CHECK" in line[3]:
            speedChecked = True
            continue
        elif "STOP_MOTOR" in line[3]:
            line[3] = 0
        elif "ROTOR_DONE" in line[3]:
            line[3] = 0

        tempRisRPM = []
        tempRisdT = []
        tempRisAccl = []
        loop = int(line[-1])

        rpm  = int(line[3])
        dT   = float(line[4])
        accl = int(line[8])

        if int(line[5]) == 1:
            # Reverse direction, need to turn RPM value negative
            rpm *= -1
        
        if len(risRPM) > 1 and risRPM[-1] > rpm:
            accl *= -1
        
        if loop > 1:
            # There is a loop
            # Add the loop-starting values to the temporary array
            tempRisRPM.append(rpm)
            tempRisdT.append(dT)
            tempRisAccl.append(accl)

            # Find all commands in the loop and add them to the array
            while int(line[-1]) != 0:
                line = fileIn.readline()
                line = line.replace("'", "")
                line = line.replace("RPM", "")
                line = [l.strip() for l in line.split()]

                rpm = int(line[3])
                dT  = float(line[4])
                accl = int(line[8])
                if int(line[5]) == 1:
                    rpm  *= -1
                
                if tempRisRPM[-1] > rpm:
                    accl *= -1
                
                tempRisRPM.append(rpm)
                tempRisdT.append(dT)
                tempRisAccl.append(accl)
            
            # Add the loop commands to the array loop # of times
            for _ in range(loop):
                risRPM  += tempRisRPM
                risdT   += tempRisdT
                risAccl += tempRisAccl
            
        else:
            # No loop
            if speedChecked:
                # Only here to handle risdT slightly differently than the other instances
                risRPM.append(rpm)
                risdT.append(dT + 0.02)
                risAccl.append(accl)
                speedChecked = False
            else:
                risRPM.append(rpm)
                risdT.append(dT)
                risAccl.append(accl)
            
    return risRPM, risdT, risAccl

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseMotCmdMsgOut()
@brief          Parse through MotCmdMsgOut text file and extracts data for instructed RPM, and instructed durations of time
@param fileIn:  Open MotCmdMsgOut text file
@return motRPM: Array containing commanded motor RPM values
@return motdT:  Array containing time durations for each RPM instruction
@return motT:   Array containing times at which the motor commands occur
'''

def parseMotCmdMsgOut(fileIn):
    line = fileIn.readline()
    if "Could not open input file" in line:
        print("Issue with ")
    while "Summary" not in line and line:
        line = fileIn.readline()

    for i in range(4):
        line = fileIn.readline()

    # motCmdInstructions = []
    motRPM = []
    motdT = []
    motT = []

    while line:
        line = fileIn.readline()
        line = line.replace("RPM", "")
        line = [l.strip() for l in line.split()]
        if len(line) < 5:
            continue
        motRPM.append(int(line[-1]))
        motdT.append(float(line[2]))
        motT.append(float(line[1]))

    return motRPM, motdT, motT

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseMsgOut()
@brief           Parse through MsgOut text file and extracts data for relevant command timestamps
@param fileIn:   Open MsgOut text file
@return msgOutT: Array containing timestamps for relevant SBC commands
'''

def parseMsgOut(fileIn):

    msgOutT = []

    line = fileIn.readline()

    while "Summary" not in line:
        line = fileIn.readline()

    for _ in range(5):
        line = fileIn.readline()

    while line:
        line = fileIn.readline()
        # if "[BR]" in line or \
        #    "[B ]" in line or \
        #    "[P ]" in line or \
        #    "[AM]" in line or \
        #    "[A ]" in line:

        if "[BR]" in line or \
           "[B ]" in line or \
           "[AM]" in line:
            
            line = [l.strip() for l in line.split()]

            msgOutT.append(float(line[1].replace(":", "")))

    return msgOutT

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseHighLevelPhases()
@brief (UNUSED) Parses RPM commands and times to capture sub-phases
'''

def parsePhases(risRPM, motRPM, motT, phase):
    # outfilename = "SubPhaseDurationsOut.csv"
    # fileOut = open(outfilename, "wt")

    timestamps = []
    durationsdict = {}
    durations = []

    shift = 0
    while motRPM[shift-1] != 100:
        shift += 1

    shift += 1

    #### Finding the different stages
    for i in range(len(motRPM)):
        match(phase):
            case Phase.INIT:
                if motRPM[i] == 100:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] # first entry, will be different than the rest
                    durations.append(timestamps[-1])
                    phase = Phase.BARCODE

            case Phase.BARCODE:
                if motRPM[i] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.TRAN2SEPARATE

            case Phase.TRAN2SEPARATE:
                if risRPM[i-shift] == -5500:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    # durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    phase = Phase.SEPARATE

            case Phase.SEPARATE:
                if risRPM[i-shift] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.TRAN2PRIMES1S2
            
            case Phase.TRAN2PRIMES1S2:
                if risRPM[i-shift] == 100:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    # durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    phase = Phase.PRIMES1S2
            
            case Phase.PRIMES1S2:
                if risRPM[i-shift] == 1500:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READCHECK1

            case Phase.READCHECK1:
                if risRPM[i-shift] == 4000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.TRAN2MIXCHAMBER

            case Phase.TRAN2MIXCHAMBER:
                if risRPM[i-shift] == 5000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    # durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    phase = Phase.MIXCHAMBER

            case Phase.MIXCHAMBER:
                if risRPM[i-shift] == 4000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.MIX1

            case Phase.MIX1:
                if risRPM[i-shift] == 1500:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READCHECK2
                    
            case Phase.READCHECK2:
                if risRPM[i-shift] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.TRAN2PRIMES3

            case Phase.TRAN2PRIMES3:
                if risRPM[i-shift] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    # durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    phase = Phase.PRIMES3

            case Phase.PRIMES3:
                
                if risRPM[i-shift] == 3000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.TRAN2DISTRIBUTECHEMS

            case Phase.TRAN2DISTRIBUTECHEMS:
                if risRPM[i-shift] == 4000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    # durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    phase = Phase.DISTRIBUTECHEMS

            case Phase.DISTRIBUTECHEMS:
                if risRPM[i-shift] == 1000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READCHECK3
                    
            case Phase.READCHECK3:
                if risRPM[i-shift] == 1000:
                    if risRPM[i-1] != 1000:
                        timestamps.append(motT[i])
                        # fileOut.write("%f\n" % motT[i])
                        durationsdict[phase] = timestamps[-1] - timestamps[-2]
                        durations.append(timestamps[-1] - timestamps[-2])
                        phase = Phase.TRAN2MIX2

            case Phase.TRAN2MIX2:
                if risRPM[i-shift] == -1900:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    # durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    phase = Phase.MIX2

            case Phase.MIX2:
                if risRPM[i-shift] == 1500:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READ

            case Phase.READ:
                if risRPM[i-shift] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    break

    # fileOut.close()
    return timestamps, durations, durationsdict

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseHighLevelPhases()
@brief (UNUSED) Parses RPM commands and times to capture high-level phases
'''

def parseHighLevelPhases(risRPM, motRPM, motT, phase):
    # outfilename = "HighLevelPhaseDurationsOut.csv"
    # fileOut = open(outfilename, "wt")

    timestamps = []
    durationsdict = {}
    durations = []

    shift = 0
    while motRPM[shift-1] != 100:
        shift += 1

    shift += 1

    #### Finding the different stages
    for i in range(len(motRPM)):
        # print(i, phase, motT[i], motRPM[i], risRPM[i-shift])
        match(phase):
            case Phase.INIT:
                if motRPM[i] == 100:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] # first entry, will be different than the rest
                    durations.append(timestamps[-1])
                    phase = Phase.BARCODE

            case Phase.BARCODE:
                # TODO: Check whether SEPARATE begins at -3000 or at 0RPM after the barcode read
                if motRPM[i] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.SEPARATE

            case Phase.SEPARATE:
                if risRPM[i-shift] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.PRIMES1S2
            
            case Phase.PRIMES1S2:
                if risRPM[i-shift] == 1500:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READCHECK1

            case Phase.READCHECK1:
                if risRPM[i-shift] == 4000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.MIXCHAMBER

            case Phase.MIXCHAMBER:
                if risRPM[i-shift] == 4000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.MIX1

            case Phase.MIX1:
                if risRPM[i-shift] == 1500:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READCHECK2
                    
            case Phase.READCHECK2:
                if risRPM[i-shift] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.PRIMES3

            case Phase.PRIMES3:
                
                if risRPM[i-shift] == 3000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.DISTRIBUTECHEMS

            case Phase.DISTRIBUTECHEMS:
                if risRPM[i-shift] == 1000:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READCHECK3
                    
            case Phase.READCHECK3:
                if risRPM[i-shift] == 1000:
                    if risRPM[i-1] != 1000:
                        timestamps.append(motT[i])
                        # fileOut.write("%f\n" % motT[i])
                        durationsdict[phase] = timestamps[-1] - timestamps[-2]
                        durations.append(timestamps[-1] - timestamps[-2])
                        phase = Phase.MIX2

            case Phase.MIX2:
                if risRPM[i-shift] == 1500:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    phase = Phase.READ

            case Phase.READ:
                if risRPM[i-shift] == 0:
                    timestamps.append(motT[i])
                    # fileOut.write("%f\n" % motT[i])
                    durationsdict[phase] = timestamps[-1] - timestamps[-2]
                    durations.append(timestamps[-1] - timestamps[-2])
                    break

    # fileOut.close()
    return timestamps, durations, durationsdict

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
durationStats()
@brief                 (UNUSED) Calculates the statistics of each phase duration comparatively to all other analyses
@param all_durations:  Array containing durations of all phases
@param phases:         Array containing names of all phases in order
@param specific_phase: Indicates whether only statistics for a specific phase should be calculated
@return:               None 
'''

def durationStats(all_durations, phases, specific_phase = None):
    if specific_phase == None:
        # Find the statistics for all of the columns
        n = len(all_durations[0]) # number of columns
        # want to handle one column at a time
        for i in range(n):
            vals = []
            for d in all_durations:
                vals.append(d[i])
            print(phases[i])
            print("\tavg: %10.5f" % np.mean(vals))
            print("\tmin: %10.5f" % np.min(vals))
            print("\tmax: %10.5f" % np.max(vals))
            print("\tstd: %10.5f" % np.std(vals))

    else:
        # Find the statistics for just the one column index
        vals = []
        index = phases.index(specific_phase)
        for d in all_durations:
            vals.append(d[index])

        print(phases[index])
        print("\tavg: %10.5f" % np.mean(vals))
        print("\tmin: %10.5f" % np.min(vals))
        print("\tmax: %10.5f" % np.max(vals))
        print("\tstd: %10.5f" % np.std(vals))

    return

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
printSectionStatistics()
@brief       Calculate and print statistics for different acceleration/flat sections of the motor speeds
@param vals: Open MotCmdMsgOut text file
@return min: Minimum value in the input array
@return max: Maximum value in the input array
@return avg: Average of values in input array
@return std: Standarad deviation of values
'''

def printSectionStatistics(vals, fileOut=None):
    if fileOut == None:
        print("  Min = %f" % np.min(vals))
        print("  Max = %f" % np.max(vals))
        print("  Avg = %f" % np.mean(vals))
        print("  Std = %f" % np.std(vals))
    else:
        fileOut.write("  Min = %f\n" % np.min(vals))
        fileOut.write("  Max = %f\n" % np.max(vals))
        fileOut.write("  Avg = %f\n" % np.mean(vals))
        fileOut.write("  Std = %f\n" % np.std(vals))
    return np.min(vals), np.max(vals), np.mean(vals), np.std(vals)

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
bestFitLine()
@brief         Calculate and print values for the line of best fit associated with scatter plot value inputs
@param x:      Array containing timestamps associated with the RPM values in the y array
@param y:      Array containing RPM values associated with the timestamps in the x array
@param polynomialOrder: Polynomial order with which to calculate the best-fit line
@return slope: Slope of the calculated best-fit line
'''

def bestFitLine(x, y, polynomialOrder, fileOut=None):
    fittedParameters = np.polyfit(x, y, polynomialOrder)
    modelPredictions = np.polyval(fittedParameters, x)
    absError = modelPredictions - y
    SE = np.square(absError) # squared errors
    MSE = np.mean(SE) # mean squared errors
    RMSE = np.sqrt(MSE) # Root Mean Squared Error, RMSE
    Rsquared = 1.0 - (np.var(absError) / np.var(y))
    if fileOut == None:
        print("  Best fit line:")
        print('    Slope:    ', fittedParameters[0])
        print('    Intercept:', fittedParameters[1])
        print('    RMSE:     ', RMSE)
        print('    R-squared:', Rsquared)
    else:
        fileOut.write("  Best fit line:\n")
        fileOut.write('    Slope:     %f\n' % fittedParameters[0])
        fileOut.write('    Intercept: %f\n' % fittedParameters[1])
        fileOut.write('    RMSE:      %f\n' % RMSE)
        fileOut.write('    R-squared: %f\n' % Rsquared)

    return fittedParameters[0]

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
calculateError()
@brief                 Calculate and print error statistic values
@param expected:       The expected value (either slope or RPM)
@param actual:         The actual value produced by motor RPM graph
@return error_offset:  Amount by which the actual value differs from the expected value
@return error_percent: Percent error
'''

def calculateError(expected, actual, fileOut=None):
    error_offset = actual - expected
    error_percent = ((actual - expected) / expected) * 100
    if fileOut == None:
        print("  Error calculations:")
        print("    Expected:", expected)
        print("    Actual:  ", actual)
        print("    Offset:  ", error_offset)
        print("    Percent:  %3.3f%%" % error_percent)
        if error_percent > 10.0:
            print("    ERROR PERCENT > 10.0%")
    else:
        fileOut.write("  Error calculations:\n")
        fileOut.write("    Expected: %f\n" % expected)
        fileOut.write("    Actual:   %f\n" % actual)
        fileOut.write("    Offset:   %f\n" % error_offset)
        fileOut.write("    Percent:  %3.3f%%\n" % error_percent)
        if error_percent > 10.0:
            fileOut.write("    ERROR PERCENT > 10.0%\n")
    return error_offset, error_percent

#-----------------------------------------------------------------------------------------------------------------------------------------#
'''
findMotCmdTolerances()
@brief         Calculates and prints statistics and tolerances for each section (flat & accl) parts of the motor RPM plot
@param motT:   Array containing timestamps for motor commands
@param motRPM: Array containing commanded motor RPM
@param risRPM: Array containing commanded RIS motor RPM
@param xtime:  Array containing timestamp values for each step of the actual motor RPM plot
@param yrpm:   Array containing motor RPM values for each step of the actual motor RPM plot
@return:       None
'''

def findMotCmdTolerances(motT, motRPM, risRPM, risAccl, xtime, yrpm, fileOut):

    idx = 0
    WINDOW = 0.80

    shift = 0
    while motRPM[shift-1] != 100:
        shift += 1

    shift += 1

    ## BARCODE

    while motRPM[idx] != 100:
        idx += 1

    barcode_vals = []
    t_barcodeStart = motT[idx]      # The time the motor command was given, NOT the start of the phase
    t_barcodeEnd = motT[idx + 1]    # The time the motor command was ended, NOT the end of the phase
    t_barcodeFindTolStart = ( t_barcodeEnd - ( WINDOW * ( t_barcodeEnd - t_barcodeStart ) ) )  # Approximate range to look at the values. Ignores the time spent getting motor up to 100RPM

    ## UNDEFINED?

    ## ACCELERATION 1 TO SEPARATE

    while motRPM[idx] != -3000:
        idx += 1

    separate_0toN3000_vals = []
    t_separate0toN3000Start = motT[idx]
    t_separate0toN3000End = motT[idx + 1]
    t_separate0toN3000FindTolStart = ( t_separate0toN3000Start + ( (1-WINDOW) * ( t_separate0toN3000End - t_separate0toN3000Start ) / 2 ) )
    t_separate0toN3000FindTolEnd = ( t_separate0toN3000End - ( (1-WINDOW) * ( t_separate0toN3000End - t_separate0toN3000Start ) / 2 ) )

    exp_separate_0toN3000_slope = risAccl[idx-shift]

    ## SEPARATE DECELERATION VAL -> SEPARATE

    while motRPM[idx] != -5500:
        idx += 1

    separate_N3000toN5500_vals = []
    t_separateN3000toN5500Start = motT[idx]
    t_separateN3000toN5500End = motT[idx + 1]
    t_separateN3000toN5500FindTolStart = ( t_separateN3000toN5500Start + ( (1-WINDOW) * ( t_separateN3000toN5500End - t_separateN3000toN5500Start ) / 2 ) )
    t_separateN3000toN5500FindTolEnd = ( t_separateN3000toN5500End - ( (1-WINDOW) * ( t_separateN3000toN5500End - t_separateN3000toN5500Start ) / 2 ) )

    exp_separate_N3000toN5500_slope = risAccl[idx-shift]
            
    ## SEPARATE

    idx += 1

    separate_vals = []
    t_separateStart = motT[idx]     # Adding one to the index because we want the flat part, not the transition from -3000 -> -5500

    while motRPM[idx] != 0:
        idx += 1
    
    t_separateEnd = motT[idx]
    t_separateFindTolStart = ( t_separateEnd - ( WINDOW * ( t_separateEnd - t_separateStart ) ) )

    exp_separate_val = risRPM[idx-shift-1]

    ## PRIME S1/S2 ACCELERATION & OVERSHOOT

    # NOTE: If the motor is at 0 then there won't be any readings, so we can't collect data on the actual prime motor speed

    while motRPM[idx] != 0:
        idx += 1

    primes1s2_N5500to0_vals = []
    primes1s2_overshoot_vals = []
    t_primes1s2Start = motT[idx]
    t_primes1s2End = motT[idx + 1]

    exp_primes1s2_slope = risAccl[idx-shift]

    ## UNNAMED

    while motRPM[idx] != 100:
        idx += 1
    
    unnamed_vals = []
    t_unnamedStart = motT[idx]
    t_unnamedEnd = motT[idx + 1]
    t_unnamedFindTolStart = ( t_unnamedEnd - ( WINDOW * ( t_unnamedEnd - t_unnamedStart ) ) )

    exp_unnamed_val = risRPM[idx-shift]
    
    ## READ CHECK 1

    while motRPM[idx] != 1500:
        idx += 1

    readcheck1_P100toP1500_vals = []
    readcheck1_P100toP1500_overshoot_vals = []
    readcheck1_vals = []
    t_readCheck1Start = motT[idx]

    while motRPM[idx] != 4000:
        idx += 1
    
    t_readCheck1End = motT[idx]
    t_readCheck1FindTolStart = ( t_readCheck1End - ( WINDOW * ( t_readCheck1End - t_readCheck1Start ) ) )
    t_readCheck1P100toP1500FindTolStart = t_readCheck1Start + ((1-WINDOW) * (t_readCheck1FindTolStart-t_readCheck1Start) / 2)

    exp_readcheck1_slope = risAccl[idx-shift]
    exp_readcheck1_val = risRPM[idx-shift-1]

    ## ACCELERATION TO MOVE TO MIX CHAMBER

    mtmc_P1500toP4000_overshoot_vals = []
    mtmc_P1500toP4000_vals = []
    t_MTMCP100toP4000Start = motT[idx] + ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )
    t_MTMCP100toP4000End = motT[idx + 1] - ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )

    exp_mtmc_P1500toP4000_slope = risAccl[idx-shift]

    ## MOVE TO MIX CHAMBER

    while motRPM[idx] != 5000:
        idx += 1
    
    mtmc_P4000toP5000_overshoot_vals = []
    mtmc_P4000toP5000_vals = []
    movetomixchamber_vals = []
    t_moveToMixChamberStart = motT[idx]
    t_moveToMixChamberEnd = motT[idx + 1]

    exp_mtmc_P4000toP5000_slope = risAccl[idx-shift]
    exp_mtmc_val = risRPM[idx-shift]

    idx += 1

    ## MIX SAMPLE

    mixsample_1000to4000_vals = []
    mixsample_4000to5000_vals = []
    mixsample_5000to1000_vals = []
    temp_mixsample_1000to4000_vals = []
    temp_mixsample_4000to5000_vals = []
    temp_mixsample_5000to1000_vals = []
    t_mixSample1000 = []
    t_mixSample4000 = []
    t_mixSample5000 = []
    exp_mixsample_1000to4000_slope = []
    exp_mixsample_4000to5000_slope = []
    exp_mixsample_5000to1000_slope = []

    while motRPM[idx + 1] != 1500:
        if motRPM[idx] == 1000:
            t_mixSample1000.append(motT[idx])
            exp_mixsample_1000to4000_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == 4000:
            t_mixSample4000.append(motT[idx])
            exp_mixsample_4000to5000_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == 5000:
            t_mixSample5000.append(motT[idx])
            exp_mixsample_5000to1000_slope.append(risAccl[idx-shift])
        idx += 1

    mixsample_t0_start = t_mixSample1000[0] + (((t_mixSample4000[0] - t_mixSample1000[0]) * (1-WINDOW)) / 2)  # divide by 2 because we are tailoring this timerange on both ends
    mixsample_t0_end   = t_mixSample4000[0] - (((t_mixSample4000[0] - t_mixSample1000[0]) * (1-WINDOW)) / 2)
    mixsample_t1_start = t_mixSample4000[0] + (((t_mixSample5000[0] - t_mixSample4000[0]) * (1-WINDOW)) / 2)
    mixsample_t1_end   = t_mixSample5000[0] - (((t_mixSample5000[0] - t_mixSample4000[0]) * (1-WINDOW)) / 2)
    mixsample_t2_start = t_mixSample5000[0] + (((t_mixSample1000[1] - t_mixSample5000[0]) * (1-WINDOW)) / 2)
    mixsample_t2_end   = t_mixSample1000[1] - (((t_mixSample1000[1] - t_mixSample5000[0]) * (1-WINDOW)) / 2)

    ## READ CHECK 2

    while motRPM[idx] != 1500:
        idx += 1

    readcheck2_P5000toP1500_vals = []
    readcheck2_P5000toP1500_overshoot_vals = []
    readcheck2_vals = []
    t_readCheck2Start = motT[idx]    
    t_readCheck2End = motT[idx + 1]
    t_readCheck2FindTolStart = ( t_readCheck2End - ( WINDOW * ( t_readCheck2End - t_readCheck2Start ) ) )
    t_readCheck2P5000toP1500FindTolStart = t_readCheck2Start + ((1-WINDOW) * (t_readCheck2FindTolStart-t_readCheck2Start) / 2)

    exp_readcheck2_slope = risAccl[idx-shift]
    exp_readcheck2_val = risRPM[idx-shift]

    ## PRIME S3 ACCELERATION & OVERSHOOT

    while motRPM[idx] != 0:
        idx += 1
    
    primes3_P1500to0_vals = []
    primes3_overshoot_vals = []
    t_primes3Start = motT[idx] + ( (1-WINDOW) * (motT[idx+1]-motT[idx]) / 2 )

    exp_primes3_slope = risAccl[idx-shift]

    while motRPM[idx] != 3000:
        idx += 1
    
    t_primes3End = motT[idx] # Not altering this one because we want to get the overshoot as well

    ## ACCELERATION 1 TO DISTRIBUTE CHEMISTRIES

    while motRPM[idx] != 3000:
        idx += 1

    distchems_0toP3000_overshoot_vals = []
    distchems_0toP3000_vals = []
    t_distChems0toP3000Start = motT[idx] + ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )
    t_distChems0toP3000End = motT[idx+1] - ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )

    exp_distchems_0toP3000_slope = risAccl[idx-shift]

    ## DISTRIBUTE CHEMISTRIES

    while motRPM[idx] != 4000:
        idx += 1

    distChems_P3000toP4000_vals = []
    distchems_vals = []
    t_distChemsStart = motT[idx]
    t_distchemsEnd = motT[idx + 1]

    exp_distchems_P3000toP4000_slope = risAccl[idx-shift]
    exp_distchems_vals = risRPM[idx-shift]

    ## READ CHECK 3

    while motRPM[idx] != 1500:
        idx += 1

    readcheck3_P4000toP1500_vals = []
    readcheck3_P4000toP1500_overshoot_vals = []
    readcheck3_vals = []
    t_readCheck3Start = motT[idx]    
    t_readCheck3End = motT[idx + 1]
    t_readCheck3FindTolStart = ( t_readCheck3End - ( WINDOW * ( t_readCheck3End - t_readCheck3Start ) ) )
    t_readCheck3P4000toP1500FindTolStart = t_readCheck3Start + ((1-WINDOW) * (t_readCheck3FindTolStart-t_readCheck3Start) / 2)

    exp_readcheck3_slope = risAccl[idx-shift]
    exp_readcheck3_val = risRPM[idx-shift]

    ## MIX CHEMISTRIES
    idx += 1

    mixchems_P1000toP1000_vals = []
    mixchems_P1000toN1900_vals = [] # accl
    mixchems_N1900toN1000_vals = [] # accl
    mixchems_N1000toN1000_vals = []
    mixchems_N1000toP1900_vals = [] # accl
    mixchems_P1900toP1000_vals = [] # accl

    temp_mixchems_P1000toP1000_vals = []
    temp_mixchems_P1000toN1900_vals = [] # accl
    temp_mixchems_N1900toN1000_vals = [] # accl
    temp_mixchems_N1000toN1000_vals = []
    temp_mixchems_N1000toP1900_vals = [] # accl
    temp_mixchems_P1900toP1000_vals = [] # accl

    t_mixChemsP1000toP1000 = []
    t_mixChemsP1000toN1900 = []
    t_mixChemsN1900toN1000 = []
    t_mixChemsN1000toN1000 = []
    t_mixChemsN1000toP1900 = []
    t_mixChemsP1900toP1000 = []

    exp_mixchems_P1000toP1000_val = []
    exp_mixchems_P1000toN1900_slope = []
    exp_mixchems_N1900toN1000_slope = []
    exp_mixchems_N1000toN1000_val = []
    exp_mixchems_N1000toP1900_slope = []
    exp_mixchems_P1900toP1000_slope = []

    while motRPM[idx] != 1500:
        if motRPM[idx] == 1000 and motRPM[idx+1] == -1900:
           t_mixChemsP1000toP1000.append(motT[idx])
           exp_mixchems_P1000toP1000_val.append(risRPM[idx-shift])
        elif motRPM[idx] == -1900 and motRPM[idx+1] == -1000:
            t_mixChemsP1000toN1900.append(motT[idx])
            exp_mixchems_P1000toN1900_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == -1000 and motRPM[idx+1] == -1000:
            t_mixChemsN1900toN1000.append(motT[idx])
            exp_mixchems_N1900toN1000_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == -1000 and motRPM[idx+1] == 1900:
            t_mixChemsN1000toN1000.append(motT[idx])
            exp_mixchems_N1000toN1000_val.append(risRPM[idx-shift])
        elif motRPM[idx] == 1900 and motRPM[idx+1] == 1000:
            t_mixChemsN1000toP1900.append(motT[idx])
            exp_mixchems_N1000toP1900_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == 1000 and motRPM[idx+1] == 1000:
            t_mixChemsP1900toP1000.append(motT[idx])
            exp_mixchems_P1900toP1000_slope.append(risAccl[idx-shift])
        idx += 1
    
    mixchems_t0_start = t_mixChemsP1900toP1000[0] + (((t_mixChemsP1000toP1000[0] - t_mixChemsP1900toP1000[0]) * (1-WINDOW)) / 2)
    mixchems_t0_end   = t_mixChemsP1000toP1000[0] - (((t_mixChemsP1000toP1000[0] - t_mixChemsP1900toP1000[0]) * (1-WINDOW)) / 2)
    mixchems_t1_start = t_mixChemsP1000toP1000[0] + (((t_mixChemsP1000toN1900[0] - t_mixChemsP1000toP1000[0]) * (1-WINDOW)) / 2)
    mixchems_t1_end   = t_mixChemsP1000toN1900[0] - (((t_mixChemsP1000toN1900[0] - t_mixChemsP1000toP1000[0]) * (1-WINDOW)) / 2)
    mixchems_t2_start = t_mixChemsP1000toN1900[0] + (((t_mixChemsN1900toN1000[0] - t_mixChemsP1000toN1900[0]) * (1-WINDOW)) / 2)
    mixchems_t2_end   = t_mixChemsN1900toN1000[0] - (((t_mixChemsN1900toN1000[0] - t_mixChemsP1000toN1900[0]) * (1-WINDOW)) / 2)
    mixchems_t3_start = t_mixChemsN1900toN1000[0] + (((t_mixChemsN1000toN1000[0] - t_mixChemsN1900toN1000[0]) * (1-WINDOW)) / 2)
    mixchems_t3_end   = t_mixChemsN1000toN1000[0] - (((t_mixChemsN1000toN1000[0] - t_mixChemsN1900toN1000[0]) * (1-WINDOW)) / 2)
    mixchems_t4_start = t_mixChemsN1000toN1000[0] + (((t_mixChemsN1000toP1900[0] - t_mixChemsN1000toN1000[0]) * (1-WINDOW)) / 2)
    mixchems_t4_end   = t_mixChemsN1000toP1900[0] - (((t_mixChemsN1000toP1900[0] - t_mixChemsN1000toN1000[0]) * (1-WINDOW)) / 2)
    mixchems_t5_start = t_mixChemsN1000toP1900[0] + (((t_mixChemsP1900toP1000[1] - t_mixChemsN1000toP1900[0]) * (1-WINDOW)) / 2)
    mixchems_t5_end   = t_mixChemsP1900toP1000[1] - (((t_mixChemsP1900toP1000[1] - t_mixChemsN1000toP1900[0]) * (1-WINDOW)) / 2)

    ## ACCELERATION TO READ

    read_P1000toP1500_vals = []
    t_readP1000toP1500Start = motT[idx] + ((1-WINDOW) * (motT[idx+1]-motT[idx]) / 2)
    t_readP1000toP1500End = motT[idx+1] - ((1-WINDOW) * (motT[idx+1]-motT[idx]) / 2)

    exp_read_slope = risAccl[idx-shift]

    ## READ

    while motRPM[idx] != 1500:
        idx += 1

    read_vals = []
    t_readStart = motT[idx]

    while motRPM[idx] != 0:
        idx += 1

    t_readEnd = motT[idx]
    t_readFindTolStart = ( t_readEnd - ( WINDOW * ( t_readEnd - t_readStart ) ) )

    exp_read_val = risRPM[idx-shift-1]

    ## Find the tolerances

    accl_counter = 0
    ACCL_STEP_SIZE = 1

    x_separate_0toN3000_vals = []
    y_separate_0toN3000_vals = []

    x_separate_N3000toN5500_vals = []
    y_separate_N3000toN5500_vals = []

    PRIMES1S2_ACCL = True
    x_primes1s2_N5500to0_vals = []
    y_primes1s2_N5500to0_vals = []

    READCHECK1_ACCL = True
    x_readcheck1_P100toP1500_vals = []
    y_readcheck1_P100toP1500_vals = []

    PRIMES3_ACCL = True
    x_primes3_P1500to0_vals = []
    y_primes3_P1500to0_vals = []

    TOMIXCHAMBER1_ACCL = True
    x_mtmc_P1500toP4000_vals = []
    y_mtmc_P1500toP4000_vals = []

    TOMIXCHAMBER2_ACCL = True
    x_mtmc_P4000toP5000_vals = []
    y_mtmc_P4000toP5000_vals = []

    TODISTCHEMS1_ACCL = True
    x_distchems_0toP3000_vals = []
    y_distchems_0toP3000_vals = []

    TODISTCHEMS2_ACCL = True
    x_distChems_P3000toP4000_vals = []
    y_distChems_P3000toP4000_vals = []

    MIXSAMPLE1000_ACCL = True
    x_mixsample_1000to4000 = [] # for best fit line
    y_mixsample_1000to4000 = []
    x_temp_mixsample_1000to4000 = []
    y_temp_mixsample_1000to4000 = []

    MIXSAMPLE4000_ACCL = True
    x_mixsample_4000to5000 = []
    y_mixsample_4000to5000 = []
    x_temp_mixsample_4000to5000 = []
    y_temp_mixsample_4000to5000 = []

    MIXSAMPLE5000_ACCL = True
    x_mixsample_5000to1000 = []
    y_mixsample_5000to1000 = []
    x_temp_mixsample_5000to1000 = []
    y_temp_mixsample_5000to1000 = []

    mixsample_counter = 0

    READCHECK2_ACCL = True
    x_readcheck2_P5000toP1500_vals = []
    y_readcheck2_P5000toP1500_vals = []

    READCHECK3_ACCL = True
    x_readcheck3_P4000toP1500_vals = []
    y_readcheck3_P4000toP1500_vals = []
    
    MIXCHEMSP1000TON1900_ACCL = True
    x_mixchems_P1000toN1900_vals = []
    y_mixchems_P1000toN1900_vals = []
    x_temp_mixchems_P1000toN1900_vals = []
    y_temp_mixchems_P1000toN1900_vals = []

    MIXCHEMSN1900TON1000_ACCL = True
    x_mixchems_N1900toN1000_vals = []
    y_mixchems_N1900toN1000_vals = []
    x_temp_mixchems_N1900toN1000_vals = []
    y_temp_mixchems_N1900toN1000_vals = []

    MIXCHEMSN1000TOP1900_ACCL = True
    x_mixchems_N1000toP1900_vals = []
    y_mixchems_N1000toP1900_vals = []
    x_temp_mixchems_N1000toP1900_vals = []
    y_temp_mixchems_N1000toP1900_vals = []

    MIXCHEMSP1900TOP1000_ACCL = True
    x_mixchems_P1900toP1000_vals = []
    y_mixchems_P1900toP1000_vals = []
    x_temp_mixchems_P1900toP1000_vals = []
    y_temp_mixchems_P1900toP1000_vals = []    

    mixchems_counter = 0

    TOREAD_ACCL = True
    x_read_P1000toP1500_vals = []
    y_read_P1000toP1500_vals = []

    for i, t in enumerate(xtime):

        if t < t_barcodeFindTolStart:
            continue

        elif t > t_barcodeFindTolStart and t < t_barcodeEnd:
            barcode_vals.append(yrpm[i])

        elif t > t_separate0toN3000FindTolStart and t < t_separate0toN3000FindTolEnd:
            x_separate_0toN3000_vals.append(t)
            y_separate_0toN3000_vals.append(yrpm[i])
            if accl_counter % ACCL_STEP_SIZE == 0:
                dt = t - xtime[i-ACCL_STEP_SIZE]
                dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                separate_0toN3000_vals.append(dv / dt)
                accl_counter = 0
            accl_counter += 1

        elif t > t_separateN3000toN5500FindTolStart and t < t_separateN3000toN5500FindTolEnd:
            x_separate_N3000toN5500_vals.append(t)
            y_separate_N3000toN5500_vals.append(yrpm[i])
            if accl_counter % ACCL_STEP_SIZE == 0:
                dt = t - xtime[i-ACCL_STEP_SIZE]
                dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                separate_N3000toN5500_vals.append(dv / dt)
                accl_counter = 0
            accl_counter += 1

        elif t > t_separateFindTolStart and t < t_separateEnd:
            separate_vals.append(yrpm[i])

        elif t > t_primes1s2Start and t < t_primes1s2End:
            # The first part of this is the acceleration to prime, and the second part is the overshoot
            if PRIMES1S2_ACCL:
                if yrpm[i] > 0:
                    PRIMES1S2_ACCL = False
                x_primes1s2_N5500to0_vals.append(t)
                y_primes1s2_N5500to0_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    primes1s2_N5500to0_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                primes1s2_overshoot_vals.append(yrpm[i])

        elif t > t_unnamedFindTolStart and t < t_unnamedEnd:
            unnamed_vals.append(yrpm[i])

        elif t > t_readCheck1P100toP1500FindTolStart and t < t_readCheck1FindTolStart:
            if READCHECK1_ACCL:
                if yrpm[i] > 1500:
                    READCHECK1_ACCL = False
                x_readcheck1_P100toP1500_vals.append(t)
                y_readcheck1_P100toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    readcheck1_P100toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                readcheck1_P100toP1500_overshoot_vals.append(yrpm[i])

        elif t > t_readCheck1FindTolStart and t < t_readCheck1End:
            readcheck1_vals.append(yrpm[i])

        elif t > t_MTMCP100toP4000Start and t < t_MTMCP100toP4000End:
            if TOMIXCHAMBER1_ACCL:
                if yrpm[i] > 4000:
                    TOMIXCHAMBER1_ACCL = False
                x_mtmc_P1500toP4000_vals.append(t)
                y_mtmc_P1500toP4000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    mtmc_P1500toP4000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                mtmc_P1500toP4000_overshoot_vals.append(yrpm[i])

        elif t > t_moveToMixChamberStart and t < t_moveToMixChamberEnd:
            if TOMIXCHAMBER2_ACCL:
                if yrpm[i] > 5000:
                    TOMIXCHAMBER2_ACCL = False
                x_mtmc_P4000toP5000_vals.append(t)
                y_mtmc_P4000toP5000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    mtmc_P4000toP5000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                movetomixchamber_vals.append(yrpm[i])

        elif t > t_mixSample1000[0] and t < t_readCheck2Start:
            if mixsample_counter < 11:
                if t > t_mixSample1000[mixsample_counter+1]:
                    mixsample_counter += 1
                    # Reset variables
                    x_mixsample_1000to4000.append(x_temp_mixsample_1000to4000)
                    y_mixsample_1000to4000.append(y_temp_mixsample_1000to4000)
                    x_mixsample_4000to5000.append(x_temp_mixsample_4000to5000)
                    y_mixsample_4000to5000.append(y_temp_mixsample_4000to5000)
                    x_mixsample_5000to1000.append(x_temp_mixsample_5000to1000)
                    y_mixsample_5000to1000.append(y_temp_mixsample_5000to1000)
                    x_temp_mixsample_1000to4000 = []
                    y_temp_mixsample_1000to4000 = []
                    x_temp_mixsample_4000to5000 = []
                    y_temp_mixsample_4000to5000 = []
                    x_temp_mixsample_5000to1000 = []
                    y_temp_mixsample_5000to1000 = []
                    mixsample_1000to4000_vals.append(temp_mixsample_1000to4000_vals)
                    mixsample_4000to5000_vals.append(temp_mixsample_4000to5000_vals)
                    mixsample_5000to1000_vals.append(temp_mixsample_5000to1000_vals)
                    temp_mixsample_1000to4000_vals = []
                    temp_mixsample_4000to5000_vals = []
                    temp_mixsample_5000to1000_vals = []
                    MIXSAMPLE1000_ACCL = True
                    MIXSAMPLE4000_ACCL = True
                    MIXSAMPLE5000_ACCL = True
                    if mixsample_counter == len(t_mixSample5000):
                        mixsample_t0_start = t_mixSample1000[mixsample_counter] + (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                        mixsample_t0_end   = t_mixSample4000[mixsample_counter] - (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                        mixsample_t1_start = t_mixSample4000[mixsample_counter] + (((t_readCheck2Start - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                        mixsample_t1_end   = t_readCheck2Start - (((t_readCheck2Start - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                        continue
                    mixsample_t0_start = t_mixSample1000[mixsample_counter] + (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t0_end   = t_mixSample4000[mixsample_counter] - (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t1_start = t_mixSample4000[mixsample_counter] + (((t_mixSample5000[mixsample_counter] - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t1_end   = t_mixSample5000[mixsample_counter] - (((t_mixSample5000[mixsample_counter] - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t2_start = t_mixSample5000[mixsample_counter] + (((t_mixSample1000[mixsample_counter+1] - t_mixSample5000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t2_end   = t_mixSample1000[mixsample_counter+1] - (((t_mixSample1000[mixsample_counter+1] - t_mixSample5000[mixsample_counter]) * (1-WINDOW)) / 2)

                if t > mixsample_t0_start and t < mixsample_t0_end:
                    if MIXSAMPLE1000_ACCL:
                        if yrpm[i] < 1000:
                            MIXSAMPLE1000_ACCL = False
                        x_temp_mixsample_1000to4000.append(t)
                        y_temp_mixsample_1000to4000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_1000to4000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixsample_t1_start and t < mixsample_t1_end:
                    if MIXSAMPLE4000_ACCL:
                        if yrpm[i] > 4000:
                            MIXSAMPLE4000_ACCL = False
                        x_temp_mixsample_4000to5000.append(t)
                        y_temp_mixsample_4000to5000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_4000to5000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1
                
                elif t > mixsample_t2_start and t < mixsample_t2_end:
                    if MIXSAMPLE5000_ACCL:
                        if yrpm[i] > 5000:
                            MIXSAMPLE5000_ACCL = False
                        x_temp_mixsample_5000to1000.append(t)
                        y_temp_mixsample_5000to1000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_5000to1000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

            else:
                if t > mixsample_t0_start and t < mixsample_t0_end:
                    if MIXSAMPLE1000_ACCL:
                        if yrpm[i] < 1000:
                            MIXSAMPLE1000_ACCL = False
                        x_temp_mixsample_1000to4000.append(t)
                        y_temp_mixsample_1000to4000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_1000to4000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixsample_t1_start and t < mixsample_t1_end:
                    if MIXSAMPLE4000_ACCL:
                        if yrpm[i] > 4000:
                            MIXSAMPLE4000_ACCL = False
                        x_temp_mixsample_4000to5000.append(t)
                        y_temp_mixsample_4000to5000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_4000to5000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

        elif t > t_readCheck2P5000toP1500FindTolStart and t < t_readCheck2FindTolStart:
            if READCHECK2_ACCL:
                if yrpm[i] < 1500:
                    READCHECK2_ACCL = False
                x_readcheck2_P5000toP1500_vals.append(t)
                y_readcheck2_P5000toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    readcheck2_P5000toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                readcheck2_P5000toP1500_overshoot_vals.append(yrpm[i])

        elif t > t_readCheck2FindTolStart and t < t_readCheck2End:
            readcheck2_vals.append(yrpm[i])

        elif t > t_primes3Start and t < t_primes3End:
            # The first part of this is the acceleration to prime, and the second part is the overshoot
            if PRIMES3_ACCL:
                if yrpm[i] < 0:
                    PRIMES3_ACCL = False
                x_primes3_P1500to0_vals.append(t)
                y_primes3_P1500to0_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    primes3_P1500to0_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                primes3_overshoot_vals.append(yrpm[i])

        elif t > t_distChems0toP3000Start and t < t_distChems0toP3000End:
            if TODISTCHEMS1_ACCL:
                if yrpm[i] > 3000:
                    TODISTCHEMS1_ACCL = False
                x_distchems_0toP3000_vals.append(t)
                y_distchems_0toP3000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    distchems_0toP3000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                distchems_0toP3000_overshoot_vals.append(yrpm[i])
            
        elif t > t_distChemsStart and t < t_distchemsEnd:
            if TODISTCHEMS2_ACCL:
                if yrpm[i] > 4000:
                    TODISTCHEMS2_ACCL = False
                x_distChems_P3000toP4000_vals.append(t)
                y_distChems_P3000toP4000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    distChems_P3000toP4000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                distchems_vals.append(yrpm[i])

        elif t > t_readCheck3P4000toP1500FindTolStart and t < t_readCheck3FindTolStart:
            if READCHECK3_ACCL:
                if yrpm[i] < 1500:
                    READCHECK3_ACCL = False
                x_readcheck3_P4000toP1500_vals.append(t)
                y_readcheck3_P4000toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    readcheck3_P4000toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                readcheck3_P4000toP1500_overshoot_vals.append(yrpm[i])

        elif t > t_readCheck3FindTolStart and t < t_readCheck3End:
            readcheck3_vals.append(yrpm[i])

        elif t > t_mixChemsP1900toP1000[0] and t < t_readStart:
            if mixchems_counter < 33:
                if t > t_mixChemsP1900toP1000[mixchems_counter+1]:
                    mixchems_counter += 1
                    mixchems_P1000toP1000_vals.append(temp_mixchems_P1000toP1000_vals)
                    mixchems_P1000toN1900_vals.append(temp_mixchems_P1000toN1900_vals)
                    mixchems_N1900toN1000_vals.append(temp_mixchems_N1900toN1000_vals)
                    mixchems_N1000toN1000_vals.append(temp_mixchems_N1000toN1000_vals)
                    mixchems_N1000toP1900_vals.append(temp_mixchems_N1000toP1900_vals)
                    mixchems_P1900toP1000_vals.append(temp_mixchems_P1900toP1000_vals)
                    temp_mixchems_P1000toP1000_vals = []
                    temp_mixchems_P1000toN1900_vals = []
                    temp_mixchems_N1900toN1000_vals = []
                    temp_mixchems_N1000toN1000_vals = []
                    temp_mixchems_N1000toP1900_vals = []
                    temp_mixchems_P1900toP1000_vals = []
                    x_mixchems_P1000toN1900_vals.append(x_temp_mixchems_P1000toN1900_vals)
                    y_mixchems_P1000toN1900_vals.append(y_temp_mixchems_P1000toN1900_vals)
                    x_mixchems_N1900toN1000_vals.append(x_temp_mixchems_N1900toN1000_vals)
                    y_mixchems_N1900toN1000_vals.append(y_temp_mixchems_N1900toN1000_vals)
                    x_mixchems_N1000toP1900_vals.append(x_temp_mixchems_N1000toP1900_vals)
                    y_mixchems_N1000toP1900_vals.append(y_temp_mixchems_N1000toP1900_vals)
                    x_mixchems_P1900toP1000_vals.append(x_temp_mixchems_P1900toP1000_vals)
                    y_mixchems_P1900toP1000_vals.append(y_temp_mixchems_P1900toP1000_vals)
                    x_temp_mixchems_P1000toN1900_vals = []
                    y_temp_mixchems_P1000toN1900_vals = []
                    x_temp_mixchems_N1900toN1000_vals = []
                    y_temp_mixchems_N1900toN1000_vals = []
                    x_temp_mixchems_N1000toP1900_vals = []
                    y_temp_mixchems_N1000toP1900_vals = []
                    x_temp_mixchems_P1900toP1000_vals = []
                    y_temp_mixchems_P1900toP1000_vals = []
                    MIXCHEMSP1000TON1900_ACCL = True
                    MIXCHEMSN1900TON1000_ACCL = True
                    MIXCHEMSN1000TOP1900_ACCL = True
                    MIXCHEMSP1900TOP1000_ACCL = True
                    if mixchems_counter == 33:
                        mixchems_t0_start = t_mixChemsP1900toP1000[mixchems_counter] + (((t_readStart - t_mixChemsP1900toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                        mixchems_t0_end   = t_readStart - (((t_readStart - t_mixChemsP1900toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                        continue
                    
                    mixchems_t0_start = t_mixChemsP1900toP1000[mixchems_counter] + (((t_mixChemsP1000toP1000[mixchems_counter] - t_mixChemsP1900toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t0_end   = t_mixChemsP1000toP1000[mixchems_counter] - (((t_mixChemsP1000toP1000[mixchems_counter] - t_mixChemsP1900toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t1_start = t_mixChemsP1000toP1000[mixchems_counter] + (((t_mixChemsP1000toN1900[mixchems_counter] - t_mixChemsP1000toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t1_end   = t_mixChemsP1000toN1900[mixchems_counter] - (((t_mixChemsP1000toN1900[mixchems_counter] - t_mixChemsP1000toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t2_start = t_mixChemsP1000toN1900[mixchems_counter] + (((t_mixChemsN1900toN1000[mixchems_counter] - t_mixChemsP1000toN1900[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t2_end   = t_mixChemsN1900toN1000[mixchems_counter] - (((t_mixChemsN1900toN1000[mixchems_counter] - t_mixChemsP1000toN1900[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t3_start = t_mixChemsN1900toN1000[mixchems_counter] + (((t_mixChemsN1000toN1000[mixchems_counter] - t_mixChemsN1900toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t3_end   = t_mixChemsN1000toN1000[mixchems_counter] - (((t_mixChemsN1000toN1000[mixchems_counter] - t_mixChemsN1900toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t4_start = t_mixChemsN1000toN1000[mixchems_counter] + (((t_mixChemsN1000toP1900[mixchems_counter] - t_mixChemsN1000toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t4_end   = t_mixChemsN1000toP1900[mixchems_counter] - (((t_mixChemsN1000toP1900[mixchems_counter] - t_mixChemsN1000toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t5_start = t_mixChemsN1000toP1900[mixchems_counter] + (((t_mixChemsP1900toP1000[mixchems_counter+1] - t_mixChemsN1000toP1900[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t5_end   = t_mixChemsP1900toP1000[mixchems_counter+1] - (((t_mixChemsP1900toP1000[mixchems_counter+1] - t_mixChemsN1000toP1900[mixchems_counter]) * (1-WINDOW)) / 2)
                    
                if t > mixchems_t0_start and t < mixchems_t0_end:
                    if MIXCHEMSP1900TOP1000_ACCL:
                        if yrpm[i] < 1000:
                            MIXCHEMSP1900TOP1000_ACCL = False
                        x_temp_mixchems_P1900toP1000_vals.append(t)
                        y_temp_mixchems_P1900toP1000_vals.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixchems_P1900toP1000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixchems_t1_start and t < mixchems_t1_end:
                    temp_mixchems_P1000toP1000_vals.append(yrpm[i])
                
                elif t > mixchems_t2_start and t < mixchems_t2_end:
                    if MIXCHEMSP1000TON1900_ACCL:
                        if yrpm[i] < -1900:
                            MIXCHEMSP1000TON1900_ACCL = False
                        x_temp_mixchems_P1000toN1900_vals.append(t)
                        y_temp_mixchems_P1000toN1900_vals.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixchems_P1000toN1900_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixchems_t3_start and t < mixchems_t3_end:
                    if MIXCHEMSN1900TON1000_ACCL:
                        if yrpm[i] > -1000:
                            MIXCHEMSN1900TON1000_ACCL = False
                        x_temp_mixchems_N1900toN1000_vals.append(t)
                        y_temp_mixchems_N1900toN1000_vals.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixchems_N1900toN1000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixchems_t4_start and t < mixchems_t4_end:
                    temp_mixchems_N1000toN1000_vals.append(yrpm[i])

                elif t > mixchems_t5_start and t < mixchems_t5_end:
                    if MIXCHEMSN1000TOP1900_ACCL:
                        if yrpm[i] > 1900:
                            MIXCHEMSN1000TOP1900_ACCL = False
                        x_temp_mixchems_N1000toP1900_vals.append(t)
                        y_temp_mixchems_N1000toP1900_vals.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixchems_N1000toP1900_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1  

            else:
                if t > mixchems_t0_start and t < mixchems_t0_end:
                    if MIXCHEMSP1900TOP1000_ACCL:
                        if yrpm[i] < 1000:
                            MIXCHEMSP1900TOP1000_ACCL = False
                        x_temp_mixchems_P1900toP1000_vals.append(t)
                        y_temp_mixchems_P1900toP1000_vals.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixchems_P1900toP1000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1
                        
        elif t > t_readP1000toP1500Start and t < t_readP1000toP1500End:
            if TOREAD_ACCL:
                if yrpm[i] > 1500:
                    TOREAD_ACCL = False
                x_read_P1000toP1500_vals.append(t)
                y_read_P1000toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    read_P1000toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            
        elif t > t_readFindTolStart and t < t_readEnd:
            read_vals.append(yrpm[i])

    # Print the tolerances
    
    fileOut.write("\nBARCODE\n")
    if len(barcode_vals) > 0:
        printSectionStatistics(barcode_vals, fileOut)

    fileOut.write("\nACCELERATION TO SEPARATE (0RPM to -3000RPM)\n")
    if len(separate_0toN3000_vals) > 0:
        printSectionStatistics(separate_0toN3000_vals, fileOut)
        slope = bestFitLine(x_separate_0toN3000_vals, y_separate_0toN3000_vals, 1, fileOut)
        calculateError(exp_separate_0toN3000_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO SEPARATE (-3000RPM to -5500RPM)\n")
    if len(separate_N3000toN5500_vals) > 0:
        printSectionStatistics(separate_N3000toN5500_vals, fileOut)
        slope = bestFitLine(x_separate_N3000toN5500_vals, y_separate_N3000toN5500_vals, 1, fileOut)
        calculateError(exp_separate_N3000toN5500_slope, slope, fileOut)

    fileOut.write("\nSEPARATE\n")
    if len(separate_vals) > 0:
        _, _, avg, _ = printSectionStatistics(separate_vals, fileOut)
        calculateError(exp_separate_val, avg, fileOut)

    fileOut.write("\nACCELERATION TO PRIME S1/S2 (-5500RPM to 0RPM)\n")
    if len(primes1s2_N5500to0_vals) > 0:
        printSectionStatistics(primes1s2_N5500to0_vals, fileOut)
        slope = bestFitLine(x_primes1s2_N5500to0_vals, y_primes1s2_N5500to0_vals, 1, fileOut)
        calculateError(exp_primes1s2_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO PRIME S1/S2 OVERSHOOT\n")
    if len(primes1s2_overshoot_vals) > 0:
        printSectionStatistics(primes1s2_overshoot_vals, fileOut)

    fileOut.write("\nUNNAMED\n")
    if len(unnamed_vals) > 0:
        _, _, avg, _ = printSectionStatistics(unnamed_vals, fileOut)
        calculateError(exp_unnamed_val, avg, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 1 (100RPM to 1500RPM)\n")
    if len(readcheck1_P100toP1500_vals) > 0:
        printSectionStatistics(readcheck1_P100toP1500_vals, fileOut)
        slope = bestFitLine(x_readcheck1_P100toP1500_vals, y_readcheck1_P100toP1500_vals, 1, fileOut)
        calculateError(exp_readcheck1_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 1 OVERSHOOT\n")
    if len(readcheck1_P100toP1500_overshoot_vals) > 0:
        printSectionStatistics(readcheck1_P100toP1500_overshoot_vals, fileOut)

    fileOut.write("\nREAD CHECK 1\n")
    if len(readcheck1_vals) > 0:
        _, _, avg, _ = printSectionStatistics(readcheck1_vals, fileOut)
        calculateError(exp_readcheck1_val, avg, fileOut)

    fileOut.write("\nACCELERATION TO MIX CHAMBER (1500RPM to 4000RPM)\n")
    if len(mtmc_P1500toP4000_vals) > 0:
        printSectionStatistics(mtmc_P1500toP4000_vals, fileOut)
        slope = bestFitLine(x_mtmc_P1500toP4000_vals, y_mtmc_P1500toP4000_vals, 1, fileOut)
        calculateError(exp_mtmc_P1500toP4000_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO MIX CHAMBER OVERSHOOT\n")
    if len(mtmc_P1500toP4000_overshoot_vals) > 0:
        printSectionStatistics(mtmc_P1500toP4000_overshoot_vals, fileOut)

    fileOut.write("\nACCELERATION TO MIX CHAMBER (4000RPM to 5000RPM)\n")
    if len(mtmc_P4000toP5000_vals) > 0:
        printSectionStatistics(mtmc_P4000toP5000_vals, fileOut)
        slope = bestFitLine(x_mtmc_P4000toP5000_vals, y_mtmc_P4000toP5000_vals, 1, fileOut)
        calculateError(exp_mtmc_P4000toP5000_slope, slope, fileOut)

    fileOut.write("\nMOVE TO MIX CHAMBER\n")
    if len(movetomixchamber_vals) > 0:
        _, _, avg, _ = printSectionStatistics(movetomixchamber_vals, fileOut)
        calculateError(exp_mtmc_val, avg, fileOut)

    fileOut.write("\n**MIX SAMPLE**\n")
    x_mixsample_1000to4000.append(x_temp_mixsample_1000to4000)
    y_mixsample_1000to4000.append(x_temp_mixsample_1000to4000)
    x_mixsample_4000to5000.append(x_temp_mixsample_4000to5000)
    y_mixsample_4000to5000.append(x_temp_mixsample_4000to5000)
    mixsample_1000to4000_vals.append(temp_mixsample_1000to4000_vals)
    mixsample_4000to5000_vals.append(temp_mixsample_4000to5000_vals)
    for i in range(len(mixsample_1000to4000_vals)):
        fileOut.write("\nROUND #%d\n" % i)
        fileOut.write("  5000RPM->1000RPM\n")
        printSectionStatistics(mixsample_1000to4000_vals[i], fileOut)
        slope = bestFitLine(x_mixsample_1000to4000[i], y_mixsample_1000to4000[i], 1, fileOut)
        calculateError(exp_mixsample_1000to4000_slope[i], slope, fileOut)
        fileOut.write("  1000RPM->4000RPM\n")
        printSectionStatistics(mixsample_4000to5000_vals[i], fileOut)
        slope = bestFitLine(x_mixsample_4000to5000[i], y_mixsample_4000to5000[i], 1, fileOut)
        calculateError(exp_mixsample_4000to5000_slope[i], slope, fileOut)
        if i < len(mixsample_5000to1000_vals):
            fileOut.write("  4000RPM->5000RPM\n")
            printSectionStatistics(mixsample_5000to1000_vals[i], fileOut)
            slope = bestFitLine(x_mixsample_5000to1000[i], y_mixsample_5000to1000[i], 1, fileOut)
            calculateError(exp_mixsample_5000to1000_slope[i], slope, fileOut)
    fileOut.write("\n**END OF MIX SAMPLE**\n")
            
    fileOut.write("\nACCELERATION TO READ CHECK 2 (5000RPM to 1500RPM)\n")
    if len(readcheck2_P5000toP1500_vals) > 0:
        printSectionStatistics(readcheck2_P5000toP1500_vals, fileOut)
        slope = bestFitLine(x_readcheck2_P5000toP1500_vals, y_readcheck2_P5000toP1500_vals, 1, fileOut)
        calculateError(exp_readcheck2_slope, slope, fileOut)

    
    fileOut.write("\nACCELERATION TO READ CHECK 2 OVERSHOOT\n")
    if len(readcheck2_P5000toP1500_overshoot_vals) != 0:
        printSectionStatistics(readcheck2_P5000toP1500_overshoot_vals, fileOut)

    fileOut.write("\nREAD CHECK 2\n")
    if len(readcheck2_vals) > 0:
        _, _, avg, _ = printSectionStatistics(readcheck2_vals, fileOut)
        calculateError(exp_readcheck2_val, avg)

    fileOut.write("\nACCELERATION TO PRIME S3 (1500RPM to 0RPM)\n")
    if len(primes3_P1500to0_vals) > 0:
        printSectionStatistics(primes3_P1500to0_vals, fileOut)
        slope = bestFitLine(x_primes3_P1500to0_vals, y_primes3_P1500to0_vals, 1, fileOut)
        calculateError(exp_primes3_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO PRIME S3 OVERSHOOT\n")
    if len(primes3_overshoot_vals) > 0:
        printSectionStatistics(primes3_overshoot_vals, fileOut)

    fileOut.write("\nACCELERATION TO DISTRIBUTE CHEMISTRIES (0RPM to 3000RPM)\n")
    if len(distchems_0toP3000_vals) > 0:
        printSectionStatistics(distchems_0toP3000_vals, fileOut)
        slope = bestFitLine(x_distchems_0toP3000_vals, y_distchems_0toP3000_vals, 1, fileOut)
        calculateError(exp_distchems_0toP3000_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO DISTRIBUTE CHEMISTRIES OVERSHOOT\n")
    if len(distchems_0toP3000_overshoot_vals) != 0:
        printSectionStatistics(distchems_0toP3000_overshoot_vals, fileOut)

    fileOut.write("\nACCELERATION TO DISTRIBUTE CHEMISTRIES (3000RPM to 4000RPM)\n")
    if len(distChems_P3000toP4000_vals) != 0:
        printSectionStatistics(distChems_P3000toP4000_vals, fileOut)
        slope = bestFitLine(x_distChems_P3000toP4000_vals, y_distChems_P3000toP4000_vals, 1, fileOut)
        calculateError(exp_distchems_P3000toP4000_slope, slope, fileOut)

    fileOut.write("\nDISTRIBUTE CHEMISTRIES\n")
    if len(distchems_vals) > 0:
        _, _, avg, _ = printSectionStatistics(distchems_vals, fileOut)
        calculateError(exp_distchems_vals, avg, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 3 (4000RPM to 1500RPM)\n")
    if len(readcheck3_P4000toP1500_vals) > 0:
        printSectionStatistics(readcheck3_P4000toP1500_vals, fileOut)
        slope = bestFitLine(x_readcheck3_P4000toP1500_vals, y_readcheck3_P4000toP1500_vals, 1, fileOut)
        calculateError(exp_readcheck3_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 3 OVERSHOOT\n")
    if len(readcheck3_P4000toP1500_overshoot_vals) != 0:
        printSectionStatistics(readcheck3_P4000toP1500_overshoot_vals, fileOut)

    fileOut.write("\nREAD CHECK 3\n")
    if len(readcheck3_vals) > 0:
        _, _, avg, _ = printSectionStatistics(readcheck3_vals, fileOut)
        calculateError(exp_readcheck3_val, avg, fileOut)
    
    fileOut.write("\n**MIX CHEMISTRIES**\n")
    mixchems_P1000toP1000_vals.append(temp_mixchems_P1000toP1000_vals)
    for i in range(len(mixchems_P1000toN1900_vals)):
        fileOut.write("\nROUND #%d\n" % (i))
        fileOut.write("  * 1900RPM->1000RPM\n")
        printSectionStatistics(mixchems_P1900toP1000_vals[i], fileOut)
        slope = bestFitLine(x_mixchems_P1900toP1000_vals[i], y_mixchems_P1900toP1000_vals[i], 1, fileOut)
        calculateError(exp_mixchems_P1900toP1000_slope[i], slope, fileOut)
        fileOut.write("\n  * 1000RPM->1000RPM\n")
        _, _, avg, _ = printSectionStatistics(mixchems_P1000toP1000_vals[i], fileOut)
        calculateError(exp_mixchems_P1000toP1000_val[i], avg, fileOut)
        fileOut.write("\n  * 1000RPM->-1900RPM\n")
        printSectionStatistics(mixchems_P1000toN1900_vals[i], fileOut)
        slope = bestFitLine(x_mixchems_P1000toN1900_vals[i], y_mixchems_P1000toN1900_vals[i], 1, fileOut)
        calculateError(exp_mixchems_P1000toN1900_slope[i], slope, fileOut)
        fileOut.write("\n  * -1900RPM->-1000RPM\n")
        printSectionStatistics(mixchems_P1900toP1000_vals[i], fileOut)
        slope = bestFitLine(x_mixchems_N1900toN1000_vals[i], y_mixchems_N1900toN1000_vals[i], 1, fileOut)
        calculateError(exp_mixchems_N1900toN1000_slope[i], slope, fileOut)
        fileOut.write("\n  * -1000RPM->-1000RPM\n")
        _, _, avg, _ = printSectionStatistics(mixchems_N1000toN1000_vals[i], fileOut)
        calculateError(exp_mixchems_N1000toN1000_val[i], avg, fileOut)
        fileOut.write("\n  * -1000RPM->1900RPM\n")
        printSectionStatistics(mixchems_N1000toP1900_vals[i], fileOut)
        slope = bestFitLine(x_mixchems_N1000toP1900_vals[i], y_mixchems_N1000toP1900_vals[i], 1, fileOut)
        calculateError(exp_mixchems_N1000toP1900_slope[i], slope, fileOut)
    fileOut.write("\nROUND #33\n")
    fileOut.write("  * 1900RPM->1000RPM\n")
    printSectionStatistics(mixchems_P1900toP1000_vals[i], fileOut)
    slope = bestFitLine(x_mixchems_P1900toP1000_vals[i], y_mixchems_P1900toP1000_vals[i], 1, fileOut)
    calculateError(exp_mixchems_P1900toP1000_slope[i], slope, fileOut)
    fileOut.write("\n**END OF MIX CHEMISTRIES**\n")
    
    fileOut.write("\nACCLERATION TO READ (1000RPM to 1500RPM)\n")
    if len(read_P1000toP1500_vals) > 0:
        printSectionStatistics(read_P1000toP1500_vals, fileOut)
        slope = bestFitLine(x_read_P1000toP1500_vals, y_read_P1000toP1500_vals, 1, fileOut)
        calculateError(exp_read_slope, slope, fileOut)

    fileOut.write("\nREAD\n")
    if len(read_vals) > 0:
        _, _, avg, _ = printSectionStatistics(read_vals, fileOut)
        calculateError(exp_read_val, avg, fileOut)
    fileOut.write("\n")

    return

#-----------------------------------------------------------------------------------------------------------------------------------------#
'''
findMotCmdTolerances_Rotor1()
@brief         Calculates and prints statistics and tolerances for each section (flat & accl) parts of the motor RPM plot
@param motT:   Array containing timestamps for motor commands
@param motRPM: Array containing commanded motor RPM
@param risRPM: Array containing commanded RIS motor RPM
@param xtime:  Array containing timestamp values for each step of the actual motor RPM plot
@param yrpm:   Array containing motor RPM values for each step of the actual motor RPM plot
@return:       None
'''

def findMotCmdTolerances_Rotor1(motT, motRPM, risRPM, risAccl, xtime, yrpm, fileOut):

    idx = 0
    WINDOW = 0.80

    shift = 0
    while motRPM[shift-1] != 100:
        shift += 1

    shift += 1

    ## BARCODE

    while motRPM[idx] != 100:
        idx += 1

    barcode_vals = []
    t_barcodeStart = motT[idx]      # The time the motor command was given, NOT the start of the phase
    t_barcodeEnd = motT[idx + 1]    # The time the motor command was ended, NOT the end of the phase
    t_barcodeFindTolStart = ( t_barcodeEnd - ( WINDOW * ( t_barcodeEnd - t_barcodeStart ) ) )  # Approximate range to look at the values. Ignores the time spent getting motor up to 100RPM

    ## UNDEFINED?

    ## ACCELERATION 1 TO SEPARATE

    while motRPM[idx] != -3000:
        idx += 1

    separate_0toN3000_vals = []
    t_separate0toN3000Start = motT[idx]
    t_separate0toN3000End = motT[idx + 1]
    t_separate0toN3000FindTolStart = ( t_separate0toN3000Start + ( (1-WINDOW) * ( t_separate0toN3000End - t_separate0toN3000Start ) / 2 ) )
    t_separate0toN3000FindTolEnd = ( t_separate0toN3000End - ( (1-WINDOW) * ( t_separate0toN3000End - t_separate0toN3000Start ) / 2 ) )

    exp_separate_0toN3000_slope = risAccl[idx-shift]

    ## SEPARATE DECELERATION VAL -> SEPARATE

    while motRPM[idx] != -5500:
        idx += 1

    separate_N3000toN5500_vals = []
    t_separateN3000toN5500Start = motT[idx]
    t_separateN3000toN5500End = motT[idx + 1]
    t_separateN3000toN5500FindTolStart = ( t_separateN3000toN5500Start + ( (1-WINDOW) * ( t_separateN3000toN5500End - t_separateN3000toN5500Start ) / 2 ) )
    t_separateN3000toN5500FindTolEnd = ( t_separateN3000toN5500End - ( (1-WINDOW) * ( t_separateN3000toN5500End - t_separateN3000toN5500Start ) / 2 ) )

    exp_separate_N3000toN5500_slope = risAccl[idx-shift]
            
    ## SEPARATE

    idx += 1

    separate_vals = []
    t_separateStart = motT[idx]     # Adding one to the index because we want the flat part, not the transition from -3000 -> -5500

    while motRPM[idx] != 0:
        idx += 1
    
    t_separateEnd = motT[idx]
    t_separateFindTolStart = ( t_separateEnd - ( WINDOW * ( t_separateEnd - t_separateStart ) ) )

    exp_separate_val = risRPM[idx-shift-1]

    ## PRIME S1/S2 ACCELERATION & OVERSHOOT

    # NOTE: If the motor is at 0 then there won't be any readings, so we can't collect data on the actual prime motor speed

    while motRPM[idx] != 0:
        idx += 1

    primes1s2_N5500to0_vals = []
    primes1s2_overshoot_vals = []
    t_primes1s2Start = motT[idx]
    t_primes1s2End = motT[idx + 1]

    exp_primes1s2_slope = risAccl[idx-shift]

    ## UNNAMED

    while motRPM[idx] != 100:
        idx += 1
    
    unnamed_vals = []
    t_unnamedStart = motT[idx]
    t_unnamedEnd = motT[idx + 1]
    t_unnamedFindTolStart = ( t_unnamedEnd - ( WINDOW * ( t_unnamedEnd - t_unnamedStart ) ) )

    exp_unnamed_val = risRPM[idx-shift]
    
    ## READ CHECK 1

    while motRPM[idx] != 1500:
        idx += 1

    readcheck1_P100toP1500_vals = []
    readcheck1_P100toP1500_overshoot_vals = []
    readcheck1_vals = []
    t_readCheck1Start = motT[idx]

    while motRPM[idx] != 4000:
        idx += 1
    
    t_readCheck1End = motT[idx]
    t_readCheck1FindTolStart = ( t_readCheck1End - ( WINDOW * ( t_readCheck1End - t_readCheck1Start ) ) )
    t_readCheck1P100toP1500FindTolStart = t_readCheck1Start + ((1-WINDOW) * (t_readCheck1FindTolStart-t_readCheck1Start) / 2)

    exp_readcheck1_slope = risAccl[idx-shift]
    exp_readcheck1_val = risRPM[idx-shift-1]

    ## ACCELERATION TO MOVE TO MIX CHAMBER

    mtmc_P1500toP4000_overshoot_vals = []
    mtmc_P1500toP4000_vals = []
    t_MTMCP100toP4000Start = motT[idx] + ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )
    t_MTMCP100toP4000End = motT[idx + 1] - ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )

    exp_mtmc_P1500toP4000_slope = risAccl[idx-shift]

    ## MOVE TO MIX CHAMBER

    while motRPM[idx] != 5000:
        idx += 1
    
    mtmc_P4000toP5000_overshoot_vals = []
    mtmc_P4000toP5000_vals = []
    movetomixchamber_vals = []
    t_moveToMixChamberStart = motT[idx]
    t_moveToMixChamberEnd = motT[idx + 1]

    exp_mtmc_P4000toP5000_slope = risAccl[idx-shift]
    exp_mtmc_val = risRPM[idx-shift]

    idx += 1

    ## MIX SAMPLE

    mixsample_1000to4000_vals = []
    mixsample_4000to5000_vals = []
    mixsample_5000to1000_vals = []
    temp_mixsample_1000to4000_vals = []
    temp_mixsample_4000to5000_vals = []
    temp_mixsample_5000to1000_vals = []
    t_mixSample1000 = []
    t_mixSample4000 = []
    t_mixSample5000 = []
    exp_mixsample_1000to4000_slope = []
    exp_mixsample_4000to5000_slope = []
    exp_mixsample_5000to1000_slope = []

    while motRPM[idx + 1] != 1500:
        if motRPM[idx] == 1000:
            t_mixSample1000.append(motT[idx])
            exp_mixsample_1000to4000_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == 4000:
            t_mixSample4000.append(motT[idx])
            exp_mixsample_4000to5000_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == 5000:
            t_mixSample5000.append(motT[idx])
            exp_mixsample_5000to1000_slope.append(risAccl[idx-shift])
        idx += 1

    mixsample_t0_start = t_mixSample1000[0] + (((t_mixSample4000[0] - t_mixSample1000[0]) * (1-WINDOW)) / 2)  # divide by 2 because we are tailoring this timerange on both ends
    mixsample_t0_end   = t_mixSample4000[0] - (((t_mixSample4000[0] - t_mixSample1000[0]) * (1-WINDOW)) / 2)
    mixsample_t1_start = t_mixSample4000[0] + (((t_mixSample5000[0] - t_mixSample4000[0]) * (1-WINDOW)) / 2)
    mixsample_t1_end   = t_mixSample5000[0] - (((t_mixSample5000[0] - t_mixSample4000[0]) * (1-WINDOW)) / 2)
    mixsample_t2_start = t_mixSample5000[0] + (((t_mixSample1000[1] - t_mixSample5000[0]) * (1-WINDOW)) / 2)
    mixsample_t2_end   = t_mixSample1000[1] - (((t_mixSample1000[1] - t_mixSample5000[0]) * (1-WINDOW)) / 2)

    ## READ CHECK 2

    while motRPM[idx] != 1500:
        idx += 1

    readcheck2_P5000toP1500_vals = []
    readcheck2_P5000toP1500_overshoot_vals = []
    readcheck2_vals = []
    t_readCheck2Start = motT[idx]    
    t_readCheck2End = motT[idx + 1]
    t_readCheck2FindTolStart = ( t_readCheck2End - ( WINDOW * ( t_readCheck2End - t_readCheck2Start ) ) )
    t_readCheck2P5000toP1500FindTolStart = t_readCheck2Start + ((1-WINDOW) * (t_readCheck2FindTolStart-t_readCheck2Start) / 2)

    exp_readcheck2_slope = risAccl[idx-shift]
    exp_readcheck2_val = risRPM[idx-shift]

    ## PRIME S3 ACCELERATION & OVERSHOOT

    while motRPM[idx] != 0:
        idx += 1
    
    primes3_P1500to0_vals = []
    primes3_overshoot_vals = []
    t_primes3Start = motT[idx] + ( (1-WINDOW) * (motT[idx+1]-motT[idx]) / 2 )

    exp_primes3_slope = risAccl[idx-shift]

    while motRPM[idx] != 3000:
        idx += 1
    
    t_primes3End = motT[idx] # Not altering this one because we want to get the overshoot as well

    ## ACCELERATION 1 TO DISTRIBUTE CHEMISTRIES

    while motRPM[idx] != 3000:
        idx += 1

    distchems_0toP3000_overshoot_vals = []
    distchems_0toP3000_vals = []
    t_distChems0toP3000Start = motT[idx] + ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )
    t_distChems0toP3000End = motT[idx+1] - ( (1-WINDOW) * (motT[idx+1] - motT[idx]) / 2 )

    exp_distchems_0toP3000_slope = risAccl[idx-shift]

    ## DISTRIBUTE CHEMISTRIES

    while motRPM[idx] != 4000:
        idx += 1

    distChems_P3000toP4000_vals = []
    distchems_vals = []
    t_distChemsStart = motT[idx]
    t_distchemsEnd = motT[idx + 1]

    exp_distchems_P3000toP4000_slope = risAccl[idx-shift]
    exp_distchems_vals = risRPM[idx-shift]

    ## READ CHECK 3

    while motRPM[idx] != 1500:
        idx += 1

    readcheck3_P4000toP1500_vals = []
    readcheck3_P4000toP1500_overshoot_vals = []
    readcheck3_vals = []
    t_readCheck3Start = motT[idx]    
    t_readCheck3End = motT[idx + 1]
    t_readCheck3FindTolStart = ( t_readCheck3End - ( WINDOW * ( t_readCheck3End - t_readCheck3Start ) ) )
    t_readCheck3P4000toP1500FindTolStart = t_readCheck3Start + ((1-WINDOW) * (t_readCheck3FindTolStart-t_readCheck3Start) / 2)

    exp_readcheck3_slope = risAccl[idx-shift]
    exp_readcheck3_val = risRPM[idx-shift]

    ## MIX CHEMISTRIES
    idx += 2

    mixchems_P1000toN1000_vals = []
    mixchems_N1000toP1000_vals = []

    temp_mixchems_P1000toN1000_vals = []
    temp_mixchems_N1000toP1000_vals = []

    t_mixChemsP1000toN1000 = []
    t_mixChemsN1000toP1000 = []

    exp_mixchems_P1000toN1000_slope = []
    exp_mixchems_N1000toP1000_slope = []

    while motRPM[idx] != 1500:
        if motRPM[idx] == 1000 and motRPM[idx+1] == -1000:
           t_mixChemsP1000toN1000.append(motT[idx])
           exp_mixchems_P1000toN1000_slope.append(risAccl[idx-shift])
        elif motRPM[idx] == -1000 and motRPM[idx+1] == 1000:
            t_mixChemsN1000toP1000.append(motT[idx])
            exp_mixchems_N1000toP1000_slope.append(risAccl[idx-shift])
        idx += 1
    
    mixchems_t0_start = t_mixChemsP1000toN1000[0] + (((t_mixChemsN1000toP1000[0] - t_mixChemsP1000toN1000[0]) * (1-WINDOW)) / 2)
    mixchems_t0_end   = t_mixChemsN1000toP1000[0] - (((t_mixChemsN1000toP1000[0] - t_mixChemsP1000toN1000[0]) * (1-WINDOW)) / 2)
    mixchems_t1_start = t_mixChemsN1000toP1000[0] + (((t_mixChemsP1000toN1000[1] - t_mixChemsN1000toP1000[0]) * (1-WINDOW)) / 2)
    mixchems_t1_end   = t_mixChemsP1000toN1000[1] - (((t_mixChemsP1000toN1000[1] - t_mixChemsN1000toP1000[0]) * (1-WINDOW)) / 2)

    ## ACCELERATION TO READ

    read_P1000toP1500_vals = []
    t_readP1000toP1500Start = motT[idx] + ((1-WINDOW) * (motT[idx+1]-motT[idx]) / 2)
    t_readP1000toP1500End = motT[idx+1] - ((1-WINDOW) * (motT[idx+1]-motT[idx]) / 2)

    exp_read_slope = risAccl[idx-shift]

    ## READ

    while motRPM[idx] != 1500:
        idx += 1

    read_vals = []
    t_readStart = motT[idx]

    while motRPM[idx] != 0:
        idx += 1

    t_readEnd = motT[idx]
    t_readFindTolStart = ( t_readEnd - ( WINDOW * ( t_readEnd - t_readStart ) ) )

    exp_read_val = risRPM[idx-shift-1]

    ## Find the tolerances

    accl_counter = 0
    ACCL_STEP_SIZE = 1

    x_separate_0toN3000_vals = []
    y_separate_0toN3000_vals = []

    x_separate_N3000toN5500_vals = []
    y_separate_N3000toN5500_vals = []

    PRIMES1S2_ACCL = True
    x_primes1s2_N5500to0_vals = []
    y_primes1s2_N5500to0_vals = []

    READCHECK1_ACCL = True
    x_readcheck1_P100toP1500_vals = []
    y_readcheck1_P100toP1500_vals = []

    PRIMES3_ACCL = True
    x_primes3_P1500to0_vals = []
    y_primes3_P1500to0_vals = []

    TOMIXCHAMBER1_ACCL = True
    x_mtmc_P1500toP4000_vals = []
    y_mtmc_P1500toP4000_vals = []

    TOMIXCHAMBER2_ACCL = True
    x_mtmc_P4000toP5000_vals = []
    y_mtmc_P4000toP5000_vals = []

    TODISTCHEMS1_ACCL = True
    x_distchems_0toP3000_vals = []
    y_distchems_0toP3000_vals = []

    TODISTCHEMS2_ACCL = True
    x_distChems_P3000toP4000_vals = []
    y_distChems_P3000toP4000_vals = []

    MIXSAMPLE1000_ACCL = True
    x_mixsample_1000to4000 = [] # for best fit line
    y_mixsample_1000to4000 = []
    x_temp_mixsample_1000to4000 = []
    y_temp_mixsample_1000to4000 = []

    MIXSAMPLE4000_ACCL = True
    x_mixsample_4000to5000 = []
    y_mixsample_4000to5000 = []
    x_temp_mixsample_4000to5000 = []
    y_temp_mixsample_4000to5000 = []

    MIXSAMPLE5000_ACCL = True
    x_mixsample_5000to1000 = []
    y_mixsample_5000to1000 = []
    x_temp_mixsample_5000to1000 = []
    y_temp_mixsample_5000to1000 = []

    mixsample_counter = 0

    READCHECK2_ACCL = True
    x_readcheck2_P5000toP1500_vals = []
    y_readcheck2_P5000toP1500_vals = []

    READCHECK3_ACCL = True
    x_readcheck3_P4000toP1500_vals = []
    y_readcheck3_P4000toP1500_vals = []

    MIXCHEMSP1000TON1000_ACCL = True
    x_mixchems_P1000toN1000_vals = []
    y_mixchems_P1000toN1000_vals = []
    x_temp_mixchems_P1000toN1000_vals = []
    y_temp_mixchems_P1000toN1000_vals = []

    MIXCHEMSN1000TOP1000_ACCL = True
    x_mixchems_N1000toP1000_vals = []
    y_mixchems_N1000toP1000_vals = []
    x_temp_mixchems_N1000toP1000_vals = []
    y_temp_mixchems_N1000toP1000_vals = []

    mixchems_counter = 0

    TOREAD_ACCL = True
    x_read_P1000toP1500_vals = []
    y_read_P1000toP1500_vals = []

    for i, t in enumerate(xtime):

        if t < t_barcodeFindTolStart:
            continue

        elif t > t_barcodeFindTolStart and t < t_barcodeEnd:
            barcode_vals.append(yrpm[i])

        elif t > t_separate0toN3000FindTolStart and t < t_separate0toN3000FindTolEnd:
            x_separate_0toN3000_vals.append(t)
            y_separate_0toN3000_vals.append(yrpm[i])
            if accl_counter % ACCL_STEP_SIZE == 0:
                dt = t - xtime[i-ACCL_STEP_SIZE]
                dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                separate_0toN3000_vals.append(dv / dt)
                accl_counter = 0
            accl_counter += 1

        elif t > t_separateN3000toN5500FindTolStart and t < t_separateN3000toN5500FindTolEnd:
            x_separate_N3000toN5500_vals.append(t)
            y_separate_N3000toN5500_vals.append(yrpm[i])
            if accl_counter % ACCL_STEP_SIZE == 0:
                dt = t - xtime[i-ACCL_STEP_SIZE]
                dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                separate_N3000toN5500_vals.append(dv / dt)
                accl_counter = 0
            accl_counter += 1

        elif t > t_separateFindTolStart and t < t_separateEnd:
            separate_vals.append(yrpm[i])

        elif t > t_primes1s2Start and t < t_primes1s2End:
            # The first part of this is the acceleration to prime, and the second part is the overshoot
            if PRIMES1S2_ACCL:
                if yrpm[i] > 0:
                    PRIMES1S2_ACCL = False
                x_primes1s2_N5500to0_vals.append(t)
                y_primes1s2_N5500to0_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    primes1s2_N5500to0_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                primes1s2_overshoot_vals.append(yrpm[i])

        elif t > t_unnamedFindTolStart and t < t_unnamedEnd:
            unnamed_vals.append(yrpm[i])

        elif t > t_readCheck1P100toP1500FindTolStart and t < t_readCheck1FindTolStart:
            if READCHECK1_ACCL:
                if yrpm[i] > 1500:
                    READCHECK1_ACCL = False
                x_readcheck1_P100toP1500_vals.append(t)
                y_readcheck1_P100toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    readcheck1_P100toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                readcheck1_P100toP1500_overshoot_vals.append(yrpm[i])

        elif t > t_readCheck1FindTolStart and t < t_readCheck1End:
            readcheck1_vals.append(yrpm[i])

        elif t > t_MTMCP100toP4000Start and t < t_MTMCP100toP4000End:
            if TOMIXCHAMBER1_ACCL:
                if yrpm[i] > 4000:
                    TOMIXCHAMBER1_ACCL = False
                x_mtmc_P1500toP4000_vals.append(t)
                y_mtmc_P1500toP4000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    mtmc_P1500toP4000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                mtmc_P1500toP4000_overshoot_vals.append(yrpm[i])

        elif t > t_moveToMixChamberStart and t < t_moveToMixChamberEnd:
            if TOMIXCHAMBER2_ACCL:
                if yrpm[i] > 5000:
                    TOMIXCHAMBER2_ACCL = False
                x_mtmc_P4000toP5000_vals.append(t)
                y_mtmc_P4000toP5000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    mtmc_P4000toP5000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                movetomixchamber_vals.append(yrpm[i])

        elif t > t_mixSample1000[0] and t < t_readCheck2Start:
            if mixsample_counter < 11:
                if t > t_mixSample1000[mixsample_counter+1]:
                    mixsample_counter += 1
                    # Reset variables
                    x_mixsample_1000to4000.append(x_temp_mixsample_1000to4000)
                    y_mixsample_1000to4000.append(y_temp_mixsample_1000to4000)
                    x_mixsample_4000to5000.append(x_temp_mixsample_4000to5000)
                    y_mixsample_4000to5000.append(y_temp_mixsample_4000to5000)
                    x_mixsample_5000to1000.append(x_temp_mixsample_5000to1000)
                    y_mixsample_5000to1000.append(y_temp_mixsample_5000to1000)
                    x_temp_mixsample_1000to4000 = []
                    y_temp_mixsample_1000to4000 = []
                    x_temp_mixsample_4000to5000 = []
                    y_temp_mixsample_4000to5000 = []
                    x_temp_mixsample_5000to1000 = []
                    y_temp_mixsample_5000to1000 = []
                    mixsample_1000to4000_vals.append(temp_mixsample_1000to4000_vals)
                    mixsample_4000to5000_vals.append(temp_mixsample_4000to5000_vals)
                    mixsample_5000to1000_vals.append(temp_mixsample_5000to1000_vals)
                    temp_mixsample_1000to4000_vals = []
                    temp_mixsample_4000to5000_vals = []
                    temp_mixsample_5000to1000_vals = []
                    MIXSAMPLE1000_ACCL = True
                    MIXSAMPLE4000_ACCL = True
                    MIXSAMPLE5000_ACCL = True
                    if mixsample_counter == len(t_mixSample5000):
                        mixsample_t0_start = t_mixSample1000[mixsample_counter] + (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                        mixsample_t0_end   = t_mixSample4000[mixsample_counter] - (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                        mixsample_t1_start = t_mixSample4000[mixsample_counter] + (((t_readCheck2Start - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                        mixsample_t1_end   = t_readCheck2Start - (((t_readCheck2Start - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                        continue
                    mixsample_t0_start = t_mixSample1000[mixsample_counter] + (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t0_end   = t_mixSample4000[mixsample_counter] - (((t_mixSample4000[mixsample_counter] - t_mixSample1000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t1_start = t_mixSample4000[mixsample_counter] + (((t_mixSample5000[mixsample_counter] - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t1_end   = t_mixSample5000[mixsample_counter] - (((t_mixSample5000[mixsample_counter] - t_mixSample4000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t2_start = t_mixSample5000[mixsample_counter] + (((t_mixSample1000[mixsample_counter+1] - t_mixSample5000[mixsample_counter]) * (1-WINDOW)) / 2)
                    mixsample_t2_end   = t_mixSample1000[mixsample_counter+1] - (((t_mixSample1000[mixsample_counter+1] - t_mixSample5000[mixsample_counter]) * (1-WINDOW)) / 2)

                if t > mixsample_t0_start and t < mixsample_t0_end:
                    if MIXSAMPLE1000_ACCL:
                        if yrpm[i] < 1000:
                            MIXSAMPLE1000_ACCL = False
                        x_temp_mixsample_1000to4000.append(t)
                        y_temp_mixsample_1000to4000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_1000to4000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixsample_t1_start and t < mixsample_t1_end:
                    if MIXSAMPLE4000_ACCL:
                        if yrpm[i] > 4000:
                            MIXSAMPLE4000_ACCL = False
                        x_temp_mixsample_4000to5000.append(t)
                        y_temp_mixsample_4000to5000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_4000to5000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1
                
                elif t > mixsample_t2_start and t < mixsample_t2_end:
                    if MIXSAMPLE5000_ACCL:
                        if yrpm[i] > 5000:
                            MIXSAMPLE5000_ACCL = False
                        x_temp_mixsample_5000to1000.append(t)
                        y_temp_mixsample_5000to1000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_5000to1000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

            else:
                if t > mixsample_t0_start and t < mixsample_t0_end:
                    if MIXSAMPLE1000_ACCL:
                        if yrpm[i] < 1000:
                            MIXSAMPLE1000_ACCL = False
                        x_temp_mixsample_1000to4000.append(t)
                        y_temp_mixsample_1000to4000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_1000to4000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixsample_t1_start and t < mixsample_t1_end:
                    if MIXSAMPLE4000_ACCL:
                        if yrpm[i] > 4000:
                            MIXSAMPLE4000_ACCL = False
                        x_temp_mixsample_4000to5000.append(t)
                        y_temp_mixsample_4000to5000.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixsample_4000to5000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

        elif t > t_readCheck2P5000toP1500FindTolStart and t < t_readCheck2FindTolStart:
            if READCHECK2_ACCL:
                if yrpm[i] < 1500:
                    READCHECK2_ACCL = False
                x_readcheck2_P5000toP1500_vals.append(t)
                y_readcheck2_P5000toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    readcheck2_P5000toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                readcheck2_P5000toP1500_overshoot_vals.append(yrpm[i])

        elif t > t_readCheck2FindTolStart and t < t_readCheck2End:
            readcheck2_vals.append(yrpm[i])

        elif t > t_primes3Start and t < t_primes3End:
            # The first part of this is the acceleration to prime, and the second part is the overshoot
            if PRIMES3_ACCL:
                if yrpm[i] < 0:
                    PRIMES3_ACCL = False
                x_primes3_P1500to0_vals.append(t)
                y_primes3_P1500to0_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    primes3_P1500to0_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                primes3_overshoot_vals.append(yrpm[i])

        elif t > t_distChems0toP3000Start and t < t_distChems0toP3000End:
            if TODISTCHEMS1_ACCL:
                if yrpm[i] > 3000:
                    TODISTCHEMS1_ACCL = False
                x_distchems_0toP3000_vals.append(t)
                y_distchems_0toP3000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    distchems_0toP3000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                distchems_0toP3000_overshoot_vals.append(yrpm[i])
            
        elif t > t_distChemsStart and t < t_distchemsEnd:
            if TODISTCHEMS2_ACCL:
                if yrpm[i] > 4000:
                    TODISTCHEMS2_ACCL = False
                x_distChems_P3000toP4000_vals.append(t)
                y_distChems_P3000toP4000_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    distChems_P3000toP4000_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                distchems_vals.append(yrpm[i])

        elif t > t_readCheck3P4000toP1500FindTolStart and t < t_readCheck3FindTolStart:
            if READCHECK3_ACCL:
                if yrpm[i] < 1500:
                    READCHECK3_ACCL = False
                x_readcheck3_P4000toP1500_vals.append(t)
                y_readcheck3_P4000toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    readcheck3_P4000toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            else:
                readcheck3_P4000toP1500_overshoot_vals.append(yrpm[i])

        elif t > t_readCheck3FindTolStart and t < t_readCheck3End:
            readcheck3_vals.append(yrpm[i])

        elif t > t_mixChemsP1000toN1000[0] and t < t_readStart:
            if mixchems_counter < 32:
                if t > t_mixChemsP1000toN1000[mixchems_counter+1]:
                    mixchems_counter += 1
                    mixchems_P1000toN1000_vals.append(temp_mixchems_P1000toN1000_vals)
                    mixchems_N1000toP1000_vals.append(temp_mixchems_N1000toP1000_vals)
                    temp_mixchems_P1000toN1000_vals = []
                    temp_mixchems_N1000toP1000_vals = []
                    x_mixchems_P1000toN1000_vals.append(x_temp_mixchems_P1000toN1000_vals)
                    y_mixchems_P1000toN1000_vals.append(y_temp_mixchems_P1000toN1000_vals)
                    x_mixchems_N1000toP1000_vals.append(x_temp_mixchems_N1000toP1000_vals)
                    y_mixchems_N1000toP1000_vals.append(y_temp_mixchems_N1000toP1000_vals)
                    x_temp_mixchems_P1000toN1000_vals = []
                    y_temp_mixchems_P1000toN1000_vals = []
                    x_temp_mixchems_N1000toP1000_vals = []
                    y_temp_mixchems_N1000toP1000_vals = []
                    MIXCHEMSP1000TON1000_ACCL = True
                    MIXCHEMSN1000TOP1000_ACCL = True
                    if mixchems_counter == 32:
                        mixchems_t0_start = t_mixChemsP1000toN1000[mixchems_counter] + (((t_readStart - t_mixChemsP1000toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                        mixchems_t0_end   = t_readStart - (((t_readStart - t_mixChemsP1000toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                        continue
                    
                    mixchems_t0_start = t_mixChemsP1000toN1000[mixchems_counter] + (((t_mixChemsN1000toP1000[mixchems_counter] - t_mixChemsP1000toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t0_end   = t_mixChemsN1000toP1000[mixchems_counter] - (((t_mixChemsN1000toP1000[mixchems_counter] - t_mixChemsP1000toN1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t1_start = t_mixChemsN1000toP1000[mixchems_counter] + (((t_mixChemsP1000toN1000[mixchems_counter+1] - t_mixChemsN1000toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    mixchems_t1_end   = t_mixChemsP1000toN1000[mixchems_counter+1] - (((t_mixChemsP1000toN1000[mixchems_counter+1] - t_mixChemsN1000toP1000[mixchems_counter]) * (1-WINDOW)) / 2)
                    
                if t > mixchems_t0_start and t < mixchems_t0_end:
                    if MIXCHEMSP1000TON1000_ACCL:
                        if yrpm[i] > 1000:
                            MIXCHEMSP1000TON1000_ACCL = False
                        x_temp_mixchems_P1000toN1000_vals.append(t)
                        y_temp_mixchems_P1000toN1000_vals.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixchems_P1000toN1000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1

                elif t > mixchems_t1_start and t < mixchems_t1_end:
                    if MIXCHEMSN1000TOP1000_ACCL:
                        if yrpm[i] < -1000:
                            MIXCHEMSN1000TOP1000_ACCL = False
                        x_temp_mixchems_N1000toP1000_vals.append(t)
                        y_temp_mixchems_N1000toP1000_vals.append(yrpm[i])
                        if accl_counter % ACCL_STEP_SIZE == 0:
                            dt = t - xtime[i-ACCL_STEP_SIZE]
                            dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                            temp_mixchems_N1000toP1000_vals.append(dv / dt)
                            accl_counter = 0
                        accl_counter += 1
                        
        elif t > t_readP1000toP1500Start and t < t_readP1000toP1500End:
            if TOREAD_ACCL:
                if yrpm[i] > 1500:
                    TOREAD_ACCL = False
                x_read_P1000toP1500_vals.append(t)
                y_read_P1000toP1500_vals.append(yrpm[i])
                if accl_counter % ACCL_STEP_SIZE == 0:
                    dt = t - xtime[i-ACCL_STEP_SIZE]
                    dv = yrpm[i] - yrpm[i-ACCL_STEP_SIZE]
                    read_P1000toP1500_vals.append(dv / dt)
                    accl_counter = 0
                accl_counter += 1
            
        elif t > t_readFindTolStart and t < t_readEnd:
            read_vals.append(yrpm[i])

    # Print the tolerances
    
    fileOut.write("\nBARCODE\n")
    if len(barcode_vals) > 0:
        printSectionStatistics(barcode_vals, fileOut)

    fileOut.write("\nACCELERATION TO SEPARATE (0RPM to -3000RPM)\n")
    if len(separate_0toN3000_vals) > 0:
        printSectionStatistics(separate_0toN3000_vals, fileOut)
        slope = bestFitLine(x_separate_0toN3000_vals, y_separate_0toN3000_vals, 1, fileOut)
        calculateError(exp_separate_0toN3000_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO SEPARATE (-3000RPM to -5500RPM)\n")
    if len(separate_N3000toN5500_vals) > 0:
        printSectionStatistics(separate_N3000toN5500_vals, fileOut)
        slope = bestFitLine(x_separate_N3000toN5500_vals, y_separate_N3000toN5500_vals, 1, fileOut)
        calculateError(exp_separate_N3000toN5500_slope, slope, fileOut)

    fileOut.write("\nSEPARATE\n")
    if len(separate_vals) > 0:
        _, _, avg, _ = printSectionStatistics(separate_vals, fileOut)
        calculateError(exp_separate_val, avg, fileOut)

    fileOut.write("\nACCELERATION TO PRIME S1/S2 (-5500RPM to 0RPM)\n")
    if len(primes1s2_N5500to0_vals) > 0:
        printSectionStatistics(primes1s2_N5500to0_vals, fileOut)
        slope = bestFitLine(x_primes1s2_N5500to0_vals, y_primes1s2_N5500to0_vals, 1, fileOut)
        calculateError(exp_primes1s2_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO PRIME S1/S2 OVERSHOOT\n")
    if len(primes1s2_overshoot_vals) > 0:
        printSectionStatistics(primes1s2_overshoot_vals, fileOut)

    fileOut.write("\nUNNAMED\n")
    if len(unnamed_vals) > 0:
        _, _, avg, _ = printSectionStatistics(unnamed_vals, fileOut)
        calculateError(exp_unnamed_val, avg, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 1 (100RPM to 1500RPM)\n")
    if len(readcheck1_P100toP1500_vals) > 0:
        printSectionStatistics(readcheck1_P100toP1500_vals, fileOut)
        slope = bestFitLine(x_readcheck1_P100toP1500_vals, y_readcheck1_P100toP1500_vals, 1, fileOut)
        calculateError(exp_readcheck1_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 1 OVERSHOOT\n")
    if len(readcheck1_P100toP1500_overshoot_vals) > 0:
        printSectionStatistics(readcheck1_P100toP1500_overshoot_vals, fileOut)

    fileOut.write("\nREAD CHECK 1\n")
    if len(readcheck1_vals) > 0:
        _, _, avg, _ = printSectionStatistics(readcheck1_vals, fileOut)
        calculateError(exp_readcheck1_val, avg, fileOut)

    fileOut.write("\nACCELERATION TO MIX CHAMBER (1500RPM to 4000RPM)\n")
    if len(mtmc_P1500toP4000_vals) > 0:
        printSectionStatistics(mtmc_P1500toP4000_vals, fileOut)
        slope = bestFitLine(x_mtmc_P1500toP4000_vals, y_mtmc_P1500toP4000_vals, 1, fileOut)
        calculateError(exp_mtmc_P1500toP4000_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO MIX CHAMBER OVERSHOOT\n")
    if len(mtmc_P1500toP4000_overshoot_vals) > 0:
        printSectionStatistics(mtmc_P1500toP4000_overshoot_vals, fileOut)

    fileOut.write("\nACCELERATION TO MIX CHAMBER (4000RPM to 5000RPM)\n")
    if len(mtmc_P4000toP5000_vals) > 0:
        printSectionStatistics(mtmc_P4000toP5000_vals, fileOut)
        slope = bestFitLine(x_mtmc_P4000toP5000_vals, y_mtmc_P4000toP5000_vals, 1, fileOut)
        calculateError(exp_mtmc_P4000toP5000_slope, slope, fileOut)

    fileOut.write("\nMOVE TO MIX CHAMBER\n")
    if len(movetomixchamber_vals) > 0:
        _, _, avg, _ = printSectionStatistics(movetomixchamber_vals, fileOut)
        calculateError(exp_mtmc_val, avg, fileOut)

    fileOut.write("\n**MIX SAMPLE**\n")
    x_mixsample_1000to4000.append(x_temp_mixsample_1000to4000)
    y_mixsample_1000to4000.append(x_temp_mixsample_1000to4000)
    x_mixsample_4000to5000.append(x_temp_mixsample_4000to5000)
    y_mixsample_4000to5000.append(x_temp_mixsample_4000to5000)
    mixsample_1000to4000_vals.append(temp_mixsample_1000to4000_vals)
    mixsample_4000to5000_vals.append(temp_mixsample_4000to5000_vals)
    for i in range(len(mixsample_1000to4000_vals)):
        fileOut.write("\nROUND #%d\n" % i)
        fileOut.write("  5000RPM->1000RPM\n")
        printSectionStatistics(mixsample_1000to4000_vals[i], fileOut)
        slope = bestFitLine(x_mixsample_1000to4000[i], y_mixsample_1000to4000[i], 1, fileOut)
        calculateError(exp_mixsample_1000to4000_slope[i], slope, fileOut)
        fileOut.write("  1000RPM->4000RPM\n")
        printSectionStatistics(mixsample_4000to5000_vals[i], fileOut)
        slope = bestFitLine(x_mixsample_4000to5000[i], y_mixsample_4000to5000[i], 1, fileOut)
        calculateError(exp_mixsample_4000to5000_slope[i], slope, fileOut)
        if i < len(mixsample_5000to1000_vals):
            fileOut.write("  4000RPM->5000RPM\n")
            printSectionStatistics(mixsample_5000to1000_vals[i], fileOut)
            slope = bestFitLine(x_mixsample_5000to1000[i], y_mixsample_5000to1000[i], 1, fileOut)
            calculateError(exp_mixsample_5000to1000_slope[i], slope, fileOut)
    fileOut.write("\n**END OF MIX SAMPLE**\n")
            
    fileOut.write("\nACCELERATION TO READ CHECK 2 (5000RPM to 1500RPM)\n")
    if len(readcheck2_P5000toP1500_vals) > 0:
        printSectionStatistics(readcheck2_P5000toP1500_vals, fileOut)
        slope = bestFitLine(x_readcheck2_P5000toP1500_vals, y_readcheck2_P5000toP1500_vals, 1, fileOut)
        calculateError(exp_readcheck2_slope, slope, fileOut)

    
    fileOut.write("\nACCELERATION TO READ CHECK 2 OVERSHOOT\n")
    if len(readcheck2_P5000toP1500_overshoot_vals) != 0:
        printSectionStatistics(readcheck2_P5000toP1500_overshoot_vals, fileOut)

    fileOut.write("\nREAD CHECK 2\n")
    if len(readcheck2_vals) > 0:
        _, _, avg, _ = printSectionStatistics(readcheck2_vals, fileOut)
        calculateError(exp_readcheck2_val, avg, fileOut)

    fileOut.write("\nACCELERATION TO PRIME S3 (1500RPM to 0RPM)\n")
    if len(primes3_P1500to0_vals) > 0:
        printSectionStatistics(primes3_P1500to0_vals, fileOut)
        slope = bestFitLine(x_primes3_P1500to0_vals, y_primes3_P1500to0_vals, 1, fileOut)
        calculateError(exp_primes3_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO PRIME S3 OVERSHOOT\n")
    if len(primes3_overshoot_vals) > 0:
        printSectionStatistics(primes3_overshoot_vals, fileOut)

    fileOut.write("\nACCELERATION TO DISTRIBUTE CHEMISTRIES (0RPM to 3000RPM)\n")
    if len(distchems_0toP3000_vals) > 0:
        printSectionStatistics(distchems_0toP3000_vals, fileOut)
        slope = bestFitLine(x_distchems_0toP3000_vals, y_distchems_0toP3000_vals, 1, fileOut)
        calculateError(exp_distchems_0toP3000_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO DISTRIBUTE CHEMISTRIES OVERSHOOT\n")
    if len(distchems_0toP3000_overshoot_vals) != 0:
        printSectionStatistics(distchems_0toP3000_overshoot_vals, fileOut)

    fileOut.write("\nACCELERATION TO DISTRIBUTE CHEMISTRIES (3000RPM to 4000RPM)\n")
    if len(distChems_P3000toP4000_vals) != 0:
        printSectionStatistics(distChems_P3000toP4000_vals, fileOut)
        slope = bestFitLine(x_distChems_P3000toP4000_vals, y_distChems_P3000toP4000_vals, 1, fileOut)
        calculateError(exp_distchems_P3000toP4000_slope, slope, fileOut)

    fileOut.write("\nDISTRIBUTE CHEMISTRIES\n")
    if len(distchems_vals) > 0:
        _, _, avg, _ = printSectionStatistics(distchems_vals, fileOut)
        calculateError(exp_distchems_vals, avg, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 3 (4000RPM to 1500RPM)\n")
    if len(readcheck3_P4000toP1500_vals) > 0:
        printSectionStatistics(readcheck3_P4000toP1500_vals, fileOut)
        slope = bestFitLine(x_readcheck3_P4000toP1500_vals, y_readcheck3_P4000toP1500_vals, 1, fileOut)
        calculateError(exp_readcheck3_slope, slope, fileOut)

    fileOut.write("\nACCELERATION TO READ CHECK 3 OVERSHOOT\n")
    if len(readcheck3_P4000toP1500_overshoot_vals) != 0:
        printSectionStatistics(readcheck3_P4000toP1500_overshoot_vals, fileOut)

    fileOut.write("\nREAD CHECK 3\n")
    if len(readcheck3_vals) > 0:
        _, _, avg, _ = printSectionStatistics(readcheck3_vals, fileOut)
        calculateError(exp_readcheck3_val, avg, fileOut)
    
    fileOut.write("\n**MIX CHEMISTRIES**\n")
    for i in range(len(mixchems_P1000toN1000_vals)):
        fileOut.write("\nROUND #%d\n" % (i))
        fileOut.write("  * 1000RPM->-1000RPM\n")
        printSectionStatistics(mixchems_P1000toN1000_vals[i], fileOut)
        slope = bestFitLine(x_mixchems_P1000toN1000_vals[i], y_mixchems_P1000toN1000_vals[i], 1, fileOut)
        calculateError(exp_mixchems_P1000toN1000_slope[i], slope, fileOut)
        fileOut.write("  * -1000RPM->1000RPM\n")
        printSectionStatistics(mixchems_N1000toP1000_vals[i], fileOut)
        slope = bestFitLine(x_mixchems_N1000toP1000_vals[i], y_mixchems_N1000toP1000_vals[i], 1, fileOut)
        calculateError(exp_mixchems_N1000toP1000_slope[i], slope, fileOut)
    fileOut.write("\n**END OF MIX CHEMISTRIES**\n")
    
    fileOut.write("\nACCLERATION TO READ (1000RPM to 1500RPM)\n")
    if len(read_P1000toP1500_vals) > 0:
        printSectionStatistics(read_P1000toP1500_vals, fileOut)
        slope = bestFitLine(x_read_P1000toP1500_vals, y_read_P1000toP1500_vals, 1, fileOut)
        calculateError(exp_read_slope, slope, fileOut)

    fileOut.write("\nREAD\n")
    if len(read_vals) > 0:
        _, _, avg, _ = printSectionStatistics(read_vals, fileOut)
        calculateError(exp_read_val, avg, fileOut)
    fileOut.write("\n")

    return

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
findPhases()
@brief          Calculates timestamps pertaining to all high-level phases and transition periods
@param msgOutT: Array containing timestamps for relevant SBC commands
@param motT:    Array containing timestamps for motor commands
@param motRPM:  Array containing commanded motor RPM
@param risAccl: Array containing commanded motor acceleration values
@return phaseT: Array containing phase timestamps
'''

def findPhases(msgOutT, motT, motRPM, risAccl):
    
    phaseT = []
    idx = 1 # Start at 1 so we can look at the i-1 timestamp without getting an error
    SCALING_FACTOR = 1.0
    shift = 0
    while motRPM[shift-1] != 100:
        shift += 1
    shift += 1

    # Barcode scan, barcode data, begin analysis message timestamps
    phaseT += msgOutT

    # End of SEPARATE timestamp
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == -5500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == -5500:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of PRIME S1/S2
    while idx < len(motRPM):
        if motRPM[idx] == 100 and motRPM[idx-1] == 0:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1
            
    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 100 and motRPM[idx-1] == 0:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of UNNAMED
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 100:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1
            
    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 100:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ CHECK 1
    while idx < len(motRPM):
        if motRPM[idx] == 4000 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1
            
    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 5000 and motRPM[idx-1] == 4000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1
    
    # End of MOVE TO MIX CHAMBER
    while idx < len(motRPM):
        if motRPM[idx] == 1000 and motRPM[idx-1] == 5000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of MIX SAMPLE
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 5000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 5000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ CHECK 2
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == 1500:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of PRIME S3
    while idx < len(motRPM):
        if motRPM[idx] == 3000 and motRPM[idx-1] == 0:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 4000 and motRPM[idx-1] == 3000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR)) # TODO: why does this one in particular not work??? why does it accelerate so slowly
            break
        else:
            idx+=1

    # End of DISTRIBUTE CHEMISTRIES
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 4000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 4000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ CHECK 3
    while idx < len(motRPM):
        if motRPM[idx] == 1000 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1000 and motRPM[idx-1] == 1500:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of MIX CHEMISTRIES
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 1000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 1000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # TODO FIGURE OUT THE TRANSITION PHASE RIGHT AFTER PRIME S3 AND WHY IT ISN'T IN THE RIGHT PLACE


    return phaseT

#-----------------------------------------------------------------------------------------------------------------------------------------#

argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:ps")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
CREATE_PLOT = False
SAVE_PLOT = False
     
for o, a in opts:
    if o == "-r":
        rotor_name = a
    elif o == "-p":
        CREATE_PLOT = True
    elif o == "-s":
        SAVE_PLOT = True

if rotor_name == "":
    usage()

print("Finding phase statistics for %s" % rotor_name)

ris_infilename = rotor_name + "_RIS_Readable.txt"
mot_infilename = rotor_name + "_MotCmdMsgOut.txt"
msg_infilename = rotor_name + "_MsgOut.txt"
motor_files = [rotor_name + "_Group1_mot.bin"]

motT = []
phaseT = []
msgOutT = []

# TODO: this is a workaround. the lipids have different RIS files. will need to analyze these alone
if "Lipid" in ris_infilename:
    print("Skipping: %s" % (ris_infilename))
    sys.exit(1)

if ris_infilename != "":

    try:
        fileIn = open(ris_infilename, 'rt')
    except:
        print("Could not open file %s" % (ris_infilename))
        sys.exit(1)

    risRPM, risdT, risAccl = parseRISReadable(fileIn)

    fileIn.close()

if mot_infilename != "":

    try:
        fileIn = open(mot_infilename, 'rt')
    except:
        print("Could not open file %s" % (mot_infilename))
        sys.exit(1)

    motRPM, motdT, motT = parseMotCmdMsgOut(fileIn)
        
    fileIn.close()

    if len(motRPM) < 2:
        print("%s did not contain any values. Exiting now." % mot_infilename)
        sys.exit(1)

    # # NOTE: this function needs to be updated to better include all stages of a phase
    # # timestamps, durations, durationdict = parsePhases(risRPM, motRPM, motT, Phase.INIT) # durationsdict currently unused for anything. purely informational
    # phaseT, durations, durationdict = parseHighLevelPhases(risRPM, motRPM, motT, Phase.INIT)

if msg_infilename != "":

    try:
        fileIn = open(msg_infilename, 'rt')
    except:
        print("Could not open file %s" % (msg_infilename))
        sys.exit(1)

    msgOutT = parseMsgOut(fileIn)

    fileIn.close()

##### Plot temps now

majorLoc = 10

fig = plt.figure(2)
plt.xlabel('Time, s')
plt.ylabel('RPM')
plt.title('Speed vs Time')
ax = fig.gca()
ax.yaxis.set_major_locator(ticker.MultipleLocator(1000))
ax.yaxis.set_minor_locator(ticker.MultipleLocator(100))
ax.xaxis.set_major_locator(ticker.MultipleLocator(100))
ax.xaxis.set_minor_locator(ticker.MultipleLocator(10))

# Find phase timestamps for plotting
phaseT = findPhases(msgOutT, motT, motRPM, risAccl)

for t in phaseT:
    plt.axvline(x=t, color='green', linestyle='--', linewidth=0.75)

colors = ['blue', 'green']
for i in range(len(motor_files)):

	basefile = motor_files[i]

	xtime = []
	yrpm = []

	structSize = struct.calcsize("2f")
	with open(basefile, 'rb') as ff:
		while 1:
			s = ff.read(structSize)
			if len(s) != structSize:
				break
			Sin = struct.unpack("2f", s)
			xtime.append(Sin[0])
			yrpm.append(Sin[1])		
	
	plt.plot(xtime, yrpm, color=colors[i], linewidth=0.5, label=motor_files[i])

## Uncomment to calculate and print statistics for each motor command section
outfilename = rotor_name + "_PhaseStatsOut.txt"
fileOut = open(outfilename, 'wt')

if "Rotor1" in rotor_name:
    findMotCmdTolerances_Rotor1(motT, motRPM, risRPM, risAccl, xtime, yrpm, fileOut)
else:
    findMotCmdTolerances(motT, motRPM, risRPM, risAccl, xtime, yrpm, fileOut)

fileOut.close()
    
plt.legend(fontsize = 8)

ax.grid(which='major')

# Make visible
if CREATE_PLOT:
    plt.show()
    
    if SAVE_PLOT:
        plt.savefig("%s_PhasePlot.png" % (rotor_name))

plt.close()

print("Done.")

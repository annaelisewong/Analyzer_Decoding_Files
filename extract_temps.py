import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import subprocess
import getopt

# Get the temperature offset from one of the messages and add the offset in here

FACTORY_airTemperatureOffset = 1.765182
PLATE_TEMPERATURE_ADC_CONVERT_MULT = 0.0010557433	# 1.0557433 millidegree C per plate ADC count
PLATE_TEMPERATURE_ADC_CONVERT_OFFSET = 7.758012		# 7.758012 degree C plate temperature ADC convert offset
PLATE_VOLTAGE_ADC_COVERT_MULT = 0.000625			# 62.5 microvolts per plate ADC count
ROTOR_TEMPERATURE_CONVERT_MULT = 0.00625			#  6.25 millidegree C per rotor temperature sensor ADC count
AMBIENT_TEMPERATURE_CONVERT_MULT = 0.0125			# 12.5 millidegree C per ambient temperature sensor ADC count
AMBIENT_TEMPERATURE_CONVERT_OFFSET = 273.15			# 0.0 degrees C is 273.15 degrees Kelvin offset for ambient temperature sensor

#-----------------------------------------------------------------------------------------------------------------------------------------#

def usage():
    print("extract_temps.py -r <rotor name> [-o] [-s] [-t]")
    print(" -r <rotor name> Full prefix name of rotor")
    print(" -o Flag to indicate output file should be created")
    print(" -s Flag to indicate figure should be saved")
    print(" -t Flag to indicate phase timestamp overlay should be shown on plot")
    sys.exit(0)

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
extractTemps()
@brief               Extracts the temperatures from the Group1Data.txt file
@param fileIn:       Group1Data file
@return ambTemp:     Array containing extracted ambient temperature values
@return ambTempTime: Array containing extracted ambient temperature timestamps
@return topTemp:     Array containing extracted top plate temperature values
@return topTempTime: Array contining extracted top plate temperature timestamps
@return botTemp:     Array containing extracted bottom plate temperature values
@return botTempTime: Array containing extracted bottom plate temperature timestamps
@return rtrTemp:     Array containing extracted rotor temperature values
@return rtrTempTime: Array containing extracted rotor temperature timestamps
'''

def extractTemps(fileIn):

    ambTemp = []       # unsure what this one is other
    ambTempTime = []
    topTemp = []   # top temperature in volts
    topTempTime = []
    botTemp = []   # bottom temperature in volts
    botTempTime = []
    rtrTemp = []   # rotor temperature in volts
    rtrTempTime = []

    ambTempCount = 0
    rtrTempCount = 0
    topTempCount = 0
    botTempCount = 0

    ambTempSum = 0.0
    topTempSum = 0
    botTempSum = 0
    rtrTempSum = 0

    for _ in range(3):
        line = fileIn.readline()

    while line:
        line = fileIn.readline()
        line = [l.strip() for l in line.split()]

        if "Temp" in line:
            ambTempCount += 1
            ambTempSum += float(line[4])
            if ambTempCount == 16:
                ambTempTime.append(float(line[2]))
                ambTemp.append(round(ambTempSum/16.0,2))
                ambTempSum = 0
                ambTempCount = 0

        elif "TOP_TEMP" in line:
            reading = int(line[11])
            topTempCount += 1
            topTempSum += ((reading >> 7) & 0xFFFF)
            if topTempCount == 16:
                topTempTime.append(float(line[1]))
                tTemp = int((topTempSum * 1.0667)/topTempCount)
                tTemp = (((tTemp * PLATE_TEMPERATURE_ADC_CONVERT_MULT) + PLATE_TEMPERATURE_ADC_CONVERT_OFFSET))
                topTemp.append(round(tTemp,2))
                topTempCount = 0
                topTempSum = 0            

        elif "BOT_TEMP" in line:
            reading = int(line[11])
            botTempCount += 1
            botTempSum += ((reading >> 7) & 0xFFFF)
            if botTempCount == 16:
                botTempTime.append(float(line[1]))
                bTemp = int((botTempSum * 1.0667)/botTempCount)
                bTemp = (((bTemp * PLATE_TEMPERATURE_ADC_CONVERT_MULT) + PLATE_TEMPERATURE_ADC_CONVERT_OFFSET))
                botTemp.append(round(bTemp,2))
                botTempCount = 0
                botTempSum = 0
        
        elif "RTR_TEMP" in line:
            reading = int(line[11])
            rtrTempCount += 1
            rtrTempSum += ((reading >> 7) & 0xFFFF)
            if rtrTempCount == 16:
                rtrTempTime.append(float(line[1]))
                rTemp = int((rtrTempSum * 1.0667)/rtrTempCount)
                rTemp = (((rTemp * ROTOR_TEMPERATURE_CONVERT_MULT) + FACTORY_airTemperatureOffset))
                rtrTemp.append(round(rTemp,2))
                rtrTempSum = 0
                rtrTempCount = 0

    return ambTemp, ambTempTime, topTemp, topTempTime, botTemp, botTempTime, rtrTemp, rtrTempTime

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
extractTraceTemps()
@brief            Extracts the temperatures from the Group1Data.txt file
@param fileIn:    Group1Data file
@return tempTime: Array containing timestamps of temperature readings
@return ambTemp:  Array containing extracted ambient temperature values
@return topTemp:  Array containing extracted top plate temperature values
@return botTemp:  Array containing extracted bottom plate temperature values
@return rtrTemp:  Array containing extracted rotor temperature values
'''

def extractTraceTemps(fileIn):
    tempTime = []

    rtrTemp = []
    topTemp = []
    botTemp = []
    ambTemp = []

    camUpT = 0.0

    analysisReadings = 0
    normalReadings = 0

    #
    # Read Group1 file

    # skip first row, it is header
    line = fileIn.readline()

    while line:
        line = fileIn.readline()

        # if len(line) <= 1:
        #     break

        # linej = " ".join(line.split())
        # linesp = linej.split()

        # if (len(linesp) < 3):
        #     continue

        linesp = [l.strip() for l in line.split()]

        if len(linesp) <= 1:
            break

        # print(linesp)

        if (linesp[3] == "[A]"):
            analysisReadings += 1
        elif (linesp[3] == "[N]"):
            normalReadings += 1
        elif (linesp[3] == "CAM_UP"):
            camUpT = float(linesp[1])
            continue
        else:
            continue

        #add readings here
        #Note the time
        tempTime.append(float(linesp[1]))

        #Note ambient temperature
        aTemp = float((int(linesp[5]))*0.0625)
        ambTemp.append(aTemp)

        #note rotor temperature
        rTemp = int(linesp[7])
        rTemp = ((rTemp >> 7) & 0xFFFF)
        rTemp = int(rTemp)
        rTemp = (((rTemp * ROTOR_TEMPERATURE_CONVERT_MULT) + FACTORY_airTemperatureOffset))
        rtrTemp.append(rTemp)

        #note top plate temperature
        tTemp = int(linesp[9])
        tTemp = ((tTemp >> 7) & 0xFFFF)
        tTemp = int(tTemp)
        tTemp = (((tTemp * PLATE_TEMPERATURE_ADC_CONVERT_MULT) + PLATE_TEMPERATURE_ADC_CONVERT_OFFSET))
        topTemp.append(tTemp)

        #note bottom plate temperature
        bTemp = int(linesp[11])
        bTemp = ((bTemp >> 7) & 0xFFFF)
        bTemp = int(bTemp)
        bTemp = (((bTemp * PLATE_TEMPERATURE_ADC_CONVERT_MULT) + PLATE_TEMPERATURE_ADC_CONVERT_OFFSET))
        botTemp.append(bTemp)

    if (analysisReadings + normalReadings != len(tempTime)):
        print("Something is wrong with the data")
        sys.exit(0)
    else:
        print("Data OK")

    return tempTime, ambTemp, topTemp, botTemp, rtrTemp, camUpT
    
#-----------------------------------------------------------------------------------------------------------------------------------------#

def extractMsgOut(fileIn):
    msgOutT = []
    dacT = []
    tempT = []

    line = fileIn.readline()

    while "Summary" not in line:
        line = fileIn.readline()

    for _ in range(5):
        line = fileIn.readline()

    while line:
        line = fileIn.readline()

        if "[HS]" in line:
           line = [l.strip() for l in line.split()]
           dacT.append(float(line[1].replace(":", "")))

        elif "[T ]" in line:
            
            line = [l.strip() for l in line.split()]

            tempT.append(float(line[1].replace(":", "")))

    return dacT, tempT

#-----------------------------------------------------------------------------------------------------------------------------------------#

def extractPhaseTimestamps(fileIn):

    phaseT = []
    phaseNames = ["Warming"]

    for _ in range(4):
        line = fileIn.readline()

    while line:
        line = fileIn.readline()
        line = [l.strip() for l in line.split()]
        if len(line) < 1:
            continue
        phaseT.append(float(line[-1]))
        s=""
        for i in range(len(line)-1):
            s += line[i]
            s += " "
        phaseNames.append(s.strip())

    return phaseT, phaseNames

#-----------------------------------------------------------------------------------------------------------------------------------------#

def extractPhaseTemps(ambTemp, ambTempTime, topTemp, topTempTime, botTemp, botTempTime, rtrTemp, rtrTempTime, phaseT):

    ambTempPhase = []
    topTempPhase = []
    botTempPhase = []
    rtrTempPhase = []

    amb_idx = 0
    top_idx = 0
    bot_idx = 0
    rtr_idx = 0

    for t in phaseT:

        # ambTemps = []
        # topTemps = []
        # botTemps = []
        # rtrTemps = []

        # while idx < len(tempTime) and tempTime[idx] < t:
        #     ambTemps.append(ambTemp[idx])
        #     topTemps.append(topTemp[idx])
        #     botTemps.append(botTemp[idx])
        #     rtrTemps.append(rtrTemp[idx])
        #     idx += 1
        
        # ambTempPhase.append(ambTemps)
        # topTempPhase.append(topTemps)
        # botTempPhase.append(botTemps)
        # rtrTempPhase.append(rtrTemps)

        temps = []
        # Ambient temperature
        while amb_idx < len(ambTempTime) and ambTempTime[amb_idx] < t:
            temps.append(ambTemp[amb_idx])
            amb_idx+=1
        ambTempPhase.append(temps)        
        
        # Top plate temperature
        temps = []
        while top_idx < len(topTempTime) and topTempTime[top_idx] < t:
            temps.append(topTemp[top_idx])
            top_idx+=1
        topTempPhase.append(temps)

        # Bottom plate temperature
        temps = []
        while bot_idx < len(botTempTime) and botTempTime[bot_idx] < t:
            temps.append(botTemp[bot_idx])
            bot_idx+=1
        botTempPhase.append(temps)
        
        # Rotor temperature
        temps = []
        while rtr_idx < len(rtrTempTime) and rtrTempTime[rtr_idx] < t:
            temps.append(rtrTemp[rtr_idx])
            rtr_idx+=1
        rtrTempPhase.append(temps)

    return ambTempPhase, topTempPhase, botTempPhase, rtrTempPhase

#-----------------------------------------------------------------------------------------------------------------------------------------#

def calculateStatistics(phaseNames, ambPhaseTemps, topPhaseTemps, botPhaseTemps, rtrPhaseTemps, fileOut):
    rtrStats = []
    for phase, amb, top, bot, rtr in zip(phaseNames, ambPhaseTemps, topPhaseTemps, botPhaseTemps, rtrPhaseTemps):
        fileOut.write("\n")
        fileOut.write("%s\n" % phase)
        fileOut.write("  Ambient Temps:\n")
        if len(amb) > 0:
            fileOut.write("    Min: %.3f\n" % np.min(amb))
            fileOut.write("    Max: %.3f\n" % np.max(amb))
            fileOut.write("    Avg: %.3f\n" % np.mean(amb))
            fileOut.write("    Std: %.3f\n" % np.std(amb))
            fileOut.write("    # Readings: %d\n" % len(amb))
        else:
            fileOut.write("    No temperature readings.\n")
        fileOut.write("  Top Plate Temps:\n")
        if len(top) > 0:
            fileOut.write("    Min: %.3f\n" % np.min(top))
            fileOut.write("    Max: %.3f\n" % np.max(top))
            fileOut.write("    Avg: %.3f\n" % np.mean(top))
            fileOut.write("    Std: %.3f\n" % np.std(top))
            fileOut.write("    # Readings: %d\n" % len(top))
        else:
            fileOut.write("    No temperature readings.\n")
        fileOut.write("  Bottom Plate Temps:\n")
        if len(bot) > 0:
            fileOut.write("    Min: %.3f\n" % np.min(bot))
            fileOut.write("    Max: %.3f\n" % np.max(bot))
            fileOut.write("    Avg: %.3f\n" % np.mean(bot))
            fileOut.write("    Std: %.3f\n" % np.std(bot))
            fileOut.write("    # Readings: %d\n" % len(bot))
        else:
            fileOut.write("    No temperature readings.\n")
        fileOut.write("  Rotor Temps:\n")
        if len(rtr) > 0:
            fileOut.write("    Min: %.3f\n" % np.min(rtr))
            fileOut.write("    Max: %.3f\n" % np.max(rtr))
            fileOut.write("    Avg: %.3f\n" % np.mean(rtr))
            fileOut.write("    Std: %.3f\n" % np.std(rtr))
            fileOut.write("    # Readings: %d\n" % len(rtr))
            rtrStats.append([phase, np.min(rtr), np.max(rtr), np.mean(rtr), np.std(rtr), len(rtr)])
        else:
            fileOut.write("    No temperature readings.\n")
    return rtrStats

#-----------------------------------------------------------------------------------------------------------------------------------------#

argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:ost")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
CREATE_OUTPUT_FILE = False
SAVE_PLOT = False
TIMESTAMP_OVERLAY = False
     
for o, a in opts:
    if o == "-r":
        rotor_name = a
    elif o == "-o":
        CREATE_OUTPUT_FILE = True
    elif o == "-s":
        SAVE_PLOT = True
    elif o == "-t":
        TIMESTAMP_OVERLAY = True

if rotor_name == "":
    usage()

g1_infilename = rotor_name + "_Group1Data.txt"
p_infilename = rotor_name + "_PhaseTimestampsOut.txt"
m_infilename = rotor_name + "_MsgOut.txt"

if not os.path.isfile(p_infilename):
    print("Phase timestamps file does not exist. Exiting now.")
    sys.exit(1)

# # In case I forgot to grab the phase timestamps
# if not os.path.isfile(p_infilename):
#     p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_phase_timestamps.py", "-r", rotor_name])
#     p.wait()

if "Group1Data" not in g1_infilename or "PhaseTimestampsOut" not in p_infilename or "MsgOut" not in m_infilename:
    print("Did not receive expected files.")
    sys.exit(0)

# Parse the Group1Data file
try:
    fileIn = open(g1_infilename, 'rt')
except:
    print("Could not open file %s" % g1_infilename)
    sys.exit(1)

print("Extracting temperatures for %s" % g1_infilename)

ambTemp, ambTempTime, topTemp, topTempTime, botTemp, botTempTime, rtrTemp, rtrTempTime = extractTemps(fileIn)

fileIn.close()

# Parse PhaseTimestampsOut file
try:
    fileIn = open(p_infilename, 'rt')
except:
    print("Could not open file %s" % p_infilename)
    TIMESTAMP_OVERLAY = False
    # sys.exit(1)

if fileIn:
    print("Extracting phase timestamps for %s" % p_infilename)
    phaseT, phaseNames = extractPhaseTimestamps(fileIn)
    fileIn.close()

# Extract temperature readings per each 
ambPhaseTemps, topPhaseTemps, botPhaseTemps, rtrPhaseTemps = extractPhaseTemps(ambTemp, ambTempTime, topTemp, topTempTime, botTemp, botTempTime, rtrTemp, rtrTempTime, phaseT)

if CREATE_OUTPUT_FILE:
    outfilename = rotor_name + "_TempStatsOut.txt"
    fileOut = open(outfilename, 'wt')
    fileOut.write("Temperature data for %s\n" % rotor_name)
    calculateStatistics(phaseNames, ambPhaseTemps, topPhaseTemps, botPhaseTemps, rtrPhaseTemps, fileOut)
    fileOut.close()

# Parse MsgOut file
try:
    fileIn = open(m_infilename, 'rt')
except:
    print("Could not open file %s" % m_infilename)
    sys.exit(1)

dacT, tempT = extractMsgOut(fileIn)

fileIn.close()

# Plot extracted values

plt.title(rotor_name + ": Temperature vs. Time")
plt.xlabel("Time (seconds)")
plt.ylabel("Temperature (C)")
plt.grid(True)

if TIMESTAMP_OVERLAY:
    pT = []
    dT = []
    tT = []

    for t in phaseT:
        pT.append(plt.axvline(x=t, color='purple', linestyle='--', linewidth=0.75))
    for t in dacT:
        dT.append(plt.axvline(x=t, color='blue', linestyle=':', linewidth=0.75))
    for t in tempT:
        tT.append(plt.axvline(x=t, color='orange', linestyle=':', linewidth=0.75))

    legend1 = plt.legend([pT[0], dT[0], tT[0]], ["Phase Timestamps", "Set DAC Timestamps", "Temp Read Timestamps"], loc=4)
    plt.gca().add_artist(legend1)

plt.plot(ambTempTime, ambTemp, label='Ambient Temperature', color='black')
plt.plot(topTempTime, topTemp, label='Top Plate Temperature', color='green')
plt.plot(botTempTime, botTemp, label='Bottom Plate Temperature', color='red')
plt.plot(rtrTempTime, rtrTemp, label='Rotor Temperature', color='blue')

plt.yticks(np.arange(21.5, 47, 2))

if SAVE_PLOT:
    plt.savefig("%s_TempPlot.png" % (rotor_name))

plt.legend()
plt.show()

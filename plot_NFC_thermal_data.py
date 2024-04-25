import matplotlib.pyplot as plt
import sys
import numpy as np
import csv
import os
import subprocess
import getopt

FACTORY_airTemperatureOffset = 1.765182
PLATE_TEMPERATURE_ADC_CONVERT_MULT = 0.0010557433	# 1.0557433 millidegree C per plate ADC count
PLATE_TEMPERATURE_ADC_CONVERT_OFFSET = 7.758012		# 7.758012 degree C plate temperature ADC convert offset
PLATE_VOLTAGE_ADC_COVERT_MULT = 0.000625			# 62.5 microvolts per plate ADC count
ROTOR_TEMPERATURE_CONVERT_MULT = 0.00625			#  6.25 millidegree C per rotor temperature sensor ADC count
AMBIENT_TEMPERATURE_CONVERT_MULT = 0.0125			# 12.5 millidegree C per ambient temperature sensor ADC count
AMBIENT_TEMPERATURE_CONVERT_OFFSET = 273.15			# 0.0 degrees C is 273.15 degrees Kelvin offset for ambient temperature sensor

#-----------------------------------------------------------------------------------------------------------------------------------------#

def usage():
    print("thermalBringupPlotNFC.py -r <rotor name> -n <NFC temperature data CSV file> [-c <CAM UP timestamp>] [-t] [-s]")
    print(" -r <rotor name> Full prefix name of rotor")
    print(" -n <NFC temperature data CSV file> CSV file containing NFC temperature reading data")
    print(" -c <CAM UP timestamp> CAM UP timestamp calculated from Logic Analyzer data")
    print(" -t Flag to overlay phase timestamps on generated plot")
    print(" -s Flag to indicate generate plot should be saved")
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
extractNFCTemps()
@brief               Extracts the temperatures from the NFC csv file
@param fileIn:       NFC file
@param camUpTimestamp: Cam up timestamp
@return nfcTempTime: Array containing extracted NFC rotor temperature timestamps
@return nfcTemp:     Array containing extracted NFC rotor temperatures
'''

def extractNFCTemps(fileIn, camUpTimestamp):
	
    nfcTempTime = []
    nfcTemp = []
    prevTempValue = 0.0

    inp = csv.reader(fileIn)

    next(inp)

    for row in inp:
        nfcTempTime.append(float(row[1]) - camUpTimestamp)
        try:
            nfcTemp.append(float(row[11]))
            prevTempValue = float(row[11])
        except:
            nfcTemp.append(prevTempValue)
            
    return nfcTempTime, nfcTemp
	
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

'''
calculateOffset()
@brief              Calculates the offset between the NFC temperature readings and calculated logic analyzer readings
@param rtrTemp:     Array containing extracted rotor temperature values
@param rtrTempTime: Array containing extracted rotor temperature timestamps
@param nfcTemp:     Array containing extracted NFC rotor temperature values
@param nfcTempTime: Array containing extracted NFC rotor temperature timestamps
@return offset:     Average value of offset between Read Phase temperature values
'''

def calculateOffset(rtrTemp, rtrTempTime, nfcTemp, nfcTempTime, phaseT):
    # Read phase = -2 index
    readPhaseStart = phaseT[-2]
    readPhaseEnd   = phaseT[-1]

    rtrReadTemps = []
    nfcReadTemps = []

    for i, t in enumerate(rtrTempTime):
        if t >= readPhaseStart and t <= readPhaseEnd:
            rtrReadTemps.append(rtrTemp[i])
    
    for i, t in enumerate(nfcTempTime):
        if t >= readPhaseStart and t <= readPhaseEnd:
            nfcReadTemps.append(nfcTemp[i])

    rtr_avg = np.mean(rtrReadTemps)
    nfc_avg = np.mean(nfcReadTemps)
    print("Phase: READ")
    print("  Rotor Average:     ", rtr_avg)
    print("  NFC Rotor Average: ", nfc_avg)
    print("  Average Offset:    ", (nfc_avg - rtr_avg))

    return (nfc_avg - rtr_avg)

#-----------------------------------------------------------------------------------------------------------------------------------------#

argc = len(sys.argv)
if argc < 3:
    usage()
    sys.exit(0)

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:n:c:ts")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
nfc_infilename = ""
camUpTimestamp = 0
OVERLAY_TIMESTAMPS = False
SAVE_PLOT = False
     
for o, a in opts:
    if o == "-r":
        rotor_name = a
    elif o == "-n":
        nfc_infilename = a
    elif o == "-c":
        camUpTimestamp = float(a)
    elif o == "-t":
        OVERLAY_TIMESTAMPS = True
    elif o == "-s":
        SAVE_PLOT = True

if rotor_name == "" or nfc_infilename == "":
    usage()

g1_infilename = rotor_name + "_Group1Data.txt"
p_infilename = rotor_name + "_PhaseTimestampsOut.txt"

# In case I forgot to grab the phase timestamps
if not os.path.exists(p_infilename):
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_phase_timestamps.py", "-r", rotor_name])
    p.wait()

# Parse Group1Data file

try:
    fileIn = open(g1_infilename, 'rt')
except:
    print("Could not open file %s" % g1_infilename)
    sys.exit(1)

print("Extracting temperatures for %s" % g1_infilename)

ambTemp, ambTempTime, topTemp, topTempTime, botTemp, botTempTime, rtrTemp, rtrTempTime = extractTemps(fileIn)

fileIn.close()

# Parse NFC file

try:
    fileIn = open(nfc_infilename, 'rt')
except:
    print("Could not open file %s" % nfc_infilename)
    sys.exit(1)

print("Extracting temperatures for %s" % nfc_infilename)

nfcTempTime, nfcTemp = extractNFCTemps(fileIn, camUpTimestamp)

fileIn.close()

# Parse PhaseTimestampsOut file
try:
    fileIn = open(p_infilename, 'rt')
except:
    print("Could not open file %s" % p_infilename)
    sys.exit(1)

print("Extracting phase timestamps for %s" % p_infilename)
phaseT, phaseNames = extractPhaseTimestamps(fileIn)
fileIn.close()

# Calculate offset in Read phase
offset = calculateOffset(rtrTemp, rtrTempTime, nfcTemp, nfcTempTime, phaseT)

# Temp plot
plt.figure(figsize=(10, 6))  # Set the figure size (optional)
plt.title("Rotor Temperature vs. Time")
plt.xlabel("Time (seconds)")
plt.ylabel("Temperature (C)")
# plt.ylim(22,50)
plt.grid(True)
plt.plot(ambTempTime, ambTemp, label='Ambient Temperature', color='black')
plt.plot(topTempTime, topTemp, label='Top Plate Temperature', color='green')
plt.plot(botTempTime, botTemp, label='Bottom Plate Temperature', color='red')
plt.plot(rtrTempTime, rtrTemp, label='Rotor Temperature', color='blue', linewidth=0.75)
plt.plot(nfcTempTime, nfcTemp, label='NFC Rotor Temperature', color='blue', linewidth=0.75, linestyle='--')
# plt.axvline(x=camUpTimestamp,color='grey',linestyle='--') # NOTE: Since we are shifting the timestamps of the nfc temp plot by camUpTimestamp, plotting camUpTimestamp would be useless because when shifted, camUpTimestamp = 0
if SAVE_PLOT:
    plt.savefig('%s_NFCTempPlot.png' % rotor_name)

plt.yticks(np.arange(21.5, 47, 2))

if OVERLAY_TIMESTAMPS:
    for t in phaseT:
        plt.axvline(x=t, color='green', linestyle='--', linewidth=0.75)

plt.legend()
plt.show()


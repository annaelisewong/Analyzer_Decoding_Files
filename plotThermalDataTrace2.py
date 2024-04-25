#
# plotThermalDataTrace.py
#
#

import matplotlib.pyplot as temp_plt
import string
import sys
import getopt
import time
import os
import math

def usage():
    print( "plotThermalDataTrace.py <Temp_Tprint.txt>")

# !!! Where is FACTORY_airTemperatureOffset from?
FACTORY_airTemperatureOffset = 1.765182
PLATE_TEMPERATURE_ADC_CONVERT_MULT = 0.0010557433	# 1.0557433 millidegree C per plate ADC count
PLATE_TEMPERATURE_ADC_CONVERT_OFFSET = 7.758012		# 7.758012 degree C plate temperature ADC convert offset
PLATE_VOLTAGE_ADC_COVERT_MULT = 0.000625			# 62.5 microvolts per plate ADC count
ROTOR_TEMPERATURE_CONVERT_MULT = 0.00625			#  6.25 millidegree C per rotor temperature sensor ADC count
AMBIENT_TEMPERATURE_CONVERT_MULT = 0.0125			# 12.5 millidegree C per ambient temperature sensor ADC count
AMBIENT_TEMPERATURE_CONVERT_OFFSET = 273.15			# 0.0 degrees C is 273.15 degrees Kelvin offset for ambient temperature sensor

PLATE_CURRENT_CONVERT_MULT = 0.000625				# 625 microamps per plate current ADC count

def CalcPlateTemp(avgAdc):
	return (float(avgAdc) * PLATE_TEMPERATURE_ADC_CONVERT_MULT) + PLATE_TEMPERATURE_ADC_CONVERT_OFFSET

def CalcPlateVoltage(avgAdc):
	return float(avgAdc) * PLATE_VOLTAGE_ADC_COVERT_MULT


#
#
#
argc = len(sys.argv)
if argc < 2:
    usage()
    sys.exit(0)

# cmd line defaults
tempfilename = sys.argv[1]

try:
	fileGrp1 = open(tempfilename, 'rt')
except:
	print( "Could not open input file %s" % (tempfilename))
	sys.exit(1)

fileOut = sys.stdout
fileOut.write("\n")

tempTime = []

rotorTemp = []
topTemp = []
botTemp = []
ambTemp = []

refTimeStamp = 0.0

analysisReadings = 0
normalReadings = 0

#
# Read Group1 file

# skip first row, it is header
line = fileGrp1.readline()

while 1:
	line = fileGrp1.readline()

	if len(line) <= 0:
		break

	linej = " ".join(line.split())
	linesp = linej.split()

	if (len(linesp) < 3):
		continue

	#print(linesp)

	if (linesp[3] == "[A]"):
		analysisReadings += 1
	elif (linesp[3] == "[N]"):
		normalReadings += 1
	elif (linesp[3] == "CAM_UP"):
		refTimeStamp = float(linesp[1])
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
	rotorTemp.append(rTemp)

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


### Sanity check ###
print("Readings taken during analysis = %d" % (analysisReadings))
print("Readings taken during idle = %d" % (normalReadings))
print("Total Ambient Temp Readings = %d" % (len(ambTemp)))
print("Total Rotor Temp Readings = %d" % (len(rotorTemp)))
print("Total Top Plate Temp Readings = %d" % (len(topTemp)))
print("Total Bottom Plate Temp Readings = %d" % (len(botTemp)))
print("Total Timestamps registered = %d" % (len(tempTime)))

if (analysisReadings + normalReadings != len(tempTime)):
	print("Something is wrong with the data")
	sys.exit(0)
else:
	print("Data OK")

#Temp plot
temp_plt.figure(figsize=(10, 6))  # Set the figure size (optional)
temp_plt.title("Temperature vs. Time")
temp_plt.xlabel("Time (seconds)")
temp_plt.ylabel("Temperature (C)")
temp_plt.grid(True)
temp_plt.plot(tempTime, rotorTemp, label='Rotor Temperature', color='black')
temp_plt.plot(tempTime, topTemp, label='Top Plate Temperature', color='green')
temp_plt.plot(tempTime, botTemp, label='Bottom Plate Temperature', color='red')
temp_plt.plot(tempTime, ambTemp, label='Ambient Temperature', color='blue')
temp_plt.axvline(x=refTimeStamp,color='grey',linestyle='--')
temp_plt.axhline(y=37.00,color='grey',linestyle='--')
temp_plt.legend()
temp_plt.savefig('TempDataPlot.png', dpi=650)
temp_plt.show()

#
# plotTemp.py
#
#

import matplotlib.pyplot as temp_plt
import matplotlib.pyplot as dac_plt
import matplotlib.pyplot as cur_plt
import string
import sys
import getopt
import time
import os
import math

def usage():
    print( "plotTemp.py <Grp1Out_file>")

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
grp1Filename = sys.argv[1]

try:
	fileGrp1 = open(grp1Filename, 'rt')
except:
	print( "Could not open input file %s" % (grp1Filename))
	sys.exit(1)

fileOut = sys.stdout
fileOut.write("\n")

botDacTime = []
topDacTime = []
rotorTempTime = []
topTempTime = []
botTempTime = []
ambTempTime = []
topCurTime = []
botCurTime = []

topDac = []
botDac = []
rotorTemp = []
topTemp = []
botTemp = []
ambTemp = []
topCur = []
botCur = []

ambTempCount = 0
rtrTempCount = 0
topTempCount = 0
botTempCount = 0
topCurCount = 0
botCurCount = 0

ambTempSum = 0.0
topTempSum = 0
botTempSum = 0
rtrTempSum = 0
topCurSum = 0
botCurSum = 0

prevTopDac = 0
prevBotDac = 0
topDacFirst = 0
botDacFirst = 0

#
# Read Group1 file

# skip first row, it is header
line = fileGrp1.readline()

while 1:
	line = fileGrp1.readline()
	if len(line) <= 0:
		break

	if len(line) <= 3:
		continue

	linej = " ".join(line.split())
	linesp = linej.split()

	if (linesp[0] == "DacA") and (linesp[6] == "Top_Set"):
	    topDacTime.append(float(linesp[2]))
	    topDac.append((int(linesp[7])))

	elif (linesp[0] == "DacA") and (linesp[6] == "Bot_Set"):
		botDacTime.append(float(linesp[2]))
		botDac.append((int(linesp[7])))

	elif (linesp[0] == "Temp"):
		ambTempCount += 1
		ambTempSum += float(linesp[4])
		if ambTempCount == 16:
		    ambTempTime.append(float(linesp[2]))
		    ambTemp.append(round(ambTempSum/16.0,2))
		    #print(round(ambTempSum/16.0,2))
		    ambTempSum = 0
		    ambTempCount = 0

	elif (linesp[0] == "ADC_SYS"):
		if (linesp[7] == "RTR_TEMP"):
			reading = int(linesp[11])
			rtrTempCount += 1
			rtrTempSum += ((reading >> 7) & 0xFFFF)
			if rtrTempCount == 16:
				rotorTempTime.append(float(linesp[1]))
				rtrTemp = int((rtrTempSum * 1.0667)/rtrTempCount)
				rtrTemp = (((rtrTemp * ROTOR_TEMPERATURE_CONVERT_MULT) + FACTORY_airTemperatureOffset))
				#print(round(rtrTemp,2))
				rotorTemp.append(round(rtrTemp,2))
				rtrTempSum = 0
				rtrTempCount = 0

		elif (linesp[7] == "TOP_TEMP"):
			reading = int(linesp[11])
			topTempCount += 1
			topTempSum += ((reading >> 7) & 0xFFFF)
			if topTempCount == 16:
				topTempTime.append(float(linesp[1]))
				tTemp = int((topTempSum * 1.0667)/topTempCount)
				tTemp = (((tTemp * PLATE_TEMPERATURE_ADC_CONVERT_MULT) + PLATE_TEMPERATURE_ADC_CONVERT_OFFSET))
				#print(round(tTemp,2))
				topTemp.append(round(tTemp,2))
				topTempCount = 0
				topTempSum = 0

		elif (linesp[7] == "BOT_TEMP"):
			reading = int(linesp[11])
			botTempCount += 1
			botTempSum += ((reading >> 7) & 0xFFFF)
			if botTempCount == 16:
				botTempTime.append(float(linesp[1]))
				bTemp = int((botTempSum * 1.0667)/botTempCount)
				bTemp = (((bTemp * PLATE_TEMPERATURE_ADC_CONVERT_MULT) + PLATE_TEMPERATURE_ADC_CONVERT_OFFSET))
				#print(round(bTemp,2))
				botTemp.append(round(bTemp,2))
				botTempCount = 0
				botTempSum = 0

		elif (linesp[7] == "TOP_CUR"):
			reading = int(linesp[11])
			topCurCount += 1
			topCurSum += ((reading >> 7) & 0xFFFF)
			if (topCurCount == 16):
				topCurTime.append(float(linesp[1]))
				tcur = int((topCurSum * 1.0667)/topCurCount)
				tcur = tcur * PLATE_VOLTAGE_ADC_COVERT_MULT
				topCur.append(round(tcur,2))
				topCurCount = 0
				topCurSum = 0

		elif (linesp[7] == "BOT_CUR"):
			reading = int(linesp[11])
			botCurCount += 1
			botCurSum += ((reading >> 7) & 0xFFFF)
			if (botCurCount == 16):
				botCurTime.append(float(linesp[1]))
				bcur = int((botCurSum * 1.0667)/botCurCount)
				bcur = bcur * PLATE_VOLTAGE_ADC_COVERT_MULT
				botCur.append(round(bcur,2))
				botCurCount = 0
				botCurSum = 0

#Temp plot
temp_plt.figure(figsize=(10, 6))  # Set the figure size (optional)
temp_plt.title("Temperature vs. Time")
temp_plt.xlabel("Time (seconds)")
temp_plt.ylabel("Temperature (C)")
temp_plt.grid(True)
temp_plt.xlim(-200,900)
temp_plt.ylim(20,45)

print(ambTemp)

temp_plt.plot(rotorTempTime, rotorTemp, label='Rotor Temperature', color='black')
temp_plt.plot(topTempTime, topTemp, label='Top Plate Temperature', color='green')
temp_plt.plot(botTempTime, botTemp, label='Bottom Plate Temperature', color='red')
temp_plt.plot(ambTempTime, ambTemp, label='Ambient Temperature', color='blue')

temp_plt.legend()
temp_plt.savefig('TempDataPlot.png', dpi=650)
temp_plt.show()

#DAC Plot
dac_plt.figure(figsize=(10, 6))  # Set the figure size (optional)
dac_plt.title("DAC Value vs. Time")
dac_plt.xlabel("Time (seconds)")
dac_plt.ylabel("DAC Setting")
dac_plt.grid(True)

dac_plt.plot(topDacTime, topDac, label='Top Plate DAC', color='orange')
dac_plt.plot(botDacTime, botDac, label='Bot Plate DAC', color='purple')

dac_plt.legend()
dac_plt.savefig('DACDataPlot.png', dpi=650)
dac_plt.show()

#Voltage plot
cur_plt.figure(figsize=(10, 6))  # Set the figure size (optional)
cur_plt.title("Voltage vs. Time")
cur_plt.xlabel("Time (seconds)")
cur_plt.ylabel("Voltage (V)")
cur_plt.grid(True)

cur_plt.plot(topCurTime, topCur, label='Top Plate Voltage', color='brown')
cur_plt.plot(botCurTime, botCur, label='Bot Plate Voltage', color='grey')

cur_plt.legend()
cur_plt.savefig('VoltageDataPlot.png', dpi=650)
cur_plt.show()
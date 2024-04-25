#
# pho_raw_beak.py
#
# Decode LA capture Photonics Cuvette strobes
#

# verbosity bit map
#   2  CUV_PULSE

import string
import sys
import getopt
import time
import os
import math
import numpy as np

DEBUG1 = 0
DEBUG2 = 0
DEBUG3 = 0
DEBUG4 = 0
AEW_DEBUG = 1

"""
Group0 Capture of 3/8/23 

 0 Time [s],
 1 CAM_UP,
 2 PHO_ADC_START,
 3 PHO_ADC_DRDY#,
 4 SPI_PHO_DAC_CS#,
 5 SPI_PHO_ADC_CS#,
 6 SPI_PHO_CLK,
 7 SPI_PHO_MOSI,
 8 SPI_PHO_MISO,
 9 CUV_PULSE,
10 BEAK_TRIG#,
11 INT_RST#,
12 INT_HOLD#,
13 RX,
14 TX,
15 DWR_CLS,
16 DWR_BRAKE
"""

IDX_TIME = 0
IDX_ADC_START = 2
IDX_ADC_DRDY = 3
IDX_DACCS = 4
IDX_CS   = 5
IDX_CLK  = 6
IDX_MOSI = 7
IDX_MISO = 8
IDX_CUV = 9
IDX_BEAK = 10
IDX_INTRST = 11
IDX_HOLD = 12
IDX_RX = 13
IDX_TX = 14

#
# ##########
#

#
# parse_cuv:
#
class parse_cuv:
	def __init__(self):
		self.numPulses = 0
		self.numIndexes = 0
		self.pulseCount = 0		# corresponds to cuvette number
		self.beakCount = 0
		self.prevEntry = -1
		self.pulseWidth = 0.0

		self.T1RefRE = 0.0
		self.T2RefFE = 0.0
		self.T3SamRE = 0.0
		self.T4BeakFE = 0.0
		self.rstRE = 0.0
		self.rstFE = 0.0
		self.T5HoldRE = 0.0
		self.holdFE = 0.0
		self.T6SamFE = 0.0
		self.T7BeakRE = 0.0
		self.timeLastFE = 0.0
		self.beakLastFE = 0.0

		self.Entries = []
		self.BeakTiming2 = []	#	
								#
								#	

	# 
	# Update method
	def update(self, cv, ev):

		#
		# Falling edge of BEAK
		#
		if ev[IDX_BEAK] == 1 and cv[IDX_BEAK] == 0:
			self.T4BeakFE = cv[IDX_TIME]
			self.beakCount += 1

			# adjust to next cuv number since the FE for this pulse is after beak FE and has not happended yet
			adjPulse = self.pulseCount+1
			if adjPulse == 30:
				adjPulse = 0

			if 1:
				fileOut.write("BEAK    %10.6f %5d Cuv %2d %d:%2.2d \n" % \
					(self.T4BeakFE, self.beakCount, adjPulse, self.numPulses/30, self.numPulses%30))

			if (adjPulse) != self.prevEntry:
				thisEntry = [adjPulse, 1, self.T4BeakFE, self.T3SamRE]
				self.Entries.append(thisEntry)
			else:
				self.Entries[-1][1] += 1
				self.Entries[-1][3] += self.T3SamRE
			self.prevEntry = adjPulse
			
			self.beakLastFE = self.T4BeakFE

		#
		# Rising edge of BEAK
		#
		if ev[IDX_BEAK] == 1 and cv[IDX_BEAK] == 1:
			self.T7BeakRE = cv[IDX_TIME]

			self.BeakTiming2.append([self.pulseCount, self.T1RefRE, self.T2RefFE, \
			                         self.T3SamRE, self.T4BeakFE, self.T5HoldRE, self.T6SamFE, \
			                         self.T7BeakRE])

		#
		# Rising edge of INT_RST#
		#
		if ev[IDX_INTRST] == 1 and cv[IDX_INTRST] == 1:
			self.rstRE = cv[IDX_TIME]

		#
		# Falling edge of INT_RST#
		#
		if ev[IDX_INTRST] == 1 and cv[IDX_INTRST] == 0:
			self.rstFE = cv[IDX_TIME]

		#
		# Rising edge of INT_HOLD
		#
		if ev[IDX_HOLD] == 1 and cv[IDX_HOLD] == 1:
			self.T5HoldRE = cv[IDX_TIME]

		#
		# Falling edge of INT_HOLD
		#
		if ev[IDX_HOLD] == 1 and cv[IDX_HOLD] == 0:
			self.holdFE = cv[IDX_TIME]

		#
		# Rising edge of ADC_START
		#
		if ev[IDX_ADC_START] == 1 and cv[IDX_ADC_START] == 1:
			pass
		#
		# Falling edge of ADC_START
		#
		if ev[IDX_ADC_START] == 1 and cv[IDX_ADC_START] == 0:
			pass

		#
		# Falling edge of ADC_DRDY
		#
		if ev[IDX_ADC_DRDY] == 1 and cv[IDX_ADC_DRDY] == 0:
			pass

		#
		# Rising edge of ADC_DRDY
		#
		if ev[IDX_ADC_DRDY] == 1 and cv[IDX_ADC_DRDY] == 1:
			pass

		#
		# Rising edge of Cuvette mark pulse
		#
		if ev[IDX_CUV] == 1 and cv[IDX_CUV] == 1:
			self.timeLastFE = self.T6SamFE
			self.T1RefRE = self.T3SamRE
			self.T3SamRE = cv[IDX_TIME]

		#
		# Falling edge of Cuvette mark pulse
		#
		if ev[IDX_CUV] == 1 and cv[IDX_CUV] == 0:
			self.T2RefFE = self.T6SamFE
			self.T6SamFE = cv[IDX_TIME]

			self.pulseWidth = self.T6SamFE - self.T3SamRE
			periodff = self.T6SamFE - self.timeLastFE

			# TODO: clean up this duplication of pulse count
			adjPulse = self.pulseCount+1
			if adjPulse == 30:
				adjPulse = 0

			if verbosity & 2:
				print ("T = %f p = %f h = %f " % (cv[IDX_TIME], periodff, self.pulseWidth), end="")

			#
			# Synchronize cuvette pulse count to index pulse
			#if (self.timeFE - self.beakLastFE) > 1.0:
			if (self.T6SamFE - self.beakLastFE) > 1.0:
				if (self.pulseWidth > 0.000585) and (periodff > 0.001290) and (periodff < 0.001450):
					self.pulseCount = 0
					self.numPulses = 0
				else:
					self.pulseCount += 1
					if self.pulseCount == 30:
						self.pulseCount = 0
			else:
				self.pulseCount += 1
				if self.pulseCount == 30:
					self.pulseCount = 0

			if verbosity & 2:
				print (" c = %d %d %d" % (self.numPulses, self.pulseCount, self.numPulses % 30))
			#

			self.numPulses += 1


	def get_entries(self):
		return self.Entries

	def get_BeakTiming2(self):
		return self.BeakTiming2

#
# ##########
#

#
# usage()
#
def usage():
    print( "pho_raw_beak -i <input file> [-g GCD (us)] [-v <verbosity_level>] [-o <output_file>]")
    print( " -i <Input file> from Saleae export ")
    print( " -g <Global_Cuvette_Delay>, microsec")
    print( " -v <Verbosity>")
    print( " -o <Output file> save results")
	
# ##########

argc = len(sys.argv)
if argc < 2:
	usage()
	sys.exit(0)

startTime = time.localtime(time.time())
tstr = time.strftime("%Y-%m-%d %H:%M:%S", startTime)
#print ("Start: %s" % (tstr))

# cmd line defaults
infilename = ''
outFileName = ''
out_text = 0
verbosity = 0
outPath = ''
gcd = 0.0

#    
# parse command line options
#
try:
	opts, args = getopt.getopt(sys.argv[1:], "i:v:o:g:")
except getopt.error:
	usage()
	sys.exit(2)

# process options
for o, a in opts:
	if o == "-i":
		infilename = a
	elif o == "-v":
		verbosity = int(a)
	elif o == "-o":
		outFileName = a
	elif o == "-g":
		gcd = float(a)

if infilename == '':
	usage()
	sys.exit(1)

try:
	fileIn = open(infilename, 'rt')
except:
	print( "Could not open input file %s" % (infilename))
	sys.exit(1)

base = os.path.basename(infilename)
basefile = os.path.splitext(base)[0]

lastmodified= os.stat("%s"%(infilename)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]

if outFileName != "":
	try:
		fileOut = open(outFileName, 'wt')
	except:
		print( "Could not open output file %s" % (outFileName))
		sys.exit(1)
else:
	fileOut = sys.stdout

fileOut.write("Input file: %s of %s\n" % (infilename, ftstr))
#fileOut.write("Start: %s\n" % (tstr))

cuv = parse_cuv()

numlines = 0

# skip first row, it is a header
line = fileIn.readline()
numlines += 1

cur_vect = [-99.0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
prev_vect = [-99.0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
edge_vect = [-99.0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]

while 1:
	line = fileIn.readline()
	if len(line) <= 0:
		break
	numlines += 1

	if len(line) <= 3:
		continue

	linesp = line.split(",")

	timestamp = float(linesp[IDX_TIME])
	cur_vect[0] = timestamp
	for i in range (1, 17):
		cur_vect[i] = int(linesp[i])

	# Detect edges
	if prev_vect[0] > -99.0:
		edge_vect[0] = cur_vect[0]
		for i in range (1, 17):
			edge_vect[i] = cur_vect[i] ^ prev_vect[i]

	# Call requested parsers
	cuv.update(cur_vect, edge_vect)

	if DEBUG1:
		print (prev_vect)
		print (cur_vect)
		print (edge_vect)
		print ("")

	prev_vect[:] = cur_vect[:]

fileOut.write("Done\n")

fileOut.write("\n")
E = cuv.get_entries()
lenE = len(E)
sumOfFlashes = 0

fileOut.write ("Strobe Chart\n")
fileOut.write ("Time 1st    Cuvette  Count\n")
fileOut.write ("----------  -------  ------\n")
for i in range(lenE):
	fileOut.write ("%10.6f  %7d  %6d\n" % (E[i][2], E[i][0], E[i][1]))
	sumOfFlashes += E[i][1]

fileOut.write ("Flash Count = %d\n" % (sumOfFlashes))

fileOut.write ("\n")

#
# self.BeakTiming2
#
fileOut.write("Beak Timing (microseconds)\n")
if gcd > 0.1:
	fileOut.write("Global Cuvette Delay = %.0f\n" % (gcd))
	fileOut.write("           [Measured]                                  [Derived]                                     \n")
	fileOut.write("     Cuv   Ref Width  RefToBeak     Integ      Cycle   BeakDelay     BeakErr    %       IntErr    %  \n")
	fileOut.write("     ---   ---------  ---------  --------  ---------   ---------   ---------  -----  ---------  -----\n")
else:
	fileOut.write("     Cuv   Ref Width  RefToBeak        Int      Cycle  BeakDelay\n")
	fileOut.write("     ---   ---------  ---------  ---------  ---------  ---------\n")

bt = cuv.get_BeakTiming2()
lenBt2 = len(bt)
list_RefWidth = []
list_delayRefToBeak = []
list_delayBeakToHold = []
list_delayBeakWidth = []
list_BeakTime = []

for i in range (lenBt2):
	delay_RefWidth = 1000000 * (bt[i][2] - bt[i][1])
	delay_delayRefToBeak = 1000000 * (bt[i][4]- bt[i][2])
	delay_delayBeakToHold = 1000000 * (bt[i][5] - bt[i][4])
	delay_delayBeakWidth = 1000000 * (bt[i][7] - bt[i][4])
	delay_BeakTime = delay_delayRefToBeak + delay_RefWidth/2
	if bt[i][0] == 1:
		delay_BeakTime -= 66

	if delay_delayBeakToHold < 4:
		continue

	list_BeakTime.append(delay_BeakTime)
	list_delayBeakToHold.append(delay_delayBeakToHold)

	if gcd > 0.1:
		err_Beak = delay_BeakTime - gcd
		err_BeakPct = 100 * err_Beak / gcd
		err_Int = delay_delayBeakToHold - 100
		err_IntPct = 100 * err_Int / 100

		fileOut.write ("%4d %3d  % 10.3f % 10.3f % 9.3f %10.3f  %10.3f  %10.6f %6.2f %10.6f %6.2f\n" % \
					(i+1, bt[i][0], delay_RefWidth, delay_delayRefToBeak, delay_delayBeakToHold, \
					delay_delayBeakWidth, delay_BeakTime, err_Beak, err_BeakPct, err_Int, err_IntPct))
	else:
		fileOut.write ("%4d %3d  % 10.3f % 10.3f % 9.3f %10.3f  %10.3f\n" % \
					(i+1, bt[i][0], delay_RefWidth, delay_delayRefToBeak, delay_delayBeakToHold, \
					delay_delayBeakWidth, delay_BeakTime))

arr_BeakTime = np.asarray(list_BeakTime)
arr_BeakToHold = np.asarray(list_delayBeakToHold)		

print ("")
print ("Timing Stats (microseconds)")
print ("        Beak Delay      Integ")
print ("        ----------    -------")
if AEW_DEBUG:
	temp = np.min(arr_BeakTime)
	if temp < 0:
		arr_BeakTime = np.delete(arr_BeakTime, np.where(arr_BeakTime == temp))
	temp = np.max(arr_BeakToHold)
	if temp > 120:
		arr_BeakToHold = np.delete(arr_BeakToHold, np.where(arr_BeakToHold == temp))

print ("Min     {0: >10.3f}  {1: >9.3f}".format(np.min(arr_BeakTime), np.min(arr_BeakToHold)))
print ("Max     {0: >10.3f}  {1: >9.3f}".format(np.max(arr_BeakTime), np.max(arr_BeakToHold)))
print ("Mean    {0: >10.3f}  {1: >9.3f}".format(np.mean(arr_BeakTime), np.mean(arr_BeakToHold)))
print ("Stdev        {0: >.3f}      {1: >.3f}".format(np.std(arr_BeakTime), np.std(arr_BeakToHold)))

if gcd > 0.1:
	beakAvgErr = np.mean(arr_BeakTime) - gcd
	beakAvgErrPct = 100 * beakAvgErr / gcd
	inthAvgErr = np.mean(arr_BeakToHold) - 100
	inthvgErrPct = 100 * inthAvgErr / 100
	print ("AvgErr      {0: >.3f}    {1: >7.3f}".format(beakAvgErr, inthAvgErr))
	print ("PctErr     {0: >6.2f}%    {1: >6.2f}%".format(beakAvgErrPct, inthvgErrPct))

estr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

#fileOut.write("End:   %s\n" % (estr))
#print ("End:   %s" % (estr))

#
# spi_pho_raw3.py
#
# Decode LA capture Photonics ADS1258 and Cuvette strobes
#

# verbosity bit map
#   1  ADC+PHO
#   2  CUV_PULSE

import string
import sys
import getopt
import time
import os
import math
import pickle

DEBUG1 = 0
DEBUG2 = 0
DEBUG3 = 0
DEBUG4 = 0

DEBUG_R1 = 0 
DEBUG_T1 = 0 
DEBUG_RXTX = 0

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
IDX_CS   = 5
IDX_CLK  = 6
IDX_MOSI = 7
IDX_MISO = 8
IDX_BEAK = 10
IDX_CUV = 9
IDX_RX = 13
IDX_TX = 14
IDX_DACCS   = 4

VREF = 2.048
"""
V = Vref * (code / 0x780000
"""


#
# ##########
#

#
#
#
class dstruct:
	d_timestamp = 0.0
	d_cuv = 0
	d_flashcount = 0
	d_340nm = 0
	d_405nm = 0
	d_467nm = 0
	d_500nm = 0
	d_515nm = 0
	d_550nm = 0
	d_600nm = 0
	d_630nm = 0
	d_850nm = 0
	d_WHT_FLASH = 0


#
# parse_adc:
#
class parse_adc:
	def __init__(self):
		self.state = 0
		self.cmdNames = {0x00:"Chan Read Dir", 0x20: "Chan Read Reg", 0x60: "Write Reg"}
		self.chanNames = {0: "340nm", 1: "405nm", 2: "467nm", 3: "500nm", \
						  4: "515nm", 5: "550nm", 6: "600nm", 7: "630nm", \
						  8: "850nm", 9: "WHT_FLASH", 10: "SPARE1", 11: "SPARE2", \
						  12: "PH_GND", 13: "nc13", 14: "nc14", 15: "nc15"}
		self.cmd = ""
		self.multi = 0
		self.reg = 0

	def conv_voltage(self, v):
		val_twos = -(v & 0x800000) | (v & 0x7fffff)
		val_volt = (VREF * float(val_twos)) / 0x780000
		if abs(val_volt) < 0.000000999:
			val_volt = 0.0
		return val_volt

	def conv_decimal(self, v):
		val_twos = -(v & 0x800000) | (v & 0x7fffff)
		val_dec = val_twos
		#if abs(val_dec) < 0.000000999:
		#	val_dec = 0.0
		return val_dec

	def show(self, begin, id, mosiBytes, misoBytes):
		self.cmd = mosiBytes[0] & 0xe0
		self.multi = mosiBytes[0] & 0x10
		self.reg = mosiBytes[0] & 0x0f
		lenMosi = len(mosiBytes)
		lenMiso = len(misoBytes)
		
		fileOut.write("ADC_PHO %10.6f %5d " % (begin, id))
		fileOut.write("%-13s " % (self.cmdNames[self.cmd]))

		#
		# Write Reg
		if self.cmd == 0x60:
			startReg = self.reg
			fileOut.write("  ")
			for j in range(lenMosi - 1):
				fileOut.write("%1d: %2.2x " % (startReg, mosiBytes[1+j]))
				startReg += 1
			
			# verbose
			if verbosity & 1:
				fileOut.write(" -> ")
				fileOut.write("[%2d] " % (lenMosi))	
				for i in range(len(mosiBytes)):
					fileOut.write ("0x%2.2x " % (mosiBytes[i]))
			fileOut.write("\n")	

		#
		# Read Data Reg
		if self.cmd == 0x20:
			status = misoBytes[1] & 0xe0
			chan = (misoBytes[1] & 0x1f) - 8
			value = (misoBytes[2] * 65536) + (misoBytes[3] * 256) + misoBytes[4]

			if status == 0x80:
				status_str = "*"
			else:
				status_str = "!"
			chan_str = self.chanNames[chan]
			volts = self.conv_voltage(value)
			dvalue = self.conv_decimal(value)	# decimal value
			fileOut.write("%s %-10s % 9.6f V 0x%6.6x %6d D" % (status_str, chan_str, volts, value, dvalue))

			# verbose
			if verbosity & 1:
				fileOut.write(" (%6.6x) <- " % (value))
				fileOut.write("[%2d] " % (lenMiso))	
				for i in range(len(misoBytes)):
					fileOut.write ("0x%2.2x " % (misoBytes[i]))
			fileOut.write("\n")	

		#
		# Read Data Direct
		if self.cmd == 0x00:
			status = misoBytes[0] & 0xe0
			chan = (misoBytes[0] & 0x1f) - 8
			value = (misoBytes[1] * 65536) + (misoBytes[2] * 256) + misoBytes[3]

			if status == 0x80:
				status_str = "*"
			else:
				status_str = "!"
			chan_str = self.chanNames[chan]
			volts = self.conv_voltage(value)
			fileOut.write("%s %-10s % 9.6f V" % (status_str, chan_str, volts))

			# verbose
			if verbosity & 1:
				fileOut.write(" (%6.6x) <- " % (value))
				fileOut.write("[%2d] " % (lenMiso))	
				for i in range(len(misoBytes)):
					fileOut.write ("0x%2.2x " % (misoBytes[i]))
			fileOut.write("\n")	


#
# parse_spi:
#
class parse_spi:
	def __init__(self, pp):
		self.state = 0
		self.mosiBytes = []
		self.misoBytes = []
		self.numBytes = 0
		self.byteIdx = 0
		self.begin = 0.0
		self.end = 0.0
		self.id = 0
		self.countBits = 0
		self.pp = pp

	def update(self, cv, ev):
		if ev[IDX_CS] == 1 and cv[IDX_CS] == 0:
			self.begin = cv[0]
			self.state = 1
			self.a = 0x00
			self.b = 0x00
			if DEBUG2:
				print ("Start %f" % self.begin)

		if self.state == 1 and ev[IDX_CLK] == 1 and cv[IDX_CLK] == 1:
			self.a = ((self.a<<1) | cv[IDX_MOSI])
			self.b = ((self.b<<1) | cv[IDX_MISO])
			self.countBits += 1
			if DEBUG2:
				print ("bits %d %d %d %d" % (self.byteIdx, self.countBits, cv[IDX_MOSI], cv[IDX_MISO]))
			if self.countBits == 8:
				self.countBits = 0
				self.byteIdx += 1
				self.mosiBytes.append(self.a)
				self.misoBytes.append(self.b)
				self.a = 0x00
				self.b = 0x00

		if ev[IDX_CS] == 1 and cv[IDX_CS] == 1:
			if self.state == 0:
				return
			if DEBUG3:
				print ("Bytes %10.6f %4d " %  (self.begin, self.id), end="")
				for i in range(self.byteIdx):
					print ("0x%2.2x " % (self.mosiBytes[i]), end="")
				print ("\n                      ", end="")	
				for i in range(self.byteIdx):
					print ("0x%2.2x " % (self.misoBytes[i]), end="")
				print("")

			self.pp.show(self.begin, self.id, self.mosiBytes, self.misoBytes)

			self.end = cv[0]
			self.state = 0
			self.countBits = 0
			self.byteIdx = 0
			self.mosiBytes = []
			self.misoBytes = []
			self.id += 1
			if DEBUG2:
				print ("End %f" % self.begin)


#
# parse_cuv:
#
class parse_cuv:
	def __init__(self):
		self.state = 0
		self.timeRE = 0.0
		self.timeFE = 0.0
		self.timeLastRE = 0.0
		self.timeLastFE = 0.0
		self.numPulses = 0
		self.numIndexes = 0
		self.pulseCount = 0		# corresponds to cuvette number
		self.beakFE = 0.0
		self.beakLastFE = 0.0
		self.beakCount = 0
		self.prevDC = 0.0
		self.Entries = []
		self.prevEntry = -1
		self.pulseWidth = 0.0
		self.lastIndexRE = 0.0
		self.indexCountB0n = 0
		self.indexCountBOff = 0

		self.IndexWidths = []	#	Zone 0 = Before and during with adjustment
								#	Zone 1 = Concurrent with Beak, ie flashing on Cuv 0
								#	Zone 2 = All other index pulses

	def update(self, cv, ev):

		# Falling edge of BEAK
		if ev[IDX_BEAK] == 1 and cv[IDX_BEAK] == 0:
			self.beakFE = cv[IDX_TIME]
			self.beakCount += 1

			# adjust to next cuv number simce the FE for this pulse is after beak FE and has not happended yet
			adjPulse = self.pulseCount+1
			if adjPulse == 30:
				adjPulse = 0
			fileOut.write("BEAK    %10.6f %5d Cuv %2d  %d:%2.2d %10.6f (%11.9f) (%11.9f)\n" % \
				(self.beakFE, self.beakCount, adjPulse, self.numPulses/30, self.numPulses%30, self.timeRE, self.beakFE-self.timeRE, self.beakFE-self.lastIndexRE))
			if (adjPulse) != self.prevEntry:
				thisEntry = [adjPulse, 1, self.beakFE, self.timeRE]
				self.Entries.append(thisEntry)
			else:
				self.Entries[-1][1] += 1
				self.Entries[-1][3] += self.timeRE
			self.prevEntry = adjPulse
			
			self.beakLastFE = self.beakFE

		# Rising edge of pulse
		if ev[IDX_CUV] == 1 and cv[IDX_CUV] == 1:
			self.timeRE = cv[IDX_TIME]
			self.timeLastFE = self.timeFE

		# Falling edge of pulse
		if ev[IDX_CUV] == 1 and cv[IDX_CUV] == 0:
			self.timeFE = cv[IDX_TIME]
			self.timeLastRE = self.timeRE

			self.pulseWidth = self.timeFE - self.timeRE
			periodff = self.timeFE - self.timeLastFE
			hitimeff = self.timeFE - self.timeRE
			dc = hitimeff / periodff

			# TODO: clean up this duplication of pulse count
			adjPulse = self.pulseCount+1
			if adjPulse == 30:
				adjPulse = 0
			
				# This is the index pulse
				# Double check width
				pulseWidth = self.timeFE - self.timeRE
				if cv[IDX_BEAK] == 0:
					beak = 1
					self.indexCountB0n += 1
				else:
					beak = 0
					self.indexCountBOff += 1
				self.IndexWidths.append([self.timeRE, self.pulseWidth, periodff, beak, 0])

			if verbosity & 2:
				print ("T = %f p = %f h = %f dc = %f" % (cv[IDX_TIME], periodff, hitimeff, dc), end="")

			if (self.timeFE - self.beakLastFE) > 1.0:
				self.state = 0
			else:
				self.state = 1

			if self.state == 0:
				if ((dc - self.prevDC) > 0.12) and periodff > 0.001290 and periodff < 0.001450:
					self.pulseCount = 0
					self.numPulses = 0
				else:
					self.pulseCount += 1
					if self.pulseCount == 30:
						self.pulseCount = 0

			elif self.state == 1:
				self.pulseCount += 1
				if self.pulseCount == 30:
					self.pulseCount = 0
					
				if ((dc - self.prevDC) > 0.12) and periodff > 0.001290 and periodff < 0.001450:
					if self.pulseCount != 0: 
						fileOut.write (" Beak Error!\n")

			if self.pulseCount == 0:
				self.lastIndexRE = self.timeRE

			if verbosity & 2:
				print (" c = %d %d %d %d" % (self.state, self.numPulses, self.pulseCount, self.numPulses % 30), end = "")
				print ("")

			self.numPulses += 1
			self.prevDC = dc

	def get_entries(self):
		return self.Entries

	def get_indexWidths(self):
		return self.IndexWidths

	def get_BeakInfo(self):
		return (self.indexCountB0n, self.indexCountBOff)


#
# parse_AsyncSerial:
#
class parse_AsyncSerial:
	def __init__(self, idx):
		self.startTime = 0.0
		self.thisTime = 0.0
		self.prevTime = -2000.0
		self.byte = 0x00
		self.bitCounter = 0
		self.Entries = []
		self.Values = []
		self.idx = idx
		self.bitsComb = 0
		self.bidx = 0
		self.debugstr = ""

	def update(self, cv, ev):
		# Begin
		self.thisTime = cv[IDX_TIME]

		# Edge on Serial line
		if (ev[self.idx] == 1):
				
			self.delta = self.thisTime - self.prevTime
			self.bitsComb = int((self.delta + 0.000008) / 0.00001734)

			if (self.bitCounter == 0):
				self.debugstr = " S"

			self.bitCounter += self.bitsComb

			if (cv[self.idx] == 0) and (self.bitCounter >= 9):
				self.debugstr = " E"
				if (self.bitsComb > 1):
					self.debugstr += "+"

			if (DEBUG_R1 and (self.idx == IDX_RX)) or (DEBUG_T1 and (self.idx == IDX_TX)):
				print ("%2d " % (self.idx), end='')

			for z in range(self.bitsComb):

				if (DEBUG_R1 and (self.idx == IDX_RX)) or (DEBUG_T1 and (self.idx == IDX_TX)):
					print ("(%2d, %1d)" % (self.bidx, cv[self.idx] ^ 1), end='')

				if (self.bidx >= 1) and (self.bidx <= 8):
					self.byte += (cv[self.idx] ^ 1) * 2 ** (self.bidx - 1)

				if self.bidx == 8:

					if (DEBUG_R1 and (self.idx == IDX_RX)) or (DEBUG_T1 and (self.idx == IDX_TX)):
						print (" VALUE %2.2x" % (self.byte), end='')

					self.debugstr = " VALUE %2.2x" % (self.byte)
					if self.prevTime > -1999.0:
						self.Values.append([self.startTime, self.byte])

				self.bidx += 1
				if self.bidx > 8:
					break

			if (DEBUG_R1 and (self.idx == IDX_RX)) or (DEBUG_T1 and (self.idx == IDX_TX)):
				print ("")

			thisEntry = [self.thisTime, self.prevTime, self.delta, cv[self.idx], \
						 self.bitCounter, self.bitsComb, self.debugstr]

			if self.prevTime > -1999.0:
				self.Entries.append(thisEntry)

			if (cv[self.idx] == 0) and (self.bitCounter >= 9):
				self.bitCounter = 0
				self.bidx = 0
				self.byte = 0
				self.startTime = self.thisTime

			self.prevTime = self.thisTime
			self.debugstr = ""

	def get_entries(self):
		return self.Entries

	def get_values(self):
		return self.Values


#
# parse_DacA:
#
class parse_DacA:
	def __init__(self):
		self.state = 0
		self.addr = 0
		self.pwr = 0
		self.spd = 0
		self.val = 0
		self.sequenceNum = 0
		self.channel = {0: "340nm", 1: "405nm", 2: "467nm", 3: "500nm", \
						4: "515nm", 5: "550nm", 6: "600nm", 7: "630nm", \
						8: "850nm", 9: "WHTFL"}

	def show(self, begin, id, mosiBytes, misoBytes):
		self.addr = (mosiBytes[0] & 0xc0) >> 6
		self.pwr = (mosiBytes[0] & 0x20) >> 5
		self.spd = (mosiBytes[0] & 0x10) >> 4
		self.val = ((mosiBytes[0] & 0x0f) << 4) + ((mosiBytes[1] & 0xf0) >> 4)
		lenMosi = len(mosiBytes)
		lenMiso = len(misoBytes)
		fileOut.write ("DAC_PHO %10.6f (" % (begin))
		for m in range (lenMosi):
			fileOut.write (" %4.4x" % (mosiBytes[m]))
		fileOut.write (" ) { ")
		for m in range (lenMosi):
			if (mosiBytes[m] & 0x0300) == 0x0300:
				fileOut.write ("%1d %-5s %3d " % \
						(self.sequenceNum, self.channel[self.sequenceNum], 0xff & mosiBytes[m]))
		fileOut.write ("}\n")
		self.sequenceNum += 1
		if self.sequenceNum >= 10:
			self.sequenceNum = 0


#
# parse_spi_d:
#
# tlv5627 16 bit access, 12 bits used, 4 channels per device, 
#         3 daisy-chained devices, total 10 channels used
class parse_spi_d:
	def __init__(self, I_CS, I_CLK, I_MOSI, I_MISO, PH_CLK, pp):
		self.state = 0
		self.mosiBytes = []
		self.misoBytes = []
		self.numBytes = 0
		self.byteIdx = 0
		self.begin = 0.0
		self.end = 0.0
		self.id = 0
		self.countBits = 0
		self.pp = pp
		self.idx_CS = I_CS
		self.idx_CLK= I_CLK
		self.idx_MOSI = I_MOSI
		self.idx_MISO = I_MISO
		self.PH_CLK = PH_CLK

	def update(self, cv, ev):
		if ev[self.idx_CS] == 1 and cv[self.idx_CS] == 0:
			self.begin = cv[0]
			self.state = 1
			self.a = 0x0000
			self.b = 0x0000
			if DEBUG2:
				print ("Start %f" % self.begin)

		if self.state == 1 and ev[self.idx_CLK] == 1 and cv[self.idx_CLK] == self.PH_CLK:
			self.a = ((self.a<<1) | cv[self.idx_MOSI])
			self.b = ((self.b<<1) | cv[self.idx_MISO])
			self.countBits += 1
			if DEBUG2:
				print ("bits %d %d %d %d" % (self.byteIdx, self.countBits, cv[self.idx_MOSI], cv[self.idx_MISO]))
			if self.countBits == 12:
				self.countBits = 0
				self.byteIdx += 1
				self.mosiBytes.append(self.a)
				self.misoBytes.append(self.b)
				self.a = 0x0000
				self.b = 0x0000

		if ev[self.idx_CS] == 1 and cv[self.idx_CS] == 1:
			if self.state == 0:
				return
			if DEBUG4:
				print ("Bytes %10.6f %4d " %  (self.begin, self.id), end="")
				for i in range(self.byteIdx):
					print ("0x%4.4x " % (self.mosiBytes[i]), end="")
				print ("\n                      ", end="")	
				for i in range(self.byteIdx):
					print ("0x%4.4x " % (self.misoBytes[i]), end="")
				print("")

			self.pp.show(self.begin, self.id, self.mosiBytes, self.misoBytes)

			self.end = cv[0]
			self.state = 0
			self.countBits = 0
			self.byteIdx = 0
			self.mosiBytes = []
			self.misoBytes = []
			self.id += 1
			if DEBUG2:
				print ("End %f" % self.begin)


#
# ##########
#

#
# usage()
#
def usage():
    print( "spi_pho_raw3 -i <rotor_name> [-v <verbosity_level>] [-a <dest_path>]")
    print( " -r Rotor name ")
    print( " -v Verbosity")
    print( " -a Save separate AsyncSerial Rx and Tx files")
	
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
outfilename = ''
out_text = 0
verbosity = 0
ASYNC_TO_FILE = 0
outPath = ''

#    
# parse command line options
#
try:
	opts, args = getopt.getopt(sys.argv[1:], "r:v:a:")
except getopt.error:
	usage()
	sys.exit(2)

# process options
rotor_name = ""

for o, a in opts:
	if o == "-r":
		rotor_name = a
	elif o == "-v":
		verbosity = int(a)
	elif o == "-a":
		ASYNC_TO_FILE = 1
		outPath = a

if rotor_name == '':
	usage()
	sys.exit(1)

infilename = rotor_name + "_Group0.csv"

try:
	fileIn = open(infilename, 'rt')
except:
	print( "Could not open input file %s" % (infilename))
	sys.exit(1)

base = os.path.basename(infilename)
basefile = os.path.splitext(base)[0]
# AEW added in:
prefix = infilename.replace(base, "")
prefix = prefix.replace("Exports", "Reports")
abspath = os.path.abspath(prefix)
outpath = abspath.replace("Exports", "Reports")
if not os.path.exists(outpath):
	os.mkdir(outpath)

outfilename = outpath + "\\" + basefile + "Data.txt"

lastmodified= os.stat("%s"%(infilename)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]

if outfilename != "":
	try:
		fileOut = open(outfilename, 'wt')
	except:
		print( "Could not open output file %s" % (outfilename))
		sys.exit(1)
else:
	fileOut = sys.stdout

fileOut.write("Input file: %s of %s\n" % (infilename, ftstr))
#fileOut.write("Start: %s\n" % (tstr))

adc = parse_adc()
spi = parse_spi(adc)
cuv = parse_cuv()
serialRx = parse_AsyncSerial(IDX_RX)
serialTx = parse_AsyncSerial(IDX_TX)
daca = parse_DacA()
spi_dac_p = parse_spi_d(IDX_DACCS, IDX_CLK, IDX_MOSI, IDX_MISO, 1, daca)

numlines = 0

fileOut.write("\n")
fileOut.write("Module  Time        ID   Command         Value\n")
fileOut.write("------- ---------- ----- -------------   -----\n")

# skip first row, it is a header
line = fileIn.readline()
numlines += 1

# Note: -600.0 value is arbitrary. If the serial data is being cut off at -599, 
# this is the reason. If data needed is beyond -600s, change value accordingly.
cur_vect = [-600.0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
prev_vect = [-600.0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
edge_vect = [-600.0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]

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
	if prev_vect[0] > -600.0:
		edge_vect[0] = cur_vect[0]
		for i in range (1, 17):
			edge_vect[i] = cur_vect[i] ^ prev_vect[i]

	# Call requested parsers
	spi.update(cur_vect, edge_vect)
	cuv.update(cur_vect, edge_vect)
	serialRx.update(cur_vect, edge_vect)
	serialTx.update(cur_vect, edge_vect)
	spi_dac_p.update(cur_vect, edge_vect)

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
	#fileOut.write ("%10.6f  %7d  %6d  %8.6f\n" % (E[i][2], E[i][0], E[i][1], E[i][3]))
	fileOut.write ("%10.6f  %7d  %6d\n" % (E[i][2], E[i][0], E[i][1]))
	sumOfFlashes += E[i][1]

fileOut.write ("Flash Count = %d\n" % (sumOfFlashes))

fileOut.write ("\n")
indexCounts = cuv.get_BeakInfo()
fileOut.write ("Index pulses with Beak   = %d\n" % (indexCounts[0]))
fileOut.write ("Index puses without beak = %d\n" % (indexCounts[1]))

W = cuv.get_indexWidths()
lenW = len(W)
fileOut.write ("Time, s    Width, s     Period, s Bk\n")
fileOut.write ("---------- ------------ --------  --\n")
for i in range (lenW):
	fileOut.write ("%10.6f %11.9f  %8.6f  B%1d\n" % (W[i][0], W[i][1], W[i][2], W[i][3]))
fileOut.write ("\n")

estr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
#fileOut.write("End:   %s\n" % (estr))
#print ("End:   %s" % (estr))

if ASYNC_TO_FILE:
	R = serialRx.get_values()
	lenR = len(R)
	# AEW edit: replace 'basefile' with new path
	# with open("%s%s_rx.txt" % (outPath, basefile), 'wt') as f:
	with open("%s%s%s_rx.txt" % (prefix, outPath, basefile), 'wt') as f:
		f.write("Time [s],Value,Parity Error,Framing Error\n")
		for x in range(lenR):
			f.write("%.15f,0x%2.2X,,\n" % (R[x][0], R[x][1]))

	T = serialTx.get_values()
	lenT = len(T)
	# AEW edit
	# with open("%s%s_tx.txt" % (outPath, basefile), 'wt') as f:
	with open("%s%s%s_tx.txt" % (prefix, outPath, basefile), 'wt') as f:
		f.write("Time [s],Value,Parity Error,Framing Error\n")
		for x in range(lenT):
			f.write("%.15f,0x%2.2X,,\n" % (T[x][0], T[x][1]))


if DEBUG_RXTX:
	R = serialRx.get_entries()
	lenR = len(R)
	print ("DUMP_R %d" % (lenR))
	for x in range(lenR):
		print ("%10.6f %10.6f %2.9f %1d %2d %6d %s" % \
				(R[x][0], R[x][1], R[x][2], R[x][3], R[x][4], R[x][5], R[x][6]))
		if R[x][4] == 9:
			print ("")

	T = serialTx.get_entries()
	lenT = len(T)
	print ("DUMP_T %d" % (lenT))
	for x in range(lenT):
		print ("%10.6f %10.6f %2.9f %1d %2d %6d %s" % \
				(T[x][0], T[x][1], T[x][2], T[x][3], T[x][4], T[x][5], T[x][6]))
		if T[x][4] == 9:
			print ("")
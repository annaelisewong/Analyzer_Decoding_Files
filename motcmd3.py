#
# motcmd.py
#
#

import string
import sys
import getopt
import time
import os
import math

IDX_TIME = 0

VERBOSE1 = 0
VERBOSE2 = 0
VERBOSE3 = 0

def usage():
    print( "motcmd <rx_file> <tx_file>")


# dir 1 = out, 0 = in


def get16(d, i):
	return (d[i] * 256) + d[i+1]
	
def get32(d, i):
	if d[i] & 0x80:
		val = (d[i] * 256 * 256 * 256) + (d[i+1] * 256 * 256) + (d[i+2] * 256) +d[i+3]
		val ^= 0xffffffff
		val += 1
		val &= 0xffffffff
		return -1 * val
	else:
		return (d[i] * 256 * 256 * 256) + (d[i+1] * 256 * 256) + (d[i+2] * 256) +d[i+3]

#
# parse_host
#
class parse_host:
	def __init__(self):
		self.state = 0
		self.UpdateCount = 0
		self.payload = []
		self.stxTime = 0.0
		self.updTime = 0.0
		self.updTimePrev = 0.0
		self.ackByte = 0

		self.CmdSummary = []
		self.countToSBC = 0
		self.countFromSBC = 0
		self.ca = ""
		self.cd = ""
		self.cv = ""
		


	def decode_payload(self, p, d):
		length = len(p)
		dir = d

		if VERBOSE1:
			print ("\nLENGTH %d" % (length))
			print ("\nPayload %d [%d] %f" % (dir, length, self.stxTime))
			print ("Addr  %2.2x" % (p[0]))
			print ("CkSum %2.2x" % (p[1]))
			print ("Axis  %2.2x " % (p[2]))
			print ("Cmd   %2.2x " % (p[3]))

		axis = p[2]
		cmd = p[3]

		if cmd == 0x02:
			cmdString = "SetMotorType"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0x34:
			cmdString = "ResetEventStatus"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0x65:
			cmdString = "SetOperatingMode"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0x72:
			cmdString = "SetPhaseInitializeTime"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0x75:
			cmdString = "SetPhaseCounts"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0x77:
			cmdString = "SetMotorCommand"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0xa0:
			cmdString = "SetProfileMode"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0xda:
			cmdString = "SetEncoderSource"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0xe0:
			cmdString = "SetOutputMode"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0xe2:
			cmdString = "SetCommutationMode"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0xe4:
			cmdString = "SetPhaseInitializeMode"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0xe8:
			cmdString = "SetPhaseCorrectionMode"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))
		elif cmd == 0x31:
			cmdString = "GetEventStatus"
			cmdLength = 0
			#argString = "%4.4x" % (get16(p, 4))
			# check tx
			argString = ''
		elif cmd == 0x8f:
			cmdString = "GetVersion"
			cmdLength = 0
			#argString = "%4.4x" % (get16(p, 4))
			# check tx
			argString = ''
		elif cmd == 0xa5:
			cmdString = "GetInstructionError"
			cmdLength = 0
			#argString = "%4.4x" % (get16(p, 4))
			# check tx
			argString = ''
		elif cmd == 0xf8:
			cmdString = "GetChecksum"
			cmdLength = 0
			#argString = "%4.4x" % (get16(p, 4))
			# check tx
			argString = ''
		elif cmd == 0x67:
			cmdString = "SetPositionLoop"
			cmdLength = 6
			argString = "%4.4x %8.8x" % (get16(p, 4), get32(p, 6))
		elif cmd == 0x10:
			cmdString = "SetPosition"
			cmdLength = 4
			argString = "%8.8x" % (get32(p, 4))
		elif cmd == 0x11:
			cmdString = "SetVelocity"
			cmdLength = 4
			argString = "%10d %10d RPM" % (get32(p, 4), get32(p, 4) / 80.21)
			self.cv = "% 5d RPM" % (get32(p, 4) / 80.21)
		elif cmd == 0x13:
			cmdString = "SetJerk"
			cmdLength = 4
			argString = "%8.8x" % (get32(p, 4))
		elif cmd == 0x48:
			cmdString = "SetEventAction"
			cmdLength = 4
			argString = "%8.8x" % (get32(p, 4))
		elif cmd == 0x90:
			cmdString = "SetAcceleration"
			cmdLength = 4
			argString = "%10d" % (get32(p, 4))
			self.ca = "%3d" % (get32(p, 4))
		elif cmd == 0x91:
			cmdString = "SetDeceleration"
			cmdLength = 4
			argString = "%10d" % (get32(p, 4))
			self.cd = "%3d" % (get32(p, 4))
		elif cmd == 0x97:
			cmdString = "SetPositionErrorLimit"
			cmdLength = 4
			argString = "%8.8x" % (get32(p, 4))
		elif cmd == 0x39:
			cmdString = "Reset"
			cmdLength = 0
			argString = ''
		elif cmd == 0x7a:
			cmdString = "InitializePhase"
			cmdLength = 0
			argString = ''
		elif cmd == 0x1a:
			# Causes buffered parameters to be copied to run-time registers
			cmdString = "Update axis"
			cmdLength = 0
			argString = ''

		elif cmd == 0x1f:
			cmdString = "UNKNOWN_COMMAND!"
			cmdLength = 2
			argString = "%4.4x" % (get16(p, 4))

		else:
			cmdString = "UNKNOWN_DECODE!"
			cmdLength = 0
			argString = ''

		if cmd == 0x1a:
			# use the "Update" to record complete motion 'update'
			fileOut.write ("Command: %10.6f <%2.2x> %s [%1d] %s {%10.6f, %10.6f}\n" % \
					(self.stxTime, p[2], cmdString, cmdLength, argString, self.updTime, self.updTime - self.updTimePrev))
			# print ("Command: %10.6f <%2.2x> %s [%1d] %s {%10.6f, %10.6f}" % \
			# 		(self.stxTime, p[2], cmdString, cmdLength, argString, self.updTime, self.updTime - self.updTimePrev))

			self.CmdSummary.append("Cmd[%3.3d] % 11.6f % 11.6f %s %s %s\n" % \
					(self.UpdateCount, self.stxTime, self.updTime - self.updTimePrev, self.ca, self.cd, self.cv)) 

			self.updTimePrev = self.updTime
			self.UpdateCount += 1
			self.ca = ""
			self.cd = ""
			self.cv = ""

			fileOut.write ("\n")
		else:
			fileOut.write ("Command: %10.6f <%2.2x> %s [%1d] %s\n" % \
					(self.stxTime, p[2], cmdString, cmdLength, argString))


	def update(self, time_in, int_in, dir):
		rs = ""
		if VERBOSE3:
			fileOut.write ("%11.6f %2.2x %d\n" % (time_in, int_in, dir))

		if dir == 0:
			if self.state == 0:
				self.stxTime = time_in
				self.state = 1
			self.updTime = self.stxTime
			self.payload.append(int_in)
			self.ackByte = 0

		elif (dir == 1) and (self.ackByte == 0):
			self.ackByte = 1
			self.decode_payload(self.payload, 0)
			if VERBOSE2:
				fileOut.write ("\nPacket Done\n")
			self.payload = []
			self.state = 0

		elif (dir == 1) and (self.ackByte == 1):
			pass

		else:
			fileOut.write ("Packet Error\n")
	

	def dump(self, e):
		if e[2] == 'r':
			ss = parser.update(e[0], e[1], 0)
		else:
			ss = parser.update(e[0], e[1], 1)
		if VERBOSE3:
			fileOut.write("\n\n")

	# parse_host


argc = len(sys.argv)
if argc < 3:
    usage()
    sys.exit(0)

# cmd line defaults
rxfilename = sys.argv[1]
txfilename = sys.argv[2]
out_text = 0

outfilename = txfilename.replace("Group1_mottx", "MotCmdMsgOut")
if os.path.exists(outfilename):
	os.remove(outfilename)
fileOut = open(outfilename, 'wt')

startnow = time.localtime(time.time())
tstr = time.strftime("%Y-%m-%d %H:%M:%S", startnow)
fileOut.write ("Starting ... %s\n" % (tstr))
fileOut.write ("Data files: \'%s\' \'%s\ \n'" % (rxfilename, txfilename))

try:
	fileRx = open(rxfilename, 'rt')
except:
	print( "Could not open input file %s" % (rxfilename))
	sys.exit(1)

try:
	fileTx = open(txfilename, 'rt')
except:
	print( "Could not open input file %s" % (txfilename))
	sys.exit(1)

"""
lastmodified= os.stat("%s"%(infilename)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)
print( "Processing file  ... %s" % (ftstr))

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]
"""
# fileOut = sys.stdout

#fileOut.write("Data file: %s of %s\n" % (infilename, ftstr))

fileOut.write("\n")

first_ts = -1.0
sequence = []

parser = parse_host()


#
# Read RX file
#
numlines = 0
numRxLines = 0
# skip first row, it is header
line = fileRx.readline()
numlines += 1

while 1:
	line = fileRx.readline()
	if len(line) <= 0:
		break
	numlines += 1
	numRxLines += 1

	if len(line) <= 3:
		continue

	linesp = line.split(",")

	timestamp = float(linesp[IDX_TIME])
	rxData = int(linesp[1], 16)
	ent = [timestamp, rxData, "r"]
	sequence.append(ent)

#
# Read TX file
#
numlines = 0
numTxLines = 0
# skip first row, it is header
line = fileTx.readline()
numlines += 1

while 1:
	line = fileTx.readline()
	if len(line) <= 0:
		break
	numlines += 1
	numTxLines += 1

	if len(line) <= 3:
		continue

	linesp = line.split(",")

	timestamp = float(linesp[IDX_TIME])
	txData = int(linesp[1], 16)
	ent = [timestamp, txData, "t"]
	sequence.append(ent)

# sort by time
sortedSequence = sorted(sequence, key = lambda ent: ent[0])   # sort by timestamp
# print (len(sequence), numRxLines, numTxLines)
fileOut.write ("%d %d %d\n" % (len(sequence), numRxLines, numTxLines))

# decode
for i in range(len(sortedSequence)):
	parser.dump(sortedSequence[i])

# # print summary
# print ("------------------------------------------------------------")
# print ("Summary")
# #print ("%4d messages to Controller" % (parser.countFromSBC))
# #print ("%4d messages to SBC" % (parser.countToSBC))
# print ("------------------------------------------------------------")
# print ("")
# print("          Time       Delta        A   D  Speed    ")
# print("          ---------- -----------  --  -- ---------")
# for i in range(len(parser.CmdSummary)):
# 	print ("%s" % parser.CmdSummary[i])



# print summary
fileOut.write ("------------------------------------------------------------\n")
fileOut.write ("Summary\n")
#fileOut.write ("%4d messages to Controller" % (parser.countFromSBC))
#fileOut.write ("%4d messages to SBC" % (parser.countToSBC))
fileOut.write ("------------------------------------------------------------\n")
fileOut.write ("")
fileOut.write("          Time       Delta        A   D  Speed    \n")
fileOut.write("          ---------- -----------  --  -- ---------\n")
for i in range(len(parser.CmdSummary)):
	fileOut.write ("%s\n" % parser.CmdSummary[i])

fileOut.close()

#
# heatanalyze.py
#
#

import string
import sys
import getopt
import time
import os
import math

DEBUG1 = 0
DEBUG2 = 0

def usage():
    print( "heatanalyze <Grp1Out_file> <MsgOut_file>")

#
#
#
argc = len(sys.argv)
if argc < 3:
    usage()
    sys.exit(0)

# cmd line defaults
grp1Filename = sys.argv[1]
msgFilename = sys.argv[2]
out_text = 0

startnow = time.localtime(time.time())
tstr = time.strftime("%Y-%m-%d %H:%M:%S", startnow)
#print ("Starting ... %s" % (tstr))
print ("Data files: \'%s\' \'%s\'" % (os.path.split(grp1Filename)[1], os.path.split(msgFilename)[1]))

try:
	fileGrp1 = open(grp1Filename, 'rt')
except:
	print( "Could not open input file %s" % (grp1Filename))
	sys.exit(1)

try:
	fileMsg = open(msgFilename, 'rt')
except:
	print( "Could not open input file %s" % (msgFilename))
	sys.exit(1)

"""
lastmodified= os.stat("%s"%(infilename)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)
print( "Processing file  ... %s" % (ftstr))

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]
"""

fileOut = sys.stdout
#fileOut.write("Data file: %s of %s\n" % (infilename, ftstr))

fileOut.write("\n")

grp1Sequence = []
msgSequence = []
phoflashcnt = 0
totcnt = 1

#
# Read Group1 file
#

numlines = 0
numRxLines = 0
# skip first row, it is header
line = fileGrp1.readline()
numlines += 1

prevSumf = 0.0
prevSum = 0
prevCount = 0

while 1:
	line = fileGrp1.readline()
	if len(line) <= 0:
		break
	numlines += 1
	numRxLines += 1

	if len(line) <= 3:
		continue

	linej = " ".join(line.split())
	linesp = linej.split()
	
	if (linesp[0] == "DacA") and (linesp[6] == "Top_Set"):
		cmdstr = "DacA %7.3f: Top_Set %3d" % (float(linesp[2]), int(linesp[7]))
		pp = [float(linesp[2]), cmdstr]
		grp1Sequence.append(pp)
		totcnt += 1

	elif (linesp[0] == "DacA") and (linesp[6] == "Bot_Set"):
		cmdstr = "DacA %7.3f: Bot_Set %3d" % (float(linesp[2]), int(linesp[7]))
		pp = [float(linesp[2]), cmdstr]
		grp1Sequence.append(pp)
		totcnt += 1

	elif (linesp[0] == "Temp"):
		prevCount += 1
		prevSumf += float(linesp[4])
		if prevCount == 16:
			prevCount = 0
			cmdstr = "Read %7.3f: Ambient = %4.1f" % (float(linesp[2]), prevSumf/16.0)
			pp = [float(linesp[2]), cmdstr]
			grp1Sequence.append(pp)
			totcnt += 1
			prevSumf = 0.0

	elif (linesp[0] == "ADC_SYS"):
		if (linesp[7] == "RTR_TEMP"):
			prevCount += 1
			prevSum += int(linesp[11])
			if DEBUG2:
				print ("%2d dbg %7.3f: RTR_TEMP     = %8d -- %6d %8d %7d" % \
						(prevCount, float(linesp[1]), int(linesp[11]), int(linesp[2]), prevSum, prevSum/prevCount))
			if prevCount == 16:
				cmdstr = "read %7.3f: Rotor temp  = %7d (%7d)" % (float(linesp[1]), int(linesp[11]), prevSum/16)
				pp = [float(linesp[1]), cmdstr]
				grp1Sequence.append(pp)
				totcnt += 1
		elif (linesp[7] == "TOP_TEMP"):
			prevCount += 1
			prevSum += int(linesp[11])
			if DEBUG2:
				print ("%2d dbg %7.3f: TOP_TEMP     = %8d -- %6d %8d %7d" % \
						(prevCount, float(linesp[1]), int(linesp[11]), int(linesp[2]), prevSum,prevSum/prevCount))
			if prevCount == 16:
				cmdstr = "read %7.3f: Top temp    = %7d (%7d)" % (float(linesp[1]), int(linesp[11]), prevSum/16)
				pp = [float(linesp[1]), cmdstr]
				grp1Sequence.append(pp)
				totcnt += 1
		elif (linesp[7] == "BOT_TEMP"):
			prevCount += 1
			prevSum += int(linesp[11])
			if DEBUG2:
				print ("%2d dbg %7.3f: BOT_TEMP     = %8d -- %6d %8d %7d" % \
						(prevCount, float(linesp[1]), int(linesp[11]), int(linesp[2]), prevSum,prevSum/prevCount))
			if prevCount == 16:
				cmdstr = "read %7.3f: Bottom temp = %7d (%7d)" % (float(linesp[1]), int(linesp[11]), prevSum/16)
				pp = [float(linesp[1]), cmdstr]
				grp1Sequence.append(pp)
				totcnt += 1
		elif (linesp[7] == "TOP_CUR"):
			prevCount += 1
			prevSum += int(linesp[11])
			if prevCount == 1:
				firstCurr = int(linesp[11])
			if DEBUG2:
				print ("%2d dbg %7.3f: TOP_CUR      = %8d -- %6d" % (prevCount, float(linesp[1]), int(linesp[11]), int(linesp[2])))
			if prevCount == 16:
				cmdstr = "read %7.3f: Top curr    = %7d, %6d, %7d" % (float(linesp[1]), int(linesp[11]), prevSum/16, firstCurr)
				pp = [float(linesp[1]), cmdstr]
				grp1Sequence.append(pp)
				totcnt += 1
		elif (linesp[7] == "BOT_CUR"):
			prevCount += 1
			prevSum += int(linesp[11])
			if prevCount == 1:
				firstCurr = int(linesp[11])
			if DEBUG2:
				print ("%2d dbg %7.3f: BOT_CUR      = %8d -- %6d" % (prevCount, float(linesp[1]), int(linesp[11]), int(linesp[2])))
			if prevCount == 16:
				cmdstr = "read %7.3f: Bottom curr = %7d, %6d, %7d" % (float(linesp[1]), int(linesp[11]), prevSum/16, firstCurr)
				pp = [float(linesp[1]), cmdstr]
				grp1Sequence.append(pp)
				totcnt += 1

		elif (linesp[3] == "Write") and (linesp[4] == "Reg") :
			prevCount = 0
			prevSum = 0


sizeGrp1 = len(grp1Sequence)
#print ("%d Grp1 entries." % (sizeGrp1))

#
# Read Msg file
#
#print ("Reading MSG file, ", end='')

numlines = 0
numTxLines = 0
# skip first row, it is header
line = fileMsg.readline()
numlines += 1

while 1:
	line = fileMsg.readline()
	if len(line) <= 0:
		break
	if line[0:7]  == "Summary":
		break

while 1:
	line = fileMsg.readline()
	if len(line) <= 0:
		break
	numlines += 1
	numTxLines += 1

	if len(line) <= 3:
		continue

	linej = " ".join(line.split())
	linesp = linej.split()
	length = len(linesp)

	if DEBUG1:
		print (length, linesp)

	if (length > 3):
		if (linesp[2][1:-1] == "HS"):
			pp = [float(linesp[1][:-1]), line[:-1]]
			msgSequence.append(pp)
		elif (linesp[2][1:-1] == "HF"):
			pp = [float(linesp[1][:-1]), line[:-1]]
			msgSequence.append(pp)
		elif (linesp[2][1:-1] == "HR"):
			pp = [float(linesp[1][:-1]), line[:-1]]
			msgSequence.append(pp)
		elif (linesp[2] == "[H"):
			pp = [float(linesp[1][:-1]), line[:-1]]
			msgSequence.append(pp)
		elif (linesp[2] == "[T"):
			pp = [float(linesp[1][:-1]), line[:-1]]
			msgSequence.append(pp)

sizeMsg = len(msgSequence)

allSequence = []
allSequence.extend(grp1Sequence)
allSequence.extend(msgSequence)
sortedSequence = sorted(allSequence, key = lambda ent: ent[0])   # sort by timestamp

#
# Print summary
#
for i in range(len(sortedSequence)):
	print ("%s" % sortedSequence[i][1])
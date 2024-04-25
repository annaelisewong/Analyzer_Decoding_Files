#
# Ris_File_Dump.py
#
# Dump contents of RIS file in easier to read format.
#

import os
import string
import sys
import getopt
import time

SHOW_MOTOR_SUMMARY = 0
SHOW_CUV_SUMMARY   = 0


d_motorRpmCommand = {32768:"NO_CHANGE", 50000:"STOP_MOTOR", 50001:"STOP_MOTOR", \
					50001:"LOW_SPEED", 	50002:"HIGH_SPEED", 50003:"SPEED_CHECK", \
					65535:"ROTOR_DONE"}

d_cuvetteCommand = {128:"FULL_ROTOR_SCAN", 129:"TEMPERATURE", 130:"WAIT_MSG_C", \
					131:"SEND_MSG_A", 132:"SEND_MSG_M", 133:"WAIT_MSG_A", \
					134:"CUV_DELAY", 135:"MOTOR_TEST_START", 252:"ADC_OFFSET_BIAS", \
					255:"NO_CUV_COMMAND"}

d_sampleType = {128:"BEAD_CHK_1", 129:"BEAD_CHK_2", 130:"DISTRIBUTION_CHK", 131:"PRE_SAMPLE", \
				132:"POST_SAMPLE", 133:"PASS_DONE", 134:"ANALYSIS_DONE", 135:"MFG_MOTOR_TEST", \
				136:"MIX_DONE", 137:"CANCEL_DONE", 138:"TEMPERATURE_TEST_DONE", 139:"CUV_DELAY_TEST_DONE", \
				140:"CUV_DELAY_SAMPLE", 141:"NDXT_SAMPLE", 142:"NDXT_TEST_DONE", 143:"MOTOR_TEST_DONE", \
				252:"NO_FLASH", 253:"OPTICAL_DACS", 254:"BLACK_OFFSETS", 255:"NO_SAMPLE_DATA"}

"""
BEAD_CHK_1		Full rotor scan sampleType / engine message A type
PASS_DONE		Engine message A, non-sample specific sampleType
MFG_MOTOR_TEST	Manufacturing test related
MIX_DONE		Engine message A, non sample specific sampleType

Engine message A, non sample specific sampleType
Manufacturing test related
Manufacturing test related
Manufacturing test related
Manufacturing test related
Manufacturing test related
Manufacturing test related
No flash sampleType
Optical DAC message A type
Offset A/D readings message A type
no readings to console (e.g. typically for cuvette 1
"""

# little endian
def get16i(d, i):
	if d[i+1] & 0x80:
		val = (d[i+1] * 256) + d[i]
		val ^= 0xffff
		val += 1
		val &= 0xffff
		return -1 * val
	else:
		return (d[i+1] * 256) + d[i]

# little endian
def get16u(d, i):
	return (d[i+1] * 256) + d[i]
	
# little endian
def get32i(d, i):
	if d[i+3] & 0x80:
		val = (d[i+3] * 256 * 256 * 256) + (d[i+2] * 256 * 256) + (d[i+1] * 256) +d[i+0]
		val ^= 0xffffffff
		val += 1
		val &= 0xffffffff
		return -1 * val
	else:
		return (d[i+3] * 256 * 256 * 256) + (d[i+2] * 256 * 256) + (d[i+1] * 256) +d[i+0]

# little endian
def get32u(d, i):
	return (d[i+3] * 256 * 256 * 256) + (d[i+2] * 256 * 256) + (d[i+1] * 256) +d[i+0]

def motor_rpm_to_string(m):
	if m <= 10000:
		str = "%6d RPM" % (m)
	else:
		str = d_motorRpmCommand.get(m)
	return str

def direction_to_string(dir):
	if dir == 0:
		str = "Forward"
	elif dir == 1:
		str = "Reverse"
	else:
		str = "UNKNOWN"
	return str

def gain_to_string(g):
	if g == 0:
		str = "PROFILE"
	elif g == 1:
		str = "SAMPLE"
	else:
		str = "UNKNOWN"
	return str

def accel_to_string(a):
	if a == 32768:
		str = "NO_CHANGE"
	else:
		str = "Value = %d" % (a)
	return str

def cuv_com_to_string(cc):		
	if cc < 30:
		str = "CUV %2.2d" % (cc)
	else:
		str = d_cuvetteCommand.get(cc)
	return str

def sample_to_string(st):
	if st < 10:
		str = "OPTICAL_BLANK_%1d" % (st)
	elif st < 20:
		str = "SAMPLE_BLANK_%1d" % (st-10)
	elif st >= 98 and st <= 127:
		str = "CUV_%2.2d_ABS" % (st - 98)
	elif st >= 128:
		str = d_sampleType.get(st)
	else:
		str = "<Analyte @ %d>" % (st)
	return str


startnow = time.localtime(time.time())
tstr = time.strftime("%Y-%m-%d %H:%M:%S", startnow)
print ("Starting ... %s" % (tstr))

# cmd line defaults
inFileName = ''
outFileName = ''
useRaw = 0

#    
# parse command line options
#
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:o:r")
except getopt.error:
    usage()
    sys.exit(2)

# process options
for o, a in opts:
    if o == "-i":
        inFileName = a
    elif o == "-o":
        outFileName = a
    elif o == "-r":
        useRaw = 1

if inFileName == '':
    usage()
    sys.exit(1)

base = os.path.basename(inFileName)
basefile = os.path.splitext(base)[0]
baseext = os.path.splitext(base)[1]
print ("%s %s %s" % (base, basefile, baseext))

lastmodified= os.stat("%s"%(inFileName)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)
print( "Processing file  ... %s" % (ftstr))

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]

if outFileName == '':
	fileOut = sys.stdout
else:
	try:
		fileOut = open(outFileName, "wt")
	except:
		print ("Cannot open \'%s\')" % (outFileName))
		sys.exit(1)

with open(inFileName, "rb") as f:
    read_data = f.read()

size = len(read_data)

print ("Input \"%s\" size %d" % (os.path.basename(inFileName), size))
print ("Output \"%s\"" % (os.path.basename(outFileName)))

allSummary = []
motSummary = []
cuvSummary = []

fileOut.write ("RIS file \"%s\" size %d bytes\n" % (os.path.basename(inFileName), size))

if useRaw:
	for i in range(size):
		byte = read_data[i]
		fileOut.write ("%4.4d 0x%2.2x %3d\n" % (i, byte, byte))
	sys.exit(0)

# else not raw, display parsed
blockSize = 12
numBlocks = float(size - 8) / 12.0
fileOut.write ("%.1f blocks\n\n" % (numBlocks))

idx = 0

ver = get32u(read_data, idx)
fileOut.write ("%-8s 0x%8.8x\n" % ("Version", ver))
idx += 4

for block in range(int(numBlocks)):
	fileOut.write ("Block %d\n" % (block))

	#
	motorRpmCommand = get16u(read_data, idx)
	idx += 2
	str = motor_rpm_to_string(motorRpmCommand)
	fileOut.write ("%-18s %6d %s\n" % ("motorRpmCommand", motorRpmCommand, str))

	#
	motorTime = get16u(read_data, idx)
	idx += 2
	fileOut.write ("%-18s %6d %7.3f sec\n" % ("motorTime", motorTime, float(motorTime) * 0.02))

	#
	motorDirection = read_data[idx]
	idx += 1
	str = direction_to_string(motorDirection)
	fileOut.write ("%-18s %6d %s\n" % ("motorDirection", motorDirection, str))

	#
	motorGain = read_data[idx]
	idx += 1
	str = gain_to_string(motorGain)
	fileOut.write ("%-18s %6d %s\n" % ("motorGain", motorGain, str))

	#
	motorAcceleration = get16u(read_data, idx)
	idx += 2
	str = accel_to_string(motorAcceleration)
	fileOut.write ("%-18s %6d %s\n" % ("motorAcceleration", motorAcceleration, str))

	#
	cuvetteCommand = read_data[idx]
	idx += 1
	str = cuv_com_to_string(cuvetteCommand)
	fileOut.write ("%-18s %6d %s\n" % ("cuvetteCommand", cuvetteCommand, str))

	#
	sampleType = read_data[idx]
	idx += 1
	str = sample_to_string(sampleType)
	fileOut.write ("%-18s %6d %s\n" % ("sampleType", sampleType, str))

	#
	flashesPerCuvette = read_data[idx]
	idx += 1
	fileOut.write ("%-18s %6d\n" % ("flashesPerCuvette", flashesPerCuvette))

	#
	loopControl = read_data[idx]
	idx += 1
	if loopControl == 1:
		str = "Process this record and move on"
	elif loopControl == 0:
		str = "Last record of loop"
	else:
		str = "Process %d passes" % (loopControl)
	fileOut.write ("%-18s %6d %s\n" % ("loopControl", loopControl, str))

	fileOut.write ("\n")

	#
	allSummary.append([block, motorRpmCommand, motorTime, motorDirection, motorAcceleration, loopControl, motorGain])
	motSummary.append([block, motorRpmCommand, motorTime, motorDirection, motorAcceleration, loopControl, motorGain])
	cuvSummary.append([block, cuvetteCommand, flashesPerCuvette, sampleType, loopControl, motorGain])

crc = get32u(read_data, size-4)
idx += 4

fileOut.write ("%-4s 0x%8.8x\n" % ("CRC", crc))
fileOut.write ("last idx %d\n" % (idx))

if SHOW_MOTOR_SUMMARY:
	fileOut.write ("\n")
	fileOut.write ("Motor Summary %d\n" % (len(motSummary)))
	fileOut.write ("    Blk Rpm   RpmCommand         Time    Dir          Acceleration     Lp  Gain    CuvCommand           SampleType            \n")
	fileOut.write ("    --- ----- ------------- ------- ------------ --------------------- --- ------- -------------------- ----------------------\n")

	for i in range(len(motSummary)):
		fileOut.write (    "%3d %3d %5d \'%11s\' %7.3f %2d \'%-7s\' %5d \'%-13s\' %3d %-7s \'%-18s\' \'%-20s\'\n" % \
			(i, motSummary[i][0], \
			motSummary[i][1], motor_rpm_to_string(motSummary[i][1]), \
			motSummary[i][2] * 0.020, \
			motSummary[i][3], direction_to_string(motSummary[i][3]), \
			motSummary[i][4], accel_to_string(motSummary[i][4]), \
			motSummary[i][5], \
			gain_to_string(motSummary[i][6]), \
			cuv_com_to_string(cuvSummary[i][1]), sample_to_string(cuvSummary[i][3])))
	
if SHOW_CUV_SUMMARY:
	fileOut.write ("\n")
	fileOut.write ("Cuvette Summary %d\n" % (len(cuvSummary)))
	fileOut.write ("    Blk Cuv CuvCommand          Cnt Sam SampleType             Lp Gain\n")
	fileOut.write ("    --- --- -------------------- -- --- ---------------------- -- -------\n")

	for i in range(len(cuvSummary)):
		fileOut.write (    "%3d %3d %3d \'%-18s\' %2d %3d \'%-20s\' %2d %-7s\n" % \
			(i, cuvSummary[i][0], \
			cuvSummary[i][1], cuv_com_to_string(cuvSummary[i][1]), \
			cuvSummary[i][2], \
			cuvSummary[i][3], sample_to_string(cuvSummary[i][3]), \
			cuvSummary[i][4], \
			gain_to_string(cuvSummary[i][5])))

fileOut.write ("\n")
fileOut.write ("Summary Full %d\n" % (len(allSummary)))
fileOut.write ("    Blk Rpm   RpmCommand    Time    Dir          Gain    Acceleration          CuvCommand           SampleType             Flash Loop \n")
fileOut.write ("    --- ----- ------------- ------- ------------ ------- --------------------- -------------------- ---------------------- ----- -=--\n")

for i in range(len(allSummary)):
	fileOut.write (    "%3d %3d %5d \'%11s\' %7.3f %2d \'%-7s\' %-7s %5d \'%-13s\' \'%-18s\' \'%-20s\'    %2d  %3d\n" % \
		(i, motSummary[i][0],										# block number		\
		motSummary[i][1], motor_rpm_to_string(motSummary[i][1]),	# motorRpmCommand	\
		motSummary[i][2] * 0.020,									# motorTime			\
		motSummary[i][3], direction_to_string(motSummary[i][3]),	# motorDirection	\
		gain_to_string(motSummary[i][6]),							# motorGain			\
		motSummary[i][4], accel_to_string(motSummary[i][4]),		# motorAcceleration	\
		cuv_com_to_string(cuvSummary[i][1]),						# cuvetteCommand	\
		sample_to_string(cuvSummary[i][3]),							# sampleType		\
		cuvSummary[i][2],											# flashesPerCuvette	\
		motSummary[i][5]))											# loop

"""
motorRpmCommand UINT_16 Motor RPM or RIS command type
motorTime UINT_16 Time for motor at RPM, Direction, Gain & Acceleration in 20 ms increments
motorDirection UINT_8 Motor forward or reverse direction
motorGain UINT_8 Motor gain set for motor profile or for cuvette photometric sampling
motorAcceleration UINT_16 Motor acceleration
cuvetteCommand UINT_8 Sampling command or other command type during sampling
sampleType UINT_8 Cuvette number or special sample command / command parameter
flashesPerCuvette UINT_8 Number of sampling flashes per cuvette at cuvette
loopControl UINT_8 parameter set greater than 1 for first record in loop, 0 for last record in loop
"""

"""
OPTICAL_BLANK_0
0
sampleType indices for a cuvette
OPTICAL_BLANK_1
1
(indices to raw readings & data reduction method for cuvette)
OPTICAL_BLANK_2
2
OPTICAL_BLANK_3
3
OPTICAL_BLANK_4
4
OPTICAL_BLANK_5
5
OPTICAL_BLANK_6
6
OPTICAL_BLANK_7
7
OPTICAL_BLANK_8
8
OPTICAL_BLANK_9
9
SAMPLE_BLANK_0
10
SAMPLE_BLANK_1
11
SAMPLE_BLANK_2
12
SAMPLE_BLANK_3
13
SAMPLE_BLANK_4
14
SAMPLE_BLANK_5
15
SAMPLE_BLANK_6
16
SAMPLE_BLANK_7
17
SAMPLE_BLANK_8
18
SAMPLE_BLANK_9
19
SYS_CUV_6
20
SYS_CUV_11
21
SYS_CUV_28
22
RQC
23
IQC_A
24
IQC_B
25
ALB
26
ALP
27
ALT_CUV_1
28
AMY
29
AST_CUV_1
30
BA_CUV_1
31
BA_CUV_2
32
BUN_CUV_1
33
CA
34
CHOL_BLANK
35
CHOL
36
CK_CUV_1
37
CL_CUV_1
38
CL_CUV_2
39
CRE_BLANK_1
40
CRE_CUV_1
41
DBIL_BLANK
42
DBIL
43
GGT
44
GLU
45
HDL_CUV_1
46
HDL_CUV_2
47
K
48
LDH
49
MG
50
NA_CUV_1
51
NA_CUV_2
52
PHOS
53
T4_OR1
54
T4_OR2
55
T4_G6P1
56
T4_L1
57
TBIL_BLANK
58
TBIL
59
TCO2
60
TP_BLANK
61
TP
62
TRIG_BLANK
63
TRIG
64
UA
65
ALT_CUV_2
66
BUN_CUV_2
67
CRE_BLANK_2
68
CRE_CUV_2
69
CHW
70
(Canine Heart Worm)
CRP_1
71
CRP_2
72
CHW_OPT
73
LAC
74
HB
75
Not Used on Any Rotor/Disc
AST_CUV_2
76
CK_CUV_2
77
PHB
78
(end of indices; add new sampleType up to 98 here)
CUV_00_ABS
98
(sampleType 98 through 127 reserved for Rotor 1 testing)
CUV_01_ABS
99
CUV_02_ABS
100
CUV_03_ABS
101
CUV_04_ABS
102
CUV_05_ABS
103
CUV_06_ABS
104
CUV_07_ABS
105
CUV_08_ABS
106
CUV_09_ABS
107
CUV_10_ABS
108
CUV_11_ABS
109
CUV_12_ABS
110
CUV_13_ABS
111
CUV_14_ABS
112
CUV_15_ABS
113
CUV_16_ABS
114
CUV_17_ABS
115
CUV_18_ABS
116
CUV_19_ABS
117
CUV_20_ABS
118
CUV_21_ABS
119
CUV_22_ABS
120
CUV_23_ABS
121
CUV_24_ABS
122
CUV_25_ABS
123
CUV_26_ABS
124
CUV_27_ABS
125
CUV_28_ABS
126
CUV_29_ABS
127
BEAD_CHK_1
128
full rotor scan sampleType / engine message A type
BEAD_CHK_2
129
DISTRIBUTION_CHK
130
PRE_SAMPLE
131
POST_SAMPLE
132
PASS_DONE
133
Engine message A, non sample specific sampleType
ANALYSIS_DONE
134
MFG_MOTOR_TEST
135
Manufacturing test related
MIX_DONE
136
Engine message A, non sample specific sampleType
CANCEL_DONE
137
Engine message A, non sample specific sampleType
TEMPERATURE_TEST_DONE
138
Manufacturing test related
CUV_DELAY_TEST_DONE
139
Manufacturing test related
CUV_DELAY_SAMPLE
140
Manufacturing test related
NDXT_SAMPLE
141
Manufacturing test related
NDXT_TEST_DONE
142
Manufacturing test related
MOTOR_TEST_DONE
143
Manufacturing test related
NO_FLASH
252
No flash sampleType
OPTICAL_DACS
253
Optical DAC message A type
BLACK_OFFSETS
254
Offset A/D readings message A type
NO_SAMPLE_DATA
255
no readings to console (e.g. typically for cuvette 1
"""

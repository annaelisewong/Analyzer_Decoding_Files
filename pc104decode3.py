#
# pc104decode3.py
#
#

import string
import sys
import getopt
import time
import os
import math
from ctypes import *

IDX_TIME = 0

DEBUG1 = 0
DEBUG2 = 0
DEBUG3 = 0

def usage():
	print( "pc104decode3.py -r <rotor_name> [-b]")
	print(" -r <rotor name> Full prefix name of rotor")
	print(" -b Flag to indicate barcode dump file should be created")
	sys.exit(0)

HC_WAITSTX = 0
HC_STX = 3
HC_PLD = 4

HC_ERROR = 7

CH_STX  = 0x02
CH_EOT  = 0x04
CH_ENQ  = 0x05
CH_ACK  = 0x06
CH_ESC  = 0x1b
CH_NACK = 0x15
CH_ETX  = 0x03
CH_CR   = 0x0d
CH_LF   = 0x0a

DIR_IN  = 0
DIR_OUT = 1

d_sampleTypes = { \
128: "BEAD_CHK_1",				\
129: "BEAD_CHK_2",				\
130: "DISTRIBUTION_CHK",		\
131: "PRE_SAMPLE",				\
132: "POST_SAMPLE",				\
133: "PASS_DONE",				\
134: "ANALYSIS_DONE",			\
136: "MIX_DONE",				\
137: "CANCEL_DONE",				\
138: "TEMPERATURE_TEST_DONE",	\
139: "CUV_DELAY_TEST_DONE",		\
140: "CUV_DELAY_SAMPLE",		\
141: "NDXT_SAMPLE",				\
142: "NDXT_TEST_DONE",			\
143: "MOTOR_TEST_DONE",			\
252: "NO_FLASH",				\
253: "OPTICAL_DACS",			\
254: "BLACK_OFFSETS"			\
}

d_fanspeeds = {0:"Low", 1:"Hi"}

# Little Endian Access
#   int16, uint16, int32, uint32
def get16i(d, i):
	if d[i+1] & 0x80:
		val = (d[i+1] * 256) +d[i]
		val ^= 0xffff
		val += 1
		val &= 0xffff
		return -1 * val
	else:
		return (d[i+1] * 256) +d[i]

def get16u(d, i):
	return (d[i+1] * 256) + d[i]
	
def get32i(d, i):
	if d[i+3] & 0x80:
		val = (d[i+3] * 256 * 256 * 256) + (d[i+2] * 256 * 256) + (d[i+1] * 256) +d[i+0]
		val ^= 0xffffffff
		val += 1
		val &= 0xffffffff
		return -1 * val
	else:
		return (d[i+3] * 256 * 256 * 256) + (d[i+2] * 256 * 256) + (d[i+1] * 256) +d[i+0]

def get32u(d, i):
	return (d[i+3] * 256 * 256 * 256) + (d[i+2] * 256 * 256) + (d[i+1] * 256) +d[i+0]

# dir 1 = out, 0 = in

# convert from hex to a Python float
def convert_to_float(h):
	cp = pointer(c_int(h))           # make this into a c integer
	fp = cast(cp, POINTER(c_float))  # cast the int pointer to a float pointer
	return fp.contents.value  

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

def CalcTemperatures(Itr, Ita, Itt, Itb, Ict, Icb):
	"""
	uint32 engineTime
	uint16 rotorTemp
	uint16 ambientTemp
	uint16 topTemp
	uint16 bottomTemp
	uint16 topCurr
	uint16 bottomCurr
	"""
	Tr = (float(Itr) * ROTOR_TEMPERATURE_CONVERT_MULT) + FACTORY_airTemperatureOffset
	Ta = (float(Ita) * AMBIENT_TEMPERATURE_CONVERT_MULT) - AMBIENT_TEMPERATURE_CONVERT_OFFSET
	Tt = CalcPlateTemp(Itt)
	Tb = CalcPlateTemp(Itb)
	Ct = CalcPlateVoltage(Ict)
	Cb = CalcPlateVoltage(Icb)

	return (Tr, Ta, Tt, Tb, Ct, Cb)
#
#
class parse_host:
	def __init__(self):
		self.state = HC_WAITSTX
		self.charCount = 0		# count of bytes being processed
		self.payloadIdx = 0		# index into payload
		self.payloadMaxIdx = 0	# from packet
		self.gotEsc = 0
		self.gotEtx = 0
		self.inPayload = 0
		self.headerLen = 0
		self.pendDecode = 0
		self.EnqCount = 0
		self.StxCount = 0
		self.EotCount = 0
		self.EnqDir = 0
		self.payload = []
		self.firstFrame = ""
		self.stxTime = 0.0

		self.CmdSummary = []
		self.countToSBC = 0
		self.countFromSBC = 0

	#
	#
	def decode_payload(self, p, d):
		length = len(p)
		dir = d
		
		if DEBUG3:
			print ("PKT:", d, length, p)

		s1 = chr(p[1])
		s2 = chr(p[2])
		commandId = s1
		if p[2] != 0x1b:
			commandId += s2

		#
		# ***  Incoming to FPGA  ***
		#
		if dir == DIR_IN:
			self.countFromSBC += 1
	
			if s1 == "D" and s2 == "C":
				c = "C<-S %7.3f: [%-2s] Door Close" % (self.stxTime, commandId)
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			elif s1 == "D" and s2 == "O":
				c = "C<-S %7.3f: [%-2s] Door Open" % (self.stxTime, commandId)
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			elif s1 == "H":
				if s2 == "R":
					xxx = "Request Heater data"
					c = "C<-S %7.3f: [%-2s] %s //{%d %d %d %d %f}//" % \
						(self.stxTime, commandId, xxx, get16u(p,6), get16u(p,8), p[10], p[11], convert_to_float(get32i(p,12)))
				elif s2 == "S":
					xxx = "Send Heater DAC setting"
					c = "C<-S %7.3f: [%-2s] %s {%d %d %d %d %f}" % \
						(self.stxTime, commandId, xxx, get16u(p,6), get16u(p,8), p[10], p[11], convert_to_float(get32i(p,12)))
				elif s2 == "F":
					xxx = "Set Fan Speed %1d (%s)" % (p[10], d_fanspeeds[p[10]])
					c = "C<-S %7.3f: [%-2s] %s {%d %d %d %d %d}" % \
						(self.stxTime, commandId, xxx, get16u(p,6), get16u(p,8), p[10], p[11], get32u(p,12))
				else:
					xxx = "UNKNOWN!"
				"""
				msg.data.engineMsg.message[0]  = 'H';
				message[1]  = cmd;    // cmd = F, set fan idle speed
				message[2]  = ESC;
				message[3]  = 10;     // LSB of binary count.
				message[4]  = 0;      // MSB of binary count.
				message[5]  = 0;      // Top DAC, two bytes for 10 bit  DAC
				message[6]  = 0;
				message[7]  = 0;      // Bootom DAC, two bytes for 10 bit DAC
				message[8]  = 0;
				message[9]  = dac;    // Fan idle speed, low = 0, high = 1 
				message[10] = 0;      // Fan Speed Dac 
				message[11] = 0;      // air temperature offset 4 bytes
				message[12] = 0;
				message[13] = 0;
				message[14] = 0;
				length = 15;
				"""

				#c = "C<-S %7.3f: [%-2s] %s {%d %d %d %d %f}" % \
				#		(self.stxTime, commandId, xxx, get16u(p,6), get16u(p,8), p[10], p[11], convert_to_float(get32i(p,12)))

				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				topDac  5  2
				botDac, 7  2
				message[9] = heaterControl_m.fanControlDac;       // idle fan speed
				message[10] = heaterControl_m.fanControlDac;      // fan speed set 
				message[11],  &heaterControl_m.airOffset, 4); // air offset				
				"""

			elif s1 == "A" :
				if s2 == 'C':
					xxx = "Cancel"
				elif s2 == 'S':
					xxx = "Mix Done"
				elif s2 == 'M':
					xxx = "Run RIS"
				else:
					xxx = "Unknown!"
				c = "C<-S %7.3f: [%-2s] Begin Analysis {%s}" % (self.stxTime, commandId, xxx)
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			elif s1 == "B" :
				c = "C<-S %7.3f: [%-2s] Scan Barcode {%4.4x (bcDac) %3d %3d (cmDac) %3d %3d}" % \
						(self.stxTime, commandId, get16u(p,4), p[6], p[7], p[8], p[9])
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				msg.data.engineMsg.message[0] = 'B';
				msg.data.engineMsg.message[1] = command;
				msg.data.engineMsg.message[2] = ESC;
				msg.data.engineMsg.message[3] = 4;		// LSB of binary count.
				msg.data.engineMsg.message[4] = 0;		// MSB of binary count.
				msg.data.engineMsg.message[5] = calibrationData->barcodeDacs[0];
				msg.data.engineMsg.message[6] = calibrationData->barcodeDacs[1];
				msg.data.engineMsg.message[7] = calibrationData->cuvetteMarkDacs[0];
				msg.data.engineMsg.message[8] = calibrationData->cuvetteMarkDacs[1];
				msg.data.engineMsg.length = 9;
				"""
			elif s1 == "C" :
				c = "C<-S %7.3f: [%-2s] Send Calibration factors (wavelengthDacTrims) {" % (self.stxTime, commandId)
				for i in range (10):
					c += " %3d" % (p[5+i])
				c += "}"
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			elif s1 == "P" :
				if risfilename != "":
					strout = "{%d saved}" % (length-10)
					for x in range(5, length-5):
						fileRis.write(int(p[x]).to_bytes(1, byteorder='little'))
					fileRis.close()
				else:
					strout = "{not saved}"
				c = "C<-S %7.3f: [%-2s] Send RIS File %s" % (self.stxTime, commandId, strout)
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			elif s1 == "F" :
				c = "C<-S %7.3f: [%-2s] Factory Setting {(gcd) %d (cd)" % \
						(self.stxTime, commandId, get16u(p,5))
				for i in range (30):
					 c += " %d" % (p[7+i])
				c += "}"
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				msg.data.engineMsg.message[0] = 'F';
				msg.data.engineMsg.message[1] = ESC;
				msg.data.engineMsg.message[2] = 32;     // LSB of binary count.
				msg.data.engineMsg.message[3] = 0;      // MSB of binary count.
				msg.data.engineMsg.message[4] = factoryData->globalCuvetteDelay & 0xFF;
				msg.data.engineMsg.message[5] = factoryData->globalCuvetteDelay >> 8;
				for (i = 0; i < 30; i++) {
					msg.data.engineMsg.message[i+6] = factoryData->cuvetteDelays[i];
				}
				msg.data.engineMsg.length = 36;
				"""

			else:
				fileOut.write ("C<-S UNKNOWN %7.3f %s %s <%d>\n" % (self.stxTime, s1, s2, length))

		#
		# ***  Outgoing from FPGA  ***
		#

		elif dir == DIR_OUT:
			self.countToSBC += 1

			if s1 == "V" :
				vss = ""
				vsf = ""
				for i in range(32):
					if p[i+5] > 0:
						vss += chr(p[i+5])
					else:
						break
						
				for j in range(32):
					if p[j+21] > 0:
						vsf += chr(p[j+21])
					else:
						break

				c = "C->S %7.3f: [%-2s] Version Information SW %s FPGA %s" % (self.stxTime, commandId, vss, vsf)
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				engSoftwareVersion [4]);
                engFpgaVersion		[20]);	
               	"""

			elif s1 == "?" :
				c = "C->S %7.3f: [%-2s] Debug Msg \"%s\"" % (self.stxTime, commandId, ''.join(chr(e) for e in p[5:-5]))
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			elif s1 == "R" :
				sampleType = p[11-1]
				if (sampleType >= 0) and (sampleType < 10):
					xx = "\'OPTICAL_BLANK_%1d" % (sampleType)
				elif (sampleType >= 10) and (sampleType < 20):
					xx = "\'SAMPLE_BLANK_%1d" % (sampleType - 10)
				elif (sampleType >= 98) and (sampleType < 128):
					xx = "\'CUV_%2.2d_ABS" % (sampleType - 98)
				elif (sampleType >= 128):
					xx = "\'%s\'" % (d_sampleTypes.get(sampleType))
				else:
					xx = "\'%2.2d\'" % (sampleType)

				c = "C->S %7.3f: [%-2s] Photometric Data {%10.10u %2u %2u %-20s" % \
					(self.stxTime,  commandId, get32u(p,6-1), p[10-1], p[12-1], xx)
				for i in range (10):
					c += " %5d" % (get16u(p,14-1+2*i))
				c += "}"
				fileOut.write ("%s\n" % (c))
				"""
				"Timestamp", get32u(p,6-1)))
				"Cuv", p[10-1]))
				"flashNumber", p[12-1]))
				"sampleType", p[11-1], d_sampleTypes.get(p[11-1])))
				10 data shorts
				"""
				self.CmdSummary.append(c)

			elif s1 == "T" :
				c = "C->S %7.3f: [%-2s] Heater Temperature Readings {%10.10u %5u %5u %5u %5u %5u %5u}" \
						% (self.stxTime, commandId, get32u(p,6-1), \
								get16u(p,10-1), get16u(p,12-1), get16u(p,14-1), \
								get16u(p,16-1), get16u(p,18-1), get16u(p,20-1))
				Tcalcs = CalcTemperatures(get16u(p,10-1), get16u(p,12-1), get16u(p,14-1), \
									      get16u(p,16-1), get16u(p,18-1), get16u(p,20-1))
				c += " { %5.2f %5.2f %5.2f %5.2f %8.6f %8.6f }" % \
							(Tcalcs[0], Tcalcs[1], Tcalcs[2], Tcalcs[3], Tcalcs[4], Tcalcs[5])
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				memcpy( &t->engineTime, &rxFrame[6], 4 );
				memcpy( &t->rotorTemperature, &rxFrame[10], 2 );
				memcpy( &t->ambientTemperature, &rxFrame[12], 2 );
				memcpy( &t->topPlateTemperature, &rxFrame[14], 2 );
				memcpy( &t->bottomPlateTemperature, &rxFrame[16], 2 );
				memcpy( &t->topPlateCurrent, &rxFrame[18], 2 );
				memcpy( &t->bottomPlateCurrent, &rxFrame[20], 2 );
				"""
			elif s1 == "H" :
				strout = ""
				c = "C->S %7.3f: [%-2s] Heater Temperature Data {%10.10u %5u %5u %5u %5u %5u %5u}" \
						% (self.stxTime, commandId, get32u(p,6-1), \
								get16u(p,10-1), get16u(p,12-1), get16u(p,14-1), \
								get16u(p,16-1), get16u(p,18-1), get16u(p,20-1))
				Tcalcs = CalcTemperatures(get16u(p,10-1), get16u(p,12-1), get16u(p,14-1), \
									      get16u(p,16-1), get16u(p,18-1), get16u(p,20-1))
				c += " { %5.2f %5.2f %5.2f %5.2f %8.6f %8.6f }" % \
							(Tcalcs[0], Tcalcs[1], Tcalcs[2], Tcalcs[3], Tcalcs[4], Tcalcs[5])
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				uint32 engineTime
				uint16 rotorTemp
				uint16 ambientTemp
				uint16 topTemp
				uint16 bottomTemp
				uint16 topCurr
				uint16 bottomCurr				
				"""

			elif s1 == "B" :
				if barfilename != "":
					strout = "{%d saved}" % (length-10)
					for x in range(5, length-5):
						fileBar.write(int(p[x]).to_bytes(1, byteorder='little'))
					fileBar.close()
				else:
					strout = "{not saved}"
				c = "C->S %7.3f: [%-2s] Barcode Data %s" % (self.stxTime, commandId, strout)
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			elif s1 == "A" :
				xx = d_sampleTypes.get(p[10-1])
				if xx == None:
					xx = str(p[10-1])

				c = "C->S %7.3f: [%-2s] Analysis Status {%10.10u %3u \'%s\'}" % \
					(self.stxTime,  commandId, get32u(p,6-1), p[11-1], xx)

				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				"Timestamp", get32u(p,6-1)))
				"Parameter", p[11-1]))
				"sampleType", p[10-1], d_sampleTypes.get(p[10-1])))
				"""

			elif s1 == "D" :
				strout = ""
				status = p[8+1]
				if status & 0x80:
					strout += "\"Jammed\" "
				if status & 0x20:
					strout += "\"Open\" "
				if status & 0x10:
					strout += "\"Closed\" "
				if status & 0x40:
					strout += "\"Rotor present\" "
				if status & 0x0c:
					strout += "\"Unexpected\" "
				if status == 0x00:
					strout += "\"Unknown!\" "

				c = "C->S %7.3f: [%-2s] Drawer Status 0x%2.2x %s" % (self.stxTime, commandId, status, strout)
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				if ( status & 0x80 )		// Drawer jammed
				else if ( status & 0x10 )	// Drawer closed
				if ( status & 0x40 )	// Rotor present
				else if ( status & 0x20 )	// Door open
				"""
			elif s1 == "X" :
				c = "C->S %7.3f: [%-2s] ADC reference offset {%10.10u %4u}" % \
					(self.stxTime,  commandId, get32u(p,6-1), get16u(p, 10-1))
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)
				"""
				time 6
				reference 10
				"""

			elif s1 == "Z" :
				# Exception two Nulls
				c = "C->S %7.3f: [%1s ] Asynchronous Engine Reset indicated {%2.2x %2.2x}" % (self.stxTime, chr(p[1]), p[2], p[3])
				fileOut.write ("%s\n" % (c))
				self.CmdSummary.append(c)

			else:
				fileOut.write ("C->S UNKNOWN %7.3f %s %s <%d>\n" % (self.stxTime, s1, s2, length))

		else:
			fileOut.write("Dir Error\n")

	#
	#
	def update(self, time_in, char_in, dir):
		# dir in = 0, out = 1
		rs = ""

		if self.state == HC_WAITSTX:
			if char_in == CH_ACK and dir == DIR_IN:
				rs = "ACK in"

			elif char_in == CH_ENQ and dir == DIR_OUT:
				rs = "ENQ out"

			elif char_in == CH_ACK and dir == DIR_OUT:
				rs = "ACK out"

			elif char_in == CH_ENQ and dir == DIR_IN:
				rs = "ENQ in"

			elif char_in == CH_EOT and dir == DIR_OUT:
				rs = "EOT out"

			elif char_in == CH_STX and dir == DIR_OUT:
				self.state = HC_STX
				rs =  "STX out"

			elif char_in == CH_ACK and dir == DIR_IN:
				rs = "ACK in"
		
			elif char_in == CH_EOT and dir == DIR_IN:
				rs = "EOT in"

			elif char_in == CH_STX and dir == DIR_IN:
				self.state = HC_STX
				rs =  "STX in"

			elif char_in == CH_ACK and dir == DIR_OUT:
				rs = "ACK out"

			# todo NACK

			else:
				rs = "PARSE CHECK_ERROR"

		elif self.state == HC_STX:
			self.stxTime = time_in
			self.StxCount += 1 # AEW DEBUG, TODO delete later
			# print("AEW DEBUG: STX time = %f, STX count = %d" % (self.stxTime, self.StxCount))
			self.state = HC_PLD
			self.inPayload = 0
			self.payload = []
			self.gotEsc = 0
			self.gotEtx = 0
			self.charCount = 0
			self.headerLen = 0
			rs = "%s" % (chr(char_in))
			self.payload.append(char_in)
			self.charCount += 1
			self.payloadMaxIdx = -1
			self.pendDecode = 0

		elif self.state == HC_PLD:
			# todo verify dir
			
			self.payload.append(char_in)
			self.charCount += 1

			if self.gotEsc == 2:
				self.gotEsc = 3
				self.payloadMaxIdx = self.payloadMaxIdx + (256 * char_in)	# from packet
				self.headerLen = self.charCount
				rs = "LEN1"

			if self.gotEsc == 1:
				self.payloadMaxIdx = char_in	# from packet
				self.gotEsc = 2
				rs = "LEN0"
				
			if char_in == CH_ESC and self.gotEsc == 0:
				self.gotEsc = 1

			if self.gotEtx == 1:
				self.gotEtx = 2
				self.headerLen = self.charCount - 1

			if char_in == CH_ETX and self.gotEtx == 0 and self.gotEsc == 0:
				self.gotEtx = 1

			if rs[0:3] == "LEN":
				pass
			elif char_in == 0x1b:
				rs = "ESC"
			elif char_in == 0x0d:
				rs = " CR"
			elif char_in == 0x0a:
				rs = " LF"
			elif char_in == 0x03:
				rs = "ETX"
			elif (char_in > 0x1f) and (char_in < 127):
				rs = str(chr(char_in))
			else:
				rs = " %2.2x" % (char_in)

			if DEBUG2:
				print ("self.charCount %d self.headerLen %d self.payloadMaxIdx %d" % \
						(self.charCount, self.headerLen, self.payloadMaxIdx))

			if (self.headerLen > 0):
				if ((self.payloadMaxIdx == -1) and (self.charCount == (self.headerLen + 4))) or \
					((self.payloadMaxIdx != -1) and (self.charCount == (self.headerLen + self.payloadMaxIdx + 4 + 1))) :
					self.state = HC_WAITSTX
					self.pendDecode = 1

		# 
		# raw output
		fileOut.write("%11.6f %6d " % (time_in, i))
		if not dir:
			fileOut.write("C <- S ")
			fileOut.write("%2.2x " % (char_in))
		else:
			fileOut.write("C -> S ")
			fileOut.write("%2.2x " % (char_in))

		fileOut.write("%3s " % (rs))
		if self.pendDecode:
			fileOut.write("\n")
			self.decode_payload(self.payload, dir)
			self.pendDecode = 0

		return rs

	#
	#
	def feed(self, e):
		if e[2] == 'r':
			ss = parser.update(e[0], e[1], 0)
		else:
			ss = parser.update(e[0], e[1], 1)
		fileOut.write("\n")

	#####

#
#
#
argc = len(sys.argv)
if argc < 2:
    usage()
    sys.exit(0)

# cmd line defaults
# risfilename = ''
# barfilename = ''
# rxfilename = sys.argv[1]
# txfilename = sys.argv[2]

# if argc > 3:
# 	risfilename = sys.argv[3]
# 	try:
# 		fileRis = open(risfilename, 'wb')
# 	except:
# 		print( "Could not open RIS dump file %s" % (risfilename))
# 		sys.exit(1)

# if argc > 4:
# 	barfilename = sys.argv[4]
# 	try:
# 		fileBar = open(barfilename, 'wb')
# 	except:
# 		print( "Could not open Barcode dump file %s" % (barfilename))
# 		sys.exit(1)

# startnow = time.localtime(time.time())
# tstr = time.strftime("%Y-%m-%d %H:%M:%S", startnow)
# #print ("Starting ... %s" % (tstr))

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:b")
except getopt.error:
    usage()
    sys.exit(2)

# Process options
rotor_name = ""
CREATE_BC_DUMP_FILE = False

for o, a in opts:
	if o == "-r":
		rotor_name = a
	elif o == "-b":
		CREATE_BC_DUMP_FILE = True

if rotor_name == "":
	usage()

rotor_name = rotor_name.replace("Exports", "Reports")

rotor_filepath = os.path.split(rotor_name)[0]
rotor_basename = os.path.split(rotor_name)[1]

if rotor_filepath != "":
	rotor_filepath += "\\"

rxfilename = rotor_filepath + "Serial" + rotor_basename + "_Group0_rx.txt" #TODO fix this bug 
txfilename = rotor_filepath + "Serial" + rotor_basename + "_Group0_tx.txt"
risfilename = rotor_name + "_RIS.bin"
barfilename = ""

if CREATE_BC_DUMP_FILE:
	barfilename = rotor_name + "_barcode.bin"

try:
	fileRx = open(rxfilename, 'rt')
except:
	print( "Could not open input Rx file %s" % (rxfilename))
	sys.exit(1)

try:
	fileTx = open(txfilename, 'rt')
except:
	print( "Could not open input Tx file %s" % (txfilename))
	sys.exit(1)

try:
	fileRis = open(risfilename, 'wb')
except:
	print( "Could not open RIS dump file %s" % (risfilename))
	sys.exit(1)

if CREATE_BC_DUMP_FILE:
	try:
		fileBar = open(barfilename, 'wb')
	except:
		print( "Could not open Barcode dump file %s" % (barfilename))
		sys.exit(1)

"""
lastmodified= os.stat("%s"%(infilename)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)
print( "Processing file  ... %s" % (ftstr))

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]
"""

outfilename = rotor_name + "_MsgOut.txt"
try:
	fileOut = open(outfilename, "wt")
except:
	print("Could not open %s" % outfilename)
	sys.exit(1)

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


#
# Sort by time
#
sortedSequence = sorted(sequence, key = lambda ent: ent[0])   # sort by timestamp
fileOut.write ("%d %d %d\n" % (len(sequence), numRxLines, numTxLines))


#
# Decode
#


for i in range(len(sortedSequence)):
	parser.feed(sortedSequence[i])




#
# Print summary
#
fileOut.write ("------------------------------------------------------------\n")
fileOut.write ("Summary\n")
fileOut.write ("%4d messages to Controller\n" % (parser.countFromSBC))
fileOut.write ("%4d messages to SBC\n" % (parser.countToSBC))
# fileOut.write ("AEW DEBUG: %d" % len(sortedSequence))
fileOut.write ("------------------------------------------------------------\n")
fileOut.write ("\n")
for i in range(len(parser.CmdSummary)):
	fileOut.write ("%s\n" % parser.CmdSummary[i])
import sys
import getopt

#-----------------------------------------------------------------------------------------------------------------------------------------#

def usage():
    print("extract_phase_timestamps.py -r <rotor name>")
    print(" -r <rotor name> Full prefix name of rotor")
    sys.exit(0)

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseMotCmdMsgOut()
@brief          Parse through MotCmdMsgOut text file and extracts data for instructed RPM, and instructed durations of time
@param fileIn:  Open MotCmdMsgOut text file
@return motRPM: Array containing commanded motor RPM values
@return motdT:  Array containing time durations for each RPM instruction
@return motT:   Array containing times at which the motor commands occur
'''

def parseMotCmdMsgOut(fileIn):
    line = fileIn.readline()
    if "Could not open input file" in line:
        print("Issue with ")
    while "Summary" not in line:
        line = fileIn.readline()

    for i in range(4):
        line = fileIn.readline()

    # motCmdInstructions = []
    motRPM = []
    motdT = []
    motT = []

    while line:
        line = fileIn.readline()
        line = line.replace("RPM", "")
        line = [l.strip() for l in line.split()]
        if len(line) < 5:
            continue
        motRPM.append(int(line[-1]))
        motdT.append(float(line[2]))
        motT.append(float(line[1]))

    return motRPM, motdT, motT

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseMsgOut()
@brief           Parse through MsgOut text file and extracts data for relevant command timestamps
@param fileIn:   Open MsgOut text file
@return msgOutT: Array containing timestamps for relevant SBC commands
'''

def parseMsgOut(fileIn):

    msgOutT = []

    line = fileIn.readline()

    while "Summary" not in line:
        line = fileIn.readline()

    for _ in range(5):
        line = fileIn.readline()

    while line:
        line = fileIn.readline()
        # if "[BR]" in line or \
        #    "[B ]" in line or \
        #    "[P ]" in line or \
        #    "[AM]" in line or \
        #    "[A ]" in line:

        if "[BR]" in line or \
           "[B ]" in line or \
           "[AM]" in line:
            
            line = [l.strip() for l in line.split()]

            msgOutT.append(float(line[1].replace(":", "")))

    return msgOutT

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
parseRISReadable()
@brief           Parse through RIS_Readable text file and extracts data for instructed RPM, and instructed durations of time
@param fileIn:   Open RIS_Readable text file
@return risRPM:  Array containing instructed RPM values
@return risdT:   Array containing time durations for each RPM instruction
@return risAccl: Array containing acceleration values between RPM instructions
'''

def parseRISReadable(fileIn):
    line = fileIn.readline()
    while "Summary Full" not in line:
        line = fileIn.readline()

    for _ in range(2):
        line = fileIn.readline()

    # risInstructions = [] # array for holding [time, RPM, direction, loops] information for easier use
    risRPM = []
    risdT = [] # only have the instructed duration, don't have the actual timestamps
    risAccl = []
    speedChecked = False
    while line:
        line = fileIn.readline()
        line = line.replace("'", "")
        line = line.replace("RPM", "")
        line = [l.strip() for l in line.split()]

        if len(line) < 1:
            continue

        if "NO_CHANGE" in line[3]:
            if "WAIT_MSG_C" in line[10] and len(risRPM) > 0:
                risRPM.append(risRPM[-1])
                risdT.append(risdT[-1])
                risAccl.append(risdT[-1]) # ?
            continue
        elif "HIGH_SPEED" in line[3]:
            line[3] = 0 # TODO: Update this value. not sure what it should be
        elif "LOW_SPEED" in line[3]:
            line[3] = 0 # TODO: Update this value, not sure what it should be
        elif "SPEED_CHECK" in line[3]:
            speedChecked = True
            continue
        elif "STOP_MOTOR" in line[3]:
            line[3] = 0
        elif "ROTOR_DONE" in line[3]:
            line[3] = 0

        tempRisRPM = []
        tempRisdT = []
        tempRisAccl = []
        loop = int(line[-1])

        rpm  = int(line[3])
        dT   = float(line[4])
        accl = int(line[8])

        if int(line[5]) == 1:
            # Reverse direction, need to turn RPM value negative
            rpm *= -1
        
        if len(risRPM) > 1 and risRPM[-1] > rpm:
            accl *= -1
        
        if loop > 1:
            # There is a loop
            # Add the loop-starting values to the temporary array
            tempRisRPM.append(rpm)
            tempRisdT.append(dT)
            tempRisAccl.append(accl)

            # Find all commands in the loop and add them to the array
            while int(line[-1]) != 0:
                line = fileIn.readline()
                line = line.replace("'", "")
                line = line.replace("RPM", "")
                line = [l.strip() for l in line.split()]

                rpm = int(line[3])
                dT  = float(line[4])
                accl = int(line[8])
                if int(line[5]) == 1:
                    rpm  *= -1
                
                if tempRisRPM[-1] > rpm:
                    accl *= -1
                
                tempRisRPM.append(rpm)
                tempRisdT.append(dT)
                tempRisAccl.append(accl)
            
            # Add the loop commands to the array loop # of times
            for _ in range(loop):
                risRPM  += tempRisRPM
                risdT   += tempRisdT
                risAccl += tempRisAccl
            
        else:
            # No loop
            if speedChecked:
                # Only here to handle risdT slightly differently than the other instances
                risRPM.append(rpm)
                risdT.append(dT + 0.02)
                risAccl.append(accl)
                speedChecked = False
            else:
                risRPM.append(rpm)
                risdT.append(dT)
                risAccl.append(accl)
            
    return risRPM, risdT, risAccl

#-----------------------------------------------------------------------------------------------------------------------------------------#

'''
findPhases()
@brief          Calculates timestamps pertaining to all high-level phases and transition periods
@param msgOutT: Array containing timestamps for relevant SBC commands
@param motT:    Array containing timestamps for motor commands
@param motRPM:  Array containing commanded motor RPM
@param risAccl: Array containing commanded motor acceleration values
@return phaseT: Array containing phase timestamps
'''

def findPhases(msgOutT, motT, motRPM, risAccl):
    
    phaseT = []
    idx = 1 # Start at 1 so we can look at the i-1 timestamp without getting an error
    SCALING_FACTOR = 1.0
    shift = 0
    while motRPM[shift-1] != 100:
        shift += 1
    shift += 1

    # Barcode scan, barcode data, begin analysis message timestamps
    phaseT += msgOutT

    # End of SEPARATE timestamp
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == -5500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == -5500:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of PRIME S1/S2
    while idx < len(motRPM):
        if motRPM[idx] == 100 and motRPM[idx-1] == 0:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1
            
    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 100 and motRPM[idx-1] == 0:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of UNNAMED
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 100:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1
            
    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 100:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ CHECK 1
    while idx < len(motRPM):
        if motRPM[idx] == 4000 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1
            
    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 5000 and motRPM[idx-1] == 4000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1
    
    # End of MOVE TO MIX CHAMBER
    while idx < len(motRPM):
        if motRPM[idx] == 1000 and motRPM[idx-1] == 5000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of MIX SAMPLE
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 5000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 5000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ CHECK 2
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == 1500:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of PRIME S3
    while idx < len(motRPM):
        if motRPM[idx] == 3000 and motRPM[idx-1] == 0:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 4000 and motRPM[idx-1] == 3000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR)) # TODO: why does this one in particular not work??? why does it accelerate so slowly
            break
        else:
            idx+=1

    # End of DISTRIBUTE CHEMISTRIES
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 4000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 4000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ CHECK 3
    while idx < len(motRPM):
        if motRPM[idx] == 1000 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1000 and motRPM[idx-1] == 1500:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of MIX CHEMISTRIES
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 1000:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # End of transition phase
    while idx < len(motRPM):
        if motRPM[idx] == 1500 and motRPM[idx-1] == 1000:
            dv = motRPM[idx]-motRPM[idx-1]
            dt = dv / risAccl[idx-shift]
            phaseT.append(motT[idx] + (dt * SCALING_FACTOR))
            break
        else:
            idx+=1

    # End of READ
    while idx < len(motRPM):
        if motRPM[idx] == 0 and motRPM[idx-1] == 1500:
            phaseT.append(motT[idx])
            break
        else:
            idx+=1

    # TODO FIGURE OUT THE TRANSITION PHASE RIGHT AFTER PRIME S3 AND WHY IT ISN'T IN THE RIGHT PLACE


    return phaseT

#-----------------------------------------------------------------------------------------------------------------------------------------#


argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
     
for o, a in opts:
    if o == "-r":
        rotor_name = a

if rotor_name == "":
    usage()

ris_infilename = rotor_name + "_RIS_Readable.txt"
mot_infilename = rotor_name + "_MotCmdMsgOut.txt"
msg_infilename = rotor_name + "_MsgOut.txt"
motor_files = [rotor_name + "_Group1_mot.bin"]

outfilename = rotor_name + "_PhaseTimestampsOut.txt"
fileOut = open(outfilename, 'wt')
print("Output file: %s" % outfilename)

fileOut.write("%s High Level Phase Timestamps\n" % rotor_name)
phases = ['Barcode Read', 'Transition', 'Separate', 'Transition', 'Prime S1/S2', 'Transition', 'Unnamed', 'Transition', 'Read Check 1', 'Transition', 'Move to Mix Chamber', 'Mix Sample', \
            'Transition', 'Read Check 2', 'Transition', 'Prime S3', 'Transition', 'Distribute Chemistries', 'Transition', 'Read Check 3', 'Transition', 'Mix Chemistries', 'Transition', 'Read', 'Idle']

motT = []
phaseT = []
msgOutT = []

# TODO: this is a workaround. the lipids have different RIS files. will need to analyze these alone
if "Lipid" in ris_infilename:
    print("Skipping: %s" % (ris_infilename))
    sys.exit(1)

if ris_infilename != "":

    try:
        fileIn = open(ris_infilename, 'rt')
    except:
        print("Could not open file %s" % (ris_infilename))
        sys.exit(1)

    risRPM, risdT, risAccl = parseRISReadable(fileIn)

    fileIn.close()

if mot_infilename != "":

    try:
        fileIn = open(mot_infilename, 'rt')
    except:
        print("Could not open file %s" % (mot_infilename))
        sys.exit(1)

    motRPM, motdT, motT = parseMotCmdMsgOut(fileIn)
        
    fileIn.close()

if msg_infilename != "":

    try:
        fileIn = open(msg_infilename, 'rt')
    except:
        print("Could not open file %s" % (msg_infilename))
        sys.exit(1)

    msgOutT = parseMsgOut(fileIn)

    fileIn.close()

# Find phase timestamps for plotting
phaseT = findPhases(msgOutT, motT, motRPM, risAccl)
fileOut.write("\nPhase Names                Timestamps\n")
fileOut.write("-------------------------  ----------\n")
for phase, time in zip(phases, phaseT):
    fileOut.write("%25s  %4.3f\n" % (phase, time))
fileOut.close()

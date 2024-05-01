import sys
import getopt

def usage():
    print("extract_phase_timestamps.py -r <rotor name> [-p] [-o]")
    print(" -r <rotor name> Full prefix name of rotor")
    print(" -p Flag to print output")
    print(" -o Flag to generate output file")
    sys.exit(0)

argc = len(sys.argv)
if argc < 2:
    usage()

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:po")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
PRINT_OUTPUT = False
CREATE_OUTPUT_FILE = False
     
for o, a in opts:
    if o == "-r":
        rotor_name = a
    elif o == "-p":
        PRINT_OUTPUT = True
    elif o == "-o":
        CREATE_OUTPUT_FILE = True

if rotor_name == "":
    usage()

infilename = rotor_name + "_MsgOut.txt"

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open input file: %s" % infilename)
    sys.exit(1)

print("\nRunning find_ack_time_delta.py for: %s\n" % infilename)

lines = fileIn.readlines()

# Create variables
prev_line   = []
enq_ackTime = []    # Start Of Message ACK times, SBC->Controller
lf_ackTime  = []    # End Of Message ACK times, SBC->Controller
enqTime     = []    # Start Of Message times, Controller->SBC
lfTime      = []    # End of Message times, Controller->SBC

for line in lines:
    if "Summary" in line:
        break

    line = [l.strip() for l in line.split()]

    if len(line) < 4 or len(line) > 8:
        continue

    if line[0] == "C->S" or line[0] == "C<-S":
        continue

    if line[-2] == "ACK" and line[-1] == "in":
        if prev_line[-2] == "ENQ" and prev_line[-1] == "out":
            enq_ackTime.append(float(line[0]))
            enqTime.append(float(prev_line[0]))
        elif prev_line[-1] == "LF":
            lf_ackTime.append(float(line[0]))
            lfTime.append(float(prev_line[0]))
        else:
            print("Unexpected ACK at %s" % line[0])
            print(prev_line)
            print(line)
    else:
        prev_line = line

if PRINT_OUTPUT:
    print(" ENQ Time   ACK Time     dT   ")
    print("---------- ---------- --------")
    for enq, ack in zip(enqTime, enq_ackTime):
        print("%10.3f %10.3f %8.3f" % (enq, ack, ack-enq))

    print("\n LF Time    ACK Time     dT   ")
    print("---------- ---------- --------")
    for lf, ack in zip(lfTime, lf_ackTime):
        print("%10.3f %10.3f %8.3f" % (lf, ack, ack-lf))
    
if CREATE_OUTPUT_FILE:
    outfilename = rotor_name + "_ACKTimeDeltaOut.txt"
    fileOut = open(outfilename, 'wt')

    print("\nOutput file created: %s" % outfilename)

    fileOut.write(" ENQ Time   ACK Time     dT   \n")
    fileOut.write("---------- ---------- --------\n")
    for enq, ack in zip(enqTime, enq_ackTime):
        fileOut.write("%10.3f %10.3f %8.3f\n" % (enq, ack, ack-enq))

    fileOut.write("\n LF Time    ACK Time     dT   \n")
    fileOut.write("---------- ---------- --------\n")
    for lf, ack in zip(lfTime, lf_ackTime):
        fileOut.write("%10.3f %10.3f %8.3f\n" % (lf, ack, ack-lf))
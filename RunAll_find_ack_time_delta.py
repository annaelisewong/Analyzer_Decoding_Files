import sys
import os
import subprocess
import getopt

def usage():
    print("RunAll_find_ack_time_delta.py [-p] [-o]")
    print(" -p Flag to indicate that the output should be printed")
    print(" -o Flag to indicate that an output file will be created")
    sys.exit(0)

argc = len(sys.argv)

file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_MsgOut" in filename]

PRINT_OUTPUT = ""
CREATE_OUTPUT_FILE = ""

if argc > 1:
    try:
        opts, args = getopt.getopt(sys.argv[1:], "op")
    except getopt.error:
        usage()
        sys.exit(2)
        
    for o, a in opts:
        if o == "-p":
            PRINT_OUTPUT = "-p"
        elif o == "-o":
            CREATE_OUTPUT_FILE = "-o"

for file in file_list:
    rotor_name = file.replace("_MsgOut.txt", "")
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\find_ack_time_delta.py", "-r", rotor_name, CREATE_OUTPUT_FILE, PRINT_OUTPUT])
    p.wait()
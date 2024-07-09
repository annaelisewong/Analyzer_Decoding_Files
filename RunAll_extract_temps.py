import sys
import os
import subprocess
import getopt

def usage():
    print("RunAll_extract_temps.py [-o] [-s] [-t] [-d]")
    print(" -o Flag to indicate output file should be created")
    print(" -s Flag to indicate figure should be saved")
    print(" -t Flag to indicate phase timestamp overlay should be shown on plot")
    print(" -d Flag to indicate that the plot will be displayed to the user.")
    sys.exit(0)

argc = len(sys.argv)

file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_Group1Data" in filename]

CREATE_OUTPUT_FILE = ""
SAVE_PLOT = ""
TIMESTAMP_OVERLAY = ""
DISPLAY_PLOT = ""

if argc > 1:
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ostd")
    except getopt.error:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == "-o":
            CREATE_OUTPUT_FILE = "-o"
        elif o == "-s":
            SAVE_PLOT = "-s"
        elif o == "-t":
            TIMESTAMP_OVERLAY = "-t"
        elif o == "-d":
            DISPLAY_PLOT = "-d"


for file in file_list:

    rotor_name = file.replace("_Group1Data.txt", "")
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_temps.py", "-r", rotor_name, CREATE_OUTPUT_FILE, SAVE_PLOT, TIMESTAMP_OVERLAY, DISPLAY_PLOT])
    p.wait()
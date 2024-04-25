import sys
import os
import subprocess
import getopt

def usage():
    print("RunAll_extract_plot_phase_stats.py [-p] [-s]")
    print(" -p Flag to indicate that an output plot should be generated")
    print(" -s Flag to indicate that an output plot should be generated and saved")
    sys.exit(0)

argc = len(sys.argv)

file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_RIS_Readable" in filename]

CREATE_PLOT = ""
SAVE_PLOT = ""

if argc > 1:
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ps")
    except getopt.error:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o == "-p":
            CREATE_PLOT = "-p"
        elif o == "-s":
            SAVE_PLOT = "-s"

for file in file_list:

    rotor_name = file.replace("_RIS_Readable.txt", "")
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_plot_phase_stats.py", "-r", rotor_name, CREATE_PLOT, SAVE_PLOT])
    p.wait()
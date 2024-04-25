import sys
import os
import subprocess

argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_BeakTimingOut" in filename]
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
elif argc == 2:
    file_list = [sys.argv[1]]

for file in file_list:

    rotor_name = file.replace("_BeakTimingOut.txt", "")
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_hold_time_stats.py", "-r", rotor_name, "-o"])
    p.wait()
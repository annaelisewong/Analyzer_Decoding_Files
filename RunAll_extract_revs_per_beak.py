import sys
import os
import subprocess

argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "BeakTimingOut.txt" in filename]
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
elif argc == 2:
    file_list = [sys.argv[1]]

file_count = 0

for infilename in file_list:

    file_count += 1

    if infilename == "":
        continue

    print("(%d/%d) Starting %s" % (file_count, len(file_list), infilename))

    rotor_name = infilename.replace("_BeakTimingOut.txt", "")

    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_revs_per_beak.py", "-r", rotor_name])
    p.wait()

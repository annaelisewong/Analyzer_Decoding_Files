import sys
import os
import subprocess

argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group1.csv" in filename]
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)

file_count = 0

for file in file_list:

    rotor_name = file.replace("_Group1.csv", "")

    file_count += 1

    print("(%d/%d) Calculating fan PWM for %s" % (file_count, len(file_list), rotor_name))
    
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\fan_pwm.py", "-r", rotor_name])
    p.wait()

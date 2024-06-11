import sys
import os
import subprocess

argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_MsgOut" in filename and "Rotor1" not in filename]
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
elif argc == 2:
    file_list = [sys.argv[1]]

file_count = 0

for file in file_list:
    file_count += 1
    rotor_name = file.replace("_MsgOut.txt", "")
    print("\n(%d/%d) Extracting ADC Photonic Test Results for %s" % (file_count, len(file_list), rotor_name))
    if "Baseline" in rotor_name:
        p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_adc_pho_test_results.py", "-i", rotor_name, "-o", "-b"])
        p.wait()
    else:
        p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_adc_pho_test_results.py", "-i", rotor_name, "-o"])
        p.wait()
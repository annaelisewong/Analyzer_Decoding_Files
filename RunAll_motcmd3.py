import sys
import os
import subprocess

argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group1_motrx.txt" in filename]
    # rx_file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group1_motrx.txt" in filename]
    # tx_file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group1_mottx.txt" in filename]
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
# elif argc == 3:
#     rx_file_list = [sys.argv[1]]
#     tx_file_list = [sys.argv[2]]

file_count = 0

# for rx_infilename, tx_infilename in zip(rx_file_list, tx_file_list):
for file in file_list:

    file_count += 1

    rotor_name = file.replace("_Group1_motrx.txt", "")

    print("(%d/%d) Running motcmd3.py on rotor %s" % (file_count, len(file_list), rotor_name))
    # NOTE: Legacy devices (rx tx), Dev platforms (tx rx)
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\motcmd3.py", "-r", rotor_name]) # Legacy
    # p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\motcmd3.py", tx_infilename, rx_infilename])
    p.wait()
    # fileOut.close()

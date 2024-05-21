import sys
import os
import subprocess

argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group0_rx.txt" in filename]
    # rx_file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group0_rx.txt" in filename]
    # tx_file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group0_tx.txt" in filename]
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
# elif argc == 2:
#     file_list = [sys.argv[1]]

file_count = 0

# for rx_infilename, tx_infilename in zip(rx_file_list, tx_file_list):
for file in file_list:

    # rotor_name = file.replace("_Group1_motrx.txt", "")

    rotor_name = file.replace("Serial", "")
    rotor_name = rotor_name.replace("Group0_rx", "MsgOut")
    rotor_name = rotor_name.replace("_MsgOut.txt", "")

    file_count += 1

    print("(%d/%d) Decoding serial files for %s" % (file_count, len(file_list), rotor_name))
    if "Serial" not in file:
        print("        'Serial' not found in file name. Skipping.")
        continue

    
    # ris_infilename = rotor_name + "_RIS.bin"

    # if os.path.exists(outfilename):
    #     os.remove(outfilename)

    # fileOut = open(outfilename, 'wt')
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\pc104decode3.py", "-r", rotor_name])
    p.wait()
    # fileOut.close()
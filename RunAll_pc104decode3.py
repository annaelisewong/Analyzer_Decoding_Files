import sys
import os
import subprocess

argc = len(sys.argv)
if argc == 1:
    rx_file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group0_rx.txt" in filename]
    tx_file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group0_tx.txt" in filename]
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
elif argc == 2:
    file_list = [sys.argv[1]]

file_count = 0

for rx_infilename, tx_infilename in zip(rx_file_list, tx_file_list):

    file_count += 1

    print("(%d/%d) Starting %s %s" % (file_count, len(tx_file_list), tx_infilename, rx_infilename))
    if "Serial" not in rx_infilename or "Serial" not in tx_infilename:
        print("        'Serial' not found in infilename. Skipping.")
        continue

    outfilename = tx_infilename.replace("Serial", "")
    outfilename = outfilename.replace("Group0_tx", "MsgOut")
    rotor_name = outfilename.replace("_MsgOut.txt", "")
    ris_infilename = rotor_name + "_RIS.bin"

    if os.path.exists(outfilename):
        os.remove(outfilename)

    fileOut = open(outfilename, 'wt')
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\pc104decode3.py", rx_infilename, tx_infilename, ris_infilename], stdout=fileOut)
    p.wait()
    fileOut.close()
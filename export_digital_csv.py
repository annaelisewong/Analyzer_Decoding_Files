# NOTE: THIS IS THE UDPATED VERSION OF ExportDigitalCsv.

import sys
import time
import os
from saleae import automation
from saleae.grpc import saleae_pb2, saleae_pb2_grpc
from dataclasses import dataclass

def usage():
    print("export_digital_csv.py")

file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if ".sal" in filename]

file_names = []
for file in file_list:
    file_names.append(os.path.split(file)[1].replace(".sal", ""))

print("Filenames:")
print(file_names)

file_count = 0

for file in file_list:
    file_count += 1
    infile = os.path.abspath(file)
    infilepath = os.path.split(infile)[0]
    infilename = os.path.split(infile)[1]
    outfilepath = infilepath[:-4] + "Exports" # Change the output folder from Data to Exports
    outfilename = infilename.replace(".sal", ".csv")

    print("(%d/%d) File: %s" % (file_count, len(file_list), file))
    print("  SAL file path: %s" % infilepath)
    print("  Local output folder: %s\n" % outfilepath)

    if os.path.exists(outfilepath + "\\" + outfilename):
        print("  File exists. Continuing.\n")
        continue
    
    try:
        print("Opening automation ...")
        manager = automation.Manager.launch()
    except:
        print("Could not open automation: %s" % infile)
        sys.exit(1)
    
    try:
        print("Opening capture ...")
        capture =  manager.load_capture(infile)
    except:
        print ("Could not open capture file")
        sys.exit(1)

    print("Exporting data ...")

    # Export raw digital data to the CSV file
    # capture.export_raw_data_csv(directory=outfilepath, digital_channels=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    capture.export_raw_data_csv(directory=outfilepath, digital_channels=[4,5,6,7,8,9,10,11,12,13,14,15], analog_channels = [0,1,2,3])

    print("Done")
    manager.close()

    # Rename general "digital.csv" to run-specific name
    print("Rename %s\\%s to %s\\%s" % (outfilepath, "digital.csv", outfilepath, outfilename))
    os.rename("%s\\%s" % (outfilepath, "digital.csv"), "%s\\%s" % (outfilepath, outfilename))
    time.sleep(2)

print("Exit")
sys.exit(0)

#
# ExportDigitalCsv.py
#
# Exports "digital.csv" from .sal files
#
# The built-in AsyncSerial protocol analyzer does not seem to honor the Radix (Hexidecimal) 
# for Data Table Export, is always 'Ascii', which is useless as it does not recognize hex values.
#
#

import sys
import getopt
import time
import os
from saleae import automation
from datetime import datetime
from saleae.grpc import saleae_pb2, saleae_pb2_grpc
from dataclasses import dataclass

# usage()
#
def usage():
    print( "ExportDigitalCsv.py -f <config_filename>")

# cmd line defaults
configFilename = ''

#    
# parse command line options
#
try:
	opts, args = getopt.getopt(sys.argv[1:], "f:")
except getopt.error:
	usage()
	sys.exit(2)

# process options
for o, a in opts:
	if o == "-f":
		configFilename = a

if configFilename == '':
	usage()
	sys.exit(1)

# Path to folder containing .sal files
salFilePath = "C:\\Users\\awong\\Documents\\Box_Logic_Analyzer_Data\\Dev_Platform\\OFS004\\240415\\Data"
salExtension = "sal"

# Get list of files to process from special text file
filenames = []
localOutput = ''
with open(configFilename) as file:
	for line in file:
		lineLen = len(line)
		if lineLen < 2:
			continue
		if line[0] == '#':		# skip commented line
			continue
		elif (lineLen >= 20) and (line[0:18] == "destinationFolder="):
			localOutput = line[18:-1]
		elif (lineLen >= 12) and (line[0:10] == "salFolder="):
			salFilePath = line[10:-1]
		else:
			filenames.append(line.rstrip())

# Output folder to save .csv files to
outputDirectory = os.path.join(os.getcwd(), localOutput)

print ("SAL file path: %s" % (salFilePath))
print ("Local output folder: %s" % (localOutput))
print ("Output file path: %s" % (outputDirectory))
print ("Filenames: ", end='')
print (filenames)

# Process each file from list
for nn in filenames:
	fullname = "%s\%s.%s" % (salFilePath, nn, salExtension)
	print ("%s" % (fullname))

	try:
		print ("Opening automation ...")
		#manager = automation.Manager.connect()
		manager = automation.Manager.launch()
	except:
		print ("Could not open automation")
		sys.exit(1)

	try:
		print ("Opening capture ...")
		capture =  manager.load_capture(fullname)
	except:
		print ("Could not open capture file")
		sys.exit(1)

	print ("Exporting data ...")

	# Export raw digital data to the CSV file
	capture.export_raw_data_csv(directory=outputDirectory, digital_channels=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])

	print ("Done")
	manager.close()

	# rename general "digital.csv" to run-specific name
	print ("Rename")
	os.rename("%s\\%s" % (outputDirectory, "digital.csv"), "%s\\%s" % (outputDirectory, "%s.csv" % (nn)))
	time.sleep(2)

print ("Exit")

import string
import sys
import os
import time
import numpy as np
import math
import getopt
import csv

# NOTE: This script takes in a csv file.
#       Run: `grep BC_SIGNAL <rotor_name>_Group1Data.txt > allbarcode.csv`

def usage():
    print("parse_barcode_data.py <input_csv_file>")

argc = len(sys.argv)
if argc < 1:
    usage()
    sys.exit()

infilename = ""

# parse command line options

try:
    args = sys.argv[1:]
except:
    usage()
    sys.exit(2)

#try:
#    opts, args = getopt.getopt(sys.argv[1:],"i")
#except getopt.error:
#    usage()
#    sys.exit(2)

# process options
#for o, a in opts:
#    if o == "-i":
#        print(o)
#        infilename = a

infilename = args[0]

if infilename == "":
    usage()
    sys.exit(1)

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open input file %s" % (infilename))
    sys.exit(1)

base = os.path.basename(infilename)
basefile = os.path.splitext(base)[0]
lastmodified= os.stat("%s"%(infilename)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]

# Analyze the barcode read times

barcode_read_times = np.loadtxt(fname=infilename, skiprows=2, usecols=1)
total_time = barcode_read_times[-1] - barcode_read_times[0]

count = len(barcode_read_times)
deltas = np.diff(barcode_read_times)
min_delta = np.min(deltas)
max_delta = np.max(deltas)
avg_delta = np.mean(deltas)
std_dev = np.std(deltas)

print("\nInput file: %s at %s\n" % (infilename, ftstr))
print("%d barcode readings over %f seconds." % (count, total_time))
print("    Average time delta between readings: %.9fs" % (avg_delta))
print("    Minimum time delta between readings: %.9fs" % (min_delta))
print("    Maximum time delta between readings: %.9fs" % (max_delta))
print("    Standard deviation of time deltas:   %.9fs" % (std_dev))

fields=[total_time, avg_delta, min_delta, max_delta, std_dev]
with open('out.csv', 'a') as f:
    writer = csv.writer(f)
    writer.writerow(fields)
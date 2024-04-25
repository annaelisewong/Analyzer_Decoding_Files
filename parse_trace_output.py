from asyncio.windows_events import NULL
import sys
import os
import re


# parse through each line until we reach "Up Time" line
# keep track of that timestamp
# TODO: compare this timestamp with the timestamp of logic analyzer?
# read through rest of the lines
# adjust timestamp so that

prev_time_char = [15, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

def usage():
    print("parse_trace_output.py <input_log_file>")

# argc = len(sys.argv)
# if argc < 1:
#     usage()
#     sys.exit()

infilename = ""

# parse command line options

# try:
#     args = sys.argv[1:]
# except:
#     usage()
#     sys.exit(2)


# infilename = args[0]
argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "TraceOutput" in filename]
    print("Number of files to check: %d\n\n" % (len(file_list)))
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
elif argc == 2:
    file_list = [sys.argv[1]]

for infilename in file_list:

    print(infilename)

    if infilename == "":
        usage()
        continue
    
    outfilename = os.path.splitext(infilename)[0] + "_parsed.txt"

    try:
        numCamUps = lambda file, s: open(file, 'rt').read().count(s)
        cam_total = numCamUps(infilename, "CAM_UP")
    except:
        print("Could not open input file %s" % infilename)
        continue

    try:
        fileIn = open(infilename, 'rt')
    except:
        print("Could not open input file %s" % (infilename))
        continue

    try:
        fileOut = open(outfilename, 'a')
    except:
        print("Could not open output file %s" % outfilename)
        continue

    up_time = 0
    line = fileIn.readline()
    cam_count = 0

    while "CAM_UP" not in line or cam_count != cam_total:
        line = fileIn.readline()
        if "CAM_UP" in line:
            cam_count += 1
        if cam_count == cam_total:
            break

    line = [l.strip("]") for l in line.split()]
    up_time = float(line[1])
    time_char = int(line[2].strip("]"), 16)
    fileOut.write("CAM_UP time: %f\n\n" % up_time)

    line = fileIn.readline()

    fileOut.write("Time\tTemp Read State\n")

    while line:
        line = line.strip('[]')
        split_line = [l.strip(']') for l in line.strip().split()]

        if len(split_line) <= 2:
            line = fileIn.readline()
            continue
        temp = int(split_line[1], 16) # convert this string to an integer value
        if time_char != prev_time_char[temp]:
            fileOut.write("Error: Missing some printed lines. Line: %s\n" % line)
        time_char = temp

        if "case" in line or "Going" in line or "---" in line or "BC" in line:
            line = fileIn.readline()
            continue

        fileOut.write("%.3f\t%s\n" % (float(split_line[0]) - up_time, split_line[4]))

        line = fileIn.readline()

    fileIn.close()
    fileOut.close()
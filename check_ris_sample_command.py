import os
import sys
import getopt

## TODO: write usage function, fix inputs and outputs, write RunAll function
# If run without any arguments, print the usage function

def usage():
    print("check_ris_sample_command.py -r <rotor name> [-o]")
    print(" -r <rotor name> Full prefix name of rotor")
    print(" -o Flag to indicate output file should be created")
    sys.exit(0)


def fullRotorScan(flash_count):
    full_rotor_scan = [[0, 0], [7, 0], [14, 0], [21, 0], [28, 0], [5, 0], [12, 0], [19, 0], [26, 0], [3, 0], \
                       [10, 0], [17, 0], [24, 0], [1, 0], [8, 0], [15, 0], [22, 0], [29, 0], [6, 0], [13, 0], \
                       [20, 0], [27, 0], [4, 0], [11, 0], [18, 0], [25, 0], [2, 0], [9, 0], [16, 0], [23, 0]]
    
    for frs in full_rotor_scan:
        frs[1] = flash_count
    
    return full_rotor_scan

argc = len(sys.argv)

if argc < 2:
    usage()
    sys.exit(0)

# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "r:o")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
rotor_name = ""
CREATE_OUTPUT_FILE = False
     
for o, a in opts:
    if o == "-r":
        rotor_name = a
    elif o == "-o":
        CREATE_OUTPUT_FILE = True

if rotor_name == "":
    usage()

g0_infilename = rotor_name + "_Group0Data.txt"
ris_infilename = rotor_name + "_RIS_Readable.txt"

outfilename = rotor_name + "_SampleCommandOut.txt" # TAKE CARE OF THIS IN A SECOND
fileOut = open(outfilename, 'wt')

if g0_infilename == "":
    print("No file name detected.")
    sys.exit(0)

print("\nGroup0Data File Name: %s" % g0_infilename)
print("RIS_Readable File Name: %s\n" % ris_infilename)
fileOut.write("\nGroup0Data File Name: %s\n" % g0_infilename)
fileOut.write("RIS_Readable File Name: %s\n" % ris_infilename)

g0_cuv_command = [] # cuvette num & flashes
ris_cuv_command = [] # cuvette num & flashes

##### RIS READABLE
try:
    ris_fileIn = open(ris_infilename, 'rt')
except:
    print("Could not open input file %s" % ris_infilename)

line = ris_fileIn.readline()

while "Summary Full" not in line:
    line = ris_fileIn.readline()

for i in range(2):
    line = ris_fileIn.readline()

while line:
    line = ris_fileIn.readline()
    
    if line == "":
        continue

    loop = int([l.strip() for l in line.split()][-1])

    if loop > 1:
        loop_array = []
        l = loop
        while l > 0:
            if "CUV" in line and "NO_CUV_COMMAND" not in line:
                line = [l.strip() for l in line.split()]
                loop_array.append([int(line[13]), int(line[-2])])
                
            elif "FULL_ROTOR_SCAN" in line:
                line = [l.strip() for l in line.split()]
                loop_array += fullRotorScan(int(line[-2]))
            
            line = ris_fileIn.readline()
            l = int([l.strip() for l in line.split()][-1])
        
        for _ in range(loop):
            ris_cuv_command += loop_array

        continue

    if "CUV" in line and "NO_CUV_COMMAND" not in line:
        line = [l.strip() for l in line.split()]
        ris_cuv_command.append([int(line[13]), int(line[-2])])

    elif "FULL_ROTOR_SCAN" in line:
        line = [l.strip() for l in line.split()]
        ris_cuv_command += fullRotorScan(int(line[-2]))

ris_fileIn.close()

#### GROUP 0 DATA
try:
    g0_fileIn = open(g0_infilename, 'rt')
except:
    print("Could not open input file %s" % (g0_infilename))
    sys.exit(1)

line = g0_fileIn.readline()

while "Strobe Chart" not in line:
    line = g0_fileIn.readline()

for i in range(2):
    line = g0_fileIn.readline()

while line:
    line = g0_fileIn.readline()
    if "Flash Count" in line:
        break
    line = [l.strip() for l in line.split()]
    if float(line[0]) < 0:
        continue
    if int(line[2]) == 54:
        g0_cuv_command.append([int(line[1]), 51])
        g0_cuv_command.append([int(line[1]), 3])
        continue
    elif len(g0_cuv_command) > len(ris_cuv_command):
        print(line)
        break
    elif int(line[2]) != ris_cuv_command[len(g0_cuv_command)-1][1]:
        # Account for any accidental combinations similar to the 54 = 51 + 3
        # in the Group0Data.txt file writing
        temp =int(line[2])
        if temp %  ris_cuv_command[len(g0_cuv_command)-1][1] == 0:
            while temp > 0:
                g0_cuv_command.append([int(line[1]),  ris_cuv_command[len(g0_cuv_command)-1][1]])
                temp -=  ris_cuv_command[len(g0_cuv_command)-1][1]
            continue
    g0_cuv_command.append([int(line[1]), int(line[2])])

g0_fileIn.close()

print("Cuvette sample order as instructed:", g0_cuv_command[1:] == ris_cuv_command)
fileOut.write("\nCuvette sample order as instructed: %r\n" % (g0_cuv_command[1:] == ris_cuv_command))

fileOut.write("\n       RIS Readable     Group 0 Data\n")
fileOut.write("        --------------   --------------\n")
fileOut.write("         cuv  samples     cuv  samples\n")
fileOut.write("[    ]     -        -    %4d %8d\n" % (g0_cuv_command[0][0], g0_cuv_command[0][1]))
for i in range(len(g0_cuv_command)-1):
    fileOut.write("[%r]  %4d %8d    %4d %8d\n" % (g0_cuv_command[i+1]==ris_cuv_command[i], g0_cuv_command[i+1][0], g0_cuv_command[i+1][1], ris_cuv_command[i][0], ris_cuv_command[i][1]))
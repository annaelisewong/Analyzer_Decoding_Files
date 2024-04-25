import os
import sys
from matplotlib import pyplot as plt

argc = len(sys.argv)

if argc < 2:
    print("Need file input.")
    sys.exit(1)

infilename = sys.argv[1]

try:
    fileIn = open(infilename, 'rt')
except:
    print("Could not open input file %s" % (infilename))
    sys.exit(1)

line = fileIn.readline()

while "chan3" not in line:
    line = fileIn.readline()
    if "Global Delay" in line:
        line.strip()
        line = [l.strip() for l in line.split()]
        gcd = float(line[2])


usec = []
chan1 = []
chan2 = []

while line:
    line = fileIn.readline()
    line.strip()
    line = [l.strip() for l in line.split()]
    if len(line) == 0:
        continue
    usec.append(float(line[0]))
    chan1.append(float(line[1]))
    chan2.append(float(line[2]))

fig = plt.figure(1)
plt.plot(usec, chan1, color='orange', linewidth=0.5, label="chan1")
plt.plot(usec, chan2, color='blue', linewidth=0.5, label="chan2")

plt.xlabel('usec')
plt.ylabel('Signal')
plt.title('Cuvette Delay')
fig.suptitle("%s" % (infilename), fontsize = 10)
plt.axvline(x = gcd, color = 'grey', linewidth=.5, label="GCD")
plt.legend(fontsize = 8)
    
plt.show()
plt.close()
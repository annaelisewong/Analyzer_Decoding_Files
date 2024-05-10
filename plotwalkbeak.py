#
# plotwalk.py
#
# Plot 
#

import string
import sys
import getopt
import time
import os
import math
import matplotlib.pyplot as plt
import numpy as np 
from matplotlib.ticker import AutoMinorLocator
import matplotlib.ticker as ticker

def usage():
	print("<input text file> <Cuvette #> <GCD>")


argc = len(sys.argv)
if argc < 2:
    usage()
    sys.exit(0)

# cmd line defaults
infilename = ''
out_text = 0
saveplot = 0

startnow = time.localtime(time.time())
tstr = time.strftime("%Y-%m-%d %H:%M:%S", startnow)
print ("Starting ... %s" % (tstr))

#    
# parse command line options
#
# try:
#     opts, args = getopt.getopt(sys.argv[1:], "i:")
# except getopt.error:
#     usage()
#     sys.exit(2)

# # process options
# for o, a in opts:
#     if o == "-i":
#         infilename = a

infilename = sys.argv[1]

if infilename == '':
    usage()
    sys.exit(1)

testCuv = int(sys.argv[2])
gcd = int(sys.argv[3])

try:
	fileIn = open(infilename, 'rt')
except:
	print( "Could not open input file %s" % (infilename))
	sys.exit(1)

base = os.path.basename(infilename)
basefile = os.path.splitext(base)[0]
baseext = os.path.splitext(base)[1]
print ("%s %s %s" % (base, basefile, baseext))

lastmodified= os.stat("%s"%(infilename)).st_mtime
aa = time.localtime(lastmodified)
ftstr = time.strftime("%Y-%m-%d %H:%M:%S", aa)
print( "Processing file  ... %s" % (ftstr))

ststr = time.strftime("%Y%m%d%H%M%S", aa)[2:]

fileOut = sys.stdout

numlines = 0

fileOut.write("Data file: %s of %s\n" % (infilename, ftstr))
looking = 0
ingroup = 0
sampdat = []
numPerGroup = 5
# testCuv = 29

while 1:
	line = fileIn.readline()
	if len(line) <= 0:
		break
	numlines += 1

	if len(line) <= 3:
		continue

	linej = " ".join(line.split())
	linesp = linej.split()
	lensp = len(linesp)

	if looking == 0:
		a = linej.find('uni')
		b = linej.find('906')
		if (a > -1) and (b > -1):
			print (numlines, linej)
			looking = 1
		continue

	print (ingroup, lensp, linesp)
	
	if ingroup and (lensp == 5) and (linesp[0] == "ADC"):
		sampleIdx = int(linesp[1][:-1])
		linelist[sampleIdx+1].append(float(linesp[3]))
		print(sampleIdx, float(linesp[3]))
		if sampleIdx == 9:
			print ("end sample")
			ingroup += 1
			if ingroup > numPerGroup:
				ingroup = 0
				sampdat.append(linelist)

	if (ingroup == 0) and (lensp == 2) and (int(linesp[0]) == testCuv):
		ingroup = 1
		linelist = [int(linesp[1]), [], [], [], [], [], [], [], [], [], []]

t = []
w340 = []
w405 = []
w467 = []
w500 = []
w515 = []
w550 = []
w600 = []
w630 = []
w850 = []
wfl = []

 
len_sampdat = len(sampdat)
for i in range(len_sampdat):

	t.append(sampdat[i][0])

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][1][j]))
		sum += sampdat[i][1][j]
	sum = sum / 5.0
	w340.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][2][j]))
		sum += sampdat[i][2][j]
	sum = sum / 5.0
	w405.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][3][j]))
		sum += sampdat[i][3][j]
	sum = sum / 5.0
	w467.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][4][j]))
		sum += sampdat[i][4][j]
	sum = sum / 5.0
	w500.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][5][j]))
		sum += sampdat[i][5][j]
	sum = sum / 5.0
	w515.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][6][j]))
		sum += sampdat[i][6][j]
	sum = sum / 5.0
	w550.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][7][j]))
		sum += sampdat[i][7][j]
	sum = sum / 5.0
	w600.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][8][j]))
		sum += sampdat[i][8][j]
	sum = sum / 5.0
	w630.append(sum)

	sum = 0.0
	for j in range(5):
		print ("%f " % (sampdat[i][9][j]))
		sum += sampdat[i][9][j]
	sum = sum / 5.0
	w850.append(sum)

	print ("%d %f" % (sampdat[i][0], sum))

# max_y = max(w340)
# max_y = max(max(w405), max_y)
# max_y = max(max(w467), max_y)
# max_y = max(max(w500), max_y)
# max_y = max(max(w515), max_y)
# max_y = max(max(w550), max_y)
# max_y = max(max(w600), max_y)
# max_y = max(max(w630), max_y)
# max_y = max(max(w850), max_y)

"""
AEW changes for testing protocols
"""
# w340_max_y = max(w340)
# w405_max_y = max(w405)
# w467_max_y = max(w467)
# w500_max_y = max(w500)
# w515_max_y = max(w515)
# w550_max_y = max(w550)
# w600_max_y = max(w600)
# w630_max_y = max(w630)
# w850_max_y = max(w850)

# w340_max_x = t(w340.index(w340_max_y))


"""
   340nm     70	uv
   405nm     60 vio
   467nm     45 blu
   500nm     40 cyan
   515nm     40 green
   550nm     48 lt green
   600nm     45 yel
   630nm     53 org
   850nm     45 ir
   WHT_FL    16

"""

fig = plt.figure(1)
plt.plot(t, w340, color='grey', linewidth=0.5, label="340")
plt.plot(t, w405, color='purple', linewidth=0.5, label="405")
plt.plot(t, w467, color='violet', linewidth=0.5, label="467")
plt.plot(t, w500, color='blue', linewidth=0.5, label="500")
plt.plot(t, w515, color='cyan', linewidth=0.5, label="500")
plt.plot(t, w550, color='green', linewidth=0.5, label="550")
plt.plot(t, w600, color='yellow', linewidth=0.5, label="600")
plt.plot(t, w630, color='orange', linewidth=0.5, label="630")
plt.plot(t, w850, color='red', linewidth=0.5, label="850")

title = basefile.replace("_Putty", "")

#plt.xlim([195, 205])
# plt.ylim([18000,27000])
plt.xlabel('Delay, us')
plt.ylabel('Signal')
plt.title('Cuvette Delay')
fig.suptitle("%s" % (title), fontsize = 10)
#plt.axhline(y=0, color='grey', linestyle=':', linewidth=1.0)
#plt.axvline(x=0, color='grey', linestyle=':', linewidth=1.0)
plt.axvline(x = gcd, color = 'grey', linewidth=.5)
# plt.axhline(y=max_y + 5, color='grey', linewidth=0.5)
# plt.axvline(x=w340_max_x, color='red', linewidth=.5) # testing to see if the line drawn is actually the max of this - delete later
# plt.axhline(y=w340_max_y, color='red', linewidth=.5) # testing to see if the line drawn intersects at the right point with the line above - delete later
#ax = fig.gca()
plt.legend(fontsize = 8)

"""
if saveplot:
	plt.savefig("%s_Fig1.png" % (basefile))

	print ("Making array")
	xarray = np.array(x_time)
	yarray = np.array(y_rpm)

	print ("Saving array")
	with open("%s.npy" % (basefile), 'wb') as fo:
		np.save(fo, xarray)
		np.save(fo, yarray)
"""

#
# Make visible
plt.show()
#time.sleep(5)
plt.close()

"""
data_colors = ['blue', 'green', 'orange', 'cyan', 'pink', 'violet', 'yellow', 'red', 'grey', 'black']
data_labels = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
data_styles = ['-', '-', '-', '-', '-', '-', '-', '-', '-', '-']
"""

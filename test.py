import sys
import os
import getopt
import numpy as np

def usage():
    print("REPLACE FILE NAME HERE [-b] [-i] [-o] [-h] [-s] [-t]")
    print(" -b Flag to amass beak and integration timing statistics")
    print(" -i Flag to amass integration timing statistics")
    print(" -o Flag to amass beak offset statistics")
    print(" -h Flag to amass hold time statistics")
    print(" -s Flag to amass spindle motor phase statistics")
    print(" -t Flag to amass temperature statistics")

class SpindleMotorPhaseStats():
    def __init__(self, phase_idx, acceleration, exp_value=None):
        self.phase_idx = phase_idx
        self.exp_value = exp_value
        self.avgs = []
        self.stdevs = []
        self.min = 9999999999999999 # TODO update this with better value
        self.max = -9999999999999999 # TODO update this with better value
        self.slopes = []
        self.acceleration = acceleration

        # Mix Samples
        if phase_idx == 14:
            self.P5000toP1000_exp = -10000
            self.P5000toP1000_min = 9999999999999999
            self.P5000toP1000_max = -9999999999999999
            self.P5000toP1000_avgs = []
            self.P5000toP1000_stdevs = []
            self.P5000toP1000_slopes = []

            self.P1000toP4000_exp = 750
            self.P1000toP4000_min = 9999999999999999
            self.P1000toP4000_max = -9999999999999999
            self.P1000toP4000_avgs = []
            self.P1000toP4000_stdevs = []
            self.P1000toP4000_slopes = []

            self.P4000toP5000_exp = 500
            self.P4000toP5000_min = 9999999999999999
            self.P4000toP5000_max = -9999999999999999
            self.P4000toP5000_avgs = []
            self.P4000toP5000_stdevs = []
            self.P4000toP5000_slopes = []

        # Mix Chemistries
        if phase_idx == 27:
            self.P1900toP1000_exp = -6000
            self.P1900toP1000_min = 9999999999999999
            self.P1900toP1000_max = -9999999999999999
            self.P1900toP1000_avgs = []
            self.P1900toP1000_stdevs = []
            self.P1900toP1000_slopes = []

            self.P1000toP1000_exp = 1000
            self.P1000toP1000_min = 9999999999999999
            self.P1000toP1000_max = -9999999999999999
            self.P1000toP1000_avgs = []
            self.P1000toP1000_stdevs = []

            self.P1000toN1900_exp = -5000
            self.P1000toN1900_min = 9999999999999999
            self.P1000toN1900_max = -9999999999999999
            self.P1000toN1900_avgs = []
            self.P1000toN1900_stdevs = []
            self.P1000toN1900_slopes = []

            self.N1900toN1000_exp = 6000
            self.N1900toN1000_min = 9999999999999999
            self.N1900toN1000_max = -9999999999999999
            self.N1900toN1000_avgs = []
            self.N1900toN1000_stdevs = []
            self.N1900toN1000_slopes = []

            self.N1000toN1000_exp = -1000
            self.N1000toN1000_min = 9999999999999999
            self.N1000toN1000_max = -9999999999999999
            self.N1000toN1000_avgs = []
            self.N1000toN1000_stdevs = []

            self.N1000toP1900_exp = 5000
            self.N1000toP1900_min = 9999999999999999
            self.N1000toP1900_max = -9999999999999999
            self.N1000toP1900_avgs = []
            self.N1000toP1900_stdevs = []
            self.N1000toP1900_slopes = []
    
    def updateMin(self, val):
        if self.phase_idx == 29:
            if val < 0:
                return
        if val < self.min:
            self.min = val
    
    def updateMax(self, val):
        if self.phase_idx == 29:
            if val > 2000:
                return
        if val > self.max:
            self.max = val
    
    def updateAvgs(self, val):
        self.avgs.append(val)

    def updateStDevs(self, val):
        self.stdevs.append(val)

    def updateSlopes(self, val):
        self.slopes.append(val)

    def updateMixMin(self, range, val):
        # Mix Sample
        if range == "5000RPM->1000RPM":
            if val < self.P5000toP1000_min:
                self.P5000toP1000_min = val
        elif range == "1000RPM->4000RPM":
            if val < self.P1000toP4000_min:
                self.P1000toP4000_min = val
        elif range == "4000RPM->5000RPM":
            if val < self.P4000toP5000_min:
                self.P4000toP5000_min = val

        # Mix Chemistries
        elif range == "1900RPM->1000RPM":
            if val < self.P1900toP1000_min:
                self.P1900toP1000_min = val
        elif range == "1000RPM->1000RPM":
            if val < self.P1000toP1000_min:
                self.P1000toP1000_min = val
        elif range == "1000RPM->-1900RPM":
            if val < self.P1000toN1900_min:
                self.P1000toN1900_min = val
        elif range == "-1900RPM->-1000RPM":
            if val < self.N1900toN1000_min:
                self.N1900toN1000_min = val
        elif range == "-1000RPM->-1000RPM":
            if val < self.N1000toN1000_min:
                self.N1000toN1000_min = val
        elif range == "-1000RPM->1900RPM":
            if val < self.N1000toP1900_min:
                self.N1000toP1900_min = val

    def updateMixMax(self, range, val):
        # Mix Sample
        if range == "5000RPM->1000RPM":
            if val > self.P5000toP1000_max:
                self.P5000toP1000_max = val
        elif range == "1000RPM->4000RPM":
            if val > self.P1000toP4000_max:
                self.P1000toP4000_max = val
        elif range == "4000RPM->5000RPM":
            if val > self.P4000toP5000_max:
                self.P4000toP5000_max = val

        # Mix Chemistries
        elif range == "1900RPM->1000RPM":
            if val > self.P1900toP1000_max:
                self.P1900toP1000_max = val
        elif range == "1000RPM->1000RPM":
            if val > self.P1000toP1000_max:
                self.P1000toP1000_max = val
        elif range == "1000RPM->-1900RPM":
            if val > self.P1000toN1900_max:
                self.P1000toN1900_max = val
        elif range == "-1900RPM->-1000RPM":
            if val > self.N1900toN1000_max:
                self.N1900toN1000_max = val
        elif range == "-1000RPM->-1000RPM":
            if val > self.N1000toN1000_max:
                self.N1000toN1000_max = val
        elif range == "-1000RPM->1900RPM":
            if val > self.N1000toP1900_max:
                self.N1000toP1900_max = val

    def updateMixAvgs(self, range, val):
        # Mix Sample
        if range == "5000RPM->1000RPM":
            self.P5000toP1000_avgs.append(val)
        elif range == "1000RPM->4000RPM":
            self.P1000toP4000_avgs.append(val)
        elif range == "4000RPM->5000RPM":
            self.P4000toP5000_avgs.append(val)
        
        # Mix Chemistries
        elif range == "1900RPM->1000RPM":
            self.P1900toP1000_avgs.append(val)
        elif range == "1000RPM->1000RPM":
            self.P1000toP1000_avgs.append(val)
        elif range == "1000RPM->-1900RPM":
            self.P1000toN1900_avgs.append(val)
        elif range == "-1900RPM->-1000RPM":
            self.N1900toN1000_avgs.append(val)
        elif range == "-1000RPM->-1000RPM":
            self.N1000toN1000_avgs.append(val)
        elif range == "-1000RPM->1900RPM":
            self.N1000toP1900_avgs.append(val)

    def updateMixStDevs(self, range, val):
        # Mix Sample
        if range == "5000RPM->1000RPM":
            self.P5000toP1000_stdevs.append(val)
        elif range == "1000RPM->4000RPM":
            self.P1000toP4000_stdevs.append(val)
        elif range == "4000RPM->5000RPM":
            self.P4000toP5000_stdevs.append(val)

        # Mix Chemistries
        elif range == "1900RPM->1000RPM":
            self.P1900toP1000_stdevs.append(val)
        elif range == "1000RPM->1000RPM":
            self.P1000toP1000_stdevs.append(val)
        elif range == "1000RPM->-1900RPM":
            self.P1000toN1900_stdevs.append(val)
        elif range == "-1900RPM->-1000RPM":
            self.N1900toN1000_stdevs.append(val)
        elif range == "-1000RPM->-1000RPM":
            self.N1000toN1000_stdevs.append(val)
        elif range == "-1000RPM->1900RPM":
            self.N1000toP1900_stdevs.append(val)

    def updateMixSlopes(self, range, val):
        # Mix Sample
        if range == "5000RPM->1000RPM":
            self.P5000toP1000_slopes.append(val)
        elif range == "1000RPM->4000RPM":
            self.P1000toP4000_slopes.append(val)
        elif range == "4000RPM->5000RPM":
            self.P4000toP5000_slopes.append(val)

        # Mix Chemistries
        elif range == "1900RPM->1000RPM":
            self.P1900toP1000_slopes.append(val)
        elif range == "1000RPM->-1900RPM":
            self.P1000toN1900_slopes.append(val)
        elif range == "-1900RPM->-1000RPM":
            self.N1900toN1000_slopes.append(val)
        elif range == "-1000RPM->1900RPM":
            self.N1000toP1900_slopes.append(val)


# Parse the command line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "biohst")
except getopt.error:
    usage()
    sys.exit(2)
    
# Process options
TYPE = ""
     
for o, a in opts:
    if o == "-b":
        TYPE = "BeakDelay"
        break
    elif o == "-i":
        TYPE = "IntTiming"
        break
    elif o == "-o":
        TYPE = "OffsetTiming"
        break
    elif o == "-h":
        TYPE = "HoldTiming"
        break
    elif o == "-s":
        TYPE = "SpindleMotorSpeeds"
        break
    elif o == "-t":
        TYPE = "Temperature"
        break

if TYPE == "":
    usage()
    sys.exit(0)

file_list = ""
if TYPE == "BeakDelay" or TYPE == "IntTiming" or TYPE == "OffsetTiming" or TYPE == "HoldTiming":
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_BeakTimingOut.txt" in filename]
elif TYPE == "SpindleMotorSpeeds":
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_PhaseStatsOut.txt" in filename]
elif TYPE == "Temperature":
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_TempStatsOut.txt" in filename]

if file_list == "":
    usage()
    sys.exit(1)


if TYPE == "SpindleMotorSpeeds":
    phases = ["BARCODE", "ACCELERATION TO SEPARATE (0RPM to -3000RPM)", "ACCELERATION TO SEPARATE (-3000RPM to -5500RPM)", "SEPARATE", "ACCELERATION TO PRIME S1/S2 (-5500RPM to 0RPM)", "ACCELERATION TO PRIME S1/S2 OVERSHOOT", \
                "UNNAMED", "ACCELERATION TO READ CHECK 1 (100RPM to 1500RPM)", "ACCELERATION TO READ CHECK 1 OVERSHOOT", "READ CHECK 1", "ACCELERATION TO MIX CHAMBER (1500RPM to 4000RPM)", "ACCELERATION TO MIX CHAMBER OVERSHOOT", \
                "ACCELERATION TO MIX CHAMBER (4000RPM to 5000RPM)", "MOVE TO MIX CHAMBER", "MIX SAMPLE", "ACCELERATION TO READ CHECK 2 (5000RPM to 1500RPM)", "ACCELERATION TO READ CHECK 2 OVERSHOOT", "READ CHECK 2", \
                "ACCELERATION TO PRIME S3 (1500RPM to 0RPM)", "ACCELERATION TO PRIME S3 OVERSHOOT", "ACCELERATION TO DISTRIBUTE CHEMISTRIES (0RPM to 3000RPM)", "ACCELERATION TO DISTRIBUTE CHEMISTRIES OVERSHOOT", \
                "ACCELERATION TO DISTRIBUTE CHEMISTRIES (3000RPM to 4000RPM)", "DISTRIBUTE CHEMISTRIES", "ACCELERATION TO READ CHECK 3 (4000RPM to 1500RPM)", "ACCELERATION TO READ CHECK 3 OVERSHOOT", "READ CHECK 3", \
                "MIX CHEMISTRIES", "ACCLERATION TO READ (1000RPM to 1500RPM)", "READ", "END"]
            
    phase_stats = [SpindleMotorPhaseStats(0,  False, 100),    # BARCODE
                   SpindleMotorPhaseStats(1,  True, -3000),   # ACCELERATION TO SEPARATE (0RPM to -3000RPM)
                   SpindleMotorPhaseStats(2,  True, -850),    # ACCELERATION TO SEPARATE (-3000RPM to -5500RPM)
                   SpindleMotorPhaseStats(3,  False,-5500),   # SEPARATE
                   SpindleMotorPhaseStats(4,  True,  3000),   # ACCELERATION TO PRIME S1/S2 (-5500RPM to 0RPM)
                   SpindleMotorPhaseStats(5,  False, 100),    # ACCELERATION TO PRIME S1/S2 OVERSHOOT
                   SpindleMotorPhaseStats(6,  False, 100),    # UNNAMED
                   SpindleMotorPhaseStats(7,  True,  3000),   # ACCELERATION TO READ CHECK 1 (100RPM to 1500RPM)
                   SpindleMotorPhaseStats(8,  False, 1500),   # ACCELERATION TO READ CHECK 1 OVERSHOOT
                   SpindleMotorPhaseStats(9,  False, 1500),   # READ CHECK 1
                   SpindleMotorPhaseStats(10, True,  3000),   # ACCELERATION TO MIX CHAMBER (1500RPM to 4000RPM)
                   SpindleMotorPhaseStats(11, False, 4000),   # ACCELERATION TO MIX CHAMBER OVERSHOOT
                   SpindleMotorPhaseStats(12, True,  500),    # ACCELERATION TO MIX CHAMBER (4000RPM to 5000RPM)
                   SpindleMotorPhaseStats(13, False, 5000),   # MOVE TO MIX CHAMBER
                   SpindleMotorPhaseStats(14, False),         # MIX SAMPLE
                   SpindleMotorPhaseStats(15, True, -3000),   # ACCELERATION TO READ CHECK 2 (5000RPM to 1500RPM)
                   SpindleMotorPhaseStats(16, False, 1500),   # ACCELERATION TO READ CHECK 2 OVERSHOOT
                   SpindleMotorPhaseStats(17, False, 1500),   # READ CHECK 2
                   SpindleMotorPhaseStats(18, True,  -750),   # ACCELERATION TO PRIME S3 (1500RPM to 0RPM)
                   SpindleMotorPhaseStats(19, False, 0),      # ACCELERATION TO PRIME S3 OVERSHOOT
                   SpindleMotorPhaseStats(20, True,  3000),   # ACCELERATION TO DISTRIBUTE CHEMISTRIES (0RPM to 3000RPM)
                   SpindleMotorPhaseStats(21, False, 3000),   # ACCELERATION TO DISTRIBUTE CHEMISTRIES OVERSHOOT
                   SpindleMotorPhaseStats(22, True,  900),    # ACCELERATION TO DISTRIBUTE CHEMISTRIES (3000RPM to 4000RPM)
                   SpindleMotorPhaseStats(23, False, 4000),   # DISTRIBUTE CHEMISTRIES
                   SpindleMotorPhaseStats(24, True, -3200),   # ACCELERATION TO READ CHECK 3 (4000RPM to 1500RPM)
                   SpindleMotorPhaseStats(25, False, 1500),   # ACCELERATION TO READ CHECK 3 OVERSHOOT
                   SpindleMotorPhaseStats(26, False, 1500),   # READ CHECK 3
                   SpindleMotorPhaseStats(27, False),         # MIX CHEMISTRIES
                   SpindleMotorPhaseStats(28, True,  2000),   # ACCELERATION TO READ (1000RPM to 1500RPM)
                   SpindleMotorPhaseStats(29, False, 1500)    # READ
                   ]
    
    
else:
    min_val = 1000000000.0
    max_val = -1000000000.0
    all_vals = []

EXP_VAL = 0.0

for file in file_list:
    try:
        fileIn = open(file, 'rt')
    except:
        print("Could not open %s" % file)
        continue

    match TYPE:
        case "BeakDelay":
                line = fileIn.readline()

                while "Global Cuvette Delay" not in line:
                    line = fileIn.readline()

                line = [l.strip() for l in line.split()]
                EXP_VAL = int(line[4])

                while "1   0" not in line:
                    line = fileIn.readline()

                line = [l.strip() for l in line.split()]

                while len(line) > 0:
                    all_vals.append(float(line[6]))
                    line = fileIn.readline()
                    line = [l.strip() for l in line.split()]
            
        case "IntTiming":
            EXP_VAL = 100

            line = fileIn.readline()

            while "Global Cuvette Delay" not in line:
                line = fileIn.readline()

            while "1   0" not in line:
                line = fileIn.readline()

            line = [l.strip() for l in line.split()]

            while len(line) > 0:
                all_vals.append(float(line[4]))
                line = fileIn.readline()
                line = [l.strip() for l in line.split()]

        case "OffsetTiming":
            EXP_VAL = 0.0

            line = fileIn.readline()

            while "Global Cuvette Delay" not in line:
                line = fileIn.readline()

            while "1   0" not in line:
                line = fileIn.readline()

            line = [l.strip() for l in line.split()]

            while len(line) > 0:
                all_vals.append(float(line[7]))
                line = fileIn.readline()
                line = [l.strip() for l in line.split()]

        case "HoldTiming":
            EXP_VAL = 700 # us

            line = fileIn.readline()

            while "Global Cuvette Delay" not in line:
                line = fileIn.readline()

            while "1   0" not in line:
                line = fileIn.readline()

            line = [l.strip() for l in line.split()]

            while len(line) > 0:
                all_vals.append(float(line[5]) - float(line[4]))
                line = fileIn.readline()
                line = [l.strip() for l in line.split()]

        case "SpindleMotorSpeeds":
            
            line = fileIn.readline()

            phase_idx = 0

            while line:                
                if phases[phase_idx] in line:
                    if phase_idx < len(phases)-1 and phase_idx != 29:
                        phase_idx += 1

                else:
                    # Mix Sample
                    if phase_idx == 15:
                        rpm_range = "5000RPM->1000RPM"

                        while "**END OF MIX SAMPLE**" not in line and line and phase_idx == 15:
                            if "5000RPM->1000RPM" in line:
                                rpm_range = "5000RPM->1000RPM"
                            elif "1000RPM->4000RPM" in line:
                                rpm_range = "1000RPM->4000RPM"
                            elif "4000RPM->5000RPM" in line:
                                rpm_range = "4000RPM->5000RPM"

                            line = [l.strip() for l in line.split()]

                            if "Min" in line:
                                phase_stats[phase_idx-1].updateMixMin(rpm_range, float(line[2]))
                            elif "Max" in line:
                                phase_stats[phase_idx-1].updateMixMax(rpm_range, float(line[2]))
                            elif "Avg" in line:
                                phase_stats[phase_idx-1].updateMixAvgs(rpm_range, float(line[2]))
                            elif "Std" in line:
                                phase_stats[phase_idx-1].updateMixStDevs(rpm_range, float(line[2]))
                            elif "Slope:" in line:
                                phase_stats[phase_idx-1].updateMixSlopes(rpm_range, float(line[1]))

                            line = fileIn.readline()
                            if "**END OF MIX SAMPLE**" in line:
                                phase_idx += 1
                                line = fileIn.readline()

                    # Mix Chemistries
                    elif phase_idx == 28:
                        rpm_range = "1900RPM->1000RPM"

                        while "**END OF MIX CHEMISTRIES**" not in line and line and phase_idx == 28:
                            if "1900RPM->1000RPM" in line:
                                rpm_range = "1900RPM->1000RPM"
                            elif "1000RPM->1000RPM" in line:
                                rpm_range = "1000RPM->1000RPM"
                            elif "1000RPM->-1900RPM" in line:
                                rpm_range = "1000RPM->-1900RPM"
                            elif "-1900RPM->-1000RPM" in line:
                                rpm_range = "-1900RPM->-1000RPM"
                            elif "-1000RPM->-1000RPM" in line:
                                rpm_range = "-1000RPM->-1000RPM"
                            elif "-1000RPM->1900RPM" in line:
                                rpm_range = "-1000RPM->1900RPM"

                            line = [l.strip() for l in line.split()]

                            if "Min" in line:
                                phase_stats[phase_idx-1].updateMixMin(rpm_range, float(line[2]))
                            elif "Max" in line:
                                phase_stats[phase_idx-1].updateMixMax(rpm_range, float(line[2]))
                            elif "Avg" in line:
                                phase_stats[phase_idx-1].updateMixAvgs(rpm_range, float(line[2]))
                            elif "Std" in line:
                                phase_stats[phase_idx-1].updateMixStDevs(rpm_range, float(line[2]))
                            elif "Slope:" in line:
                                phase_stats[phase_idx-1].updateMixSlopes(rpm_range, float(line[1]))

                            line = fileIn.readline()
                            if "**END OF MIX CHEMISTRIES**" in line:
                                phase_idx += 1
                                line = fileIn.readline()

                    # ACCELERATION TO READ (1000RPM to 1500RPM)
                    # Note: need to do this because the phases were changing from this
                    # phase to READ because "READ" is in this line technically
                    elif phase_idx == 29:
                        while "READ" not in line and line:
                            line = [l.strip() for l in line.split()]
                            # Check if acceleration
                            if phase_stats[phase_idx-1].acceleration:
                                if "Slope:" in line:
                                    phase_stats[phase_idx-1].updateSlopes(float(line[1]))

                            if "Min" in line:
                                phase_stats[phase_idx-1].updateMin(float(line[2]))
                            elif "Max" in line:
                                phase_stats[phase_idx-1].updateMax(float(line[2]))
                            elif "Avg" in line:
                                phase_stats[phase_idx-1].updateAvgs(float(line[2]))
                            elif "Std" in line:
                                phase_stats[phase_idx-1].updateStDevs(float(line[2]))
                            line = fileIn.readline()
                            if "READ" in line:
                                line = fileIn.readline()
                                phase_idx += 1

                    line = [l.strip() for l in line.split()]

                    # Check if acceleration
                    if phase_stats[phase_idx-1].acceleration:
                        if "Slope:" in line:
                            phase_stats[phase_idx-1].updateSlopes(float(line[1]))
                    
                    if "Min" in line:
                        phase_stats[phase_idx-1].updateMin(float(line[2]))
                    elif "Max" in line:
                        phase_stats[phase_idx-1].updateMax(float(line[2]))
                    elif "Avg" in line:
                        phase_stats[phase_idx-1].updateAvgs(float(line[2]))
                    elif "Std" in line:
                        phase_stats[phase_idx-1].updateStDevs(float(line[2]))
                        
                line = fileIn.readline()

        case "Temperature":
            pass

    fileIn.close()

if TYPE == "SpindleMotorSpeeds":
    for i in range(len(phase_stats)):
        print(phases[i])

        # Mix Sample
        if i == 14:
            print("5000RPM->1000RPM")
            print("  Min = %.5f" % np.min(phase_stats[i].P5000toP1000_avgs))
            print("  Max = %.5f" % np.max(phase_stats[i].P5000toP1000_avgs))
            print("  Avg = %.5f" % np.mean(phase_stats[i].P5000toP1000_avgs))
            print("  Std = %.5f" % np.std(phase_stats[i].P5000toP1000_avgs))
            print("  Slope = %.5f" % np.mean(phase_stats[i].P5000toP1000_slopes))
            print("    Exp = %.5f" % phase_stats[i].P5000toP1000_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].P5000toP1000_slopes)-phase_stats[i].P5000toP1000_exp))
            print("    Error = %.5f%%" % (((np.mean(phase_stats[i].P5000toP1000_slopes)-phase_stats[i].P5000toP1000_exp)/phase_stats[i].P5000toP1000_exp)*100))

            print("1000RPM->4000RPM")
            print("  Min = %.5f" % np.min(phase_stats[i].P1000toP4000_avgs))
            print("  Max = %.5f" % np.max(phase_stats[i].P1000toP4000_avgs))
            print("  Avg = %.5f" % np.mean(phase_stats[i].P1000toP4000_avgs))
            print("  Std = %.5f" % np.std(phase_stats[i].P1000toP4000_avgs))
            print("  Slope = %.5f" % np.mean(phase_stats[i].P1000toP4000_slopes))
            print("    Exp = %.5f" % phase_stats[i].P1000toP4000_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].P1000toP4000_slopes)-phase_stats[i].P1000toP4000_exp))
            print("    Error = %.5f%%" % (((np.mean(phase_stats[i].P1000toP4000_slopes)-phase_stats[i].P1000toP4000_exp)/phase_stats[i].P1000toP4000_exp) * 100))

            print("4000RPM->5000RPM")
            print("  Min = %.5f" % np.min(phase_stats[i].P4000toP5000_avgs))
            print("  Max = %.5f" % np.max(phase_stats[i].P4000toP5000_avgs))
            print("  Avg = %.5f" % np.mean(phase_stats[i].P4000toP5000_avgs))
            print("  Std = %.5f" % np.std(phase_stats[i].P4000toP5000_avgs))
            print("  Slope = %.5f" % np.mean(phase_stats[i].P4000toP5000_slopes))
            print("    Exp = %.5f" % phase_stats[i].P4000toP5000_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].P4000toP5000_slopes)-phase_stats[i].P4000toP5000_exp))
            print("    Error = %.5f%%" % (((np.mean(phase_stats[i].P4000toP5000_slopes)-phase_stats[i].P4000toP5000_exp)/phase_stats[i].P4000toP5000_exp)*100))

        # Mix Chemistries
        elif i == 27:
            print("1900RPM->1000RPM")
            print("  Min = %.5f" % np.min(phase_stats[i].P1900toP1000_avgs))
            print("  Max = %.5f" % np.max(phase_stats[i].P1900toP1000_avgs))
            print("  Avg = %.5f" % np.mean(phase_stats[i].P1900toP1000_avgs))
            print("  Std = %.5f" % np.std(phase_stats[i].P1900toP1000_avgs))
            print("  Slope = %.5f" % np.mean(phase_stats[i].P1900toP1000_slopes))
            print("    Exp = %.5f" % phase_stats[i].P1900toP1000_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].P1900toP1000_slopes)-phase_stats[i].P1900toP1000_exp))
            print("    Error = %.5f%%" % (((np.mean(phase_stats[i].P1900toP1000_slopes)-phase_stats[i].P1900toP1000_exp)/phase_stats[i].P1900toP1000_exp)*100))

            print("1000RPM->1000RPM")
            print("  Min = %.5f" % phase_stats[i].P1000toP1000_min)
            print("  Max = %.5f" % phase_stats[i].P1000toP1000_max)
            print("  Avg = %.5f" % np.mean(phase_stats[i].P1000toP1000_avgs))
            print("  Std = %.5f" % np.mean(phase_stats[i].P1000toP1000_stdevs))
            print("    Exp = %.5f" % phase_stats[i].P1000toP1000_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].P1000toP1000_avgs)-phase_stats[i].P1000toP1000_exp))
            print("    Error = %.5f%%" % (((np.mean(phase_stats[i].P1000toP1000_avgs)-phase_stats[i].P1000toP1000_exp)/phase_stats[i].P1000toP1000_exp)*100))

            print("1000RPM->-1900RPM")
            print("  Min = %.5f" % np.min(phase_stats[i].P1000toN1900_avgs))
            print("  Max = %.5f" % np.max(phase_stats[i].P1000toN1900_avgs))
            print("  Avg = %.5f" % np.mean(phase_stats[i].P1000toN1900_avgs))
            print("  Std = %.5f" % np.std(phase_stats[i].P1000toN1900_avgs))
            print("  Slope = %.5f" % np.mean(phase_stats[i].P1000toN1900_slopes))
            print("    Exp = %.5f" % phase_stats[i].P1000toN1900_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].P1000toN1900_slopes)-phase_stats[i].P1000toN1900_exp))
            print("    Error = %.5f%%" % (((np.mean(phase_stats[i].P1000toN1900_slopes)-phase_stats[i].P1000toN1900_exp)/phase_stats[i].P1000toN1900_exp)*100))

            print("-1900RPM->-1000RPM")
            print("  Min = %.5f" % np.min(phase_stats[i].N1900toN1000_avgs))
            print("  Max = %.5f" % np.max(phase_stats[i].N1900toN1000_avgs))
            print("  Avg = %.5f" % np.mean(phase_stats[i].N1900toN1000_avgs))
            print("  Std = %.5f" % np.std(phase_stats[i].N1900toN1000_avgs))
            print("  Slope = %.5f" % np.mean(phase_stats[i].N1900toN1000_slopes))
            print("    Exp = %.5f" % phase_stats[i].N1900toN1000_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].N1900toN1000_slopes)-phase_stats[i].N1900toN1000_exp))
            print("    Error = %.5f%%" % (100*(np.mean(phase_stats[i].N1900toN1000_slopes)-phase_stats[i].N1900toN1000_exp)/phase_stats[i].N1900toN1000_exp))

            print("-1000RPM->-1000RPM")
            print("  Min = %.5f" % phase_stats[i].N1000toN1000_min)
            print("  Max = %.5f" % phase_stats[i].N1000toN1000_max)
            print("  Avg = %.5f" % np.mean(phase_stats[i].N1000toN1000_avgs))
            print("  Std = %.5f" % np.mean(phase_stats[i].N1000toN1000_stdevs))
            print("    Exp = %.5f" % phase_stats[i].N1000toN1000_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].N1000toN1000_avgs)-phase_stats[i].N1000toN1000_exp))
            print("    Error = %.5f%%" % (((np.mean(phase_stats[i].N1000toN1000_avgs)-phase_stats[i].N1000toN1000_exp)/phase_stats[i].N1000toN1000_exp) * 100))

            print("-1000RPM->1900RPM")
            print("  Min = %.5f" % np.min(phase_stats[i].N1000toP1900_avgs))
            print("  Max = %.5f" % np.max(phase_stats[i].N1000toP1900_avgs))
            print("  Avg = %.5f" % np.mean(phase_stats[i].N1000toP1900_avgs))
            print("  Std = %.5f" % np.std(phase_stats[i].N1000toP1900_avgs))
            print("  Slope = %.5f" % np.mean(phase_stats[i].N1000toP1900_slopes))
            print("    Exp = %.5f" % phase_stats[i].N1000toP1900_exp)
            print("    Offset = %.5f" % (np.mean(phase_stats[i].N1000toP1900_slopes)-phase_stats[i].N1000toP1900_exp))
            print("    Error = %.5f%%" % (100*(np.mean(phase_stats[i].N1000toP1900_slopes)-phase_stats[i].N1000toP1900_exp)/phase_stats[i].N1000toP1900_exp))

        # All others
        elif phase_stats[i].exp_value != None and len(phase_stats[i].avgs) > 0:
            if phase_stats[i].acceleration:
                print("Min = %.5f" % np.min(phase_stats[i].avgs))
                print("Max = %.5f" % np.max(phase_stats[i].avgs))
                print("Avg = %.5f" % np.mean(phase_stats[i].avgs))
                print("Std = %.5f" % np.std(phase_stats[i].avgs))
                print("Slope = %.5f" % np.mean(phase_stats[i].slopes))
                print("  Exp = %.5f" % phase_stats[i].exp_value)
                print("  Offset = %.5f" % (np.mean(phase_stats[i].slopes)-phase_stats[i].exp_value))
                print("  Error = %.5f%%" % (100*(np.mean(phase_stats[i].slopes)-phase_stats[i].exp_value)/phase_stats[i].exp_value))
            
            else:
                print("Min = %.5f" % phase_stats[i].min)
                print("Max = %.5f" % phase_stats[i].max)
                print("Avg = %.5f" % np.mean(phase_stats[i].avgs))
                print("Std = %.5f" % np.std(phase_stats[i].avgs))
                print("  Exp = %.5f" % phase_stats[i].exp_value)
                print("  Offset = %.5f" % (np.mean(phase_stats[i].avgs)-phase_stats[i].exp_value))
                print("  Error = %.5f%%" % (100*(np.mean(phase_stats[i].avgs)-phase_stats[i].exp_value)/phase_stats[i].exp_value))
            
        print("\n")
    sys.exit(0)

print("%s\n" % TYPE)
print("Exp = %.5f" % EXP_VAL)
print("Min = %.5f" % np.min(all_vals))
print("Max = %.5f" % np.max(all_vals))
print("Avg = %.5f" % np.mean(all_vals))
print("Std = %.5f" % np.std(all_vals))
print("\n")
print("Offset = %.5f" % (np.mean(all_vals)-EXP_VAL))
if TYPE != "OffsetTiming":
    print("Error = %.5f%%" % ((((np.mean(all_vals)-EXP_VAL))/EXP_VAL)*100))


### DO THE MIX CHEMISTRIES THE SAME AS MIX SAMPLE :/
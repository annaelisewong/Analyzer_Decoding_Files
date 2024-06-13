import csv

# Variables!!!!
ANALOG_GAIN         = 2.375
ADC_REF             = 2.048
POWER_SUPPLY_CH1    = 0.018         # V
POWER_SUPPLY_CH2    = 0.09          # V
POWER_SUPPLY_CH3    = 0.169          # V
DAC_GAIN_MAX        = 1
DAC_GAIN_80_PERCENT = 0.8
DAC_GAIN_40_PERCENT = 0.4
ADC_REF_MAX         = 7864320
INT_RC              = 0.000027336
INT_TIME            = 0.0001        # s

# Create output file
outfilename = "ADCPhoTargetValues.csv"

print("Output file: %s" % outfilename)

name = []
targetV = []
targetADCCount = []

with open(outfilename,'wt', newline='') as myfile:
    wrtr = csv.writer(myfile, delimiter=',', quotechar='"')

#--------------------------------------------------------------------------------------#

    # Test 1

    ch0_targetV = POWER_SUPPLY_CH1 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))
    ch3_targetV = POWER_SUPPLY_CH2 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))
    ch7_targetV = POWER_SUPPLY_CH3 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))

    ch0_targetADCCount = ch0_targetV * ADC_REF_MAX / ADC_REF
    ch3_targetADCCount = ch3_targetV * ADC_REF_MAX / ADC_REF
    ch7_targetADCCount = ch7_targetV * ADC_REF_MAX / ADC_REF

    name.append(["Test #1"])
    targetV.append([ch0_targetV, "", ch3_targetV, "", ch7_targetV])
    targetADCCount.append([round(ch0_targetADCCount), "", round(ch3_targetADCCount), "", round(ch7_targetADCCount)])

#--------------------------------------------------------------------------------------#

    # Test 2

    ch0_targetV = POWER_SUPPLY_CH1 * ANALOG_GAIN * DAC_GAIN_80_PERCENT * (1 + (INT_TIME / INT_RC))
    ch3_targetV = POWER_SUPPLY_CH2 * ANALOG_GAIN * DAC_GAIN_80_PERCENT * (1 + (INT_TIME / INT_RC))
    ch7_targetV = POWER_SUPPLY_CH3 * ANALOG_GAIN * DAC_GAIN_80_PERCENT * (1 + (INT_TIME / INT_RC))

    ch0_targetADCCount = ch0_targetV * ADC_REF_MAX / ADC_REF
    ch3_targetADCCount = ch3_targetV * ADC_REF_MAX / ADC_REF
    ch7_targetADCCount = ch7_targetV * ADC_REF_MAX / ADC_REF

    name.append(["Test #2"])
    targetV.append([ch0_targetV, "", ch3_targetV, "", ch7_targetV])
    targetADCCount.append([round(ch0_targetADCCount), "", round(ch3_targetADCCount), "", round(ch7_targetADCCount)])

#--------------------------------------------------------------------------------------#

    # Test 3

    ch0_targetV = POWER_SUPPLY_CH1 * ANALOG_GAIN * DAC_GAIN_40_PERCENT * (1 + (INT_TIME / INT_RC))
    ch3_targetV = POWER_SUPPLY_CH2 * ANALOG_GAIN * DAC_GAIN_40_PERCENT * (1 + (INT_TIME / INT_RC))
    ch7_targetV = POWER_SUPPLY_CH3 * ANALOG_GAIN * DAC_GAIN_40_PERCENT * (1 + (INT_TIME / INT_RC))

    ch0_targetADCCount = ch0_targetV * ADC_REF_MAX / ADC_REF
    ch3_targetADCCount = ch3_targetV * ADC_REF_MAX / ADC_REF
    ch7_targetADCCount = ch7_targetV * ADC_REF_MAX / ADC_REF

    name.append(["Test #3"])
    targetV.append([ch0_targetV, "", ch3_targetV, "", ch7_targetV])
    targetADCCount.append([round(ch0_targetADCCount), "", round(ch3_targetADCCount), "", round(ch7_targetADCCount)])

#--------------------------------------------------------------------------------------#

    # Test 4

    ch0_targetV = POWER_SUPPLY_CH2 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))
    ch3_targetV = POWER_SUPPLY_CH3 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))
    ch7_targetV = POWER_SUPPLY_CH1 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))

    ch0_targetADCCount = ch0_targetV * ADC_REF_MAX / ADC_REF
    ch3_targetADCCount = ch3_targetV * ADC_REF_MAX / ADC_REF
    ch7_targetADCCount = ch7_targetV * ADC_REF_MAX / ADC_REF

    name.append(["Test #4"])
    targetV.append([ch0_targetV, "", ch3_targetV, "", ch7_targetV])
    targetADCCount.append([round(ch0_targetADCCount), "", round(ch3_targetADCCount), "", round(ch7_targetADCCount)])

#--------------------------------------------------------------------------------------#

    # Test 5
    
    ch0_targetV = POWER_SUPPLY_CH3 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))
    ch3_targetV = POWER_SUPPLY_CH1 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))
    ch7_targetV = POWER_SUPPLY_CH2 * ANALOG_GAIN * DAC_GAIN_MAX * (1 + (INT_TIME / INT_RC))

    ch0_targetADCCount = ch0_targetV * ADC_REF_MAX / ADC_REF
    ch3_targetADCCount = ch3_targetV * ADC_REF_MAX / ADC_REF
    ch7_targetADCCount = ch7_targetV * ADC_REF_MAX / ADC_REF

    name.append(["Test #5"])
    targetV.append([ch0_targetV, "", ch3_targetV, "", ch7_targetV])
    targetADCCount.append([round(ch0_targetADCCount), "", round(ch3_targetADCCount), "", round(ch7_targetADCCount)])

#--------------------------------------------------------------------------------------#

    for n, v, ct in zip(name, targetV, targetADCCount):
            wrtr.writerow(n)
            wrtr.writerow(v)
            wrtr.writerow(ct)
            wrtr.writerow("\n")
# Semi-automated regression testing
# Runs decoding scripts against .sal files and looks at the outputs of those scripts.

import os
import csv
import sys
import subprocess

# Create the Exports and Reports folders
if not os.path.exists(".\\Exports\\"):
    os.makedirs(".\\Exports\\")

if not os.path.exists(".\\Reports\\"):
    os.makedirs(".\\Reports\\")

# Export data from .sal files
print("\n* export_digital_csv.py\n")
p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\export_digital_csv.py"])
p.wait()

# Get the files and rotor_name list
file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group0.csv" in filename]
rotor_names = []
for file in file_list:
    # NOTE: don't know if I need to change Exports to Reports here, or if it is fine in spi_pho/u18_raw3.py for now, since spi_pho/u18_raw3 needs the .csv file
    rotor_names.append(file.replace("_Group0.csv", ""))

# Start a reports tracking file
status_tracker = open(".\\Reports\\status_tracker.csv", "wt")
statuswriter = csv.writer(status_tracker, delimiter = ' ')
titles = ['Script'] + rotor_names
statuswriter.writerow(titles)

# # spi_pho_raw3.py
# print("\n\n* spi_pho_raw3.py\n")
# file_count = 0
# status = []
# for rotor_name in rotor_names:
#     file_count += 1
#     print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
#     result = subprocess.run(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\spi_pho_raw3.py", "-r", rotor_name, "-a", "Serial"], capture_output=False, text=True)
#     if result != 0:
#         status.append("no")
#     else:
#         status.append("yes")
#     # p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\spi_pho_raw3.py", "-r", rotor_name, "-a", "Serial"])
#     # p.wait()
# statuswriter.writerow(status)
# status_tracker.close()
# sys.exit(0)

# # pc104decode3.py
# print("\n* pc104decode3.py\n")
# file_count = 0
# for rotor_name in rotor_names:
#     file_count += 1
#     print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
#     p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\pc104decode3.py", "-r", rotor_name])
#     p.wait()

# # Ris_File_Dump.py
# print("\n* Ris_File_Dump.py\n")
# file_count = 0
# for rotor_name in rotor_names:
#     file_count += 1
#     print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
#     p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\Ris_File_Dump.py", "-r", rotor_name])
#     p.wait()

# # spi_u18_raw3.py
# print("\n* spi_u18_raw3.py\n")
# file_count = 0
# for rotor_name in rotor_names:
#     file_count += 1
#     print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
#     p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\spi_u18_raw3.py", "-r", rotor_name, "-a"])
#     p.wait()

# # motcmd3.py
# print("\n* motcmd3.py\n")
# file_count = 0
# for rotor_name in rotor_names:
#     file_count += 1
#     print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
#     p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\motcmd3.py", "-r", rotor_name])
#     p.wait()

# pho_raw_beak.py
print("\n* pho_raw_beak.py\n")
# file_count = 0
# for rotor_name in rotor_names:
    # file_count += 1
    # print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\RunAll_pho_raw_beak.py"])
p.wait()

# extract_beak_timing_stats.py
print("\n* extract_beak_timing_stats.py\n")
file_count = 0
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_beak_timing_stats.py", "-r", rotor_name])
    p.wait()

# extract_beak_offset_stats.py
print("\n* extract_beak_offset_stats.py\n")
file_count = 0
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_beak_offset_stats.py", "-r", rotor_name])
    p.wait()

# extract_hold_time_stats.py
print("\n* extract_hold_time_stats.py\n")
file_count = 0
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_hold_time_stats.py", "-r", rotor_name])
    p.wait()

# extract_phase_timestamps.py
print("\n* extract_phase_timestamps.py\n")
file_count = 0
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_phase_timestamps.py", "-r", rotor_name])
    p.wait()

# extract_temps.py
print("\n* extract_temps.py\n")
file_count = 0
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    p = subprocess.Popen(["python3", "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\extract_temps.py", "-r", rotor_name, "-o"])
    p.wait()
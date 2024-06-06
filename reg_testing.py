# Semi-automated regression testing
# Runs decoding scripts against .sal files and looks at the outputs of those scripts.

import os
import csv
import subprocess

# Create a variable to make it easier for other people to use the script
script_path = "C:\\Users\\awong\\Documents\\Analyzer_Decoding_Files\\"

# # Create the Exports and Reports folders
# if not os.path.exists(".\\Exports\\"):
#     os.makedirs(".\\Exports\\")

# if not os.path.exists(".\\Reports\\"):
#     os.makedirs(".\\Reports\\")

# Export data from .sal files
print("\n* export_digital_csv.py\n")
p = subprocess.Popen(["python3", script_path + "export_digital_csv.py"])
p.wait()

# Get the files and rotor_name list
file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "Group0.csv" in filename]
rotor_names = []
for file in file_list:
    rotor_names.append(file.replace("_Group0.csv", ""))

# Start a reports tracking file
status_tracker = open("status_tracker.csv", "wt")
statuswriter = csv.writer(status_tracker, delimiter = ',')
titles = ['Script Names'] + [os.path.basename(rotor_name) for rotor_name in rotor_names]
statuswriter.writerow(titles)

# spi_pho_raw3.py
print("\n\n* spi_pho_raw3.py\n")
file_count = 0
status = ["spi_pho_raw3.py"]
for rotor_name in rotor_names:
    # Make sure Results folder exists
    if not os.path.exists(os.path.dirname(rotor_name).replace("Exports", "Reports")):
        os.makedirs(os.path.dirname(rotor_name).replace("Exports", "Reports"))

    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "spi_pho_raw3.py", "-r", rotor_name, "-a", "Serial"], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# pc104decode3.py
print("\n* pc104decode3.py\n")
file_count = 0
status = ["pc104decode3.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "pc104decode3.py", "-r", rotor_name], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# Ris_File_Dump.py
print("\n* Ris_File_Dump.py\n")
file_count = 0
status = ["Ris_File_Dump.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "Ris_File_Dump.py", "-r", rotor_name], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# spi_u18_raw3.py
print("\n* spi_u18_raw3.py\n")
file_count = 0
status = ["spi_u18_raw3.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "spi_u18_raw3.py", "-r", rotor_name, "-a"], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# motcmd3.py
print("\n* motcmd3.py\n")
file_count = 0
status = ["motcmd3.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "motcmd3.py", "-r", rotor_name], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# pho_raw_beak.py
print("\n* pho_raw_beak.py\n")
file_count = 0
status = ["pho_raw_beak.py"]
result = subprocess.run(["python3", script_path + "RunAll_pho_raw_beak.py"], capture_output=False, text=True)
# if result.returncode != 0:
#     status.append("no")
# else:
#     status.append("yes")
statuswriter.writerow(status)

# extract_beak_timing_stats.py
print("\n* extract_beak_timing_stats.py\n")
file_count = 0
status = ["extract_beak_timing_stats.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "extract_beak_timing_stats.py", "-r", rotor_name, "-o"], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# extract_beak_offset_stats.py
print("\n* extract_beak_offset_stats.py\n")
file_count = 0
status = ["extract_beak_offset_stats.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "extract_beak_offset_stats.py", "-r", rotor_name, "-o"], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# extract_hold_time_stats.py
print("\n* extract_hold_time_stats.py\n")
file_count = 0
status = ["extract_hold_time_stats.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "extract_hold_time_stats.py", "-r", rotor_name, "-o"], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# extract_phase_timestamps.py
print("\n* extract_phase_timestamps.py\n")
file_count = 0
status = ["extract_phase_timestamps.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "extract_phase_timestamps.py", "-r", rotor_name], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)

# extract_temps.py
print("\n* extract_temps.py\n")
file_count = 0
status = ["extract_temps.py"]
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "extract_temps.py", "-r", rotor_name, "-o", "-s", "-t"], capture_output=False, text=True)
    if result.returncode != 0:
        status.append("no")
    else:
        status.append("yes")
statuswriter.writerow(status)
status_tracker.close()

# compare_tolerances.py
print("\n* compare_tolerances.py")
file_count = 0
outfilename = "ToleranceComparisonOut.txt"
fileOut = open(outfilename, "wt")
for rotor_name in rotor_names:
    file_count += 1
    print("  (%d/%d) Input file prefix: %s" % (file_count, len(rotor_names), rotor_name))
    result = subprocess.run(["python3", script_path + "compare_tolerances.py", "-r", rotor_name, "-t", script_path + "Tolerances.csv"], capture_output=False, text=True)
import sys
import os
import time
import csv
from enum import Enum
from pathlib import Path

"""
DESCRIPTION OF FUNCTIONALITY

Reads in lines from MsgOut.txt file and cycles through a state machin of different states pertaining 
to the expected serial protocol.

"WAIT_FOR_X" states occur when there is only one acceptable byte that needs to be received. With the 
exception of some ENQ data, these bytes do not need to be saved.

"GET_X" states occur when there are multiple bytes of data that can/need to be received. These bytes are 
typically saved as they are important in later states.

If an expected/acceptable byte does not occur where it should, an error state is entered. An error_info 
array is filled out which contains information about the type of error, what state the error occurred in, 
and what line the error occurred at. Within this error state, this information is printed to the terminal/
output file.

In order to escape the error state, the file is read until a line with "ENQ" is found. The number of lines 
read through from the error line to the new line to process is recorded for the user to see. The purpose
behind this is that when searching for a new "ENQ" line, there is a possibility that other errors are 
occurring between those two lines that will not be recorded. It is difficult to capture these errors because
you might not know what state you are returning to if you were to pick up with the next line of the file, 
rather than finding the next "ENQ" and starting the state machine over.

TODO:
- determine a way to capture all errors, not just the starts of errors
- in situations where there are multiple messages between an ENQ/EOT pair, if an error occurs within one 
    message, should the error state find the next ENQ, or should it try to find the start of the next message?
    NOTE: I did attempt to do this, but for some reason there were other errors that occurred when I put in 
    the "find STX or ENQ" clause of the while loop. To be looked into further
- determine why the error state sometimes gets stuck on "WAIT_FOR_CR" errors unless it has it's own if statement 
    in the error state. As far as I know, there is nothing that is different about that statement than the 
    catchall statement.
- put any repetitive code into a helper function so that all changes to that code can be made in one place
"""

DIR_IN  = "in"
DIR_OUT = "out"

#----------------------------------------------------------------------#
## Enums ##

s = Enum('State', ['WAIT_FOR_ENQ', 'WAIT_FOR_BEG_ACK', 'WAIT_FOR_STX',
                       'WAIT_FOR_MAGIC_1', 'GET_LETTERS', 'GET_LEN',
                       'GET_PAYLOAD', 'GET_CHECKSUM', 'WAIT_FOR_CR', 'WAIT_FOR_LF',
                       'WAIT_FOR_END_ACK', 'WAIT_FOR_EOT_OR_STX', 'ERROR', 'EOF'])

#----------------------------------------------------------------------#
## Helper Functions ##

def openFile(infilename, utf16le=False):
    # NOTE: This is a hack. The files shouldn't be encoded when they are
    # opened, but for some reason some of them are.
    if utf16le:
        try:
            print("had to open file with encoding")
            fileIn = open(infilename, 'rt', encoding='utf_16_le')
        except:
            print("Could not open input file %s" % (infilename))
            sys.exit(1)
    else:
        try:
            fileIn = open(infilename, 'rt')
        except:
            print("Could not open input file %s" % (infilename))
            sys.exit(1)
    return fileIn

def endOfFileCheck(line):
    if len(line) == 0 or line == "------------------------------------------------------------\n" or "Summary" in line: 
        return True
    return False

#----------------------------------------------------------------------#
## Class ##

class SerialProtocolParse():

    def __init__(self):
        self.total_errors = 0
        self.resetVariables()
        
    def resetVariables(self):
        self.state = s.WAIT_FOR_ENQ
        self.direction = DIR_IN
        self.payload_length = 0
        self.num_payload_bytes = 0
        self.letters = []
        self.checksum = []
        self.error_info = []

        self.enq_time = 0
    
    # Returns the updated state
    def stateMachine(self, line, fileIn):

        match self.state:
            case s.WAIT_FOR_ENQ:
                if "ENQ" not in line:
                    self.error_info = ["ERROR: Expected ENQ.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                
                if "in" in line: self.direction = DIR_IN
                else: self.direction = DIR_OUT

                line = line.split()
                line = [l.strip() for l in line]
                self.enq_time = float(line[0])
                self.state = s.WAIT_FOR_BEG_ACK

            case s.WAIT_FOR_BEG_ACK:
                if "ACK" not in line:
                    self.error_info = ["ERROR: Expected ACK after ENQ.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                
                if self.direction in line:
                    self.error_info = ["ERROR: ACK in same direction as ENQ.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                
                self.state = s.WAIT_FOR_STX

            case s.WAIT_FOR_STX:
                if "STX" not in line:
                    self.error_info = ["ERROR: Expected STX.", self.state, line]
                    self.state = s.ERROR
                    return self.state

                if self.direction not in line:
                    self.error_info = ["ERROR: STX in opposite direction as ENQ.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                
                self.state = s.WAIT_FOR_MAGIC_1
            
            case s.WAIT_FOR_MAGIC_1:
                if "31   1" not in line:
                    self.error_info = ["ERROR: Expected 1.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                
                self.state = s.GET_LETTERS

            case s.GET_LETTERS:
                # NOTE: could do a while loop instead to be faster, but would that
                #       introduce possible other bugs?
                if "ESC" not in line and "ETX" not in line:
                    line = line.split()
                    line = [l.strip() for l in line]
                    self.letters.append(line[6])
                elif "ETX" in line:
                    # No payload in this message, skip to the end
                    self.state = s.GET_CHECKSUM
                elif "ESC" in line:
                    if len(self.letters) == 0:
                        self.error_info = ["ERROR: No letters provided.", self.state, line]
                        self.state = s.ERROR
                        return self.state

                    # Resets the letters between different payloads
                    self.letters = []

                    self.state = s.GET_LEN

            case s.GET_LEN:
                if "LEN0" not in line and "LEN1" not in line:
                    self.error_info = ["ERROR: Expected LEN0 or LEN1.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                elif "LEN0" in line:
                    line = line.split()
                    line = [l.strip() for l in line]
                    self.payload_length = int(line[5], 16)
                elif "LEN1" in line:
                    line = line.split()
                    line = [l.strip() for l in line]
                    self.payload_length += (int(line[5], 16) << 8)
                    

                    # NOTE: I'm not sure if this is an actual error, because there are other
                    #       messages that don't have a payload.
                    if self.payload_length == 0:
                        self.error_info = ["ERROR: Length of payload is 0.", self.state, line]
                        self.state = s.ERROR
                        return self.state

                    self.state = s.GET_PAYLOAD

            case s.GET_PAYLOAD:
                if self.num_payload_bytes < self.payload_length:
                    self.num_payload_bytes += 1
                elif "ETX" not in line:
                    self.error_info = ["ERROR: Expected ETX at end of payload of length %d." % (self.payload_length), self.state, line]
                    self.state = s.ERROR
                    self.num_payload_bytes = 0
                    return self.state
                elif "ETX" in line:
                    self.num_payload_bytes = 0
                    self.state = s.GET_CHECKSUM
                    
            case s.GET_CHECKSUM:
                line = line.split()
                line = [l.strip() for l in line]
                self.checksum.append(line[5])

                if len(self.checksum) == 2:
                    self.checksum = []
                    self.state = s.WAIT_FOR_CR

            case s.WAIT_FOR_CR:
                if "CR" not in line:
                    self.error_info = ["ERROR: Expected CR.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                
                self.state = s.WAIT_FOR_LF

            case s.WAIT_FOR_LF:
                if "LF" not in line:
                    self.error_info = ["ERROR: Expected LF.", self.state, line]
                    self.state = s.ERROR
                    return self.state

                self.state = s.WAIT_FOR_END_ACK

            case s.WAIT_FOR_END_ACK:
                if "ACK" not in line:
                    self.error_info = ["ERROR: Expected ACK after message.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                elif "ACK" in line:
                    # There are some instances of "BLACK_OFFSETS" in the file, which
                    # throws off the finding of the correct "ACK"
                    line = line.split()
                    line = [l.strip() for l in line]
                    if line[6] != "ACK":
                        self.error_info = ["ERROR: Expected ACK after message.", self.state, line]
                        self.state = s.ERROR
                        return self.state
                
                if self.direction in line:
                    self.error_info = ["ERROR: ACK in same direction as ENQ.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                
                self.state = s.WAIT_FOR_EOT_OR_STX

            case s.WAIT_FOR_EOT_OR_STX:
                if "EOT" not in line and "STX" not in line:
                    self.error_info = ["ERROR: Expected EOT or STX.", self.state, line]
                    self.state = s.ERROR
                    return self.state
                elif "EOT" in line:
                    if self.direction not in line:
                        self.error_info = ["ERROR: EOT in opposite direction from ENQ.", self.state, line]
                        self.state = s.ERROR
                        return self.state
                    self.state = s.WAIT_FOR_ENQ
                elif "STX" in line:
                    if self.direction not in line:
                        self.error_info = ["ERROR: EOT in opposite direction from ENQ.", self.state, line]
                        self.state = s.ERROR
                        return self.state
                    self.state = s.WAIT_FOR_MAGIC_1

            case s.ERROR:
                i = 0
                if len(self.error_info) < 2:
                    print("No error info, but entering ERROR state with line:\n    ", line)
                    while "ENQ" not in line:
                        i += 1
                        line = fileIn.readline()
                        if endOfFileCheck(line) == True:
                            return s.EOF

                # This accounts for the printing of the decoded message in the MsgOut file
                # This isn't _technically_ an error, but it will be dealt with here because
                # the expected line was not received.
                elif self.error_info[1] == s.WAIT_FOR_END_ACK:
                    while "ACK" not in line or "BLACK" in line:
                        i += 1
                        line = fileIn.readline()
                        if endOfFileCheck(line) == True:
                            return s.EOF
                        
                    # Only count as an error if the number of rows looked at before
                    # an end ACK was found was greater than 3. Otherwise parsing
                    # through the printed debug message and newline after each message
                    # would result in an error.
                    if i > 3:
                        self.total_errors += 1
                        print("(%s)" % (self.total_errors), self.error_info[0])
                        print(" ")
                        print("    State:", self.error_info[1])
                        print("    Line:", self.error_info[2])

                    if "ACK" in line:
                        # There are some instances of "BLACK_OFFSETS" in the file, which
                        # throws off the finding of the correct "ACK"
                        e_line = line.split()
                        e_line = [l.strip() for l in e_line]
                        if e_line[6] != "ACK":
                            self.error_info = ["ERROR: Expected ACK after message.", self.state, line]
                            self.state = s.ERROR
                            return self.state

                    if self.direction in line:
                        self.error_info = ["ERROR: ACK in same direction as ENQ.", self.state, line]
                        self.state = s.ERROR
                        return self.state
                    
                    self.state = s.WAIT_FOR_EOT_OR_STX

                    

                # NOTE: This is also kind of a hack...I don't know why it doesn't work unless this specific case is accounted
                #       for as well, but alas.
                elif self.error_info[1] == s.WAIT_FOR_CR:
                    self.total_errors += 1
                    print("(%s)" % (self.total_errors), self.error_info[0])
                    print(" ")
                    print("    State:", self.error_info[1])
                    print("    Line:", self.error_info[2])
                    
                    while "ENQ" not in line and "STX" not in line:
                        i += 1
                        line = fileIn.readline()
                        if endOfFileCheck(line) == True:
                            return s.EOF

                    if "in" in line: self.direction = DIR_IN
                    else: self.direction = DIR_OUT
                    
                    if "STX" in line:
                        self.state = s.WAIT_FOR_MAGIC_1
                    else:
                        newline = line.split()
                        newline = [l.strip() for l in newline]
                        self.enq_time = float(newline[0])
                        self.state = s.WAIT_FOR_BEG_ACK

                    print("    Lines read until exiting error state:", i)
                    print("    Next state to enter:", self.state)
                    print("    Current line evaluated:", line)

                else:
                    self.total_errors += 1
                    print("(%s)" % (self.total_errors), self.error_info[0])
                    print(" ")
                    print("    State:", self.error_info[1])
                    print("    Line:", self.error_info[2])
                    
                    # 1/16/24 edit: if there is a group of messages between an ENQ/EOT pair
                    # and there is an error with one of them, should we continue to skip all
                    # of them? Or would it be worth finding the next ENQ or STX?

                    while "ENQ" not in line and "STX" not in line:
                        i += 1
                        line = fileIn.readline()
                        if endOfFileCheck(line) == True:
                            return s.EOF

                    # Get the new directional information no matter what
                    # TODO: figure out if this should really be changed just in
                    #       case one of the messages inside an ENQ/EOT pair is
                    #       in the wrong direction
                    if "in" in line: self.direction = DIR_IN
                    else: self.direction = DIR_OUT
                    
                    if "STX" in line:
                        self.state = s.WAIT_FOR_MAGIC_1
                    else:
                        newline = line.split()
                        newline = [l.strip() for l in newline]
                        self.enq_time = float(newline[0])
                        self.state = s.WAIT_FOR_BEG_ACK

                    print("    Lines read until exiting error state:", i)
                    print("    Next state to enter:", self.state)
                    print("    Current line evaluated:", line)

                # Clear the error_info list to make room for the next error
                self.error_info = []   

            case _:
                print("Unknown state. Exiting out.")
    
        return self.state

#----------------------------------------------------------------------#
## Main Code ##

# Determine which files to run script against
argc = len(sys.argv)
if argc == 1:
    file_list = [os.path.join(dirpath, filename) for dirpath, _, filenames in os.walk('.') for filename in filenames if "_MsgOut" in filename]
    print("Number of files to check: %d\n\n" % (len(file_list)))
if argc > 2:
    print("Too many arguments.")
    sys.exit(0)
elif argc == 2:
    file_list = [sys.argv[1]]

for infilename in file_list:
    startnow = time.localtime(time.time())
    tstr = time.strftime("%Y-%m-%d %H:%M:%S", startnow)
    print("Starting... %s" % (tstr))
    print("MsgOut file: %s\n\n" % (infilename))

    fileIn = openFile(infilename, False)
    
    outfilename = "serial_" + Path(infilename).stem + ".csv"

    # This is a hack way of doing this. TODO update
    line = fileIn.readline()
    if 'x' in line:
        fileIn = openFile(infilename, True)
        line = fileIn.readline()

    # This is another hack way of doing this. On the first line
    # of every file, there is a string of numbers at the top
    # before the actual messages begin (just something from the
    # way MsgOut.txt files are written.) Want to skip this
    line = fileIn.readline()

    # Create an serial parse object
    spp = SerialProtocolParse()

    state = spp.state

    # Read through all the lines in the MsgOut file
    while 1:
        # Read line in only if we are not in an error state
        # If we are in an error state, we want to assess what
        # is going on with the line that errored out, not with
        # the line that comes after, thus not reading a new line.
        if state != s.ERROR:
            line = fileIn.readline()

        if endOfFileCheck(line) == True or state == s.EOF:
            break

        # print(state, line)

        # ACK check
        if spp.state != s.GET_PAYLOAD and spp.state != s.GET_LEN and spp.state != s.WAIT_FOR_BEG_ACK and spp.state != s.WAIT_FOR_END_ACK:
            if "ACK" in line and "BLACK" not in line or "06  06" in line:
                spp.error_info = ["ERROR: Got an unexpected ACK.", spp.state, line]
                spp.state = s.ERROR

        # if "PARSE CHECK_ERROR" in line:
        #     spp.error_info = ["ERROR: PARSE CHECK_ERROR.", spp.state, line]
        #     spp.state = s.ERROR

        state = spp.stateMachine(line, fileIn)

        if state == s.EOF:
            break

        

    print("TOTAL ERRORS: ", spp.total_errors)
    print("--------------------------------------------------------------------------------------------------\n")
    spp.resetVariables()
    spp.total_errors = 0
    fileIn.close()
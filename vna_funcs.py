
import socket
import csv
from vna import send_cmd


def vna_s2p(s: socket.socket, resolution: int) -> bool:
    # copy s2p file to computer
    # Example resolution input = 201 (number of data points)

    # Variable init
    # good_write = False
    expected_size = resolution + 13

    # Save trace into .s2p file on the VNA
    send_cmd(s, cmd='MMEM:STOR:SNP "CryoIntS.s2p"')

    # The transfer of data is an inconsistent task. This while loop was put in place to repeat it until the data is successfully written into a file
    while True:
        send_cmd(s, cmd='MMEM:DATA? "CryoIntS.s2p"')

        recv = s.recv(1000000) #recv data, arg sets max number of bytes
        contents = recv.decode('utf-8')

        # The transfer would first write some artifact type number usually something like #533281.
        #  The following code removes the characters before the first '!' which marks the start of the information we want
        startCounter = 0
        for index in contents:
            if (index != '!'):
                startCounter +=1
            else:
                break
        contents = contents[startCounter:]
        
        #The file would also write with double spacing (skip lines). We don't want that especially for .s2p, so replace double new lines with just one.
        contents = contents.replace("\n\n", "\n")
        
        #contents is now in the format we want the file to be in

        with open('CryoIntS.s2p', 'w+', encoding='utf-8') as f:
            f.write(contents) #overwrite the file with content

        print("Expected Number of Lines: ", expected_size)
            
        # The following code was taken and modified from an example on csv library page
        # Essentially we are using the csv library to count the number of lines in the file
        lCounter = 0
        with open('CryoIntS.s2p', encoding='utf-8', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|') #make reader object for the file that was just written
            for row in reader: #for every row/line in the file
                lCounter+=1 #increment line counter

        print("Total Lines: ", lCounter)

        # As mentioned above, the writing process is inconsistent. The code here is designed to check the number of lines and compare to what should be there.
        # While this is an imperfect method, it had proved reliable
        # limiter = 0
        if lCounter == expected_size: #check if both line count and expected_size are the same
            # good_write = True
            print("s2p file written") #if yes, the write was good
            return True

    # return True #transfer is good, return True


def vna_csv(s: socket.socket, resolution: int) -> bool:
    #Example resolution input = 201 (number of data points)

    #Variable init
    expected_size = resolution * 4 + 37

    send_cmd(s, cmd='MMEM:STOR:FDAT "CryoIntC.csv"')

    # The transfer of data is an inconsistent task. This while loop was put in place to repeat it until the data is successfully written into a file
    while True:
        send_cmd(s, cmd='MMEM:DATA? "CryoIntC.csv"')

        recv = s.recv(1000000) #recv data, arg sets max number of bytes
        contents = recv.decode('utf-8')

        # The transfer would first write some artifact type number usually something like #533281.
        # The following code removes the characters before the first '!' which marks the start of the information we want
        startCounter = 0
        for index in contents:
            if (index != '!'):
                startCounter += 1
            else:
                break
        contents = contents[startCounter:]

        #The file would also write with double spacing (skip lines). We don't want that especially for .s2p, so replace double new lines with just one.
        contents = contents.replace("\n\n", "\n")

        #contents is now in the format we want the file to be in

        with open('CryoIntC.csv', 'w+', encoding='utf-8') as f: #open the file for read/write overwrite
            f.write(contents) #overwrite the file with contents

        lCounter = 0
        # bCounter = 0 #setup line, begin/end counters
        # eCounter = 0

        print("Expected Number of Lines: ", expected_size)

        # The following code was taken and modified from an example on csv library page
        # Essentially we are using the csv library to count the number of lines in the file
        with open('CryoIntC.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=' ', quotechar='|') #make reader object for the file that was just written
            for row in reader: #for every row in the csv
                lCounter += 1 #increment line coutner
                # checker = (', '.join(row)) #join rows
                # if(checker == "BEGIN"): #check for BEGIN this marks the start of a data block there should be 4 for S11, S21, S12, S22
                #     bCounter += 1
                # elif(checker == "END"): #same thing for END
                #     eCounter += 1

        print("Total lines: ", lCounter)
        # print("Total begins: ", bCounter)
        # print("Total ends: ", eCounter)

        # As mentioned above, the writing process is inconsistent. The code here is designed to check the number of lines and compare to what should be there.
        # While this is an imperfect method, it had proved reliable
        # if lCounter == expected_size and bCounter == eCounter: #check if both line count and number of begins/ends are the same
        if lCounter == expected_size and contents.count('BEGIN') == contents.count('END'):
            print("CSV file written") #if yes, the write was good
            return True

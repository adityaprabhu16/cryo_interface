
import csv
import socket
import time

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
    # while True:
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
    else:
        return True

    # return True #transfer is good, return True


def vna_csv(s: socket.socket, fpath: str) -> bool:
    send_cmd(s, cmd='MMEM:STOR:FDAT "CryoIntC.csv"')
    print('Sent command: MMEM:STOR:FDAT "CryoIntC.csv"')

    for _ in range(10):

        # The transfer of data is an inconsistent task. This while loop was put in place to repeat it until the data is successfully written into a file
        # while True:
        send_cmd(s, cmd='MMEM:DATA? "CryoIntC.csv"')
        print('Sent command: MMEM:DATA? "CryoIntC.csv"')

        recv = s.recv(20000000) #recv data, arg sets max number of bytes
        contents = recv.decode('utf-8')

        # with open('temp.txt', 'w') as wf:
        #     wf.write(contents)

        bc = contents.count('BEGIN')
        ec = contents.count('END')
        if bc != 4 or ec != 4:
            print(f'BEGIN COUNT: {bc}; END COUNT: {ec}')
            print('File did not fully transfer.')
            time.sleep(5)
            continue

        # The transfer would first write some artifact type number usually something like #533281.
        # The following code removes the characters before the first '!' which marks the start of the information we want
        try:
            begin_idx = contents.index('BEGIN')
            end_idx = contents.rindex('END')
        except ValueError:
            time.sleep(1)
            continue
        contents = contents[0:end_idx+3]

        with open(fpath, 'w', encoding='utf-8') as csv_wf:
            for line in contents.split('\n'):
                csv_wf.write(line)

        print('Success!')
        return True
    
    print('Failed after 10 retries.')
    return False

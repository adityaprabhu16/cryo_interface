
import csv
import logging
import socket
import time

from vna import send_cmd


def ping_vna(s: socket.socket) -> bool:
    """
    :return: True if the VNA could be pinged, False otherwise.
    """
    try:
        # Ask the VNA to identify itself.
        send_cmd(s, cmd='*IDN?')
        # Read the response back.
        recv = s.recv(2048)
        return True
    except:
        logging.exception('Error.')
        try:
            s.close()
        except:
            logging.exception('Error closing connection.')
        return False

def vna_s2p(s: socket.socket, resolution: int, fpath: str) -> bool:
    # copy s2p file to computer
    # Example resolution input = 201 (number of data points)

    # 12 additional rows for data
    expected_size = resolution + 12

    # Save trace into .s2p file on the VNA
    send_cmd(s, cmd='MMEM:STOR:SNP "CryoIntS.s2p"')

    # The transfer of data is an inconsistent task. This while loop was put in place to repeat it until the data is successfully written into a file
    for _ in range(10):
        send_cmd(s, cmd='MMEM:DATA? "CryoIntS.s2p"')

        recv = s.recv(1000000) #recv data, arg sets max number of bytes
        contents = recv.decode('utf-8')

        try:
            idx = contents.index('!')
            contents = contents[idx:]
        except ValueError:
            time.sleep(1)
            print('Trying again...')
            continue

        lines = contents.rstrip().split('\r\n')
        
        # print(f'expected={expected_size}; actual={len(lines)}')

        with open(fpath, 'w', encoding='utf-8') as wf:
            for line in lines:
                wf.write(line+'\n')

        if len(lines) == expected_size:
            print('Success!')
            return True
        else:
            time.sleep(1)
            print('Trying again...')
            continue

    # return True #transfer is good, return True
    print('Failed after 10 tries.')
    return False


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

        try:
            idx = contents.index('!')
            contents = contents[idx:]
        except ValueError:
            time.sleep(1)
            continue

        bc = contents.count('BEGIN')
        ec = contents.count('END')
        if bc != 4 or ec != 4:
            print(f'BEGIN COUNT: {bc}; END COUNT: {ec}')
            print('File did not fully transfer.')
            time.sleep(1)
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

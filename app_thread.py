
import logging
import os
import queue
import serial
from threading import Thread
import time
import socket

from config import Config


def build_cmd(cmd: str) -> bytes:
    cmd = cmd + '\n'
    return bytes(cmd, 'utf-8')


class AppThread(Thread):

    def __init__(self):
        super().__init__()
        self.running = False
        self.con = None
        self.queue_pool = []
        self.metadata = None
        self.config = Config(period=5.0)
        self.dir = None
        self.experiment_selected = False

        self.data = []

        self.killed = False

        self.vna_con = None

    def run(self):

        # port = 'COM3'
        # baudrate = 9600  # Set this to what it will actually be
        # timeout = 5

        # self.con = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

        # self.con.write('*IDN?\n'.encode('utf-8'))
        # self.con.flush()
        # print(self.con.readline().decode('utf-8').rstrip())


        # HOST = '169.254.146.205'  # IP address of the device, this may (more like probably will) change
        # PORT = 5025  # Keysight says this port is standard for their instruments

        # self.vna_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.vna_con.connect((HOST, PORT))

        # self.vna_con.send(build_cmd('*IDN?'))
        # recv = self.vna_con.recv(2048)
        # print(recv.decode('utf-8'))

        # Run forever as long as the thread has not been killed.
        while not self.killed:

            if self.running:
                with open(os.path.join('experiments', self.dir, 'data.csv'), 'w+') as wf:
                    while self.running and not self.killed:

                        try:
                            if self.con:
                                # Request temperature from ESP32
                                self.con.write('GET TEMP\n'.encode('utf-8'))
                                self.con.flush()

                                data = self.con.readline().decode('utf-8').rstrip()
                                t = time.time()
                                temp1, temp2 = [float(x) for x in data.split(',')]

                                data = {
                                    'time': t,
                                    'temp1': temp1,
                                    'temp2': temp2,
                                }

                                # Store data points in memory.
                                self.data.append(data)
                                
                                # Write to the CSV file.
                                wf.write(f'{t},{temp1},{temp2}\n')

                                # Send data to every queue in the pool.
                                for queue in self.queue_pool:
                                    queue.put(data)
                            
                            if self.vna_con:
                                self.vna_con.send(build_cmd('MMEM:DATA? "FTEST.csv"'))
                                recv = self.vna_con.recv(100000)
                                text = recv.decode('utf-8')
                                # print(text[text.index('BEGIN'):])
                            
                                try:
                                    end_idx = text.index('END')
                                    # print('[BEGIN]')
                                    with open('temp.csv', 'w') as csv_wf:
                                        for line in text[text.index('BEGIN'):text.index('END')].split('\n')[1:]:
                                            csv_wf.write(line)
                                    print('Done writing to CSV.')
                                    # print('[END]')
                                except ValueError:
                                    # Incomplete transmission, END not found
                                    pass
                                

                            # Sleep until it's time to collect the next data point.
                            time.sleep(self.config.period)

                        except serial.serialutil.SerialException:
                            logging.exception('Encountered an error while communicating with the ESP32. Closing connection.')
                            try:
                                self.con.close()
                            except:
                                logging.exception('Error closing connection.')
                            self.con = None
                        except:
                            logging.exception('Exception encountered in app thread.')
                
            while not self.running and not self.killed:
                # Sleep to avoid wasting CPU resources.
                time.sleep(0.01)
                
    
    def get_queue(self) -> queue.Queue:
        q = queue.Queue()
        for item in self.data:
            q.put(item)
        self.queue_pool.append(q)
        return q

    def start(self) -> None:
        return super().start()
    
    def stop(self):
        self.killed = True
        if self.con:
            self.con.close()
        if self.vna_con:
            self.vna_con.close()

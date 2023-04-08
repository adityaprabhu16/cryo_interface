
import logging
from metadata import Metadata
import os
import queue
import serial
import socket
from threading import Thread
import time
from typing import List, Optional

from config import Config
from vna import build_cmd


class AppThread(Thread):

    def __init__(self):
        super().__init__()

        # Application metadata.
        self.metadata: Optional[Metadata] = None

        # Application runtime configuration.
        self.config: Config = Config(period=30.0)

        # Whether an experiment has been selected.
        self.experiment_selected = False

        # Whether or not the experiment is running.
        self.running = False

        # Serial connection to microcontroller.
        self.con: Optional[serial.Serial] = None

        # VNA connections.
        self.vna_con1: Optional[socket.socket] = None
        self.vna_con2: Optional[socket.socket] = None

        # Temperature data collected by the experiment.
        self.data = []

        # Collection of queues used for data streaming.
        self.queue_pool: List[queue.Queue] = []

        # Directory to store data in.
        self.dir: Optional[str] = None

        # Wether or not the application has been killed.
        self.killed = False

    def run(self):

        # Run forever as long as the thread has not been killed.
        while not self.killed:

            # If the experiment is running.
            if self.running:
                # Open the file for saving temperature data.
                with open(os.path.join('experiments', self.dir, 'data.csv'), 'w+') as wf:
                    # We loop here so check again if the experiment is running and the application is alive.
                    while self.running and not self.killed:

                        # Whether we need to try again at taking data due to an error.
                        retry = False

                        # Get the current time.
                        t = time.time()

                        # If we have a USB connection.
                        if self.con:
                            try:
                                # Request temperature from ESP32
                                self.con.write('GET TEMP\n'.encode('utf-8'))
                                self.con.flush()

                                # Read until the newline character, decode to utf-8, and remove the ending newline character.
                                data = self.con.readline().decode('utf-8').rstrip()
                                # Get temperatures from the string.
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

                            except serial.serialutil.SerialException:
                                logging.exception('Encountered an error while communicating with the ESP32. Closing connection.')
                                try:
                                    self.con.close()
                                except:
                                    logging.exception('Error closing connection.')
                                self.con = None
                            except:
                                logging.exception('Exception encountered in app thread.')
                        
                        # If we are connected to VNA 1.
                        if self.vna_con1:
                            try:
                                self.vna_con1.send(build_cmd('MMEM:DATA? "FTEST.csv"'))
                                recv = self.vna_con1.recv(100000)
                                text = recv.decode('utf-8')

                                try:
                                    end_idx = text.index('END')
                                    with open(os.path.join('experiments', self.dir, f'vna1_{int(t)}.csv'), 'w') as csv_wf:
                                        for line in text[text.index('BEGIN'):text.index('END')].split('\n')[1:]:
                                            csv_wf.write(line)
                                    print('Done writing to CSV.')
                                except ValueError:
                                    logging.exception('Error.')
                                    retry = True
                                    pass
                            except:
                                logging.exception('Error')
                                try:
                                    self.vna_con1.close()
                                except:
                                    logging.exception('Error closing connection')
                                self.vna_con1 = None
                        
                        # If we are connected to VNA 2.
                        if self.vna_con2:
                            try:
                                self.vna_con2.send(build_cmd('MMEM:DATA? "FTEST.csv"'))
                                recv = self.vna_con2.recv(100000)
                                text = recv.decode('utf-8')

                                try:
                                    end_idx = text.index('END')
                                    with open(os.path.join('experiments', self.dir, f'vna2_{int(t)}.csv'), 'w') as csv_wf:
                                        for line in text[text.index('BEGIN'):text.index('END')].split('\n')[1:]:
                                            csv_wf.write(line)
                                    print('Done writing to CSV.')
                                except ValueError:
                                    logging.exception('Error.')
                                    retry = True
                                    pass
                            except:
                                logging.exception('Error')
                                try:
                                    self.vna_con2.close()
                                except:
                                    logging.exception('Error closing connection')
                                self.vna_con2 = None
                        
                        if not retry:
                            # Sleep until it's time to collect the next data point.
                            time.sleep(self.config.period)
                
            while not self.running and not self.killed:
                # Sleep to avoid wasting CPU resources.
                time.sleep(0.01)
                
    
    def get_queue(self) -> queue.Queue:
        """
        Get a new queue for the data stream.
        
        :return: A queue containing all data up to this point.
        """
        # Create a new queue.
        q = queue.Queue()

        # Add previous data to the queue.
        for item in self.data:
            q.put(item)
        
        # Add the queue to the queue pool.
        self.queue_pool.append(q)

        return q

    def start(self) -> None:
        return super().start()
    
    def stop(self):
        self.killed = True
        # Close all connections.
        if self.con:
            self.con.close()
        if self.vna_con1:
            self.vna_con1.close()
        if self.vna_con2:
            self.vna_con2.close()

"""
Module for the AppThread class.
"""

from datetime import datetime
import logging
import os
import queue
import socket
from threading import Thread
import time
from typing import List, Optional

import serial

from config import Config
from metadata import Metadata
from vna import build_cmd


class AppThread(Thread):
    """
    Thread for running data logging activities concurrently with the web server.
    """

    def __init__(self):
        super().__init__()

        # Application metadata.
        self.metadata: Optional[Metadata] = None

        # Application runtime configuration.
        self.config: Config = Config(period=15*60)

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
        """
        Function that is run when the thread is started.
        """
        # Run forever as long as the thread has not been killed.
        while not self.killed:

            last_temp_reading = 0

            # If the experiment is running.
            if self.running:
                path = os.path.join('experiments', self.dir, 'data.csv')
                # Open the file for saving temperature data.
                with open(path, 'w+', encoding='utf-8') as wf:
                    # We loop here so check again if the experiment is running and the
                    # application is alive.
                    while self.running and not self.killed:

                        # Whether we need to try again at taking data due to an error.
                        retry = False

                        # Get the current time.
                        t = time.time()

                        # If we have a USB connection.
                        if self.con:
                            try:
                                temp1, temp2 = self._read_temp_data()
                                
                                data = {
                                    'time': t,
                                    'temp1': temp1,
                                    'temp2': temp2,
                                }

                                # Store data points in memory.
                                self.data.append(data)
                                # Write to the CSV file.
                                wf.write(f'{t},{temp1},{temp2}\n')

                                last_temp_reading = t

                                # Send data to every queue in the pool.
                                for q in self.queue_pool:
                                    q.put(data)

                            except serial.serialutil.SerialException:
                                msg = 'Encountered an error while communicating with the ESP32.' \
                                      'Closing connection.'
                                logging.exception(msg)
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
                                # Send command to copy a file from the VNA.
                                self.vna_con1.send(build_cmd('MMEM:DATA? "FTEST.csv"'))

                                # Receive up to 100KB of data.
                                recv: bytes = self.vna_con1.recv(100000)

                                # Decode the received data.
                                text: str = recv.decode('utf-8')

                                try:
                                    # TODO: we need to find the last END index
                                    # TODO: we need to count that the instances of BEGIN == instances of END
                                    begin_idx = text.index('BEGIN')
                                    end_idx = text.index('END')
                                    
                                    dt = datetime.fromtimestamp(t)
                                    f_name = f'{dt.year}_{dt.month}_{dt.day}_{dt.hour}_{dt.minute}_{dt.second}_vna1.csv'
                                    path = os.path.join('experiments', self.dir, f_name)
                                    
                                    with open(path, 'w', encoding='utf-8') as csv_wf:
                                        for line in text[begin_idx:end_idx].split('\n')[1:]:
                                            csv_wf.write(line)
                                    logging.info('Done writing to CSV.')
                                except ValueError:
                                    logging.exception('Error.')
                                    retry = True
                            except:
                                logging.exception('Error.')
                                try:
                                    self.vna_con1.close()
                                except:
                                    logging.exception('Error closing connection.')
                                self.vna_con1 = None

                        # If we are connected to VNA 2.
                        if self.vna_con2:
                            try:
                                self.vna_con2.send(build_cmd('MMEM:DATA? "FTEST.csv"'))
                                recv = self.vna_con2.recv(100000)
                                text = recv.decode('utf-8')

                                try:
                                    end_idx = text.index('END')
                                    path = os.path.join('experiments',
                                                        self.dir,
                                                        f'vna2_{int(t)}.csv')
                                    with open(path, 'w', encoding='utf-8') as csv_wf:
                                        for line in text[text.index('BEGIN'):text.index('END')].split('\n')[1:]:
                                            csv_wf.write(line)
                                    print('Done writing to CSV.')
                                except ValueError:
                                    logging.exception('Error.')
                                    retry = True
                            except:
                                logging.exception('Error')
                                try:
                                    self.vna_con2.close()
                                except:
                                    logging.exception('Error closing connection')
                                self.vna_con2 = None
                        if not retry:
                            # Sleep until it's time to collect the next data point.
                            end_time = t + self.config.period
                            while self.running and not self.killed and time.time() < end_time:
                                t = time.time()
                                if self.con and t >= last_temp_reading + 15:
                                    temp1, temp2 = self._read_temp_data()
                                    data = {
                                        'time': t,
                                        'temp1': temp1,
                                        'temp2': temp2,
                                    }

                                    # Store data points in memory.
                                    self.data.append(data)

                                    last_temp_reading = t

                                    # Send data to every queue in the pool.
                                    for q in self.queue_pool:
                                        q.put(data)
                                # Sleep to avoid wasting CPU resources.
                                time.sleep(0.001)

            while not self.running and not self.killed:
                t = time.time()
                if self.con and t >= last_temp_reading + 15:
                    temp1, temp2 = self._read_temp_data()
                    data = {
                        'time': t,
                        'temp1': temp1,
                        'temp2': temp2,
                    }

                    # Store data points in memory.
                    self.data.append(data)

                    last_temp_reading = t

                    # Send data to every queue in the pool.
                    for q in self.queue_pool:
                        q.put(data)
                # Sleep to avoid wasting CPU resources.
                time.sleep(0.001)

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

    def stop(self):
        """
        Stop the thread.
        """
        self.killed = True
        # Close all connections.
        if self.con:
            self.con.close()
        if self.vna_con1:
            self.vna_con1.close()
        if self.vna_con2:
            self.vna_con2.close()

    def _read_temp_data(self):
        # Request temperature from ESP32
        self.con.write('GET TEMP\n'.encode('utf-8'))
        self.con.flush()

        # Read until the newline character, decode to utf-8,
        # and remove the ending newline character.
        data = self.con.readline().decode('utf-8').rstrip()
        # Get temperatures from the string.
        temp1, temp2 = [float(x) for x in data.split(',')]

        return temp1, temp2

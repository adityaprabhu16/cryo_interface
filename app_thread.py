
import logging
import os
import queue
import serial
from threading import Thread
import time

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
        self.config = Config(period=30.0)
        self.dir = None
        self.experiment_selected = False

        self.data = []

        self.vna_con1 = None
        self.vna_con2 = None

        self.killed = False

    def run(self):

        # Run forever as long as the thread has not been killed.
        while not self.killed:

            if self.running:
                with open(os.path.join('experiments', self.dir, 'data.csv'), 'w+') as wf:
                    while self.running and not self.killed:

                        retry = False

                        t = time.time()

                        if self.con:
                            try:
                                # Request temperature from ESP32
                                self.con.write('GET TEMP\n'.encode('utf-8'))
                                self.con.flush()

                                data = self.con.readline().decode('utf-8').rstrip()
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

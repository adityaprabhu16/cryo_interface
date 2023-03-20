
import logging
import os
import queue
import serial
from threading import Thread
import time

from config import Config


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

    def run(self):

        # port = 'COM3'
        # baudrate = 9600  # Set this to what it will actually be
        # timeout = 5

        # self.con = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

        # self.con.write('*IDN?\n'.encode('utf-8'))
        # self.con.flush()
        # print(self.con.readline().decode('utf-8').rstrip())

        # while not self.killed:
        #     self.con.write('GET TEMP\n'.encode('utf-8'))
        #     self.con.flush()
        #     print(self.con.readline().decode('utf-8').rstrip())
        #     time.sleep(1)

        a, b = 0.0, 0.0

        # # send previous data
        # for item in self.data:
        #     for queue in self.queue_pool:
        #         queue.put(item)

        # Run forever as long as the thread has not been killed.
        while not self.killed:

            if self.running:
                with open(os.path.join('experiments', self.dir, 'data.csv'), 'w+') as wf:
                    # testing
                    while self.running and not self.killed:
                        
                        a, b = a+1, b+1
                        data = {
                                'time': time.time(),
                                'temp1': a,
                                'temp2': b,
                            }

                        # Store data points in memory.
                        self.data.append(data)
                        
                        # Write to the CSV file.
                        wf.write(f'{data["time"]},{data["temp1"]},{data["temp2"]}\n')

                        # Send data to every queue in the pool.
                        for queue in self.queue_pool:
                            queue.put(data)

                        # Sleep until it's time to collect the next data point.
                        # logging.debug('Sleeping while running.')
                        time.sleep(self.config.period)
                
            while not self.running and not self.killed:
                # Sleep to avoid wasting CPU resources.
                # logging.debug('Sleeping while not running.')
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

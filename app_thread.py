
import queue
import serial
from threading import Thread
import time


class AppThread(Thread):

    def __init__(self):
        super().__init__()
        self.running = False
        self.con = None
        self.queue = queue.Queue()

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

        # TODO: load data that was previously logged

        # testing
        while self.running:
            # TODO: log to file
            self.queue.put({
                'time': time.time(),
                'temp1': 21.0,
                'temp2': 22.0,
            })
            time.sleep(1)

    def start(self) -> None:
        self.running = True
        return super().start()
    
    def stop(self):
        self.running = False
        if self.con:
            self.con.close()

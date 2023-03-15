
import serial
from threading import Thread
import time


class AppThread(Thread):

    def __init__(self):
        super().__init__()
        self.killed = False
        self.con = None

    def run(self):

        port = 'COM3'
        baudrate = 9600  # Set this to what it will actually be
        timeout = 5

        self.con = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

        self.con.write('*IDN?\n'.encode('utf-8'))
        self.con.flush()
        print(self.con.readline().decode('utf-8').rstrip())

        while not self.killed:
            self.con.write('GET TEMP\n'.encode('utf-8'))
            self.con.flush()
            print(self.con.readline().decode('utf-8').rstrip())
            time.sleep(1)
    
    def stop(self):
        self.killed = True
        if self.con:
            self.con.close()

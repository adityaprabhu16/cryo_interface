
import serial
import time


# This changes depending on what port the MCU is plugged into
port = 'COM3'
baudrate = 9600  # Set this to what it will actually be
timeout = 5

con = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

try:
    con.write('*IDN?\n'.encode('utf-8'))
    print(con.readline().decode('utf-8').rstrip())
    
    while True:
        con.write('GET TEMP\n'.encode('utf-8'))
        print(con.readline().decode('utf-8').rstrip())
        time.sleep(1)
    
except Exception as e:
    print(e)
finally:
    # Always close the connection
    con.close()

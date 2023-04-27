
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import json
import logging
import os
import socket
from typing import Dict
from urllib.parse import urlparse

import serial

from app_thread import AppThread
from metadata import Metadata
from utils import EnhancedJSONEncoder, find_available_devices, find_previous_experiments
from vna import build_cmd, VNA_PORT


USB_BAUD_RATE = 9600


def build_response_handler(app_thread: AppThread):
    """
    Build the HTTP response handler class.
    
    :param app_thread: AppThread that will run application operations concurrent to server
    operations.

    :return: ResponseHandler class that extends BaseHTTPRequestHandler.
    """

    class ResponseHandler(BaseHTTPRequestHandler):
        """
        Handles responding to HTTP requests.
        """

        def do_GET(self):
            """
            Handle HTTP GET requests.
            """
            # Parse the URL this request is coming from.
            parsed = urlparse(self.path)

            # Serve this request depending on the requested path.
            if parsed.path in ['/', '/index', '/index.html']:
                self.send_file_response('fetch/index.html')
            elif parsed.path == '/index.js':
                self.send_file_response('fetch/index.js', 'application/javascript')
            elif parsed.path == '/index.css':
                self.send_file_response('fetch/index.css', 'text/css')
            elif parsed.path == '/plotly-2.19.1.min.js':
                self.send_file_response('fetch/plotly-2.19.1.min.js', content_type='application/javascript')
            elif parsed.path == '/favicon-16x16.png':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open('fetch/favicon-16x16.png', 'rb') as f:
                    self.wfile.write(f.read())
            elif parsed.path == '/favicon-32x32.png':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                with open('fetch/favicon-32x32.png', 'rb') as f:
                    self.wfile.write(f.read())
            elif parsed.path == '/api/metadata':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(app_thread.metadata, cls=EnhancedJSONEncoder).encode('utf-8'))
            elif parsed.path == '/api/config':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(app_thread.config, cls=EnhancedJSONEncoder).encode('utf-8'))
            elif parsed.path == '/api/devices':
                devices = find_available_devices()
                self.send_json_response(devices)
            elif parsed.path == '/api/stream_data':
                self.stream_data()
            elif parsed.path == '/api/running':
                self.send_json_response(app_thread.running)
            elif parsed.path == '/api/previous_experiments':
                self.send_json_response(find_previous_experiments())
            elif parsed.path == '/api/experiment_selected':
                self.send_json_response(app_thread.experiment_selected)
            elif parsed.path == '/api/devices_connected':
                # these checks are not perfect
                # a failure in the appthread has to occur for the connection to be set to None
                data = {
                    'temperature': (app_thread.con is not None),
                    'vna1': (app_thread.vna_con1 is not None),
                    'vna2': (app_thread.vna_con2 is not None),
                }
                self.send_json_response(data)
            else:
                self.send_response_only(HTTPStatus.NOT_FOUND)
                self.end_headers()
        
        def do_POST(self):
            """
            Handle HTTP POST requests.
            """
            # Parse the URL this request is coming from.
            parsed = urlparse(self.path)

            # Serve this request depending on the requested path.
            if parsed.path == '/api/config':
                self.update_config()
            elif parsed.path == '/api/generate_combined_csv':
                # TODO: implement this last (once we have some data to work with)
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
            elif parsed.path == '/api/start':
                self.start()
            elif parsed.path == '/api/stop':
                app_thread.running = False
                self.send_json_response('Data collection stopped!', status=HTTPStatus.OK)
            elif parsed.path == '/api/create_experiment':
                self.create_experiment()
            elif parsed.path == '/api/connect':
                self.connect()
            elif parsed.path == '/api/connect_vna1':
                self.connect_vna1()
            elif parsed.path == '/api/connect_vna2':
                self.connect_vna2()
            else:
                self.send_response_only(HTTPStatus.NOT_FOUND)
                self.end_headers()

        def send_file_response(self, path: str, content_type='text/html') -> None:
            """
            Respond with the contents of the file at the provided path.

            :param path: Path of the file to be read.
            :param content_type: Content type of the file, defaults to 'text/html'
            """
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            with open(path, encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        
        def send_json_response(self, data, status=HTTPStatus.OK) -> None:
            """
            Respond with JSON content.

            :data: Data that can be serialized to json.
            :status: HTTPStatus to respond with, defaults to HTTPStatus.OK
            """
            self.send_response(status)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

        def stream_data(self) -> None:
            """
            Send a stream of JSON events for the temperature data until the connection is closed.
            """
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/event-stream')
            self.end_headers()

            # Get a queue from the app thread for the temperature data.
            queue = app_thread.get_queue()

            try:
                # Run until the connection is closed.
                while True:
                    # Block until data is available.
                    data: Dict = queue.get()
                    # String formatted for event.
                    s = 'event: temperature\ndata: ' + json.dumps(data) + '\n\n'
                    # Write to stream.
                    self.wfile.write(s.encode('utf-8'))
            except:
                # An exception occured and the connection is closed, remove the queue from the pool.
                app_thread.queue_pool.remove(queue)
                logging.exception('An error occured while serving stream data.')

        def update_config(self) -> None:
            """
            Update the server's runtime configuration.
            """
            # Check if we got the expected content-type
            if self.headers.get('content-type') != 'application/json':
                self.send_json_response("'content-type' was not 'application/json'.", status=HTTPStatus.BAD_REQUEST)
                return
            
            try:
                length = int(self.headers.get('length'))
            except TypeError:
                self.send_json_response("'length' was not an integer.", status=HTTPStatus.BAD_REQUEST)
                return
            
            try:
                content = self.rfile.read(length)
            except:
                self.send_json_response('Error reading request contents.', status=HTTPStatus.BAD_REQUEST)
                return

            try:
                config = json.loads(content)
            except:
                self.send_json_response('Error loading JSON contents.', status=HTTPStatus.BAD_REQUEST)
                return
            
            period = config.get('period')

            if type(period) != int:
                self.send_json_response("'period' was not an integer.", status=HTTPStatus.BAD_REQUEST)
                return

            app_thread.config.period = period

            self.send_json_response({
                "period": app_thread.config.period
            })

        def start(self) -> None:
            """
            Start collecting data if an experiment has been selected.
            """
            if app_thread.experiment_selected:
                app_thread.running = True
                msg = 'Data Collection started!'
                self.send_json_response(msg, status=HTTPStatus.OK)
            else:
                msg = 'Cannot start data collection before starting an experiment.'
                logging.warning(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                
        def connect(self) -> None:
            """
            Connect to microcontroller for temperature measurement.
            """
            # Check if a temperature sensor was selected
            if app_thread.metadata.temp1 is None and app_thread.metadata.temp2 is None:
                msg = 'No temperature sensor was selected for this experiment.'
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return
            
            try:
                length = int(self.headers.get('length'))
            except TypeError:
                self.send_json_response("'length' was not an integer.", status=HTTPStatus.BAD_REQUEST)
                return
            
            try:
                port = json.loads(self.rfile.read(length).decode('utf-8'))
            except:
                self.send_json_response('Error reading JSON contents.', status=HTTPStatus.BAD_REQUEST)
                return

            # Check if there's an existing connection that we need to close.
            if app_thread.con:
                try:
                    logging.info('Closing existing serial connection.')
                    app_thread.con.close()
                except:
                    logging.exception('An error occured while closing the existing connection.')
            
            # Find available ports
            available = find_available_devices()

            # Check if the requested  port is one the available ports
            if port not in available:
                msg = f"The requested port '{port}' is not available."
                logging.warning(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return
            
            timeout = 5

            try:
                app_thread.con = serial.Serial(port=port, baudrate=USB_BAUD_RATE, timeout=timeout)
            except:
                msg = f"Unable to open port '{port}'"
                logging.exception(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return

            logging.info(f'Connected to USB device at {port}')
            self.send_json_response('Connection successful.')
        
        def connect_vna1(self) -> None:
            """
            Connect to the VNA at the provided IP address.
            """
            # Check if VNA 1 has been selected
            if app_thread.metadata.vna1 is None:
                msg = 'VNA 1 was not selected for this experiment.'
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return

            # Get the length of the request's contents.
            try:
                length = int(self.headers.get('length'))
            except TypeError:
                self.send_json_response("'length' was not an integer.", status=HTTPStatus.BAD_REQUEST)
                return

            # Read the VNA IP address from the requests contents.
            try:
                host = json.loads(self.rfile.read(length).decode('utf-8'))
            except:
                self.send_json_response('Error reading JSON contents.', status=HTTPStatus.BAD_REQUEST)
                return

            # Check if the connection to the VNA already exists.
            if app_thread.vna_con1:
                # Try closing the socket connection.
                try:
                    logging.info('Closing existing socket connection.')
                    app_thread.vna_con1.close()
                except:
                    logging.exception('Error closing socket connection.') 

            try:
                # Create socket object.
                app_thread.vna_con1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Connect to that socket.
                app_thread.vna_con1.connect((host, VNA_PORT))
                # Send the identify command to the VNA.
                app_thread.vna_con1.send(build_cmd('*IDN?'))
                # Read the VNA's reply.
                recv = app_thread.vna_con1.recv(2048)
                logging.info(f"Connected to {recv.decode('utf-8')}")
            except:
                # Set the connection to None.
                app_thread.vna_con1 = None
                msg = 'Error occured while connecting to VNA.'
                logging.exception(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return

            # Everything was good, respond with OK.
            self.send_json_response('Successfully connected to VNA 1.', HTTPStatus.OK)
        
        def connect_vna2(self) -> None:
            """
            Connect to the VNA at the provided IP address.
            """
            # Check if VNA 2 has been selected
            if app_thread.metadata.vna2 is None:
                msg = 'VNA 2 was not selected for this experiment.'
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return
            
            # Get the length of the request's contents.
            try:
                length = int(self.headers.get('length'))
            except TypeError:
                self.send_json_response("'length' was not an integer.", status=HTTPStatus.BAD_REQUEST)
                return

            # Read the VNA IP address from the requests contents.
            try:
                host = json.loads(self.rfile.read(length).decode('utf-8'))
            except:
                self.send_json_response('Error reading JSON contents.', status=HTTPStatus.BAD_REQUEST)
                return

            # Check if the connection to the VNA already exists.
            if app_thread.vna_con2:
                # Try closing the socket connection.
                try:
                    logging.info('Closing existing socket connection.')
                    app_thread.vna_con2.close()
                except:
                    logging.exception('Error closing socket connection.') 

            try:
                # Create socket object.
                app_thread.vna_con2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Connect to that socket.
                app_thread.vna_con2.connect((host, VNA_PORT))
                # Send the identify command to the VNA.
                app_thread.vna_con2.send(build_cmd('*IDN?'))
                # Read the VNA's reply.
                recv = app_thread.vna_con2.recv(2048)
                logging.info(f"Connected to {recv.decode('utf-8')}")
            except:
                # Set the connection to None.
                app_thread.vna_con2 = None
                msg = 'Error occured while connecting to VNA.'
                logging.exception(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return

            # Everything was good, respond with OK.
            self.send_json_response('Successfully connected to VNA 2.', HTTPStatus.OK)

        def create_experiment(self) -> None:
            """
            Handle the request to create a new experiment.
            """
            # Make sure that we haven't already selected an experiment.
            if app_thread.experiment_selected:
                self.send_json_response('No experiment selected.', status=HTTPStatus.BAD_REQUEST)
                return

            # We expect JSON content for this request.
            if self.headers.get('content-type') != 'application/json':
                self.send_json_response("content-type was not 'application/json'", status=HTTPStatus.BAD_REQUEST)
                return

            # Determine content length, read the data, decode it, and load it as JSON.
            # TODO: add better error handling here.
            try:
                length = int(self.headers.get('length'))
            except TypeError:
                self.send_json_response("'length' was not an integer.", status=HTTPStatus.BAD_REQUEST)
                return
            
            try:
                content = self.rfile.read(length).decode('utf-8')
            except:
                self.send_json_response('Error reading request contents.', status=HTTPStatus.BAD_REQUEST)
                return
            
            try:
                metadata = json.loads(content)
            except:
                self.send_json_response('Error parsing JSON contents.', status=HTTPStatus.BAD_REQUEST)
                return
            
            title = metadata.get('title').replace(' ', '_')
            name = metadata.get('name')
            cpa = metadata.get('cpa')
            date = metadata.get('date')

            # Check that a name, cpa, and date were provided
            if name is None or cpa is None or date is None or title is None:
                self.send_json_response('Missing required field.', status=HTTPStatus.BAD_REQUEST)
                return

            directory = f'{name}-{title}-{cpa}-{date}'

            try:
                # Attempt to create the directory for storing experimental data.
                os.makedirs(os.path.join('experiments', directory))
            except FileExistsError:
                # If the directory already exists log a warning and exit.
                msg = 'The requested directory already exists.'
                logging.warning(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return
            except Exception:
                # If we encounter an unexpected exception log it and return.
                msg = 'Error creating experiment directory.'
                logging.exception(msg)
                self.send_json_response(msg, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            
            temp1 = metadata.get('temp1')
            if temp1 == '':
                temp1 = 'temp1'

            temp2 = metadata.get('temp2')
            if temp2 == '':
                temp2 = 'temp2'
            
            vna1 = metadata.get('vna1')
            if vna1 == '':
                vna1 = 'vna1'
            
            vna2 = metadata.get('vna2')
            if vna2 == '':
                vna2 = 'vna2'

            vna1_temp = metadata.get('vna1_temp')
            # Check that the associated temperature selection was actually selected.
            if (vna1_temp == 'temp1' and not temp1) or (vna1_temp == 'temp2' and not temp2):
                msg = 'The temperature sensor associated with VNA 1 was not selected.'
                logging.warning(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return

            vna2_temp = metadata.get('vna2_temp')
            # Check that the associated temperature selection was actually selected.
            if (vna2_temp == 'temp1' and not temp1) or (vna2_temp == 'temp2' and not temp2):
                msg = 'The temperature sensor associated with VNA 2 was not selected.'
                logging.warning(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return

            app_thread.metadata = Metadata(title=title,
                                           name=name,
                                           cpa=cpa,
                                           date=date,
                                           temp1=temp1,
                                           temp2=temp2,
                                           vna1=vna1,
                                           vna2=vna2,
                                           vna1_temp=vna1_temp,
                                           vna2_temp=vna2_temp)
            app_thread.dir = directory
            app_thread.experiment_selected = True

            self.save_metadata()
            self.send_response_only(HTTPStatus.OK)
            self.end_headers()

        def save_metadata(self) -> bool:
            """
            Save metadata to the metadata.json file in the experiments directory.

            :return: True if the write was sucessful, False otherwise.
            """
            try:
                # Check if a directory has been set. (It is set when the experiment is created.)
                if app_thread.dir:
                    with open(os.path.join('experiments', app_thread.dir, 'metadata.json'), 'w') as wf:
                        wf.write(json.dumps(app_thread.metadata, cls=EnhancedJSONEncoder, indent=4))
                    return True
            except:
                logging.exception('Error occured while writing metadata.')
            return False

    return ResponseHandler

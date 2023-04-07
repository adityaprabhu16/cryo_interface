
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
import json
import logging
from metadata import Metadata
import os
import serial
import socket
from typing import Dict
from urllib.parse import urlparse

from app_thread import AppThread
from utils import EnhancedJSONEncoder, find_available_devices, find_previous_experiments


VNA_PORT = 5025


def build_cmd(cmd: str) -> bytes:
    cmd = cmd + '\n'
    return bytes(cmd, 'utf-8')


def build_response_handler(app_thread: AppThread):
    """
    Build the HTTP response handler class.
    
    :param app_thread: AppThread that will run application operations concurrent to server operations.

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
            elif parsed.path == '/plotly-2.19.1.min.js':
                self.send_file_response('fetch/plotly-2.19.1.min.js', content_type='application/javascript')
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
                self.send_json_response("Data collection stopped!", status=HTTPStatus.BAD_REQUEST)
                # self.send_response_only(HTTPStatus.OK)
                # self.end_headers()
            elif parsed.path == '/api/create_experiment':
                self.create_experiment()
            elif parsed.path == '/api/select_existing_experiment':
                # TODO
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
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
            self.send_header('Content-type', content_type)
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
                self.send_json_response("'content-type' was not 'application/json'", status=HTTPStatus.BAD_REQUEST)
                return
            
            length = int(self.headers.get('length'))
            content = self.rfile.read(length)
            config = json.loads(content)

            period = config.get('period')

            if type(period) != int:
                self.send_json_response("'period' was not an integer", status=HTTPStatus.BAD_REQUEST)
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
                msg = "Data Collection started!"
                self.send_json_response(msg, status=HTTPStatus.OK)
                # self.send_response_only(HTTPStatus.OK)
                self.end_headers()
            else:
                msg = 'Cannot start data collection before starting an experiment.'
                logging.warning(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                
        
        def connect(self) -> None:
            length = int(self.headers.get('length'))
            port = json.loads(self.rfile.read(length).decode('utf-8'))
            if app_thread.con:
                try:
                    logging.info('Closing existing serial connection.')
                    app_thread.con.close()
                except:
                    logging.exception('An error occured while closing the existing connection.')
            available = find_available_devices()
            if port not in available:
                msg = f"The requested port '{port}' is not available."
                logging.warning(msg)
                self.send_json_response(msg, status=HTTPStatus.BAD_REQUEST)
                return
            baudrate = 9600
            timeout = 5

            # TODO: this may fail, should add error handling
            app_thread.con = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

            logging.info(f'Connected to USB device at {port}')
            self.send_response_only(HTTPStatus.OK)
            self.end_headers()
        
        def connect_vna1(self) -> None:
            """
            Connect to the VNA at the provided IP address.
            """
            # Get the length of the request's contents.
            length = int(self.headers.get('length'))

            # Read the VNA IP address from the requests contents.
            host = json.loads(self.rfile.read(length).decode('utf-8'))

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
            self.send_response_only(HTTPStatus.OK)
            self.end_headers()
        
        def connect_vna2(self) -> None:
            """
            Connect to the VNA at the provided IP address.
            """
            # Get the length of the request's contents.
            length = int(self.headers.get('length'))

            # Read the VNA IP address from the requests contents.
            host = json.loads(self.rfile.read(length).decode('utf-8'))

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
            self.send_response_only(HTTPStatus.OK)
            self.end_headers()

        def create_experiment(self) -> None:
            # Make sure that we haven't already selected an experiment.
            if app_thread.experiment_selected:
                self.send_response_only(HTTPStatus.BAD_REQUEST)
                self.end_headers()
                return

            # We expect JSON content for this request.
            if self.headers.get('content-type') != 'application/json':
                self.send_response_only(HTTPStatus.BAD_REQUEST)
                self.end_headers()
                return

            # Determine content length, read the data, decode it, and load it as JSON.
            length = int(self.headers.get('length'))
            content = self.rfile.read(length).decode('utf-8')
            metadata = json.loads(content)

            name = metadata.get('name')
            cpa = metadata.get('cpa')
            date = metadata.get('date')

            # Check that a name, cpa, and date were provided
            if name is None or cpa is None or date is None:
                self.send_response_only(HTTPStatus.BAD_REQUEST)
                self.end_headers()
                return

            directory = f'{name}_{cpa}_{date}'

            try:
                # Attempt to create the directory for storing experimental data.
                os.makedirs(os.path.join('experiments', directory))
            except FileExistsError:
                # If the directory already exists log a warning and exit.
                logging.warning('The requested directory already exists.')
                self.send_response_only(HTTPStatus.BAD_REQUEST)
                self.end_headers()
                return
            except Exception:
                # If we encounter an unexpected exception log it and return.
                logging.exception('Error creating experiment directory.')
                self.send_response_only(HTTPStatus.BAD_REQUEST)
                self.end_headers()
                return
            
            app_thread.metadata = Metadata(name=name,
                                           cpa=cpa,
                                           date=date,
                                           temp1=metadata.get('temp1'),
                                           temp2=metadata.get('temp2'),
                                           vna1=metadata.get('vna1'),
                                           vna2=metadata.get('vna2'))
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
                        wf.write(json.dumps(app_thread.metadata, cls=EnhancedJSONEncoder))
                    return True
            except:
                logging.exception('Error occured while writing metadata.')
            return False

    return ResponseHandler

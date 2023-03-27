
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from metadata import Metadata
import os
import serial
from typing import Dict
from urllib.parse import urlparse

from app_thread import AppThread
from utils import EnhancedJSONEncoder, find_available_devices, find_previous_experiments


def build_response_handler(app_thread: AppThread):

    class ResponseHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            parsed = urlparse(self.path)
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
                # TODO: right now this only reports which ports devices are connected to
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
            parsed = urlparse(self.path)
            if parsed.path == '/api/metadata':
                if self.headers.get('content-type') != 'application/json':
                    self.send_response_only(HTTPStatus.BAD_REQUEST)
                    self.end_headers()
                    return
                length = int(self.headers.get('length'))
                content = self.rfile.read(length)
                # TODO
                # metadata = json.loads(content)
                # self.save_metadata()
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
                # TODO: return updated metadata
            elif parsed.path == '/api/config':
                if self.headers.get('content-type') != 'application/json':
                    self.send_response_only(HTTPStatus.BAD_REQUEST)
                    self.end_headers()
                    return
                length = int(self.headers.get('length'))
                content = self.rfile.read(length)
                # TODO
                # config = json.loads(content)
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
                # TODO: return the updated config
            elif parsed.path == '/api/generate_combined_csv':
                # TODO: implement this last (once we have some data to work with)
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
            elif parsed.path == '/api/start':
                if app_thread.experiment_selected:
                    app_thread.running = True
                    self.send_response_only(HTTPStatus.OK)
                    self.end_headers()
                else:
                    logging.warning('Cannot start data collection before starting an experiment.')
                    self.send_response_only(HTTPStatus.BAD_REQUEST)
                    self.end_headers()
            elif parsed.path == '/api/stop':
                app_thread.running = False
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
            elif parsed.path == '/api/create_experiment':
                self.create_experiment()
            elif parsed.path == '/api/select_existing_experiment':
                # dir = ''
                # Check that dir is in the list of allowed dirs
                # Save this as our dir to use
                # return metadata
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
            elif parsed.path == '/api/connect':
                length = int(self.headers.get('length'))
                port = json.loads(self.rfile.read(length).decode('utf-8'))
                # print(length, port)
                if app_thread.con:
                    try:
                        logging.info('Closing existing serial connection.')
                        app_thread.con.close()
                    except:
                        logging.exception('An error occured while closing the existing connection.')
                available = find_available_devices()
                if port not in available:
                    logging.warning(f"The requested port '{port}' is not available.")
                    self.send_response_only(HTTPStatus.BAD_REQUEST)
                    self.end_headers()
                    return
                baudrate = 9600
                timeout = 5
                app_thread.con = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
                logging.info(f'Connected to USB device at {port}')
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
            else:
                self.send_response_only(HTTPStatus.NOT_FOUND)
                self.end_headers()

        def send_file_response(self, path: str, content_type='text/html'):
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', content_type)
            self.end_headers()
            with open(path, encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        
        def send_json_response(self, data):
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

        def stream_data(self) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/event-stream')
            self.end_headers()
            queue = app_thread.get_queue()
            try:
                while True:
                    data: Dict = queue.get()
                    s = 'event: temperature\ndata: ' + json.dumps(data) + '\n\n'
                    self.wfile.write(s.encode('utf-8'))
            except Exception:
                app_thread.queue_pool.remove(queue)
                logging.exception('An error occured while serving stream data.')

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

            # Name, cpa, and date must be present for the operation to be sucessful.
            if 'name' not in metadata or 'cpa' not in metadata or 'date' not in metadata:
                self.send_response_only(HTTPStatus.BAD_REQUEST)
                self.end_headers()

            name = metadata['name']
            cpa = metadata['cpa']
            date = metadata['date']

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
            
            app_thread.metadata = Metadata(name=name, cpa=cpa, date=date)
            app_thread.dir = directory
            app_thread.experiment_selected = True

            self.save_metadata()
            self.send_response_only(HTTPStatus.OK)
            self.end_headers()

        def save_metadata(self) -> bool:
            if app_thread.dir:
                with open(os.path.join('experiments', app_thread.dir, 'metadata.json'), 'w') as wf:
                    wf.write(json.dumps(app_thread.metadata, cls=EnhancedJSONEncoder))
                return True
            return False

    return ResponseHandler


def run_server(server_class, handler_class):
    server_address = ('', 4951)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def main():
    app_thread = AppThread()
    app_thread.start()
    try:
        run_server(ThreadingHTTPServer, build_response_handler(app_thread))
    except:
        app_thread.stop()
        print('Application stopped.')


if __name__ == "__main__":
    main()

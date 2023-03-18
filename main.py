
import glob
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import serial
import sys
from typing import Dict, List
from urllib.parse import urlparse

from app_thread import AppThread


# I don't like global variables
metadata: Dict[str, str] = {}
config = {}


def find_available_devices() -> Dict[str, str]:
    """
    Lists serial port names.
    Based off of: https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python

    :raises EnvironmentError: On unsupported or unknown platforms
    :returns: A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result: Dict[str, str] = {}
    for port in ports:
        try:
            s = serial.Serial(port)
            s.write('*IDN?\n'.encode('utf-8'))
            s.flush()
            r = s.readline().decode('utf-8').rstrip()
            s.close()
            result[port] = r
        except (OSError, serial.SerialException):
            pass
    return result


def find_previous_experiments() -> List[str]:
    return [dir[0] for dir in os.walk('experiments/')]


def build_response_handler(app_thread):

    class ResponseHandler(BaseHTTPRequestHandler):

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path in ['/', '/index', '/index.html']:
                self.send_file_response('fetch/index.html')
            elif parsed.path in ['/dashboard', '/dashboard.html']:
                self.send_file_response('fetch/dashboard.html')
            elif parsed.path == '/chart.js':
                self.send_file_response('fetch/chart.js', content_type='application/javascript')
            elif parsed.path == '/plotly-2.19.1.min.js':
                self.send_file_response('fetch/plotly-2.19.1.min.js', content_type='application/javascript')
            elif parsed.path == '/dashboard.js':
                self.send_file_response('fetch/dashboard.js', content_type='application/javascript')
            elif parsed.path == '/dashboard.css':
                self.send_file_response('fetch/dashboard.css', content_type='text/css')
            elif parsed.path == '/api/metadata':
                self.send_json_response(metadata)
            elif parsed.path == '/api/config':
                self.send_json_response(config)
            elif parsed.path == '/api/devices':
                devices = find_available_devices()
                self.send_json_response(devices)
            elif parsed.path == '/api/stream_data':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'text/event-stream')
                self.end_headers()
                # TODO: we should create a new queue here so that multiple browser tabs can be open at once
                while True:
                    data = app_thread.queue.get()
                    s = 'event: test\ndata: ' + json.dumps(data) + '\n\n'
                    self.wfile.write(s.encode('utf-8'))
                # TODO: delete the queue once the connection is lost
            elif parsed.path == '/api/running':
                self.send_json_response(app_thread.running)
            elif parsed.path == '/api/previous_experiments':
                self.send_json_response(find_previous_experiments())
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
                length = int(self.headers.get('content-length'))
                content = self.rfile.read(length)
                global metadata
                metadata = json.loads(content)
                self.save_metadata()
                print(metadata)
                # TODO: return an error if data is invalid (make sure we have the fields we need)
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
            elif parsed.path == '/api/config':
                if self.headers.get('content-type') != 'application/json':
                    self.send_response_only(HTTPStatus.BAD_REQUEST)
                    self.end_headers()
                    return
                length = int(self.headers.get('content-length'))
                content = self.rfile.read(length)
                # TODO: it will be important to verify that the config is valid
                global config
                config = json.loads(content)
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
                # TODO: return the updated config?
            elif parsed.path == '/api/generate_combined_csv':
                # TODO: implement this last (once we have some data to work with)
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
            elif parsed.path == '/api/start':
                app_thread.start()
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
            elif parsed.path == '/api/stop':
                app_thread.stop()
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
            elif parsed.path == '/api/create_experiment':
                # TODO: look at provided metadata to determine the directory name
                # TODO: store this directory name for later
                dir = 'NAME_CPA_DATE'
                os.mkdir(os.path.join(['experiment', dir]))
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
            elif parsed.path == '/api/select_existing_experiment':
                # dir = ''
                # Check that dir is in the list of allowed dirs
                # Save this as our dir to use
                # return metadata
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
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
        
        def save_metadata(self) -> None:
            # TODO: we'll want to put this file into the correct folder
            with open('metadata.json', 'w') as wf:
                wf.write(json.dumps(metadata))

    return ResponseHandler


def run_server(server_class, handler_class):
    server_address = ('', 4951)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def main():
    app_thread = AppThread()
    try:
        run_server(ThreadingHTTPServer, build_response_handler(app_thread))
    except:
        app_thread.stop()
        print('Application stopped.')


if __name__ == "__main__":
    main()

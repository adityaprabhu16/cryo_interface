
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import time
from typing import Dict, List
from urllib.parse import urlparse

from app_thread import AppThread


# I don't like global variables
metadata: Dict[str, str] = {}
config = {}
running = False


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
            elif parsed.path == '/dashboard.js':
                self.send_file_response('fetch/dashboard.js', content_type='application/javascript')
            elif parsed.path == '/dashboard.css':
                self.send_file_response('fetch/dashboard.css', content_type='text/css')
            elif parsed.path == '/api/metadata':
                self.send_json_response(metadata)
            elif parsed.path == '/api/config':
                self.send_json_response(config)
            elif parsed.path == '/api/devices':
                devices = self.find_available_devices()
                self.send_json_response(devices)
            elif parsed.path == '/api/stream_data':
                self.send_response(HTTPStatus.OK)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                while True:
                    # TODO: send actual data from devices
                    s = 'event: test\ndata: ' + json.dumps({'time': time.time()}) + '\n\n'
                    self.wfile.write(s.encode('utf-8'))
                    time.sleep(5)
            elif parsed.path == '/api/running':
                self.send_json_response(running)
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
            elif parsed.path == '/api/stop':
                self.send_response_only(HTTPStatus.OK)
                self.end_headers()
                global running
                running = False
            elif parsed.path == '/api/generate_combined_csv':
                # TODO: implement this once we have some data to work with
                self.send_response_only(HTTPStatus.NOT_IMPLEMENTED)
                self.end_headers()
            else:
                self.send_response_only(HTTPStatus.NOT_FOUND)
                self.end_headers()

        def send_file_response(self, path: str, content_type='text/html'):
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', content_type)
            self.end_headers()
            with open(path) as f:
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
            
        def find_available_devices(self) -> List[str]:
            """
            :return: list of available devices
            """
            # TODO: actually search for devices
            return ['VNA 1', 'VNA 2', 'Temp 1', 'Temp 2']
    
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
    except KeyboardInterrupt:
        app_thread.stop()
        print('KeyboardInterrupt: Shutting down.')
        pass


if __name__ == "__main__":
    main()

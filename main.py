
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Dict, List
from urllib.parse import urlparse

from app_thread import AppThread


def build_response_handler(app_thread):

    class ResponseHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            # TODO: provide a way to stream temperature data
            parsed = urlparse(self.path)
            if parsed.path in ['/', '/index', '/index.html']:
                self.send_file_response('fetch/index.html')
            elif parsed.path in ['/dashboard', '/dashboard.html']:
                self.send_file_response('fetch/dashboard.html')
            elif parsed.path in ['/chart.js']:
                self.send_file_response('fetch/chart.js', content_type='application/javascript')
            elif parsed.path in ['/dashboard.js']:
                self.send_file_response('fetch/dashboard.js', content_type='application/javascript')
            elif parsed.path in ['/dashboard.css']:
                self.send_file_response('fetch/dashboard.css', content_type='text/css')
            else:
                self.send_response_only(404)
                self.end_headers()
        
        def do_POST(self):
            # TODO: handle updates to experiment config (sampling rate, etc)
            parsed = urlparse(self.path)
            if parsed.path in ['/metadata']:
                # TODO: check that the content type is json
                # TODO: handle metadata from form
                length = int(self.headers.get('content-length'))
                content = self.rfile.read(length)
                data = json.loads(content)
                print(data)
                # TODO: return an error if data is invalid
                self.send_response_only(200)
                self.end_headers()
            else:
                self.send_response_only(404)
                self.end_headers()

        def send_file_response(self, path: str, content_type='text/html'):
            self.send_response(200)  # OK
            self.send_header('Content-type', content_type)
            self.end_headers()
            with open(path) as f:
                self.wfile.write(f.read().encode('utf-8'))

        def get_available_devices(self) -> List[str]:
            """
            :return: list of available devices
            """
            # just hard-coding this for now
            return ['VNA 1', 'VNA 2', 'Temp 1', 'Temp 2']
        
        def save_metadata(self, metadata: Dict[str, str]) -> None:
            # TODO: we'll want to put this file into the correct folder
            with open('metadata.json', 'w') as wf:
                wf.write(metadata)
            
        def find_available_devices(self) -> None:
            pass
    
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

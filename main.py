"""
Main module for running the application.
"""

from http.server import ThreadingHTTPServer

from app_thread import AppThread
from handler import build_response_handler


def run_server(server_class, handler_class) -> None:
    """
    Run the server.
    :param server_class: Type of server to run.
    :param handler_class: HTTP response handler.
    """
    server_address = ('', 4951)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


def main():
    """
    Main function.
    """
    app_thread = AppThread()
    app_thread.start()
    try:
        run_server(ThreadingHTTPServer, build_response_handler(app_thread))
    except:
        # If the server runs raises an exception, stop the app thread.
        app_thread.stop()
        print('Application stopped.')


if __name__ == "__main__":
    main()

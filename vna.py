
import socket


VNA_PORT = 5025


def build_cmd(cmd: str) -> bytes:
    cmd = cmd + '\n'
    return cmd.encode('utf-8')


def send_cmd(s: socket.socket, cmd: str):
    encoded = build_cmd(cmd)
    bytes_sent = s.send(encoded)
    if bytes_sent != len(encoded):
        raise RuntimeError('Not all data was sent.')

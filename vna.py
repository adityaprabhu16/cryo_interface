
VNA_PORT = 5025

def build_cmd(cmd: str) -> bytes:
    cmd = cmd + '\n'
    return cmd.encode('utf-8')

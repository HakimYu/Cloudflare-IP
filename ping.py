import socket

def portPing(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((str(host), int(port)))
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    if result == 0:
        return 1
    else:
        return 0

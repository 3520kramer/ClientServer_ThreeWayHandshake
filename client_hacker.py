import socket

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('localhost', 10000)

message = b'msg-0=hej'
sock.sendto(message, server_address)

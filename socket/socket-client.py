import socket

client = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
client.connect( ( '127.0.0.1', 9988 ) )
client.send( 'Hello from Client'.encode() )
print( client.recv(1024).decode() )


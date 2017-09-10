"""Raspberry Pi Camera Script

Uses picamera library to take pictures from the Raspberry Pi Camera
Outputs individual snapshots to a stream
Set the stream-to location with --server <ADDRESS>

"""

import json
import os
import io
import socket
import struct
import time
import picamera
from optparse import OptionParser

#constants
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

#general
server_address = '127.0.0.1'
server_port = 8000

#command line arguments
parser = OptionParser()
parser.add_option("-s", "--server", dest="server",
    help="address of the server to send picamera image to")
parser.add_option("-p", "--port", dest="port",
    help="port socket will use")
parser.add_option("-x", "--width", dest="width",
    help="width of camera resolution")
parser.add_option("-y", "--height", dest="height",
    help="height of camera resolution")

(options, args) = parser.parse_args()
#server address
if options.server:
    server_address = options.server
if options.port:
    server_port = options.port
#adjust camera resolution
if options.width:
    CAMERA_WIDTH = options.width
if options.height:
    CAMERA_HEIGHT = options.height

#connect a client socket to server
client_socket = socket.socket()
client_socket.connect((server_address, server_port))

#file object to be sent over connection
connection = client_socket.makefile('wb')
#capture_continuous actually drops after a period of time, so do again in that instance
while True:
    with picamera.PiCamera() as camera:
        camera.resolution = (CAMERA_WIDTH, CAMERA_HEIGHT)
        
        start = time.time()
        stream = io.BytesIO()
        for foo in camera.capture_continuous(stream, 'jpeg'):
            # Write the length of the capture to the stream and flush to
            # ensure it actually gets sent
            connection.write(struct.pack('<L', stream.tell()))
            connection.flush()
            # Rewind the stream and send the image data over the wire
            stream.seek(0)
            connection.write(stream.read())
            # If we've been capturing for more than 30 seconds, quit
            if time.time() - start > 30:
                break
            # Reset the stream for the next capture
            stream.seek(0)
            stream.truncate()
    # Write a length of zero to the stream to signal we're done
    connection.write(struct.pack('<L', 0))
connection.close()
client_socket.close()
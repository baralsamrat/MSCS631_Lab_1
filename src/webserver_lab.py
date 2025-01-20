
from socket import *
import sys
from concurrent.futures import ThreadPoolExecutor
import os

# Function to handle each client connection
# Processes the HTTP request, retrieves the requested file, and sends the response

def handle_client(connectionSocket):
    try:
        # Receive the HTTP request from the client
        try:
            message = connectionSocket.recv(1024).decode()
        except UnicodeDecodeError:
            # Handle cases where the request cannot be decoded
            print("Failed to decode client message.")
            connectionSocket.send("HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n".encode())
            connectionSocket.send("<html><body><h1>400 Bad Request</h1></body></html>\r\n".encode())
            return

        print("Received message:\n", message)

        # Extract the requested filename from the HTTP request
        try:
            filename = message.split()[1]
        except IndexError:
            # Handle cases where the HTTP request is malformed
            print("Malformed HTTP request.")
            connectionSocket.send("HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n".encode())
            connectionSocket.send("<html><body><h1>400 Bad Request</h1></body></html>\r\n".encode())
            return

        # Sanitize the filename to prevent directory traversal attacks
        sanitized_filename = os.path.normpath(filename[1:])
        if sanitized_filename.startswith(".."):
            # Respond with a 403 Forbidden if a directory traversal attempt is detected
            print("Directory traversal attempt detected.")
            connectionSocket.send("HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n\r\n".encode())
            connectionSocket.send("<html><body><h1>403 Forbidden</h1></body></html>\r\n".encode())
            return

        # Attempt to open and read the requested file
        with open(sanitized_filename, "r") as f:
            outputdata = f.read()

        # Send HTTP response header indicating success
        connectionSocket.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n".encode())

        # Send the content of the requested file to the client
        connectionSocket.send(outputdata.encode())
        connectionSocket.send("\r\n".encode())

    except IOError:
        # Handle the case where the requested file does not exist by sending a 404 response
        connectionSocket.send("HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n".encode())
        connectionSocket.send("<html><body><h1>404 Not Found</h1></body></html>\r\n".encode())

    finally:
        # Close the connection socket after serving the request
        connectionSocket.close()

# Create a socket for the server using IPv4 and TCP
# Set up the server to listen for connections on the specified port

def create_server_socket():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverPort = 6789

    # Bind the server socket to the specified port
    serverSocket.bind(("", serverPort))
    # Start listening for incoming connections with a specified backlog size
    serverSocket.listen(10)
    print("Web server is running on port", serverPort)

    return serverSocket

serverSocket = create_server_socket()

# Use a ThreadPoolExecutor to manage a pool of threads
# Allows concurrent handling of multiple client requests

with ThreadPoolExecutor(max_workers=10) as executor:
    while True:
        # Wait for and accept a new client connection
        print("Ready to serve...")
        connectionSocket, addr = serverSocket.accept()
        print(f"Connection established with {addr}")

        # Submit the client handler to the thread pool for execution
        executor.submit(handle_client, connectionSocket)

# Close the server socket (unreachable in this implementation)
serverSocket.close()
sys.exit()

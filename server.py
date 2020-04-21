import socket, re, time, threading, configparser, logging, datetime

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the port
server_address = ('localhost', 10000)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Sets a timeout on the server to 4 seconds
#sock.settimeout(4)

# Reads config file and sets status of heartbeat
config = configparser.ConfigParser()
config.read('opt.conf')

#
logging.basicConfig(filename='handshakes.log', level=logging.INFO)

# Boolean to check if the first part of handshake is completed
firstpartofhandshakecompleted = False

# Boolean to check if three-way handshake is successful
successful_connection = False

#
message_number = 0

# Sets client_address list as empty, so it can be checked if exception is thrown
client_address = ['0','0']

#
def logger():
    #
    if successful_connection and firstpartofhandshakecompleted:
        logging.info("%s: Handshake successful" % datetime.datetime.now())

    # If the
    '''elif successful_connection and firstpartofhandshakecompleted == False:
        logging.info("%s: Handshake unsuccessful" % datetime.datetime.now())'''

    if successful_connection == False:
        logging.info("%s: Communication attempted without successful handshake" % datetime.datetime.now())


class packageCounterThread(threading.Thread):
    # variable to count incoming packages, time and to let text be printed only once in while loop
    number_of_packages = None
    maximum_number_of_packages = config.getint('Packages', 'MaximumPackages')
    reached_max_packets = False

    start_time = None
    time_interval_in_seconds = config.getint('Packages', 'TimeIntervalInSeconds')

    def __init__(self):
        threading.Thread.__init__(self)
        self.reset()

    def reset(self):
        self.number_of_packages = 0
        self.start_time = time.time()
        self.reached_max_packets = False

    def run(self):
        while True:
            if self.number_of_packages >= self.maximum_number_of_packages and self.reached_max_packets is False:
                # Sends package to client to activate block
                message = b'con-max lock'
                sock.sendto(message, client_address)
                print("[SERVER]: Connection to client blocked! Maximum of", self.maximum_number_of_packages,
                      "received packages every", self.time_interval_in_seconds, "second exceeded")
                self.reached_max_packets = True

            # If less more than or one second has passed and client address is a tuple
            # the server sends a package to the server to lock is senddata function
            if self.start_time + 1 <= time.time() and client_address != ['0','0']:
                # Sends package to client to deactivate block
                message = b'con-max open'
                sock.sendto(message, client_address)

                # If the message on connection message has been printed earlier i print this message
                if self.reached_max_packets == True:
                    print("[SERVER]: Connection to client is open again")

                self.reset()


# Create and starts thread which counts incoming packages
packagecount = packageCounterThread()
packagecount.start()

# Keeps client/server connection open as long as program is running
while True:

    # I create my data variable to hold the data which is sent from the client
    # To prevent old data being passed on, i clear the data in the list before each iteration
    data = ""

    try:
        # Receive data
        if packagecount.number_of_packages <= 5:
            data, client_address = sock.recvfrom(4096)
            packagecount.number_of_packages += 1
            data = data.decode()

    except socket.timeout:
        if client_address == ['0','0']:
            # If no client is online the list will be 'empty' and the server will wait for connection from client
            print("[SERVER]: No client online")
        else:
            # Sends reset package to client if a client is online, but hasn't sent anything for a while
            message = b'con-res 0xFE'
            sent = sock.sendto(message, client_address)
            successful_connection = False
            firstpartofhandshakecompleted = False
            print('[SERVER]: ' + message.decode() + ': connection reset')

    # Save received data and ip-address in list
    splittedData = re.split('[\s=-]', data)
    splittedData.append(client_address[0])

    # Checks if incoming data follows protocol
    if successful_connection == False :
        if splittedData[0] == 'com' \
                and splittedData[1] == '0' \
                and splittedData[2] == client_address[0]:

            # Prints data with ip-address
            print('[CLIENT]: ' + data + ' from: ' + client_address[0])

            # Send data
            message = b'com-0 accept'
            sent = sock.sendto(message, client_address)
            print('[SERVER]: ' + message.decode() + ' to ' + client_address[0])

            # The first part of the handshake is completed so boolean is set to true
            firstpartofhandshakecompleted = True

        elif splittedData[0] == 'com' \
                and splittedData[1] == '0' \
                and splittedData[2] == 'accept' \
                and splittedData[3] == client_address[0] \
                and firstpartofhandshakecompleted == True:

            # Prints data and sets connection to true
            print('[CLIENT]: ' + data + ' from: ' + client_address[0])
            successful_connection = True
            message_number = 0
            logger()

        elif splittedData[0] == 'con' \
                and splittedData[1] == 'res' \
                and splittedData[2] == '0xFF':
            print('[SERVER]: Disconnected from client: ' + client_address[0])

        elif splittedData[0] == 'con' \
                and splittedData[1] == 'h' \
                and splittedData[2] == '0x00':
            print('heartbeat: ' + data)

        else:
            logger()

    # When protocol is followed, the client will be able to communicate with server
    elif successful_connection :
        if splittedData[0] == 'msg':
            # Prints data from client
            print('[CLIENT]: ' + data)

            # Sets message number by adding one to the received number
            # Parsed to an int to make it possible to add one
            message_number = int(splittedData[1])+1
            # Parsed back to string to be able to encode it to bytes
            message_number = str(message_number)

            # Sends the same response to the client no matter what is received
            message = b'res-'+message_number.encode()+b'=I am server'
            sent = sock.sendto(message, client_address)
            print('[SERVER]: ' + message.decode())

        elif splittedData[0] == 'con' \
                and splittedData[1] == 'h' \
                and splittedData[2] == '0x00':
            print("[CLIENT]: " + data + ": I'm still here, dont worry!")

import serial.tools.list_ports
import serial
import threading


class SerialCom():
    def __init__(self, responseCallback=None, exceptionCallback=None):
        self.ser = None
        self.port = None
        self.baudrate = None
        self.receive_thread = None
        self.is_running = False
        self.responseCallback = responseCallback
        self.exceptionCallback = exceptionCallback

    def configCallbacks(self, responseCallback=None, exceptionCallback=None):
        if responseCallback:
            self.responseCallback = responseCallback

        if exceptionCallback:
            self.exceptionCallback = exceptionCallback

    def getPorts(self):
        # Return a list of available COM ports
        return [port.device for port in serial.tools.list_ports.comports()]
    
    def getBaudrates(self):
        # Add other baud rate options dynamically if needed
        baud_rate_list = ["9600", "19200", "38400", "57600", "115200"]
        return baud_rate_list
    
    def connect(self, com_port, baudrate):
        try:
            self.ser = serial.Serial(com_port, baudrate, timeout=1)
            self.is_running = True
            self.thread()
        
        except serial.SerialException as e:
            msg = f"{e}"
            self.exceptionCallback(msg)

    def disconnect(self):
        self.is_running = False
        self.ser.close()
        self.receive_thread.join()

    def send(self, command):
        if self.is_running:
            try:
                self.ser.write(command.encode('utf-8'))
        
            except serial.SerialException as e:
                msg = f"{e}"
                self.exceptionCallback(msg)

    def thread(self):
        self.receive_thread = threading.Thread(target=self.receive)
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def receive(self):
        while self.is_running:
            try:
                receive_data = self.ser.readline().decode('utf-8')

                if receive_data:
                    if self.responseCallback:
                        self.responseCallback(receive_data)

            except serial.SerialException as e:
                msg = f"{e}"

                if self.exceptionCallback:
                    self.is_running = False
                    self.exceptionCallback(msg)
                break
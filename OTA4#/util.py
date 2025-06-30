import os
import queue
import collections
import configparser
from pathlib import Path

class CallbackHandler(object):
    handlers = None

    def __init__(self):
        self.handlers = collections.defaultdict(set)

    def register(self, event, callback):
        self.handlers[event].add(callback)

    def fire(self, event, **kwargs):
        for handler in self.handlers.get(event, []):
            handler(**kwargs)

class FileHandler():
    def __init__(self):
        self.ini_parser = configparser.ConfigParser()
            
    def getCWD(self):
        return Path.cwd()

    def getPath(self, dir=None, file=None):
        path = ""
        if dir and file:
            path = Path(dir, file)
        
        else:
            if dir:
                path = Path(self.getCWD(), dir)

            if file:
                path = Path(self.getCWD(), file)
        
        return path
    
    def makeDir(self, directory):
        if directory:
            dir_path = Path(self.getCWD(), directory)
            os.mkdir(dir_path)

    def checkDir(self, directory):
        if directory:
            dir_path = Path(self.getCWD(), directory)
            if os.path.isdir(dir_path):
                    pass
            else:
                os.mkdir(dir_path)

    def updateFile(self, config_path):
        with open(config_path, 'w') as configfile:
            self.ini_parser.write(configfile)

    def addParameter(self, section, key, value):
        if self.ini_parser.has_section(section):
            self.ini_parser.set(section, key, value)
        
        else:
            self.ini_parser[section] = {key : value}

    def getValues(self, section, key):
        if self.ini_parser.has_section(section):
            if self.ini_parser.has_option(section, key):
                return self.ini_parser.get(section, key)


class Gcode():
    def __init__(self):
        self.queue = queue.Queue()
        self.callback = None
        self.gcode = None
        self.ack_list = []
        self.axis_pos_list = []
        self.sd_card_files_list = []
        self.ok_flag = False
        self.home_flag = False
        self.temp_report_flag = False
        self.sd_write_flag = False
        self.init_print_flag = False
        self.gcode_ext_tuple = (".gco", ".g", ".gcode")
        self.sd_card_files_list = []
        self.sd_file_open_flag = False
        self.m400_flag = False
        self.sd_abort_flag = False
        self.sd_abort_response_flag = False

        self.gcode_dict = {
            "home" : "G28",
            "lmove1" : "G1",
            "set-pos" : "G92",
            "get-pos" : "M114",
            "list-SD" : "M20",
            "init-SD" : "M21",
            "select-SD" : "M23",
            "start-SD" : "M24",
            "pause-SD" : "M25",
            "resume-SD" : "M24",
            "delete-SD" : "M30",
            "ext-rel" : "M82",
            "finish-move" : "M400",
            "abort-SD" : "M524",
            "extruder" : "M302 S0",
            "set-stepsmm" : "M92",
            "ex-pos" : "G92 E0"
        }

    def attachCallback(self, callback_obj):
        if callback_obj:
            self.callback = callback_obj

    def fireCallback(self, code):
        if self.callback:
            self.callback.fire(code)

    def encode(self, cmd):
        self.queue.put(cmd)

    def readQueue(self):
        try:
            self.gcode = self.queue.get()
            print(f"Queue : {self.gcode}")

        except Queue.Empty:
            pass

        else:
            pass

    def decode(self, response):
        rx_data = response.strip()

        if rx_data == "ok":
            self.ok_flag = True
            self.readQueue()
            self.process(self.gcode, self.ack_list)
            self.ack_list = []
            self.fireCallback("ok")

        else:
            if "echo:busy" in response:
                if self.sd_abort_flag:
                    self.sd_abort_response_flag = True

            elif 'T:' in response and 'B:' in response and '@:' in response:
                self.temp_report_flag = True

            elif 'Done printing file' in response:
                code = "SDdone"
                self.fireCallback(code)

            elif "X:0.00 Y:0.00 Z:5.00" in response and self.sd_abort_response_flag:
                self.sd_abort_response_flag = False
                self.sd_abort_flag = False
                code = "SDabt"
                self.fireCallback(code)
            
            else:
                self.ack_list.append(rx_data)

    def process(self, gcode, response_list):
        print(f"Gcode : {gcode}")
        print(f"ACK : {response_list}")

        try:
            if "G28" in gcode:
                self.goHome(response_list)

            if "G92" in gcode:
                self.getAxisPos(response_list)

            if gcode == "M114":
                self.getAxisPos(response_list)

            if gcode == "M20":
                self.listSDCard(response_list)

            if "M23" in gcode:
                self.initSDPrint(response_list)

            if "M28" in gcode:
                self.sd_write_flag = True

            if gcode == "M29": 
                self.sd_write_flag = False

            if "M524" in gcode:
                self.sd_abort_flag = True

        except Exception as e:
            pass

        else:
            code = gcode.split(" ")[0]
            print(f"code = {code}")
            self.fireCallback(code)

    def checksum(self, gcode):
        cs = ord(gcode[0])
        for ch in gcode[1:]:
            cs = cs ^ ord(ch)

        return cs
    
    def goHome(self, cmd_list):
        self.home_flag = False
        self.getAxisPos(cmd_list)

    def getAxisPos(self, cmd_list):
        self.pos_list = [pos for pos in cmd_list[0].split('Count')[0].split()]
        print(f"position : {self.pos_list}")

    def listSDCard(self, cmd_list):
        self.sd_card_files_list = [data.split(" ")[0] for data in cmd_list if data.split(" ")[0].lower().endswith(self.gcode_ext_tuple)]
        print(f"SD card : {self.sd_card_files_list}")

    def initSDPrint(self, response_list):
        if "File opened" in response_list[1]:
            self.sd_file_open_flag = True
        
        elif "open failed" in response_list[1]:
            self.sd_file_open_flag = False

class Utils():
    def __init__(self):
        self.debugflag = [False]    # flag to print debug info
        self.msg_list = []

    def setDebugMsgFlag(self, setFlag):
        self.debugflag[0] = setFlag

    def debugMsg(self, text):
        if self.debugflag[0]:
            print(text)

    def putMessage(self, *args):
        for msg in args:
            self.msg_list.append(msg)

    def getMessage(self):
        return self.msg_list

    def clearMessage(self):
        self.msg_list = []

    def argIsNotNone(*args):
        return all(arg is not None for arg in args)
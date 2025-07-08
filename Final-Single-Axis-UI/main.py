import sys
import os
# from PySide6 import uic
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QProgressBar, QTextEdit, QPushButton, QDial, QSlider, QLCDNumber, QMessageBox, QLineEdit, QComboBox, QGroupBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QScreen
from PySide6.QtGui import QPainter
from PySide6.QtUiTools import QUiLoader

from com import SerialCom
from util import CallbackHandler, FileHandler, Gcode, Utils
from laserconf import Laser


class UI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        loader = QUiLoader()
        self.parent = loader.load("app.ui", None)
        self.setCentralWidget(self.parent)

        self.serial_com = SerialCom()
        self.fh = FileHandler()
        self.gcode = Gcode()
        self.ut = Utils()
        self.cb = CallbackHandler()

        test_width = 780
        test_height = 705

        self.setFixedSize(test_width, test_height)  # (x, y, width, height)
        print(f"UI set to: {test_width}x{test_height}")

        config_dir = "config"
        config_file = "config.ini"

        self.config_dir_path = self.fh.getPath(dir=config_dir)
        self.config_file_path = self.fh.getPath(dir=self.config_dir_path, file=config_file)

        self.port_list = []
        self.baudrate_list = []
        self.laser_type_list = []
        laser_option = ["1W", "2W", "8W"]
        self.laser_ty = Laser(laser_option)
        self.com_errorFlag = False

        self.step = 1
        self.xmin = 0
        self.xmax = 150
        self.ymin = 0
        self.ymax = 150
        self.zmin = 0
        self.zmax = 100
        self.xpos = 0
        self.ypos = 0
        self.zpos = 0
        self.emin = 0
        self.emax = 100
        self.epos = 0
        self.step = 1
        self.step_index = 1
        self.jog_code = ["p", "m"]
        self.jog_inc_code = self.jog_code[0]
        self.jog_dec_code = self.jog_code[1]

        self.temp_report_hide_flag = True

        self.serial_com.configCallbacks(responseCallback = self.updateData, exceptionCallback = self.updateException)

        self.gcode.attachCallback(self.cb)
        self.cb.register(self.gcode.gcode_dict.get("get-pos"), self.setPos)
        
        # uic.loadUi("app.ui", self)

        self.parent.xhome_btn.clicked.connect(self.xhome)
        self.parent.yhome_btn.clicked.connect(self.yhome)
        self.parent.zhome_btn.clicked.connect(self.zhome)
        self.parent.home_btn.clicked.connect(self.home)

        self.parent.xplus_btn.clicked.connect(self.xplus)
        self.parent.xminus_btn.clicked.connect(self.xminus)
        self.parent.yplus_btn.clicked.connect(self.yplus)
        self.parent.yminus_btn.clicked.connect(self.yminus)

        self.parent.zplus_btn.clicked.connect(self.zplus)
        self.parent.zminus_btn.clicked.connect(self.zminus)
        self.parent.zcenter_btn.clicked.connect(self.zcenter)

        self.parent.step1_btn.clicked.connect(self.step1)
        self.parent.step2_btn.clicked.connect(self.step2)
        self.parent.step3_btn.clicked.connect(self.step3)
        self.parent.step4_btn.clicked.connect(self.step4)
        
        self.parent.set_machine_btn.clicked.connect(self.setSetting)
        self.laser_type = self.parent.findChild(QComboBox, "laser_type")
        self.zaxi_travel = self.parent.findChild(QLineEdit, "zaxi_travel")
        self.set_default_focus = self.parent.findChild(QLineEdit, "set_default_focus")

        self.parent.refresh_btn.clicked.connect(self.refreshCom)
        self.parent.connect_btn.clicked.connect(self.connectCom)
        
        self.fh.checkDir(self.config_dir_path)
        self.fh.ini_parser.read(self.config_file_path)
        
        self.showComPort()
        self.showBaudRate()
        self.showLaserType()
        self.autoComConnect()
        self.loadSettings()
        
        self.ter_edit = self.parent.findChild(QLineEdit, "ter_edit")
        self.ter_browser = self.parent.findChild(QTextEdit, "ter_browser")
        self.ter_btn = self.parent.findChild(QPushButton, "ter_btn")
        self.parent.ter_btn.clicked.connect(self.terAck)
        self.ter_edit.returnPressed.connect(self.terAck)
        
        #according to me 1st
        self.laser_dia = self.parent.findChild(QLineEdit, "laser_dia")
        self.laser_current = self.parent.findChild(QLineEdit, "laser_current")
        self.laser_density = self.parent.findChild(QLineEdit, "laser_density")
        self.set_parameter = self.parent.findChild(QGroupBox, "set_parameter")
        self.parent.set_para.clicked.connect(self.setPara)
        
        self.parent.laser_dia.returnPressed.connect(self.setPara)
        self.parent.laser_current.returnPressed.connect(self.setPara)

        #2nd
        self.focus_pos_mm = self.parent.findChild(QLineEdit, "focus_pos_mm")
        self.focus_pos = self.parent.findChild(QGroupBox, "focus_pos")
        self.parent.focus_btn.clicked.connect(self.setFocus)
        self.parent.laser_btn.clicked.connect(self.setLaser)
        
        #3rd
        self.object_height = self.parent.findChild(QLineEdit, "object_height")
        self.set_obj_height = self.parent.findChild(QGroupBox, "set_obj_height")
        self.parent.object_height.returnPressed.connect(self.setObjectHeight)
                
        #4th
        self.hrs = self.parent.findChild(QLineEdit, "hrs")
        self.mins = self.parent.findChild(QLineEdit, "mins")
        self.secs = self.parent.findChild(QLineEdit, "secs")
        self.set_laser_time = self.parent.findChild(QGroupBox, "set_laser_time")
        self.parent.set_time.clicked.connect(self.setTime)
        
        #5th
        self.time = self.parent.findChild(QGroupBox, "time")
        self.hr = self.parent.findChild(QLCDNumber, "hr")
        self.min = self.parent.findChild(QLCDNumber, "min")
        self.sec = self.parent.findChild(QLCDNumber, "sec")
        
        self.parent.start_btn.clicked.connect(self.startBtn)
        self.parent.pause_btn.clicked.connect(self.pauseBtn)
        self.parent.reset_btn.clicked.connect(self.resetBtn)
        self.parent.restart_btn.clicked.connect(self.restartBtn)
        
        self.parent.laser_dia.textChanged.connect(self.validateSettings)
        self.parent.laser_current.textChanged.connect(self.validateSettings)
        self.parent.laser_density.textChanged.connect(self.validateSettings)

        self.validateSettings()
        self.parent.time.setEnabled(False)
  
    def validateSettings(self):
        self.parent.focus_pos.setEnabled(False)
        self.parent.set_obj_height.setEnabled(False)
        self.parent.set_laser_time.setEnabled(False)
        self.parent.time.setEnabled(False)
        self.parent.laser_density.setEnabled(False)
        self.parent.set_para.setEnabled(False)

    def setPara(self):
        dia = self.parent.laser_dia.text().strip()
        current = self.parent.laser_current.text().strip()

        if not dia or not current:
            QMessageBox.warning(self, "Input Error", "Please enter valid Diameter and Current values.")
            return

        try:
            dia = float(dia)
            current = float(current)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter numerical values for Diameter and Current.")
            return

        print(f"Laser Spot Diameter: {dia}")
        print(f"Laser Current: {current}")
        print(f"Laser Type: {self.parent.laser_type.currentText()}")

        laserConf = Laser(self.laser_type_list)
        laserConf.setLaserType(str(self.parent.laser_type.currentText()))

        dstatus, density = laserConf.getDensity(current, dia)

        print(f"Density Status: {dstatus}, Value: {density}")

        if dstatus == "valid":
            self.parent.laser_density.setText(str(density))
            self.parent.set_para.setEnabled(True)
            
            self.parent.set_para.clicked.connect(lambda: self.parent.focus_pos.setEnabled(True))
            
        else:
            self.laser_density.clear()
            self.parent.set_para.setEnabled(False)
            self.parent.focus_pos.setEnabled(False)
            QMessageBox.warning(self, "Invalid Density", "The entered values resulted in an invalid density.")

    def setFocus(self):
        print("Focus Position Button Pressed")
        focus_position = self.focus_pos_mm.text().strip() if self.focus_pos_mm else ""
        try:
            focus_position = float(focus_position)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid Focus Position. Please enter a valid number.")
            return
        set_Object_Height = f"G1 Z{focus_position} F500"
        self.sendGcode(set_Object_Height)
        print(f"Moving Z-axis to {set_Object_Height} (set_Object_Height)")
        
        self.parent.set_obj_height.setEnabled(True)
            
    def setLaser(self):
        if self.parent.laser_btn.text() == "Laser On":
            self.sendGcode("M106 P0 S255")
            self.parent.laser_btn.setText("Laser Off")
        else:
            self.sendGcode("M106 P0 S0")
            self.parent.laser_btn.setText("Laser On")
    
    def setObjectHeight(self):
        object_height_value = self.object_height.text().strip() if self.object_height else ""

        if not object_height_value:
            QMessageBox.warning(self, "Input Error", "Please enter an object height.")
            return

        try:
            object_height_value = float(object_height_value)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid Object Height. Please enter a valid number.")
            return

        if object_height_value > 0:
            set_object_height_cmd = f"G1Z{object_height_value}F500"
            self.sendGcode(set_object_height_cmd)
            print(f"Command Sent: {set_object_height_cmd}")
        else:
            QMessageBox.warning(self, "Validation Error", "Object height cannot be zero!")
            
        self.parent.set_laser_time.setEnabled(True)
            
    def setTime(self):
        hrs = self.hrs.text().strip()
        mins = self.mins.text().strip()
        secs = self.secs.text().strip()

        if not hrs and not mins and not secs:
            QMessageBox.warning(self, "Invalid Input", "Please set a valid time before proceeding.")
            return

        hrs = hrs if hrs else "00"
        mins = mins if mins else "00"
        secs = secs if secs else "00"

        self.time.setEnabled(True)

        self.remaining_time = int(hrs) * 3600 + int(mins) * 60 + int(secs)
        self.updateTimeDisplay()
        self.parent.pause_btn.setEnabled(False)
        self.parent.reset_btn.setEnabled(False)

    def startBtn(self):
        # self.pause_btn.setEnabled()
        # self.reset_btn.setEnabled(True)
        if self.remaining_time > 0:
            self.set_laser_time.setEnabled(False)
            self.sendGcode("M106 P0 S255")

            if not hasattr(self, 'timer'):
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.updateTimer)

            self.timer.start(1000)
            
            self.parent.start_btn.setEnabled(False)
            self.parent.pause_btn.setEnabled(True)
            self.parent.reset_btn.setEnabled(True)
            # self.reset_btn.setEnabled(True)

    def updateTimer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.updateTimeDisplay()
        else:
            self.timer.stop()
            self.parent.time.setEnabled(False)
            self.parent.set_laser_time.setEnabled(True)

            self.parent.start_btn.setEnabled(True)
            self.parent.pause_btn.setEnabled(False)
            self.parent.reset_btn.setEnabled(False)
            self.sendGcode("M106 P0 S0")

    def updateTimeDisplay(self):
        hrs = self.remaining_time // 3600
        mins = (self.remaining_time % 3600) // 60
        secs = self.remaining_time % 60
        # self.time.setTitle(f"Time: {hrs:02}:{mins:02}:{secs:02}")
        
        self.hr.display(hrs)
        self.min.display(mins)
        self.sec.display(secs)

        
    def pauseBtn(self):
        if self.timer.isActive():
            self.timer.stop()
            self.parent.pause_btn.setText("Resume")
            self.sendGcode("M106 P0 S0")
        else:
            self.timer.start(1000)
            self.parent.pause_btn.setText("Pause")
            self.sendGcode("M106 P0 S255")
    
    def resetBtn(self):
        self.hrs.clear()
        self.mins.clear()
        self.secs.clear()
        if hasattr(self, "timer"):
            self.timer.stop()
            
        self.hr.display(0)
        self.min.display(0)
        self.sec.display(0)

        self.sendGcode("M106 S0 P0")
        self.parent.time.setEnabled(False)
        self.parent.set_laser_time.setEnabled(True)
        self.parent.start_btn.setEnabled(True)
        
    def restartBtn(self):
        self.laser_dia.clear()
        self.laser_current.clear()
        self.laser_density.clear()

        self.object_height.clear()
        self.sendGcode("M106 S0 P0")
        
        self.hrs.clear()
        self.mins.clear()
        self.secs.clear()
        
        if hasattr(self, "timer"):
            self.timer.stop()
            
        self.hr.display(0)
        self.min.display(0)
        self.sec.display(0)
            
        self.parent.focus_pos.setDisabled(True)
        self.parent.set_obj_height.setDisabled(True)
        self.parent.set_laser_time.setDisabled(True)
        self.parent.time.setDisabled(True)
        
    def setSetting(self):
        z_travel = self.zmax - self.zmin

        self.laser_type = self.findChild(QComboBox, "laser_type")
        laser_type = self.laser_type.currentText() if self.laser_type else ""

        set_default_focus = self.set_default_focus.text().strip() if self.set_default_focus else ""
        
        if not z_travel or not set_default_focus or not laser_type:
            QMessageBox.warning(self, "Warning", "Please fill in all fields!")
            return

        section = "MACHINE_SETTINGS"
        self.fh.addParameter(section, "z_travel", str(z_travel))
        self.fh.addParameter(section, "laser_type", laser_type)
        self.fh.addParameter(section, "set_default_focus", set_default_focus)
        
        self.fh.updateFile(self.config_file_path)
        self.focus_pos_mm.setText(set_default_focus)

        print(f"Settings Saved: Z-axis Travel = {z_travel}, Laser Type = {laser_type}, Set Default Focus = {set_default_focus}")
        QMessageBox.information(self, "Settings", "Z-axis travel, Laser Type, and Set Default Focus saved successfully.")
        
    def loadSettings(self):
        section = "MACHINE_SETTINGS"

        z_travel = self.fh.getValues(section, "z_travel") if self.fh.getValues(section, "z_travel") else "100"
        laser_type = self.fh.getValues(section, "laser_type") if self.fh.getValues(section, "laser_type") else ""
        set_default_focus = self.fh.getValues(section, "set_default_focus") if self.fh.getValues(section, "set_default_focus") else "10"
        
        self.parent.zaxi_travel.setText(z_travel)
        self.parent.laser_type.setCurrentText(laser_type)
        self.parent.set_default_focus.setText(set_default_focus)

        self.parent.focus_pos_mm.setText(set_default_focus)

        print(f"Loaded Settings: Z-axis Travel = {z_travel}, Laser Type = {laser_type}, Set Default Focus = {set_default_focus}")
            
    def terAck(self):
        print("Terminal")
        if self.ter_edit:
            gcode_text = self.ter_edit.text()
            if gcode_text:
                self.ter_edit.clear()
                print(f"G-code: {gcode_text}")
                self.sendGcode(gcode_text)
            else:
                pass

    def comboAddList(self, combo_box, data_list):
        combo_box.clear()
        combo_box.addItems(data_list)

    def getComPort(self):
        self.port_list = self.serial_com.getPorts()
        
    def getLasersType(self):
        self.laser_type_list = self.laser_ty.getLasersType()

    def getBaudRate(self):
        self.baudrate_list = self.serial_com.getBaudrates()

    def setComPara(self, **kwargs):
        port = kwargs.get("port", "COM1")
        baud = kwargs.get("baud", "115200")
        
        if port:
            self.serial_com.port = port

        if baud:
            self.serial_com.baudrate = baud

    def comThread(self, action):
        print(f"serial thread : {action}")
        if action == "start":
            if self.serial_com.port and self.serial_com.baudrate:
                self.serial_com.connect(self.serial_com.port, self.serial_com.baudrate)
                print("Serial Thread started")

        elif action == "stop":
            if self.serial_com.is_running:
                self.serial_com.disconnect()
                print("Serial Thread stopped")

    def updateData(self, msg):
        if msg:
            data = msg.strip("\n")

        if data:
            self.gcode.decode(data)

            if data == "ok":
                data = f"{data}\n"

            if self.gcode.temp_report_flag and self.temp_report_hide_flag:
                self.gcode.temp_report_flag = False
            
            else:
                print(f"Received : {data}")
                self.ter_browser.append(data)

    def updateException(self, args):
        print(f"args : {args}")
        self.com_errorFlag = True
        print(f"error flag: True : {self.com_errorFlag}")

        self.comAction("stop")

    def serialSend(self, arg):
        self.serial_com.send(arg)

    def sendGcode(self, gstr):
        self.gcode.encode(gstr)

        if self.gcode.sd_write_flag:
            cs = self.gcode.checksum(gstr)
            gcode = f"{gstr}*{cs}\r\n"

        else:
            gcode = f"{gstr}\r\n"

        self.serial_com.send(gcode)
        print(f"Gcode : {gcode}")

    def setPos(self):
        print(f"POS : {self.gcode.pos_list}")

        xpos, ypos, zpos = None, None, None

        for item in self.gcode.pos_list:
            axis, value = item.split(':')
            if axis == 'X':
                xpos = float(value)
            elif axis == 'Y':
                ypos = float(value)
            elif axis == 'Z':
                zpos = float(value)
       
        print(f"xpos = {xpos}")
        print(f"ypos = {ypos}")
        print(f"zpos = {zpos}")

        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos

        self.setAxis(xpos, ypos, zpos)

    def setAxis(self, x, y, z):
        xpos_str = str(x)
        ypos_str = str(y)
        zpos_str = str(z)

        self.parent.xcord.display(xpos_str)
        self.parent.ycord.display(ypos_str)
        self.parent.zcord.display(zpos_str)

    def axisTravel(self, dir, pos, step, min, max):
        if dir == self.jog_inc_code:
            pos = pos + step

        elif dir == self.jog_dec_code:
            pos = pos - step

        if pos > max:
            pos = max

        if pos < min:
            pos = min

        print(f"axis travel > dir : {dir}, pos : {pos}, step : {step}, min : {min}, max : {max}")

        return pos

    def jogAxis(self, arg):
        axis = arg[0].upper()
        dir = arg[-1]

        pos_args = {"X" : self.xpos, "Y" : self.ypos, "Z" : self.zpos}
        min_args = {"X" : self.xmin, "Y" : self.ymin, "Z" : self.zmin}
        max_args = {"X" : self.xmax, "Y" : self.ymax, "Z" : self.zmax}
        travel = 0

        pos = pos_args.get(axis)
        min = min_args.get(axis)
        max = max_args.get(axis)
        step = self.step

        if self.ut.argIsNotNone(self, pos, min, max):
            pos = self.axisTravel(dir, pos, step, min, max)
            travel = pos

            print(f"axis : {axis}, direction : {dir}, step : {self.step}, pos : {travel}")

            gcode = f"{self.gcode.gcode_dict.get("lmove1")} {axis}{travel} F1200"
            self.sendGcode(gcode)
            self.sendGcode(self.gcode.gcode_dict.get("get-pos"))

        else:
            print("Jog error")

    def showComPort(self, port_list=None):
        if port_list is None:
            self.getComPort()
            port_list = self.port_list

        self.comboAddList(self.parent.port_combo, port_list)

    def showBaudRate(self, baud_list=None):
        if baud_list is None:
            self.getBaudRate()
            baud_list = self.baudrate_list

        self.comboAddList(self.parent.baudrate_combo, baud_list)
        
    def showLaserType(self, laser_option=None):
        if laser_option is None:
            self.getLasersType()
            laser_option = self.laser_type_list
            
        self.comboAddList(self.laser_type, laser_option)

    def xhome(self):
        print("X home Btn press")
        self.sendGcode("G28 X")
        self.homePos()

    def yhome(self):
        print("Y home Btn press")
        self.sendGcode("G28 Y")
        self.homePos()

    def zhome(self):
        print("Z home Btn press")
        self.sendGcode("G28 Z")
        self.homePos()

    def home(self):
        print("Home Btn press")
        self.sendGcode("G28")
        self.homePos()
        
    def homePos(self):
        self.sendGcode("M114")

    def xplus(self):
        print("X Plus Btn press")
        self.jogAxis("xp")

    def xminus(self):
        print("X Minus Btn press")
        self.jogAxis("xm")

    def yplus(self):
        print("Y Plus Btn press")
        self.jogAxis("yp")

    def yminus(self):
        print("Y Minus Btn press")
        self.jogAxis("ym")
    

    def zplus(self):
        print("Z Plus Btn press")
        self.jogAxis("zp")

    def zminus(self):
        print("Z Minus Btn press")
        self.jogAxis("zm")

    def zcenter(self):
        print("Z Center Button Pressed")
        set_default_focus = self.set_default_focus.text().strip() if self.set_default_focus else ""
        try:
            z_focus_position = float(set_default_focus)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid Z Focus Position. Please enter a valid number.")
            return
        set_focus_pos = f"G1 Z{z_focus_position} F500"
        self.sendGcode(set_focus_pos)
        print(f"Moving Z-axis to {set_focus_pos} (set_focus_pos)")

    def step1(self):
        print("Step1 Btn press")
        self.step = 10.0

    def step2(self):
        print("Step2 Btn press")
        self.step = 5.0

    def step3(self):
        print("Step3 Btn press")
        self.step = 1.0

    def step4(self):
        print("Step4 Btn press")
        self.step = 0.1

    def refreshCom(self):
        print("Refresh Btn press")
        self.getComPort()
        self.getBaudRate()

        self.port_list.insert(0, " ")
        self.baudrate_list.insert(0, " ")

        self.comboAddList(self.port_combo, self.port_list)
        self.comboAddList(self.baudrate_combo, self.baudrate_list)

        self.com_errorFlag = False

    def connectCom(self):
        print("Connect Btn press")
        self.comAction(self.connect_btn.text())
        
    def setSerialPort(self, port):
        self.serial_com.port = port

    def setSerialBaud(self, baudrate):
        self.serial_com.baudrate = baudrate

    def comAction(self, action):
        if not self.com_errorFlag:
            pass

        if action == "Connect" and not self.com_errorFlag:
            self.parent.connect_btn.setText("Disconnect")

            port = self.parent.port_combo.currentText()
            baudrate = self.parent.baudrate_combo.currentText()
            print(f"Port : {port}, Baudrate : {baudrate}")

            if port and baudrate:
                self.setSerialPort(port)
                self.setSerialBaud(baudrate)

                if port in self.serial_com.getPorts():
                    self.serialThread("start")

                    self.fh.addParameter("com", "port", port)
                    self.fh.addParameter("com", "baudrate", baudrate)

                    self.fh.updateFile(self.config_file_path)

                else:
                    print(f"Port : {port} is unavailable")
                    self.parent.connect_btn.setText("Connect")

        if action == "Disconnect":
            self.parent.connect_btn.setText("Connect")
            
            if not self.com_errorFlag:
                self.serialThread("stop")
                
    def serialThread(self, action):
        print(f"serial thread : {action}")
        if action == "start":
            if self.serial_com.port and self.serial_com.baudrate:
                self.serial_com.connect(self.serial_com.port, self.serial_com.baudrate)
                print("Serial Thread started")

        elif action == "stop":
            if self.serial_com.is_running:
                self.serial_com.disconnect()
                print("Serial Thread stopped")
                
    def autoComConnect(self):
        com_port = self.fh.getValues("com", "port")
        com_baud = self.fh.getValues("com", "baudrate")
        print(f"port : {com_port}, baudrate : {com_baud}")

        if com_port and com_baud:
            if com_port in self.serial_com.getPorts():
                self.parent.connect_btn.setText("Disconnect")

                self.setSerialPort(com_port)
                self.setSerialBaud(com_baud)

                if com_port in self.port_list:
                    index = self.port_list.index(com_port)  
                    self.parent.port_combo.setCurrentIndex(index)

                if com_baud in self.baudrate_list:
                    index = self.baudrate_list.index(com_baud)  
                    self.parent.baudrate_combo.setCurrentIndex(index)

                self.serialThread("start")

                msg = "Auto Com connect successfull"
                print(msg)

            else:
                msg = "Auto Com connect failed"
                print(msg)

    def comDisconnect(self):
        self.parent.connect_btn.setText("Connect")
            
        if not self.com_errorFlag:
            self.comThread("stop")

        
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = UI()
    win.show()
    sys.exit(app.exec())


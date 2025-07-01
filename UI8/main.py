import sys
import os
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox, QInputDialog, QLineEdit
from PySide6.QtCore import QFile, Qt
from PySide6.QtCore import QUrl
import requests
from pathlib import Path
from PySide6.QtGui import QDesktopServices

from com import SerialCom
from util import CallbackHandler, FileHandler, Gcode, Utils

class UI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.parent = parent

        self.serial_com = SerialCom()
        self.fh = FileHandler()
        self.gcode = Gcode()
        self.ut = Utils()
        self.cb = CallbackHandler()

        config_dir = "config"
        config_file = "config.ini"

        self.config_dir_path = self.fh.getPath(dir=config_dir)
        self.config_file_path = self.fh.getPath(dir=self.config_dir_path, file=config_file)

        self.port_list = []
        self.baudrate_list = []
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

        # self.parent.eplus_btn.clicked.connect(self.eplus)
        # self.parent.eminus_btn.clicked.connect(self.eminus)
        # self.parent.ezero_btn.clicked.connect(self.ezero)

        self.parent.step1_btn.clicked.connect(self.step1)
        self.parent.step2_btn.clicked.connect(self.step2)
        self.parent.step3_btn.clicked.connect(self.step3)
        self.parent.step4_btn.clicked.connect(self.step4)
        
        self.parent.update_btn.clicked.connect(self.updateBtn)

        # self.parent.set_btn.clicked.connect(self.setSetting)
        # self.parent.factory_btn.clicked.connect(self.factorySetting)

        self.parent.refresh_btn.clicked.connect(self.refreshCom)
        self.parent.connect_btn.clicked.connect(self.connectCom)
        
        self.showComPort()
        self.showBaudRate()
        self.autoComConnect()
        
    def updateBtn(self):

        reply = QMessageBox.question(
            self,
            "Confirm Update",
            "Are you sure you want to update your UI?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:

            password, ok = QInputDialog.getText(
                self,
                "Authentication Required",
                "Enter your password:",
                QLineEdit.Password
            )

            if ok:
                if password == "admin123":
                    print("Password correct. Proceeding with update...")

                    QMessageBox.information(
                        self,
                        "Success",
                        "You have successfully entered the password."
                    )

                    url = QUrl("https://github.com/prities04/ota-update-demo")
                    QDesktopServices.openUrl(url)
                    
                    self.download_github_repo_to_desktop()

                else:
                    QMessageBox.warning(self, "Error", "Incorrect password.")
            else:
                print("Password input canceled.")
        
    def download_github_repo_to_desktop(self):
        # def download_github_repo_to_desktop(self):
        folder_url = "https://github.com/prities04/ota-update-demo/tree/main/OTA4%23"
        downgit_url = f"https://minhaskamal.github.io/DownGit/#/home?url={folder_url}"

        # Open DownGit folder download page in browser
        QDesktopServices.openUrl(QUrl(downgit_url))

        QMessageBox.information(
            self,
            "Download Folder",
            "The folder will open in your browser. Click the download button to save it as a ZIP file."
        )
            
    def comboAddList(self, combo_box, data_list):
        combo_box.clear()
        combo_box.addItems(data_list)

    def getComPort(self):
        self.port_list = self.serial_com.getPorts()        

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

    def updateException(self, args):
        print(f"args : {args}")
        self.com_errorFlag = True
        print(f"error flag: True : {self.com_errorFlag}")

        self.comAction("stop")
        
        # self.serialErrorHandle()

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

        # Initialize variables
        xpos, ypos, zpos, epos = None, None, None

        # Iterate over the POS list and assign values
        for item in self.gcode.pos_list:
            axis, value = item.split(':')
            if axis == 'X':
                xpos = float(value)
            elif axis == 'Y':
                ypos = float(value)
            elif axis == 'Z':
                zpos = float(value)
            elif axis == 'E':
                epos = float(value)
       
        print(f"xpos = {xpos}")
        print(f"ypos = {ypos}")
        print(f"zpos = {zpos}")
        print(f"epos = {epos}")

        self.xpos = xpos
        self.ypos = ypos
        self.zpos = zpos
        self.epos = epos

        self.setAxis(xpos, ypos, zpos, epos)

    def setAxis(self, x, y, z, e):
        xpos_str = str(x)
        ypos_str = str(y)
        zpos_str = str(z)
        epos_str = str(e)
        self.parent.xcord.display(xpos_str)
        self.parent.ycord.display(ypos_str)
        self.parent.zcord.display(zpos_str)
        self.parent.ecord.display(epos_str)

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

        pos_args = {"X" : self.xpos, "Y" : self.ypos, "Z" : self.zpos, "E" : self.epos}
        min_args = {"X" : self.xmin, "Y" : self.ymin, "Z" : self.zmin, "E" : self.emin}
        max_args = {"X" : self.xmax, "Y" : self.ymax, "Z" : self.zmax, "E" : self.emax}
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

        self.comboAddList(self.parent.baud_combo, baud_list)


    def xhome(self):
        print("X home Btn press")
        self.sendGcode("G28 X")

    def yhome(self):
        print("Y home Btn press")
        self.sendGcode("G28 Y")

    def zhome(self):
        print("Z home Btn press")
        self.sendGcode("G28 Z")

    def home(self):
        print("Home Btn press")
        self.sendGcode("G28")


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
        print("Z Center Btn press")
        self.sendGcode("G28")

    def eplus(self):
        print("E Plus Btn press")
        self.jogAxis("ep")       

    def eminus(self):
        print("E minus Btn press")
        pass

    def ezero(self):
        print("E Zero Btn press")


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


    def setSetting(self):
        print("Set Btn press")

    def factorySetting(self):
        print("Factory Btn press")

    def refreshCom(self):
        print("Refresh Btn press")
        self.getComPort()
        self.getBaudRate()

        self.port_list.insert(0, " ")
        self.baudrate_list.insert(0, " ")

        self.comboAddList(self.parent.port_combo, self.port_list)
        self.comboAddList(self.parent.baud_combo, self.baudrate_list)

        self.com_errorFlag = False

    def connectCom(self):
        print("Connect Btn press")
        self.comAction(self.parent.connect_btn.text())

    def comAction(self, action):
        if action == "Connect" or action == "connect":
            self.parent.connect_btn.setText("Disconnect")
            self.comConnect()

        if action == "Disconnect" or action == "disconnect":
            self.parent.connect_btn.setText("Connect")
            self.comDisconnect()

    def comConnect(self):
        port = self.parent.port_combo.currentText()
        baudrate = self.parent.baud_combo.currentText()
        print(f"Port : {port}, Baudrate : {baudrate}")

        if port and baudrate:
            self.setComPara(port=port, baud=baudrate)

            if port in self.serial_com.getPorts():
                self.comThread("start")

                self.fh.addParameter("com", "port", port)
                self.fh.addParameter("com", "baudrate", baudrate)

                self.fh.updateFile(self.config_file_path)

            else:
                print(f"Port : {port} is unavailable")
                self.parent.connect_btn.setText("Connect")
                
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
    loader = QUiLoader()
    window = loader.load("app.ui", None)
    UI(window)
    window.show()
    app.exec()


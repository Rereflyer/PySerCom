#!coding:utf-8

import re
import sys
import serial
import serial.tools.list_ports
import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QToolTip
from PyQt5.QtCore import QTimer
from PyQt5.uic import loadUi

class Cla_Com_Tool(QMainWindow):
    def __init__(self):
        super().__init__()

        loadUi('ui_SerCom.ui',self)

        # init parameter
        self.ser = None

        self.vi_com_open = False #vb - v 变量 i整形
        self.vi_hex_show= False
        self.vi_hex_send = False
        self.vs_send_str_hex = ""
        self.vs_send_str_char = ""
        self.vb_read_data = b""
        self.vi_rxd_num = 0
        self.vi_send_num = 0
        self.vi_show_time = 0
        self.vi_time_make = 0
        self.read_time = 0
        self.write_time = 0

        self.tmr_send_Ser = None
        self.tmr_read_Ser = None
        self.tmr_stcha_Ser = None

        self.initSys()

    def initSys(self):
        self.ser = serial.Serial()
        self._find_port()

        self._close_ser()
        self.show()
        #-----------------------
        self.tmr_send_Ser = QTimer()
        #-----------------------
        self.read_time = 20   #间隔读取时间
        self.tmr_read_Ser = QTimer()
        self.tmr_read_Ser.setInterval(20)
        self.tmr_read_Ser.timeout.connect(self._time_read_event)
        self.tmr_read_Ser.start()
        self.write_time = 0  #间隔发送时间
        #-----------------------
        self.tmr_stcha_Ser = QTimer()
        self.read_time = 20   #间隔读取时间
        self.tmr_stcha_Ser.setInterval(100)
        self.tmr_stcha_Ser.timeout.connect(self._send_hex_check)
        #-----------------------
        self.open_com_qpb.clicked.connect(self._open_com)
        self.show_clear_qpb.clicked.connect(self._clear_show_data)
        self.hex_show_chb.stateChanged.connect(self._hex_char_show)
        self.hex_send_chb.stateChanged.connect(self._hex_char_send)
        self.send_qpb.clicked.connect(self._send_data)
        self.comname_cob.highlighted.connect(self._find_port)
        self.interval_chb.stateChanged.connect(self._interval_send_tmr)
        self.interval_spb.valueChanged.connect(self._interval_send_tmr)
        self.send_pte.textChanged.connect(self.tmr_stcha_Ser.start)
        self.time_make_chb.stateChanged.connect(self._time_make_tmr)
             
        
    def _time_make_tmr(self):
        if self.time_make_chb.isChecked():
            self.vi_time_make = 1
            self.show_rx_qte.append("")
            self.tmr_read_Ser.stop()
            self.read_time = self.interval_spb.value()   #间隔读取时间，只在设置时有效
            self.tmr_read_Ser.setInterval(self.read_time)
            self.tmr_read_Ser.start()
        else:
            self.vi_time_make = 0
            self.show_rx_qte.append("")
            self.tmr_read_Ser.stop()
            self.tmr_read_Ser.setInterval(20)
            self.tmr_read_Ser.start()
        

    def _send_hex_check(self):    #发送HEX切换槽
        self.tmr_stcha_Ser.stop
        if self.vi_hex_send:
            vs_temp = self.send_pte.toPlainText()
            
            vs_temp_1=re.sub(r'[^0-9^a-f^A-F]',"",vs_temp)
            self.vs_send_str_hex = re.sub(r"(.{2})","\\1 ",vs_temp_1)
            self.send_pte.setPlainText(self.vs_send_str_hex)
            
            cursor =  self.send_pte.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.send_pte.setTextCursor(cursor)
        else:
            self.vs_send_str_char = self.send_pte.toPlainText()     
        
        
    def _interval_send_tmr(self):     #间隔发送槽
        if(self.vi_com_open):
            if self.interval_chb.isChecked():
                send_time = self.interval_spb.value()   #间隔读取时间
                self.tmr_send_Ser.setInterval(send_time)
                self.tmr_send_Ser.timeout.connect(self._send_data)
                self.tmr_send_Ser.start()
            else:
                self.tmr_send_Ser.stop()
        

    def _send_data(self):  #发送数据
        if self.vi_hex_send:
            #self.vs_send_str_hex = self.send_pte.toPlainText() 
            vs_aa = self.vs_send_str_hex
            if(len(self.vs_send_str_hex) >= 2):
                if(self.vs_send_str_hex[-2]==" "):
                    vs_aa=self.vs_send_str_hex[0:-1]+"0"+self.vs_send_str_hex[-1]
                else:
                    vs_aa =self.vs_send_str_hex
            elif(len(self.vs_send_str_hex) == 1):
                    vs_aa = '0'+ self.vs_send_str_hex
            vb_temp = bytes.fromhex(vs_aa)
            #print(vb_temp)
            #vb_bb =bytes(''.join([chr(int(x,16)) for x in vs_aa.split()]), encoding = "gbk")
        else:
            #self.vs_send_str_char = self.send_pte.toPlainText() 
            vb_temp = bytes(self.vs_send_str_char, encoding = "gbk")
            
        self.ser.write(vb_temp)
        self.vi_send_num += len(vb_temp)
        self.send_num_lcd.display( self.vi_send_num)
        
    def _gbk_format(self, vb_input):
        vi_count = len(vb_input)
        vi_num = 0
        vb_gbk=b""
        while(vi_num < vi_count):
            if(vb_input[vi_num] < 0x7F):
                vs_hex = hex(vb_input[vi_num])
                if(vb_input[vi_num]>15):
                    
                    vs_hex = vs_hex[-2]+vs_hex[-1]
                else:
                    vs_hex = '0'+vs_hex[-1]
                vb_gbk += bytes.fromhex(vs_hex) 
                vi_num+=1
            elif ((vb_input[vi_num] >= 0x81) and (vb_input[vi_num]<=0xFE) and (vi_num+1 < vi_count)):
                if(vb_input[vi_num+1] >= 0x40 and vb_input[vi_num+1]<=0xFE and vb_input[vi_num+1]!=0x7F):
                    vs_hex = hex(vb_input[vi_num])
                    if(vb_input[vi_num]>15):
                        vs_hex = vs_hex[-2]+vs_hex[-1]
                    else:
                        vs_hex = '0'+vs_hex[-1]
                    vb_gbk += bytes.fromhex(vs_hex)
                    
                    vs_hex = hex(vb_input[vi_num+1])
                    if(vb_input[vi_num+1]>15):
                        vs_hex = vs_hex[-2]+vs_hex[-1]
                    else:
                        vs_hex = '0'+vs_hex[-1]
                    vb_gbk += bytes.fromhex(vs_hex)
                else:
                    vb_gbk += b'??'
                vi_num += 2
            else:
                vb_gbk += b'?'
                vi_num += 1   
        return vb_gbk    
            
        
    def _hex_char_show(self, state): #Hex发送显示
        if state==QtCore.Qt.Checked:  #self.hex_show_chb.isChecked())
            self.vi_hex_show= True
            #vs_temp = self.show_rx_qte.toPlainText()
            #vs_ss =" ".join("{:02x}".format(ord(c)) for c in vs_temp)
            vs_ss =' '.join([('%02X' % i) for i in self.vb_read_data])+" "
            self.show_rx_qte.setPlainText(vs_ss)
            
        elif state==QtCore.Qt.Unchecked:
            self.vi_hex_show= False
            #vb_ss = self.vb_read_data.decode('gbk', errors='ignore') 
            vs_ss = self._gbk_format(self.vb_read_data)
            try:
                #vs_b=vs_a.encoding('gbk', errors='ignore')
                vs_a = str(vs_ss, encoding = "gbk")
            except:
                return
            self.show_rx_qte.setPlainText(vs_a)
    
    def _hex_char_send(self):
        if self.hex_send_chb.isChecked():
            self.vi_hex_send = True
            self.send_pte.setPlainText(self.vs_send_str_hex)
            self.enter_show_chb.setEnabled(False)
        else:
            self.vi_hex_send = False
            self.send_pte.setPlainText(self.vs_send_str_char)
            self.enter_show_chb.setEnabled(True)


    def _clear_show_data(self):
        self.show_rx_qte.clear()
        self.vb_read_data = b""
        self.vi_rxd_num = 0
        self.vi_send_num = 0
        self.rec_num_lcd.display(0)
        self.send_num_lcd.display(0)
        

    def  _time_read_event(self):
        #QMessageBox.about(self,'提示','定时到')
        if not self.vi_com_open:
            return
            #----------------------
        try:
            num = self.ser.inWaiting()
        except:
            self._close_ser()
            QMessageBox.about(self,'提示','串口丢失，请检查端口')
            return
        if num > 0:
            vb_rxd_char = self.ser.read(num)
            self.vi_rxd_num += num
            self.vb_read_data  += vb_rxd_char
            if(self.vi_time_make): 
                ct=datetime.datetime.now()
                vi_aa = ct.microsecond
                vs_ms = str(vi_aa)
                if(vi_aa >= 100):
                    vs_time = "[" + ct.strftime("%H:%M:%S-") + vs_ms[0] + vs_ms[1] + vs_ms[2] + "]  "
                elif(vi_aa >= 10):
                    vs_time = "[" + ct.strftime("%H:%M:%S-") + vs_ms[0] + vs_ms[1]  + "0]  "
                else:
                    vs_time = "[" + ct.strftime("%H:%M:%S-") + vs_ms[0]  + "00]  "
                self.show_rx_qte.insertPlainText(vs_time)
                
            if self.vi_hex_show == True:   #vb：bytes 变量   vs：str变量
                self.show_rx_qte.insertPlainText(' '.join([('%02X' % i) for i in vb_rxd_char]))
                self.show_rx_qte.insertPlainText(' ')
                
            else:
                vb_bb = b''
                vb_bb = self._gbk_format(vb_rxd_char)
                try:
                    vs_a=str(vb_bb, encoding = "gbk")
                except:
                    return
                self.show_rx_qte.insertPlainText(vs_a)
                
            if(self.vi_time_make): 
                self.show_rx_qte.append('')
                
            cursor =  self.show_rx_qte.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            self.show_rx_qte.setTextCursor(cursor)
            self.rec_num_lcd.display(self.vi_rxd_num)

            #----------------------
            
    def _find_port(self):
        port_list = list(serial.tools.list_ports.comports())
        if(len(port_list) ==0):
            self.comname_cob.clear()
            self.comname_cob.addItems(["None"])
        else:
            if (self.comname_cob.count() == len(port_list)):
                for x in range(len(port_list)):
                    if(self.comname_cob.itemText(x)!=port_list[x].description):
                        print(self.comname_cob.itemText(x), " != ", port_list[x].description)
                        self.comname_cob.clear()
                        self.comname_cob.addItems([port.description for port in port_list])
                        return
                return
            else:
                self.comname_cob.clear()
                self.comname_cob.addItems([port.description for port in port_list])
            

    def _open_com(self):
        if(self.vi_com_open):
            self._close_ser()
        else:
            self._open_ser()

    def _open_ser(self):
        cha_port_name = self.comname_cob.currentText()
        lis_com = list(serial.tools.list_ports.comports())
        self.ser.port = None
        for y in range(len(lis_com)):
            #print(lis_com[y].description," V S  " , cha_port_name)
            if(lis_com[y].description == cha_port_name ):
                #print(lis_com[y].description,"  ==  " , cha_port_name)
                self.ser.port = lis_com[y].device
                break
        if(self.ser.port == None):
            self._close_ser()
            QMessageBox.about(self,'提示','串口获取失败')
            return
        self.ser.baudrate = int(self.baud_cob.currentText())
        self.ser.bytesize = 8 #int(self.bitbox.currentText())
        self.ser.parity = 'N' #self.crcbox.currentText()[0]
        self.ser.stopbits = 1 #int(self.stopbox.currentText())
        self.ser.xonxoff  = False  #软件流控
        self.ser.rtscts = False     #硬件流控
        self.ser.dsrdtr = False    #应答准备
        self.ser.close()
        try:
            self.ser.open()			
        except:
            self._close_ser()
            QMessageBox.about(self,'提示','串口打开失败')
            return
        self.vi_com_open = True	
        self.open_com_qpb.setText("关闭")
        self.send_qpb.setEnabled(True)
        self.interval_chb.setEnabled(True)
        self.open_com_qpb.setStyleSheet("background-color:green");
        #self._dis_ser_par(True)
        
    def _close_ser(self):
        self.ser.close()
        self.vi_com_open = False
        self.open_com_qpb.setText("打开")
        self.send_qpb.setEnabled(False)
        self.interval_chb.setEnabled(False)
        self.open_com_qpb.setStyleSheet("background-color:red");
        
    def _message_box(self, event):
        reply = QMessageBox.about(self,"消息框标题","消息框标题")
        self.echo(reply)
            
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ex = Cla_Com_Tool()
    sys.exit(app.exec_())

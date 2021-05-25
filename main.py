""""
@Auth: Cople
@Time: 2021.5
@IDE: PyCharm
"""
import binascii
import re
import sys

import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5 import QtCore
from PyQt5.Qt import *
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtWidgets import *

import queue
import random
from paho.mqtt import client as mqtt_client

datalist = []
cmdlist = []

num = 0

DATAQUEUE = queue.Queue()

TITLE = "电化学工作站"

# 用户信息
port = 1883
# sub_topic = "test"  # 订阅的主题
# pub_topic = "pub"  # 发布主题
# 随机生成Client ID
client_id = f'ternimal-mqtt-{random.randint(0, 100)}'


class PyQt_Serial(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tableWidget = QTableWidget()  # 创建一个列表
        self.PlotLayout = QGridLayout()
        self.ResultLayout = QHBoxLayout()  # 创建水平布局文件
        self.DataTab = QWidget()
        self.ResultTab = QWidget()
        self.PlotTab = QWidget()

        self.addTab(self.DataTab, "控制台")
        self.addTab(self.ResultTab, "测试结果")
        self.addTab(self.PlotTab, "数据打印")


        self.CreateItems()
        self.CreateLayout()
        self.CreateSignalSlot()

        self.Init_PlotUI()

        self.setWindowTitle('电化学工作站')
        self.setWindowIcon(QIcon('ICON.ico'))
        self.setFont(QFont('宋体', 9))

        # 创建变量
        self.sendCount = 0
        self.receiveCount = 0
        self.encoding = 'utf-8'
        self.updateTimer.start(100)
        self.scan_1_button_flag = 0  # 按钮按下标志位
        self.scan_2_button_flag = 0
        self.connectFlag = 1  # 连接变量
        self.wifiFlag = 0  # 连接成功标志 用于区分串口工作还是无线工作
        self.cmdstr = ''
        self.reverseFlag = 0  # 双向标志
        self.funCnt = 0

        self.scan_1_finish_flag = 0
        self.scan_2_finish_flag = 0

        self.broker = ""
        self.pubTopic = ""
        self.subTopic = ""
        self.du = 0
        self.U0 = 0
        self.U1 = 0
        self.dt = 0

        # measure
        self.measure_Ip = 0
        self.measure_Ep = 0
        self.measure_Ah = 0

        # set Value
        self.set_high_Ev = 0
        self.set_low_Ev = 0

    def CreateItems(self):
        self.com = QSerialPort()
        self.comNameLabel = QLabel('串口号')
        self.comNameLabel.setFixedWidth(80)
        self.comNameCombo = QComboBox()
        self.on_refreshCom()

        self.comNameCombo.setFixedWidth(80)
        self.baudLabel = QLabel('波特率')
        self.baudLabel.setFixedWidth(80)
        self.baudCombo = QComboBox()
        self.baudCombo.addItems(
            ('9600', '19200', '115200', '250000', '1000000'))
        self.baudCombo.setEditable(True)
        self.baudCombo.setCurrentIndex(2)
        self.baudCombo.setFixedWidth(80)
        self.bupt = QLabel('')  # BUPT
        self.bupt.setFont(QFont('Arial', 40, italic=True))

        ######## 编码方式 ##########
        self.comencodingLabel = QLabel('串口编码')
        self.UTF8Button = QRadioButton('UTF-8')
        self.GBKButton = QRadioButton('GBK')
        self.encodingGroup = QButtonGroup()
        self.encodingGroup.addButton(self.UTF8Button, 0)
        self.encodingGroup.addButton(self.GBKButton, 1)
        self.UTF8Button.setChecked(True)
        ######## 编码方式 ##########

        ######## Open & Close UART and so on##########

        self.clearReceivedButton = QPushButton('清空数据打印')
        self.clearReceivedButton.setFixedWidth(100)
        self.stopShowingButton = QPushButton('停止显示')
        self.stopShowingButton.setFixedWidth(100)
        self.hexShowingCheck = QCheckBox('Hex显示')
        self.hexShowingCheck.setFixedWidth(100)
        self.saveReceivedButton = QPushButton('保存显示数据')
        self.saveReceivedButton.setFixedWidth(100)
        self.refreshComButton = QPushButton('刷新串口')
        self.refreshComButton.setFixedWidth(100)

        self.openButton = QPushButton('打开串口')
        self.openButton.setFocus()
        self.openButton.setFixedWidth(80)
        self.closeButton = QPushButton('关闭串口')
        self.closeButton.setFixedWidth(80)

        self.scan_1Button = QPushButton('1-Scan')
        self.scan_1Button.setFixedWidth(100)
        self.PlotButton = QPushButton('2-Scan')
        self.PlotButton.setFixedWidth(100)

        self.connectButton = QPushButton('connect')
        self.connectButton.setFocus()
        self.connectButton.setFixedWidth(100)
        self.disconnectButton = QPushButton('disconnect')
        self.disconnectButton.setFixedWidth(100)

        self.setParaButton = QPushButton('设置参数')
        self.setParaButton.setFixedWidth(100)

        self.saveFigButton = QPushButton('保存图片')
        self.saveFigButton.setFixedWidth(100)

        self.clearFigButton = QPushButton('清除绘图')
        self.clearFigButton.setFixedWidth(100)
        ######## Open & Close UART and so on ##########

        ######## 数据显示 ##########
        self.receivedDataEdit = QPlainTextEdit()
        self.receivedDataEdit.setReadOnly(True)
        self.receivedDataEdit.setFont(QFont('Times New Roman', 12))

        self.inputEdit = QPlainTextEdit()
        self.inputEdit.setFixedHeight(70)
        self.inputEdit.setFont(QFont('Times New Roman', 12))

        self.urlLabel = QLabel('URL:')
        self.urlLabel.setFixedHeight(30)
        self.urlEdit = QLineEdit('mqtt.coplemqtt.xyz')
        self.urlEdit.setFixedHeight(30)
        self.urlEdit.setFixedWidth(200)

        self.pub_topicLabel = QLabel('Pub Topic:')
        self.pub_topicLabel.setFixedHeight(30)
        self.pubTopicEdit = QLineEdit('pub')
        self.pubTopicEdit.setFixedHeight(30)
        self.pubTopicEdit.setFixedWidth(80)

        self.sub_topicLabel = QLabel('Sub Topic:')
        self.sub_topicLabel.setFixedHeight(30)
        self.subTopicEdit = QLineEdit('test')
        self.subTopicEdit.setFixedHeight(30)
        self.subTopicEdit.setFixedWidth(80)

        # du
        self.duLabel = QLabel('du:')
        self.duLabel.setFixedHeight(30)
        self.duEdit = QLineEdit('1')
        self.duEdit.setFixedHeight(30)
        self.duEdit.setFixedWidth(80)

        # U0
        self.U0Label = QLabel('U0:')
        self.U0Label.setFixedHeight(30)
        self.U0Edit = QLineEdit('0')
        self.U0Edit.setFixedHeight(30)
        self.U0Edit.setFixedWidth(80)

        # U1
        self.U1Label = QLabel('U1:')
        self.U1Label.setFixedHeight(30)
        self.U1Edit = QLineEdit('1000')
        self.U1Edit.setFixedHeight(30)
        self.U1Edit.setFixedWidth(80)

        # dt
        self.dtLabel = QLabel('dt(ms):')
        self.dtLabel.setFixedHeight(30)
        self.dtEdit = QLineEdit('15')
        self.dtEdit.setFixedHeight(30)
        self.dtEdit.setFixedWidth(80)

        self.sendButton = QPushButton('发送')
        self.sendButton.setFixedWidth(105)
        self.sendButton.setFixedHeight(70)
        self.hexSendingCheck = QCheckBox('Hex发送')
        self.timerSendCheck = QCheckBox('定时发送   发送周期(毫秒)')

        self.timerPeriodEdit = QLineEdit('1000')
        self.timerPeriodEdit.setFixedHeight(20)
        self.timerPeriodEdit.setFixedWidth(50)

        self.clearInputButton = QPushButton('清空重填')
        self.clearCouterButton = QPushButton('计数清零')
        ######## 数据显示 ##########

        ######## 串口状态显示 ##########
        self.comStatus = QLabel('COM State：COM CLOSE')
        self.sendCountLabel = QLabel('S cnt：0')
        self.receiveCountLabel = QLabel('R cnt：0')
        ######## 串口状态显示 ##########

        self.sendTimer = QTimer()
        self.updateTimer = QTimer()
        self.mqttSendTimer = QTimer()
        self.doubleSendTimer = QTimer()

        self.closeButton.setEnabled(False)
        self.disconnectButton.setEnabled(False)
        self.sendButton.setEnabled(False)

    def CreateLayout(self):  # 布局
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.comNameLabel, 0, 0)
        self.mainLayout.addWidget(self.comNameCombo, 0, 1)
        self.mainLayout.addWidget(self.baudLabel, 1, 0)
        self.mainLayout.addWidget(self.baudCombo, 1, 1)

        self.mainLayout.addWidget(self.openButton, 2, 0)
        self.mainLayout.addWidget(self.closeButton, 2, 1)

        self.mainLayout.addWidget(self.urlLabel, 3, 0, 1, 1)
        self.mainLayout.addWidget(self.urlEdit, 4, 0, 1, 2)

        self.mainLayout.addWidget(self.pub_topicLabel, 5, 0)
        self.mainLayout.addWidget(self.pubTopicEdit, 5, 1)
        self.mainLayout.addWidget(self.sub_topicLabel, 6, 0)
        self.mainLayout.addWidget(self.subTopicEdit, 6, 1)

        self.mainLayout.addWidget(self.connectButton, 7, 0)
        self.mainLayout.addWidget(self.disconnectButton, 7, 1)
        # self.mainLayout.addItem(self.spacer,6,0,1,1)
        self.mainLayout.addWidget(self.duLabel, 8, 0, 1, 1, QtCore.Qt.AlignJustify)
        self.mainLayout.addWidget(self.duEdit, 8, 1, 1, 2)
        self.mainLayout.addWidget(self.U0Label, 9, 0, 1, 1, QtCore.Qt.AlignJustify)
        self.mainLayout.addWidget(self.U0Edit, 9, 1, 1, 2)
        self.mainLayout.addWidget(self.U1Label, 10, 0, 1, 1, QtCore.Qt.AlignJustify)
        self.mainLayout.addWidget(self.U1Edit, 10, 1, 1, 2)
        self.mainLayout.addWidget(self.dtLabel, 11, 0, 1, 1, QtCore.Qt.AlignJustify)
        self.mainLayout.addWidget(self.dtEdit, 11, 1, 1, 2)
        self.mainLayout.addWidget(self.setParaButton, 12, 0)
        self.mainLayout.addWidget(self.scan_1Button, 13, 0)
        self.mainLayout.addWidget(self.PlotButton, 13, 1)  # 1-Scan & 2-Scan
        self.mainLayout.addWidget(self.saveFigButton, 14, 0)
        self.mainLayout.addWidget(self.clearFigButton, 14, 1)

        self.PlotLayout.addWidget(self.receivedDataEdit)
        self.PlotTab.setLayout(self.PlotLayout)

        self.tableWidget.setRowCount(4)  # 设置行数
        self.tableWidget.setColumnCount(3)  # 设置列数
        self.ResultLayout.addWidget(self.tableWidget)
        self.ResultTab.setLayout(self.ResultLayout)


        self.mainLayout.addWidget(self.stopShowingButton, 15, 0, 1, 1)
        self.mainLayout.addWidget(self.saveReceivedButton, 15, 1, 1, 1)
        self.mainLayout.addWidget(self.refreshComButton, 16, 0, 1, 1)
        self.mainLayout.addWidget(self.clearReceivedButton, 16, 1, 1, 1)

        self.mainLayout.addWidget(self.inputEdit, 17, 2, 1, 6)
        self.mainLayout.addWidget(self.sendButton, 17, 8)
        self.mainLayout.addWidget(self.hexShowingCheck, 19, 2, 1, 1)
        self.mainLayout.addWidget(self.hexSendingCheck, 19, 3, 1, 1)

        self.mainLayout.addWidget(self.clearInputButton, 19, 5, 1, 1)
        self.mainLayout.addWidget(self.clearCouterButton, 20, 5, 1, 1)
        self.mainLayout.addWidget(self.timerSendCheck, 20, 2, 1, 1)
        self.mainLayout.addWidget(self.timerPeriodEdit, 20, 3, 1, 1)
        self.mainLayout.addWidget(self.sendCountLabel, 21, 7, 1, 1)
        self.mainLayout.addWidget(self.comStatus, 21, 0, 1, 3)
        self.mainLayout.addWidget(self.receiveCountLabel, 21, 8, 1, 1)
        self.mainLayout.setSpacing(5)

        self.setFixedSize(1265, 780)
        self.DataTab.setLayout(self.mainLayout)

    def CreateSignalSlot(self):  # 创建逻辑
        self.openButton.clicked.connect(self.on_openSerial)  # 打开串口
        self.closeButton.clicked.connect(self.on_closeSerial)  # 关闭串口
        self.com.readyRead.connect(self.on_receiveData)  # 接收数据
        self.sendButton.clicked.connect(self.on_sendData)  # 发送数据
        self.refreshComButton.clicked.connect(self.on_refreshCom)  # 刷新串口状态
        self.clearInputButton.clicked.connect(self.inputEdit.clear)  # 清空输入
        self.clearReceivedButton.clicked.connect(self.receivedDataEdit.clear)  # 清空接收
        self.stopShowingButton.clicked.connect(self.on_stopShowing)  # 停止显示
        self.clearCouterButton.clicked.connect(self.on_clearCouter)  # 清空计数

        self.saveReceivedButton.clicked.connect(self.on_saveReceivedData)  # 保存数据
        self.saveFigButton.clicked.connect(self.on_saveFigure)
        self.clearFigButton.clicked.connect(self.on_clearFigure)

        self.timerSendCheck.clicked.connect(self.on_timerSendChecked)  # 定时发送开关
        self.sendTimer.timeout.connect(self.on_sendData)  # 定时发送
        self.mqttSendTimer.timeout.connect(self.on_mqttSendData)
        self.doubleSendTimer.timeout.connect(self.on_doubleMqttSendData)

        self.updateTimer.timeout.connect(self.on_updateTimer)  # 界面刷新
        self.hexShowingCheck.stateChanged.connect(
            self.on_hexShowingChecked)  # 十六进制显示
        self.timerPeriodEdit.textChanged.connect(self.on_timerSendChecked)

        self.hexSendingCheck.stateChanged.connect(
            self.on_hexSendingChecked)  # 十六进制发送

        self.urlEdit.textChanged.connect(self.on_setUrl)
        self.pubTopicEdit.textChanged.connect(self.on_setPubTopic)
        self.subTopicEdit.textChanged.connect(self.on_setSubTopic)

        self.connectButton.clicked.connect(self.mqtt_run)
        self.disconnectButton.clicked.connect(self.mqtt_stop)

        self.duEdit.textChanged.connect(self.on_setdu)
        self.U0Edit.textChanged.connect(self.on_setU0)
        self.U1Edit.textChanged.connect(self.on_setU1)
        self.dtEdit.textChanged.connect(self.on_setdt)

        # 设置参数按钮
        self.setParaButton.clicked.connect(self.on_setdu)
        self.setParaButton.clicked.connect(self.on_setU0)
        self.setParaButton.clicked.connect(self.on_setU1)
        self.setParaButton.clicked.connect(self.on_setdt)
        self.setParaButton.clicked.connect(self.on_setQinfo)

        self.scan_1Button.clicked.connect(self.on_scan_1Button)  # 单次扫描
        self.PlotButton.clicked.connect(self.on_scan_2Button)  # 双向扫描

    def Init_PlotUI(self):
        self.openButton.clicked.connect(self.on_plot)  # 绘图
        self.connectButton.clicked.connect(self.on_plot)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')  # 设置背景色
        self.pw = pg.PlotWidget()
        self.pw.showGrid(x=True, y=True)
        self.mainLayout.addWidget(self.pw, 0, 2, 17, 7)

    def on_plot(self):
        timer = QTimer(self)
        timer.timeout.connect(self.update_plot)
        timer.start(0)

    def update_plot(self):
        global num
        if len(cmdlist):
            data_list = list(float(i) for i in datalist)
            cmd_list_re = list(float(i) for i in cmdlist)
            pg.QtGui.QApplication.processEvents()
            self.pw.plot(cmd_list_re, data_list, pen=pg.mkPen(color='r', width=1.5), clear=True,
                         symbol=None)  # symbol设置显示点的形状

            self.measure_Ip = max(data_list)
            self.set_high_Ev = max(cmd_list_re)
            self.set_low_Ev = min(cmd_list_re)
            if (cmd_list_re[-1] >= self.U1) and (self.scan_1_finish_flag == 1):
                cmd_list_re.clear()
                cmdlist.clear()
                data_list.clear()
                datalist.clear()
                self.scan_1_finish_flag = 0
                QMessageBox().information(self, "完成", "单向扫描完成！\n"
                                        + "ip=" + str(self.measure_Ip) + "A\n"
                                        + "Ep=" + str(self.measure_Ep) + "V\n"
                                        + "Ah=" + str(self.measure_Ah) + "C\n"
                                        + "High E(V)=" + str(self.set_high_Ev) + "mV\n"
                                        + "Low E(V)=" + str(self.set_low_Ev) + "mV\n")

            elif (cmd_list_re[-1] <= int(self.U0Edit.text())) and (self.scan_2_finish_flag == 1):
                cmd_list_re.clear()
                cmdlist.clear()
                data_list.clear()
                datalist.clear()
                self.scan_2_finish_flag = 0
                QMessageBox.information(self, "完成", "双向扫描完成！\n"
                                        + "ip=" + str(self.measure_Ip) + "A\n"
                                        + "Ep=" + str(self.measure_Ep) + "V\n"
                                        + "Ah=" + str(self.measure_Ah) + "C\n"
                                        + "High E(V)=" + str(self.set_high_Ev) + "mV\n"
                                        + "Low E(V)=" + str(self.set_low_Ev) + "mV\n")
            num = num + 1
        pass

    def on_clearFigure(self):
        print("clear")
        reply = QMessageBox.information(self, '清空绘图', '是否清空绘图？',
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            datalist.clear()
            cmdlist.clear()
            data_list = list(float(i) for i in datalist)
            self.pw.plot(data_list, pen=pg.mkPen(color='r', width=1.5), clear=True,
                         symbol=None)  #

    def on_refreshCom(self):
        self.comNameCombo.clear()
        com = QSerialPort()
        for info in QSerialPortInfo.availablePorts():
            com.setPort(info)

            if com.open(QSerialPort.ReadWrite):
                self.comNameCombo.addItem(info.portName())
                com.close()

    def on_setUrl(self):
        self.broker = self.urlEdit.text()

    def on_setPubTopic(self):
        self.pubTopic = self.pubTopicEdit.text()

    def on_setSubTopic(self):
        self.subTopic = self.subTopicEdit.text()

    def on_setdu(self):
        self.du = int(self.duEdit.text())

    def on_setU0(self):
        self.U0 = int(self.U0Edit.text())

    def on_setU1(self):
        self.U1 = int(self.U1Edit.text())

    def on_setdt(self):
        self.dt = int(self.dtEdit.text())
        print(type(self.dt))

    def on_setQinfo(self):
        self.cmdstr = ''
        if (self.dt < 14):
            QMessageBox().information(None, "提示", "时间间隔小于14ms串口数据易丢失！")
        else:
            QMessageBox.information(self, "设置参数", "设置成功！")

    def on_openSerial(self):
        comName = self.comNameCombo.currentText()
        comBaud = int(self.baudCombo.currentText())
        self.com.setPortName(comName)

        try:
            if not self.com.open(QSerialPort.ReadWrite):
                QMessageBox.critical(self, 'ERROR', 'COM opens failed！')
                return
        except:
            QMessageBox.critical(self, 'ERROR', 'COM opens failed！')
            return

        self.com.setBaudRate(comBaud)
        if self.timerSendCheck.isChecked():
            self.sendTimer.start(int(self.timerPeriodEdit.text()))
        datalist.clear()
        cmdlist.clear()
        self.wifiFlag = 0
        self.openButton.setEnabled(False)
        self.closeButton.setEnabled(True)
        self.comNameCombo.setEnabled(False)
        self.baudCombo.setEnabled(False)
        self.sendButton.setEnabled(True)
        self.refreshComButton.setEnabled(False)
        self.comStatus.setText('COM State：%s  OPEN   BAUD: %s' % (comName, comBaud))

    def on_closeSerial(self):
        self.com.close()
        self.openButton.setEnabled(True)
        self.closeButton.setEnabled(False)
        self.comNameCombo.setEnabled(True)
        self.baudCombo.setEnabled(True)
        self.sendButton.setEnabled(False)
        self.comStatus.setText('COM State：%s  CLOSE' % self.com.portName())
        if self.sendTimer.isActive():
            self.sendTimer.stop()

    def on_timerSendChecked(self):
        if self.com.isOpen():
            if self.timerSendCheck.isChecked():
                self.sendTimer.start(int(self.timerPeriodEdit.text()))
            else:
                self.sendTimer.stop()
        return

    def on_stopShowing(self):
        if self.stopShowingButton.text() == '停止显示':
            self.stopShowingButton.setText('继续显示')
        else:
            self.stopShowingButton.setText('停止显示')

    def on_clearCouter(self):
        self.sendCount = 0
        self.receiveCount = 0
        pass

    def on_updateTimer(self):
        self.sendCountLabel.setText('S cnt：%d' % self.sendCount)
        self.receiveCountLabel.setText('R cnt：%d' % self.receiveCount)
        pass

    def on_sendData(self):
        txData = self.inputEdit.toPlainText()
        if len(txData) == 0:
            return
        if self.hexSendingCheck.isChecked():
            s = txData.replace(' ', '')
            if len(s) % 2 == 1:  # 如果16进制不是偶数个字符,去掉最后一个
                QMessageBox.critical(self, '错误', '十六进制数不是偶数个')
                return
            if not s.isalnum():
                QMessageBox.critical(self, '错误', '包含非十六进制数')
                return

            try:
                hexData = binascii.a2b_hex(s)
            except:
                QMessageBox.critical(self, '错误', '转换编码错误')
                return

            try:
                n = self.com.write(hexData)
            except:
                QMessageBox.critical(self, '异常', '十六进制发送错误')
                return
        else:
            n = self.com.write(txData.encode(self.encoding, "ignore"))  # txdata write

        self.sendCount += n

    def on_receiveData(self):
        global datalist, cmdlist
        try:
            '''将串口接收到的QByteArray格式数据转为bytes,并用gkb或utf8解码'''
            receivedData = bytes(self.com.readAll())  # 使用串口接收，读到换行符即停readLine()比较慢，数据变少
            print(receivedData)
        except:
            QMessageBox.critical(self, '严重错误', '串口接收数据错误')
        if len(receivedData) > 0:
            self.receiveCount += len(receivedData)
            if self.stopShowingButton.text() == '停止显示':
                if not self.hexShowingCheck.isChecked():  # 若不是16进制显示
                    receivedData = receivedData.decode(self.encoding, 'ignore')
                    received_split_str = receivedData.split(',')
                    # print(type(received_split_str))
                    cmd_str = received_split_str[0][1:]
                    value_str = received_split_str[1][:-1]
                    # print('cmd:', cmd_str, 'value:', value_str)

                    cmd_list = self.decodeFrame(cmd_str)
                    value_list = self.decodeFrame(value_str)
                    print(cmd_list, value_list)

                    datalist.extend(value_list)
                    cmdlist.extend(cmd_list)  # 注意追加的变量

                    self.receivedDataEdit.insertPlainText(receivedData)  # 回显
                else:
                    data = binascii.b2a_hex(receivedData).decode('ascii')
                    pattern = re.compile('.{2}')
                    hexStr = ' '.join(pattern.findall(data)) + ' '
                    self.receivedDataEdit.insertPlainText(hexStr.upper())

    def on_hexShowingChecked(self):
        self.receivedDataEdit.insertPlainText('\n')

    def on_hexSendingChecked(self):
        if self.hexSendingCheck.isChecked():
            data = self.inputEdit.toPlainText().upper()
            self.inputEdit.clear()
            self.inputEdit.insertPlainText(data)

    def on_saveReceivedData(self):
        fileName, fileType = QFileDialog.getSaveFileName(
            self, '保存数据', 'data', "文本文档(*.txt);;所有文件(*.*)")
        print('Save f0ile', fileName, fileType)
        writer = QTextDocumentWriter(fileName)
        writer.write(self.receivedDataEdit.document())
        QMessageBox.information(self, "保存数据", ("成功保存至" + fileName + "!"))

    def on_saveFigure(self):
        print("save")
        fileName, fileType = QFileDialog.getSaveFileName(
            self, '保存图片', 'figure', "PNG可移植网络图形格式(*.png);;JPEG文件交换格式(*.jpg);;所有文件(*.*)")
        ex = pyqtgraph.exporters.ImageExporter(self.pw.scene())
        ex.export(fileName=fileName)

    def create_cmd_frame(self):
        self.scan_1_finish_flag = 1
        self.scan_2_finish_flag = 0
        self.funCnt += 1
        if (self.funCnt == 1) and (self.U0 == int(self.U0Edit.text())):
            self.U0 = self.U0
        elif (self.funCnt > 1) and (self.U0 < self.U1):
            self.U0 += self.du
        else:
            self.on_scan_1Button()

        if self.U0 >= 0:
            self.cmdstr = 'P:' + str(self.U0).zfill(4) + '\n'
        else:
            self.cmdstr = 'N:' + str(-self.U0).zfill(4) + '\n'

    def decodeFrame(self, frame_arr):  # 解帧函数
        if frame_arr[0] == 'P':  # 判断命令帧格式
            pdat = re.sub(r'^\D\:', '+', frame_arr)  # 使用正则表达式decode命令帧
            cmd = re.findall(r"\+\d?.*\d+", pdat)
        elif frame_arr[0] == 'N':
            ndat = re.sub(r'^\D\:', '-', frame_arr)
            cmd = re.findall(r"-\d?.*\d+", ndat)
        return cmd

    def on_mqttSendData(self):
        if self.wifiFlag == 0:
            if len(self.cmdstr) != 0:  # 防止出现空帧
                n = self.com.write(self.cmdstr.encode("utf-8"))  # 起始处多发个0 com write
            else:
                n = 0
            self.sendCount += n
        elif self.wifiFlag == 1:
            if len(self.cmdstr) != 0:  # 防止出现空帧
                self.mqtt_publish(myclient, self.pubTopic, self.cmdstr)
                # print(self.cmdstr)
        self.create_cmd_frame()

    def on_doubleCmdFrame(self):
        self.scan_1_finish_flag = 0
        self.scan_2_finish_flag = 1
        if (self.U0 < self.U1) and (self.reverseFlag == 0):
            self.U0 += self.du
        elif (self.U0 == self.U1) and (self.reverseFlag == 0):
            self.reverseFlag = 1
            self.U0 = self.U0 - self.du
        elif (self.reverseFlag == 1) and (self.U0 > int(self.U0Edit.text())):
            self.U0 -= self.du
        else:
            self.reverseFlag = 0
            self.on_scan_2Button()
            # QMessageBox.information(self, "完成", "双向扫描完成")

        if self.U0 >= 0:
            self.cmdstr = 'P:' + str(self.U0).zfill(4) + '\n'
        else:
            self.cmdstr = 'N:' + str(-self.U0).zfill(4) + '\n'

    def on_doubleMqttSendData(self):
        if self.wifiFlag == 0:
            if len(self.cmdstr) != 0:  # 防止出现空帧
                n = self.com.write(self.cmdstr.encode("utf-8"))  # 起始处多发个0  double mqtt write
            else:
                n = 0
            self.sendCount += n
        elif self.wifiFlag == 1:
            if len(self.cmdstr) != 0:  # 防止出现空帧
                self.mqtt_publish(myclient, self.pubTopic, self.cmdstr)
        self.on_doubleCmdFrame()

    def on_scan_1Button(self):
        self.scan_1_button_flag += 1
        if self.scan_1_button_flag == 1:
            self.mqttSendTimer.start(int(self.dtEdit.text()))
        elif self.scan_1_button_flag == 2:
            self.cmdstr = ''  # ！！！清空命令帧，防止按键中断导致下一次起始命令帧错误
            self.funCnt = 0  # 第二次发送命令和第一次不同
            self.U0 = int(self.U0Edit.text())
            self.mqttSendTimer.stop()
            self.scan_1_button_flag = 0

    def on_scan_2Button(self):
        self.scan_2_button_flag += 1
        if self.scan_2_button_flag == 1:
            self.doubleSendTimer.start(int(self.dtEdit.text()))
        elif self.scan_2_button_flag == 2:
            self.cmdstr = ''  # ！！！清空命令帧，仿真按键中断导致下一次起始命令帧错误

            self.U0 = int(self.U0Edit.text())
            self.doubleSendTimer.stop()
            self.scan_2_button_flag = 0

    def _connect_mqtt(self) -> mqtt_client:
        self.broker = self.urlEdit.text()
        self.subTopic = self.subTopicEdit.text()
        self.pubTopic = self.pubTopicEdit.text()

        def on_connect(client, userdata, flags, rc):  # rc的值决定连接成功与否，0->成功
            if rc == 0:
                print("Connected to MQTT Broker!")
            elif rc == 1:
                print("rc==%d, Mqtt version is error!\n", rc)
            elif rc == 2:
                print("rc==%d, Cline is error!\n", rc)
            elif rc == 3:
                print("rc==%d, Serve is error!\n", rc)
            elif rc == 4:
                print("rc==%d, Usr name or name is error!\n", rc)
            elif rc == 5:
                print("rc==%d, No permission!\n", rc)
            else:
                print("Error! %d\n", rc)

        client = mqtt_client.Client(client_id)
        client.on_connect = on_connect
        client.connect(self.broker, port)
        return client  # 返回连接成功客户个体

    def _subscribe(self, client: mqtt_client):  # 订阅函数
        def on_message(client, userdata, msg):  # 收到消息调用
            receivedData = msg.payload.decode(self.encoding, 'ignore')  # 使用MQTT接收，加判断
            received_split_str = receivedData.split(',')
            cmd_str = received_split_str[0][1:]
            value_str = received_split_str[1][:-1]
            cmd_list = self.decodeFrame(cmd_str)
            value_list = self.decodeFrame(value_str)

            datalist.extend(value_list)
            cmdlist.extend(cmd_list)  # 注意追加的变量

            print(value_list, cmd_list)

        client.subscribe(self.subTopic)
        client.on_message = on_message

    # 发布函数
    def mqtt_publish(self, client: mqtt_client, pub_topic, pub_payload):
        client.publish(topic=pub_topic, payload=pub_payload, qos=0)

    def mqtt_run(self):
        global myclient
        if self.connectFlag == 1:
            myclient = self._connect_mqtt()  # 连接服务器
            self._subscribe(myclient)  # 订阅消息
            QMessageBox.information(self, "连接提示", ("连接成功！\n且已订阅" + self.subTopic + "！"))
            self.wifiFlag = 1
            datalist.clear()  # 清空list
            cmdlist.clear()
            myclient.loop_start()  # 开启新线程处理MQTT数据
        elif self.connectFlag == 0:
            QMessageBox.information(self, "连接提示", "断开连接!")
            myclient.disconnect()
            myclient.loop_stop(force=False)
            self.connectFlag = 1
        self.connectButton.setEnabled(False)
        self.disconnectButton.setEnabled(True)

    def mqtt_stop(self):
        self.connectFlag = 0
        self.mqtt_run()
        self.connectButton.setEnabled(True)
        self.disconnectButton.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    win = PyQt_Serial()
    win.show()
    app.exec_()
    app.exit()

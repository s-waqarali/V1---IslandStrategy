import sys
import importlib.util
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QProcess, QTime, QTimer
from PyQt5.QtGui import QIcon
import os
import shutil
import requests

class App(QtWidgets.QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        ui_path = os.path.join(sys._MEIPASS, 'main.ui')
        uic.loadUi(ui_path, self)
        icon_path = os.path.join(sys._MEIPASS, 'favicon.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.showMaximized() 
        # Set the path to the script files
        self.islandPath = os.path.join(sys._MEIPASS, 'island.py')
        self.liveIBKRPath = os.path.join(sys._MEIPASS, 'liveIBKR.py')
        
        # Connect the buttons to the functions
        self.btnRun.clicked.connect(self.run_script)
        self.btnSaveSetting.clicked.connect(self.save_config)
        #self.rdAutoStart.clicked.connect(self.enable_auto_start)
        self.findChild(QtWidgets.QTimeEdit, "txtAutoStart").timeChanged.connect(self.on_time_changed)

        # Load the configuration
        self.load_config()
        
    def load_config(self):
        # Load the configuration
        config_path = os.path.join(sys._MEIPASS, "config.py")
        spec = importlib.util.spec_from_file_location("config", config_path)
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)

        # Set integer values to QSpinBox
        self.sbFirstGap.setValue(config.first_gap_per)
        self.sbSecondGap.setValue(config.second_gap_per)
        self.sbConsGap.setValue(config.cons_gap_per)
        self.sbConsPeriod.setValue(config.cons_period)
        self.sbStopLoss.setValue(config.stop_loss_atr)
        self.sbNextStopLoss.setValue(config.next_stop_loss_atr)
        self.sbSlowSma.setValue(config.slow_sma)
        self.sbFastSma.setValue(config.fast_sma)

        # Set string values to QLineEdit
        #self.txtDuration.setText(config.duration)
        self.sbCash.setValue(config.Cash)
        self.sbCanTradeUpto.setValue(config.can_trade_upto)
        
        # # Set baseline values
        # if config.use_baseline:
        #     self.rdBaselineTrue.setChecked(True)
        # else:
        #     self.rdBaselineFalse.setChecked(True)
        
        # self.txtBaseline.setText(config.baseline_index)
        # self.sbBaselineSlowSma.setValue(config.baseline_slow_sma)
        # self.sbBaselineFastSma.setValue(config.baseline_fast_sma)
        # self.txtBaselineDuration.setText(config.baseline_duration)
        # self.txtTimeInterval.setText(config.time_interval)
        
        self.txtPort.setText(str(config.ib_config['port']))
        self.txtIp.setText(config.ib_config['ip'])
        self.txtClientId.setText(str(config.ib_config['clientId']))

    def save_config(self):
        # Save the configuration
        config_path = os.path.join(sys._MEIPASS, "config.py")
        with open(config_path, "w") as config_file:
            config_file.write(f"first_gap_per = {self.sbFirstGap.value()}\n")
            config_file.write(f"second_gap_per = {self.sbSecondGap.value()}\n")
            config_file.write(f"cons_gap_per = {self.sbConsGap.value()}\n")
            config_file.write(f"cons_period = {self.sbConsPeriod.value()}\n")
            config_file.write(f"stop_loss_atr = {self.sbStopLoss.value()}\n")
            config_file.write(f"next_stop_loss_atr = {self.sbNextStopLoss.value()}\n")
            config_file.write(f"slow_sma = {self.sbSlowSma.value()}\n")
            config_file.write(f"fast_sma = {self.sbFastSma.value()}\n\n")

            #config_file.write(f"duration = '{self.txtDuration.text()}' # Supported \" '30 D', '13 W', '6 M', '10 Y'\"\n\n")

            config_file.write("####### account details###############\n")
            config_file.write(f"Cash = {self.sbCash.value()}\n")
            config_file.write(f"can_trade_upto = {self.sbCanTradeUpto.value()} # hold maximum 4 tickers at same time \n")
            config_file.write(f"max_allocation = Cash / can_trade_upto \n")
            config_file.write("######################\n\n")

            config_file.write("# baseline config \n\n")

            # Check if the baseline is enabled
            # if self.rdBaselineTrue.isChecked():
            #     config_file.write(f"use_baseline = True\n")
            # else:
            #     config_file.write(f"use_baseline = False\n")
            # config_file.write(f"baseline_index = '{self.txtBaseline.text()}'\n")
            # config_file.write(f"baseline_slow_sma = {self.sbBaselineSlowSma.value()}\n")
            # config_file.write(f"baseline_fast_sma = {self.sbBaselineFastSma.value()}\n")
            # config_file.write(f"baseline_duration = '{self.txtBaselineDuration.text()}' # suggested to use 1 year extra data \n")

            config_file.write("# recommend to not change without consulting it might produce an error\n\n")
            #config_file.write(f"time_interval = '{self.txtTimeInterval.text()}'\n")
            config_file.write("folder_name = 'Strategy_Directory'\n\n")

            config_file.write("# IBKR connect\n")
            config_file.write(f"ib_config = {{'port': {int(self.txtPort.text())}, 'ip': '{self.txtIp.text()}', 'clientId': {int(self.txtClientId.text())}}}\n")

    # def run_script(self):
    #     # Check if a script file is selected
    #     if self.rdIsland.isChecked():
    #         script_path = self.islandPath
    #     elif self.rdLiveIBKR.isChecked():
    #         script_path = self.liveIBKRPath
    #     else:
    #         QMessageBox.critical(self, "Error", "Please select a script file.")
    #         return

    #     # Clear the output text box
    #     self.txtOutput.clear()

    #     # Create a QProcess object
    #     self.process = QProcess(self)

    #     # Connect the process output to the slot that will update the text box
    #     self.process.readyReadStandardOutput.connect(self.on_ready_read_standard_output)
    #     self.process.readyReadStandardError.connect(self.on_ready_read_standard_error)

    #     # Start the process
    #     self.process.start(sys.executable, [script_path])


    # Upper code was given by client and below one is mine in which i added an api which fetches license keys and match that with the license key in the config.py and after that it run the script but i tried to run the script with the upper run func but i was getting errors
    def run_script(self):
        api_url = "https://backend.ntstrading.com/api/getAllCustomers"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            api_data = response.json()

            print("API Data Received:", api_data)

            client_ids = api_data.get('licenseKeys', [])
            if not client_ids:
                QMessageBox.critical(self, "Error", "No license keys found in API response.")
                return

            # Checking license_key from UI text field
            license_input = self.findChild(QtWidgets.QLineEdit, "lineEdit_licenseKey")
            license_key = license_input.text()
            print("License Key:", license_key)
            if not license_key:
                QMessageBox.critical(self, "Error", "Please enter Liscense Key.")
                return
            if license_key not in client_ids:
                QMessageBox.critical(self, "Error", "Invalid License Key.")
                return

        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch data from API: {e}")
            return
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid JSON response from API.")
            return

        if not self.rdIsland.isChecked():
            QMessageBox.critical(self, "Error", "Please select a strategy.")
            return
        
        if not os.path.isfile(".\stocks.csv"):
            QMessageBox.critical(self, "Error", "Missing file ""stocks.csv""")
            return

        if not self.rdIsland.isChecked():
            QMessageBox.critical(self, "Error", "Please select a strategy.")
            return

        if not os.path.exists(self.islandPath):
            QMessageBox.critical(self, "Error", f"Script file not found: {self.islandPath}")
            return

        self.txtOutput.clear()

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_ready_read_standard_output)
        self.process.readyReadStandardError.connect(self.on_ready_read_standard_error)
        self.process.finished.connect(self.on_script_finished)

        try:
            python_path = shutil.which("python")
            self.process.start(python_path, [self.islandPath])
            print("Started Running Script: "+ self.islandPath)
            if not self.process.waitForStarted(5000):
                QMessageBox.critical(self, "Error", "Failed to start the strategy.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start process: {e}")
            return


    def on_ready_read_standard_output(self):
        # Read the standard output and append it to the text box with white color
        output = self.process.readAllStandardOutput().data().decode()
        self.txtOutput.append(f"<span style='color: white;'>{output}</span>")

    def on_ready_read_standard_error(self):
        # Read the standard error and append it to the text box with red color
        error = self.process.readAllStandardError().data().decode()
        self.txtOutput.append(f"<span style='color: red;'>{error}</span>")
    
    def on_script_finished(self):
        self.txtOutput.clear()
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_ready_read_standard_output)
        self.process.readyReadStandardError.connect(self.on_ready_read_standard_error)

        try:
            python_path = shutil.which("python")
            self.process.start(python_path, [self.liveIBKRPath])
            print("Started Running Script: "+ self.liveIBKRPath)
            if not self.process.waitForStarted(5000):
                QMessageBox.critical(self, "Error", "Failed to start the script process.")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start process: {e}")
            return
        
    def on_time_changed(self):
        if self.rdAutoStart.isChecked():
            time_widget = self.findChild(QtWidgets.QTimeEdit, "txtAutoStart")
            self.auto_start_time = time_widget.time()
            # Start timer to keep checking time
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.check_auto_start_time)
            self.timer.start(1000)  # check every second

    def check_auto_start_time(self):
        current_time = QTime.currentTime()
        if current_time.hour() == self.auto_start_time.hour() and current_time.minute() == self.auto_start_time.minute():
            self.timer.stop()  # Stop after running once
            self.run_script()  # <-- Run Script

def showDisclaimer():
    disclaimer_box = QMessageBox()
    disclaimer_box.setWindowTitle("Disclaimer")
    disclaimer_box.setText("By using NTS ToolBox, you agree that it is an automated tool connecting to Interactive Brokers API for data analysis and trade execution, provided “as is” without warranties. It is not financial advice, and you assume all risks of trading losses or errors. NTS Trading LLC  is not liable for any damages, losses, or issues arising from its use. You are solely responsible for your account settings and trade decisions.")
    disclaimer_box.setIcon(QMessageBox.Information)

    accept_button = disclaimer_box.addButton("Agree", QMessageBox.AcceptRole)
    cancel_button = disclaimer_box.addButton("Cancel", QMessageBox.RejectRole)

    disclaimer_box.exec_()

    if disclaimer_box.clickedButton() == accept_button:
        return True
    else:
        return False
        

# Run the application
if __name__ == "__main__":
    print("Starting Application..")
    app = QtWidgets.QApplication(sys.argv)
    icon_path = os.path.join(sys._MEIPASS, 'favicon.ico')
    app.setWindowIcon(QIcon(icon_path))    
    bDisclaimerAccepted = showDisclaimer()
    if bDisclaimerAccepted == True:
        window = App()
        window.show()
        sys.exit(app.exec_())

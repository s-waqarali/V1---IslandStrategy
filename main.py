import sys
import importlib.util
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QProcess
import subprocess
import os

class App(QtWidgets.QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        uic.loadUi('main.ui', self)

        # Set the path to the script files
        self.islandPath = os.path.join(os.path.dirname(__file__), 'island.py')
        self.liveIBKRPath = os.path.join(os.path.dirname(__file__), 'liveIBKR.py')
        
        # Connect the buttons to the functions
        self.btnRun.clicked.connect(self.run_script)
        self.btnSaveSetting.clicked.connect(self.save_config)

        # Load the configuration
        self.load_config()
        
    def load_config(self):
        # Load the configuration
        config_path = os.path.join(os.path.dirname(__file__), 'config.py')
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
        self.txtDuration.setText(config.duration)
        self.sbCash.setValue(config.Cash)
        self.sbCanTradeUpto.setValue(config.can_trade_upto)
        
        # Set baseline values
        if config.use_baseline:
            self.rdBaselineTrue.setChecked(True)
        else:
            self.rdBaselineFalse.setChecked(True)
        
        self.txtBaseline.setText(config.baseline_index)
        self.sbBaselineSlowSma.setValue(config.baseline_slow_sma)
        self.sbBaselineFastSma.setValue(config.baseline_fast_sma)
        self.txtBaselineDuration.setText(config.baseline_duration)
        self.txtTimeInterval.setText(config.time_interval)
        
        self.txtPort.setText(str(config.ib_config['port']))
        self.txtIp.setText(config.ib_config['ip'])
        self.txtClientId.setText(str(config.ib_config['clientId']))

    def save_config(self):
        # Save the configuration
        config_path = os.path.join(os.path.dirname(__file__), 'config.py')
        with open(config_path, "w") as config_file:
            config_file.write(f"first_gap_per = {self.sbFirstGap.value()}\n")
            config_file.write(f"second_gap_per = {self.sbSecondGap.value()}\n")
            config_file.write(f"cons_gap_per = {self.sbConsGap.value()}\n")
            config_file.write(f"cons_period = {self.sbConsPeriod.value()}\n")
            config_file.write(f"stop_loss_atr = {self.sbStopLoss.value()}\n")
            config_file.write(f"next_stop_loss_atr = {self.sbNextStopLoss.value()}\n")
            config_file.write(f"slow_sma = {self.sbSlowSma.value()}\n")
            config_file.write(f"fast_sma = {self.sbFastSma.value()}\n\n")

            config_file.write(f"duration = '{self.txtDuration.text()}' # Supported \" '30 D', '13 W', '6 M', '10 Y'\"\n\n")

            config_file.write("####### account details###############\n")
            config_file.write(f"Cash = {self.sbCash.value()}\n")
            config_file.write(f"can_trade_upto = {self.sbCanTradeUpto.value()} # hold maximum 4 tickers at same time \n")
            config_file.write(f"max_allocation = Cash / can_trade_upto \n")
            config_file.write("######################\n\n")

            config_file.write("# baseline config \n\n")

            # Check if the baseline is enabled
            if self.rdBaselineTrue.isChecked():
                config_file.write(f"use_baseline = True\n")
            else:
                config_file.write(f"use_baseline = False\n")
            config_file.write(f"baseline_index = '{self.txtBaseline.text()}'\n")
            config_file.write(f"baseline_slow_sma = {self.sbBaselineSlowSma.value()}\n")
            config_file.write(f"baseline_fast_sma = {self.sbBaselineFastSma.value()}\n")
            config_file.write(f"baseline_duration = '{self.txtBaselineDuration.text()}' # suggested to use 1 year extra data \n")

            config_file.write("# recommend to not change without consulting it might produce an error\n\n")
            config_file.write(f"time_interval = '{self.txtTimeInterval.text()}'\n")
            config_file.write("folder_name = 'Strategy_Directory'\n\n")

            config_file.write("# IBKR connect\n")
            config_file.write(f"ib_config = {{'port': {int(self.txtPort.text())}, 'ip': '{self.txtIp.text()}', 'clientId': {int(self.txtClientId.text())}}}\n")

    def run_script(self):
        # Check if a script file is selected
        if self.rdIsland.isChecked():
            script_path = self.islandPath
        elif self.rdLiveIBKR.isChecked():
            script_path = self.liveIBKRPath
        else:
            QMessageBox.critical(self, "Error", "Please select a script file.")
            return

        # Clear the output text box
        self.txtOutput.clear()

        # Create a QProcess object
        self.process = QProcess(self)

        # Connect the process output to the slot that will update the text box
        self.process.readyReadStandardOutput.connect(self.on_ready_read_standard_output)
        self.process.readyReadStandardError.connect(self.on_ready_read_standard_error)

        # Start the process
        self.process.start(sys.executable, [script_path])

    def on_ready_read_standard_output(self):
        # Read the standard output and append it to the text box with white color
        output = self.process.readAllStandardOutput().data().decode()
        self.txtOutput.append(f"<span style='color: white;'>{output}</span>")

    def on_ready_read_standard_error(self):
        # Read the standard error and append it to the text box with red color
        error = self.process.readAllStandardError().data().decode()
        self.txtOutput.append(f"<span style='color: red;'>{error}</span>")

# Run the application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())

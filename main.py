import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import serial as serial_module
import math
import sqlite3
from datetime import datetime


def push_to_db(time, time_since_start, temperature, pressure, battery_voltage, battery_current, generator_voltage, generator_current, height, battery_degree):
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    cursor.execute('''
    INSERT INTO Data (Time, Time_since_start, Temperature, Pressure, Battery_voltage, Battery_current, Generator_voltage, Generator_current, Height, Degree_of_charge)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (time, time_since_start, temperature, pressure, battery_voltage, battery_current, generator_voltage, generator_current, height, battery_degree))
    db.commit()
    db.close()


def get_time():
    current_time = datetime.now()
    current_time = current_time.strftime("%H:%M:%S %d:%m:%Y")
    return current_time


def calculate_height(initial_pressure, current_pressure, temp):
    R = 8.134
    T = temp + 273.15
    g = 9.81
    mu = 0.02896
    initial_pressure = initial_pressure * 10000
    current_pressure = current_pressure * 10000
    height = -(R * T) / (mu * g) / \
        (math.log(current_pressure) - math.log(initial_pressure))
    return height


class RadioDataGraph(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        self.temperature_plot = pg.PlotWidget()
        self.temperature_plot.setTitle("Temperature Over Time")
        self.temperature_plot.setLabel('left', 'Temperature', units='°C')
        self.temperature_plot.setLabel('bottom', 'Time', units='s')
        self.temperature_data_plot = self.temperature_plot.plot(
            pen=(29, 185, 84))
        self.temperature_data_array = np.zeros((30, 7))
        self.temperature_ptr = -29

        self.pressure_plot = pg.PlotWidget()
        self.pressure_plot.setTitle("Pressure Over Time")
        self.pressure_plot.setLabel('left', 'Pressure', units='Pa')
        self.pressure_plot.setLabel('bottom', 'Time', units='s')
        self.pressure_data_plot = self.pressure_plot.plot(pen=(0, 114, 189))
        self.pressure_data_array = np.zeros((30, 7))
        self.pressure_ptr = -29

        self.battery_charge_plot = pg.PlotWidget()
        self.battery_charge_plot.setTitle("Battery charge Over Time")
        self.battery_charge_plot.setLabel('left', 'Battery charge', units='%')
        self.battery_charge_plot.setLabel('bottom', 'Time', units='s')
        self.battery_charge_data_plot = self.battery_charge_plot.plot(
            pen=(255, 0, 0))
        self.battery_charge_data_array = np.zeros((30, 7))
        self.battery_charge_ptr = -29

        self.current_generator_plot = pg.PlotWidget()
        self.current_generator_plot.setTitle("Generated Current Over Time")
        self.current_generator_plot.setLabel(
            'left', 'Generated Current', units='A')
        self.current_generator_plot.setLabel('bottom', 'Time', units='s')
        self.current_generator_data_plot = self.current_generator_plot.plot(
            pen=(0, 0, 255))
        self.current_generator_data_array = np.zeros((30, 7))
        self.current_generator_ptr = -29

        self.height_plot = pg.PlotWidget()
        self.height_plot.setTitle("Height Over Time")
        self.height_plot.setLabel('left', 'Height', units='m')
        self.height_plot.setLabel('bottom', 'Time', units='s')
        self.height_data_plot = self.height_plot.plot(pen=(255, 255, 0))
        self.height_data_array = np.zeros((30, 7))
        self.height_ptr = 0

        self.layout.addWidget(self.temperature_plot)
        self.layout.addWidget(self.pressure_plot)
        self.layout.addWidget(self.battery_charge_plot)
        self.layout.addWidget(self.current_generator_plot)
        self.layout.addWidget(self.height_plot)

        self.setLayout(self.layout)

        self.serial_port = serial_module.Serial('COM6', 9600)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(500)  # Update every 500 milliseconds

    def update_data(self):
        radio_data = self.serial_port.readline().decode().strip()
        data_parts = radio_data.split(":")
        if len(data_parts) < 2:
          # =  print("Invalid data format received from radio module")
            return

        try:
            data_values = data_parts[1].split()
            values = [float(val) for val in data_values]

            if len(values) != 7:
                raise ValueError(
                    "Invalid number of values received from radio module")

            new_data = values
        except ValueError as e:
            print(f"Error processing data from radio module: {e}")
            return

        
        self.temperature_data_array[:-1] = self.temperature_data_array[1:]
        self.temperature_data_array[-1] = new_data
        self.temperature_ptr += 1
        self.temperature_data_plot.setData(self.temperature_data_array[:, 0])
        self.temperature_data_plot.setPos(self.temperature_ptr, 0)

        self.pressure_data_array[:-1] = self.pressure_data_array[1:]
        self.pressure_data_array[-1] = new_data
        self.pressure_ptr += 1
        self.pressure_data_plot.setData(self.pressure_data_array[:, 1])
        self.pressure_data_plot.setPos(self.pressure_ptr, 0)

        self.battery_charge_data_array[:-
                                       1] = self.battery_charge_data_array[1:]
        self.battery_charge_data_array[-1] = (
            new_data[2] - 2.5) / (3.7 - 2.5) * 100
        self.battery_charge_ptr += 1
        self.battery_charge_data_plot.setData(
            self.battery_charge_data_array[:, 2])
        self.battery_charge_data_plot.setPos(self.battery_charge_ptr, 0)

        self.current_generator_data_array[:-
                                          1] = self.current_generator_data_array[1:]
        self.current_generator_data_array[-1] = new_data[5]/1000
        self.current_generator_ptr += 1
        self.current_generator_data_plot.setData(
            self.current_generator_data_array[:, 5])
        self.current_generator_data_plot.setPos(self.current_generator_ptr, 0)

        self.height_data_array[:-1] = self.height_data_array[1:]
        self.height_data_array[-1] = calculate_height(
            986, values[1], values[0])
        self.height_ptr += 1
        self.height_data_plot.setData(self.height_data_array[:, 4])
        self.height_data_plot.setPos(self.height_ptr, 0)

        time = get_time()
        push_to_db(time, UZUPEŁNIĆ ARGUMENTY) #time, time_since_start, temperature, pressure, battery_voltage, battery_current, generator_voltage, generator_current, height, battery_degree
        
        print(values)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.radio_data_graph = RadioDataGraph()

        self.setCentralWidget(self.radio_data_graph)
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Radio Data Graph')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

import argparse
import logging

# arduino stuff
import serial
import time

from PyQt5.QtCore import Qt
from pyqtgraph import AxisItem

import sys

import pyqtgraph as pg
from PyQt5 import QtWidgets
import PyQt5.QtWidgets
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from brainflow.data_filter import DataFilter, FilterTypes, WindowOperations, DetrendOperations
from PyQt5.QtWidgets import QApplication, QGraphicsEllipseItem
from pyqtgraph import ViewBox
from PyQt5.QtCore import QTimer

# the circle stuff:
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QGraphicsEllipseItem

focus_counter = 0

# arduino stuff
# --------------------------------------------------------------------------------------------------
arduino_port = '/dev/cu.usbmodem11401'
arduino_baudrate = 57600

ser = serial.Serial(arduino_port, arduino_baudrate)
time.sleep(2)
# -------------------------------------------------------------------------------------------------


class CircleItem(QGraphicsEllipseItem):
    def __init__(self, x, y, diameter):
        super().__init__(x, y, diameter, diameter)
        self.setBrush(QColor(255, 0, 0))

    def set_color(self, color):
        self.setBrush(QColor(color))


class Graph:
    def __init__(self, board_shim):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.fhandle = open("silly.txt", "w")

        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate

        self.app = QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(
            title='BrainFlow Plot', size=(800, 600))
        self.win.show()

        self._init_pens()
        self._init_timeseries()
        self._init_psd()
        self._init_band_plot()

        timer = QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)

        self.circle_color = None

        sys.exit(self.app.exec_())

        # <-------------------------------------------- Adruino connection closing command.
        ser.close()

    def _init_pens(self):
        self.pens = list()
        self.brushes = list()
        colors = ['#5B45A4', '#A473B6', '#5B45A4', '#2079D2',
                  '#32B798', '#2FA537', '#9DA52F', '#A57E2F', '#A53B2F']
        for i in range(len(colors)):
            pen = pg.mkPen({'color': colors[i], 'width': 2})
            self.pens.append(pen)
            brush = pg.mkBrush(colors[i])
            self.brushes.append(brush)

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(len(self.exg_channels)):
            p = self.win.addPlot(row=i, col=0)
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot(pen=self.pens[i % len(self.pens)])
            # curve.setDownsampling(auto=True, method='mean', ds=3)
            self.curves.append(curve)

    def _init_psd(self):
        self.psd_plot = self.win.addPlot(
            row=0, col=1, rowspan=len(self.exg_channels) // 2)
        self.psd_plot.showAxis('left', False)
        self.psd_plot.setMenuEnabled('left', False)
        self.psd_plot.setTitle('PSD Plot')
        self.psd_plot.setLogMode(False, True)
        self.psd_curves = list()
        self.psd_size = DataFilter.get_nearest_power_of_two(self.sampling_rate)
        for i in range(len(self.exg_channels)):
            psd_curve = self.psd_plot.plot(pen=self.pens[i % len(self.pens)])
            psd_curve.setDownsampling(auto=True, method='mean', ds=3)
            self.psd_curves.append(psd_curve)

    def _init_band_plot(self):
        bottom_axis = AxisItem(orientation="bottom")
        tick_labels = {1: "Delta\n(2-4 Hz)", 2: "Theta\n(4-8 Hz)",
                       3: "Alpha\n(8-13 Hz)", 4: "Beta\n(13-30 Hz)", 5: "Gamma\n(30-50 Hz)"}
        tick_positions = [[(pos, tick_labels[pos]) for pos in tick_labels]]

        bottom_axis.setTicks(tick_positions)

        self.band_plot = self.win.addPlot(row=len(self.exg_channels) // 2, col=1, rowspan=len(
            self.exg_channels) // 2, axisItems={'bottom': bottom_axis})
        self.band_plot.showAxis('left', False)
        self.band_plot.setMenuEnabled('left', False)
        self.band_plot.setTitle('BandPower Plot')
        y = [0, 0, 0, 0, 0]
        x = [1, 2, 3, 4, 5]
        self.band_bar = pg.BarGraphItem(
            x=x, height=y, width=0.5, pen=self.pens[0], brush=self.brushes[0])
        self.band_plot.addItem(self.band_bar)

        # the circle stuff:
        self.view_box = ViewBox()
        self.band_plot.scene().addItem(self.view_box)
        self.view_box.setGeometry(
            self.band_plot.getViewBox().sceneBoundingRect())
        # Make sure the ViewBox is underneath the PlotItem
        self.view_box.setZValue(-1)

        self.circle_item = CircleItem(6, 3, 0)
        self.view_box.addItem(self.circle_item)

    def update(self):

        data = self.board_shim.get_current_board_data(self.num_points)
        avg_bands = [0, 0, 0, 0, 0]
        for count, channel in enumerate(self.exg_channels):
            # plot timeseries
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 3.0, 45.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 48.0, 52.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 58.0, 62.0, 2,
                                        FilterTypes.BUTTERWORTH.value, 0)
            self.curves[count].setData(data[channel].tolist())
            if data.shape[1] > self.psd_size:
                # plot psd
                psd_data = DataFilter.get_psd_welch(data[channel], self.psd_size, self.psd_size // 2,
                                                    self.sampling_rate,
                                                    WindowOperations.BLACKMAN_HARRIS.value)
                lim = min(70, len(psd_data[0]))
                self.psd_curves[count].setData(
                    psd_data[1][0:lim].tolist(), psd_data[0][0:lim].tolist())
                # plot bands
                avg_bands[0] = avg_bands[0] + \
                    DataFilter.get_band_power(psd_data, 2.0, 4.0)
                self.fhandle.write(str(avg_bands[0]) + ", ")
                avg_bands[1] = avg_bands[1] + \
                    DataFilter.get_band_power(psd_data, 4.0, 8.0)
                self.fhandle.write(str(avg_bands[1]) + ", ")
                avg_bands[2] = avg_bands[2] + \
                    DataFilter.get_band_power(psd_data, 8.0,  13.0)
                self.fhandle.write(str(avg_bands[2]) + ", ")
                avg_bands[3] = avg_bands[3] + \
                    DataFilter.get_band_power(psd_data, 13.0, 30.0)
                self.fhandle.write(str(avg_bands[3]) + ", ")
                avg_bands[4] = avg_bands[4] + \
                    DataFilter.get_band_power(psd_data, 30.0, 50.0)
                self.fhandle.write(str(avg_bands[4]) + ", ")
                self.fhandle.write("\t")
# this shows the actual value of the bands
        print("average band 3", avg_bands[3])
        #data1 = avg_bands[3]
        # print(avg_bands[1])
        #ser.write(data1)
        #global focus_counter

        # and not 80 <= avg_bands[1] < 90: #and not 80 <= avg_bands[2] < 90 and not 80 <= avg_bands[3] < 90 and not 80 <= avg_bands[4] < 90: #over here what we can do is define the ratios for each band. we saw how three bands seemed to consistently stay the same way when focussed, so we can add those values here and get a classifier which uses three bands to identify focus.
        if not 1 < avg_bands[3] < 3000:  # and focus_counter != 1000:
        #if not 15 < avg_bands[3] < 30:  # and focus_counter != 1000:
            #global focus_counter
            print('not focussing!')
            # <----------------------------------------------------Arduino OFF
            ser.write(b'digitalWrite 14 1\r\n')
        #    print(avg_bands[1])
        #    focus_counter = focus_counter + 1 #<---- IMP
        else:
            print('----------> bro focussin <-------------')
            # <----------------------------------------------------Arduino ON
            ser.write(b'digitalWrite 14 0\r\n')

        # the circle stuff
        alpha = 0.5  # You can adjust this value to control the weight of the current value in the average
        if self.circle_color is None:
            self.circle_color = avg_bands
        else:
            self.circle_color = [
                alpha * x + (1 - alpha) * y for x, y in zip(avg_bands, self.circle_color)
            ]

        # self.circle_color_band = None # this make the circle blank and the plot of the bands is not there when I use this
        # When I use this I get no circle, idk if this is because of the lack of dongle or not
        circle_color_band = None
        if self.circle_color[2] >= self.circle_color[1] and self.circle_color[2] >= self.circle_color[3]:
            self.circle_color_band = "yellow"
        elif self.circle_color[3] >= self.circle_color[2] and self.circle_color[3] >= self.circle_color[4]:
            self.circle_color_band = "green"
        else:
            self.circle_color_band = "red"

        self.circle_item.set_color(circle_color_band)
        # circle_item.set_color(circle_color_band)

        avg_bands = [int(x * 100 / len(self.exg_channels)) for x in avg_bands]
        self.band_bar.setOpts(height=avg_bands)

        self.app.processEvents()

    # ser.close()

# def timer():
   # while focus_counter != 100:
   #     print()


def main():
    BoardShim.enable_dev_board_logger()
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
    parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False,
                        default=0)
    parser.add_argument('--ip-port', type=int,
                        help='ip port', required=False, default=0)
    parser.add_argument('--ip-protocol', type=int, help='ip protocol, check IpProtocolType enum', required=False,
                        default=0)
    parser.add_argument('--ip-address', type=str,
                        help='ip address', required=False, default='')
    parser.add_argument('--serial-port', type=str,
                        help='serial port', required=False, default='')
    parser.add_argument('--mac-address', type=str,
                        help='mac address', required=False, default='')
    parser.add_argument('--other-info', type=str,
                        help='other info', required=False, default='')
    parser.add_argument('--streamer-params', type=str,
                        help='streamer params', required=False, default='')
    parser.add_argument('--serial-number', type=str,
                        help='serial number', required=False, default='')
    parser.add_argument('--board-id', type=int, help='board id, check docs to get a list of supported boards',
                        required=False, default=BoardIds.SYNTHETIC_BOARD)
    parser.add_argument('--file', type=str, help='file',
                        required=False, default='')
    parser.add_argument('--master-board', type=int, help='master board id for streaming and playback boards',
                        required=False, default=BoardIds.NO_BOARD)
    args = parser.parse_args()

    params = BrainFlowInputParams()
    params.ip_port = args.ip_port
    params.serial_port = args.serial_port
    params.mac_address = args.mac_address
    params.other_info = args.other_info
    params.serial_number = args.serial_number
    params.ip_address = args.ip_address
    params.ip_protocol = args.ip_protocol
    params.timeout = args.timeout
    params.file = args.file
    params.master_board = args.master_board

    board_shim = BoardShim(args.board_id, params)
    try:
        board_shim.prepare_session()
        board_shim.start_stream(450000, args.streamer_params)
        Graph(board_shim)
    except BaseException:
        logging.warning('Exception', exc_info=True)
    finally:
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()


if __name__ == '__main__':
    main()

print(focus_counter)

if focus_counter > 1000:
    print('subject not focus')

#
# @file field.py
# @author Mit Bailey (mitbailey@outlook.com)
# @brief The Image Realignment Assistant v0.1 GUI and program.
# @version See Git tags for version information.
# @date 2022.10.11
# 
# @copyright Copyright (c) 2022
# 
#

import os
import weakref
import sys

try:
    exeDir = sys._MEIPASS
except Exception:
    exeDir = os.getcwd()

if getattr(sys, 'frozen', False):
    appDir = os.path.dirname(sys.executable)
elif __file__:
    appDir = os.path.dirname(__file__)

from PyQt5 import uic
from PyQt5.Qt import QTextOption
from PyQt5.QtCore import (pyqtSignal, pyqtSlot, Q_ARG, QAbstractItemModel,
                          QFileInfo, qFuzzyCompare, QMetaObject, QModelIndex, QObject, Qt,
                          QThread, QTime, QUrl, QSize, QEvent, QCoreApplication, QFile, QIODevice, QMutex, QWaitCondition)
from PyQt5.QtGui import QColor, qGray, QImage, QPainter, QPalette, QIcon, QKeyEvent, QMouseEvent, QFontDatabase, QFont
from PyQt5.QtMultimedia import (QAbstractVideoBuffer, QMediaContent,
                                QMediaMetaData, QMediaPlayer, QMediaPlaylist, QVideoFrame, QVideoProbe)
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QMainWindow, QDoubleSpinBox, QApplication, QComboBox, QDialog, QFileDialog,
                             QFormLayout, QHBoxLayout, QLabel, QListView, QMessageBox, QPushButton,
                             QSizePolicy, QSlider, QStyle, QToolButton, QVBoxLayout, QWidget, QLineEdit, QPlainTextEdit,
                             QTableWidget, QTableWidgetItem, QSplitter, QAbstractItemView, QStyledItemDelegate, QHeaderView, QFrame, QProgressBar, QCheckBox, QToolTip, QGridLayout, QSpinBox,
                             QLCDNumber, QAbstractSpinBox, QStatusBar, QAction)
from PyQt5.QtCore import QTimer
from io import TextIOWrapper

import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets

import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from skmpython import TransformImage

class NavigationToolbar(NavigationToolbar2QT):
    def edit_parameters(self):
        super(NavigationToolbar, self).edit_parameters()

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, tight_layout = True)
        self.parent = weakref.proxy(parent)
        self.axes = fig.add_subplot(111)
        self.axes.set_frame_on(False)
        super(MplCanvas, self).__init__(fig)

    def get_toolbar(self, parent) -> NavigationToolbar:
        self.toolbar = NavigationToolbar(self, parent)
        return self.toolbar

    def update_plots(self, data):
        self.axes.cla()
        self.axes.imshow(data, origin='lower')
        self.axes.axis('off')
        self.draw()
        return

class Ui(QMainWindow):
    EXIT_CODE_FINISHED = 0
    EXIT_CODE_REBOOT = 1

    def __init__(self, application, uiresource = None):
        self.application: QApplication = application
        args = self.application.arguments()
        super(Ui, self).__init__()
        uic.loadUi(uiresource, self)

        self.setWindowTitle("Image Realignment Assistant v0.1")

        # GRAPHICS ELEMENTS FETCHING

        # Graph Widgets
        self.a_graph = self.findChild(QWidget, "a_graph")
        self.b_graph = self.findChild(QWidget, "b_graph")
        self.ab_graph = self.findChild(QWidget, "ab_graph")

        # Graph Toolbars
        self.a_toolbar = self.findChild(QWidget, "a_toolbar")
        self.b_toolbar = self.findChild(QWidget, "b_toolbar")
        self.ab_toolbar = self.findChild(QWidget, "ab_toolbar")

        # Labels
        self.steps_label = self.findChild(QLabel, "steps_label")
        self.angle_label = self.findChild(QLabel, "angle_label")
        self.zoom_label = self.findChild(QLabel, "zoom_label")

        # SpinBoxes
        self.steps_spin = self.findChild(QDoubleSpinBox, "steps_spin")
        self.angle_spin = self.findChild(QDoubleSpinBox, "angle_spin")
        self.zoom_spin = self.findChild(QDoubleSpinBox, "zoom_spin")

        self.steps_spin.valueChanged.connect(self.SLOT_steps_spin)
        self.angle_spin.valueChanged.connect(self.SLOT_angle_spin)
        self.zoom_spin.valueChanged.connect(self.SLOT_zoom_spin)

        # Control Panel
        self.rotate_left = self.findChild(QPushButton, "rotate_left")
        self.rotate_right = self.findChild(QPushButton, "rotate_right")
        self.translate_up = self.findChild(QPushButton, "translate_up")
        self.translate_left = self.findChild(QPushButton, "translate_left")
        self.translate_right = self.findChild(QPushButton, "translate_right")
        self.translate_down = self.findChild(QPushButton, "translate_down")
        self.zoom_out = self.findChild(QPushButton, "zoom_out")
        self.zoom_in = self.findChild(QPushButton, "zoom_in")
        self.reset = self.findChild(QPushButton, "reset")

        self.rotate_left.clicked.connect(self.SLOT_rotate_left)
        self.rotate_right.clicked.connect(self.SLOT_rotate_right)
        self.translate_up.clicked.connect(self.SLOT_translate_up)
        self.translate_left.clicked.connect(self.SLOT_translate_left)
        self.translate_right.clicked.connect(self.SLOT_translate_right)
        self.translate_down.clicked.connect(self.SLOT_translate_down)
        self.zoom_out.clicked.connect(self.SLOT_zoom_out)
        self.zoom_in.clicked.connect(self.SLOT_zoom_in)
        self.reset.clicked.connect(self.SLOT_reset)

        # Buttons
        self.load_a_button = self.findChild(QPushButton, "load_a_button")
        self.load_b_button = self.findChild(QPushButton, "load_b_button")
        self.save_button = self.findChild(QPushButton, "save_button")

        self.load_a_button.clicked.connect(self.SLOT_load_a_button)
        self.load_b_button.clicked.connect(self.SLOT_load_b_button)
        self.save_button.clicked.connect(self.SLOT_save_button)

        # Plots
        self.plot_a = MplCanvas(self, width=5, height=5, dpi=100)
        self.plot_b = MplCanvas(self, width=5, height=5, dpi=100)
        self.plot_ab = MplCanvas(self, width=5, height=5, dpi=100)

        self.nav_a = self.plot_a.get_toolbar(self)
        self.nav_b = self.plot_b.get_toolbar(self)
        self.nav_ab = self.plot_ab.get_toolbar(self)

        layout = QHBoxLayout()
        layout.addWidget(self.plot_a)
        self.a_graph.setLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(self.plot_b)
        self.b_graph.setLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(self.plot_ab)
        self.ab_graph.setLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(self.nav_a)
        self.a_toolbar.setLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(self.nav_b)
        self.b_toolbar.setLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(self.nav_ab)
        self.ab_toolbar.setLayout(layout)

        data = np.random.random((1024,1024))
        self.plot_a.update_plots(data)

        data = np.random.random((1024,1024))
        self.plot_b.update_plots(data)

        data = np.random.random((1024,1024))
        self.plot_ab.update_plots(data)

        self.show()

    def SLOT_steps_spin(self):
        pass
    def SLOT_angle_spin(self):
        pass
    def SLOT_zoom_spin(self):
        pass
    def SLOT_rotate_left(self):
        pass
    def SLOT_rotate_right(self):
        pass
    def SLOT_translate_up(self):
        pass
    def SLOT_translate_left(self):
        pass
    def SLOT_translate_right(self):
        pass
    def SLOT_translate_down(self):
        pass
    def SLOT_zoom_out(self):
        pass
    def SLOT_zoom_in(self):
        pass
    def SLOT_reset(self):
        pass
    def SLOT_load_a_button(self):
        pass
    def SLOT_load_b_button(self):
        pass
    def SLOT_save_button(self):
        pass

if __name__ == '__main__':
    application = QApplication(sys.argv)
    ui_file_name = exeDir + '/ui/field.ui'
    ui_file = QFile(ui_file_name)
    if not ui_file.open(QIODevice.ReadOnly):
        print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
        sys.exit(-1)
    
    exit_code = Ui.EXIT_CODE_REBOOT
    while exit_code == Ui.EXIT_CODE_REBOOT:
        exit_code = Ui.EXIT_CODE_FINISHED
        mainWindow = Ui(application, ui_file)
        exit_code = application.exec_()
        del mainWindow
    
    sys.exit(exit_code)
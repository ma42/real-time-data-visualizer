# """ Demo for radar"""
import os
import pickle
import random
import math
import numpy as np
import pyqtgraph as pg
import metayaml
from enum import Enum, auto
from collections import deque
from os import listdir
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph.parametertree import Parameter, ParameterTree
from code.Timer import Timer
from code.Model import Model

class State(Enum):
    """State is an enum that describes the state of the program. There are three states: 1. STREAM, 2. STOPPED"""
    STREAM = auto()
    STOPPED = auto()

class SensorInstance:
    def __init__(self, n_samp, n_ramp, networksink_reader):
        self.n_samp = n_samp
        self.n_ramp = n_ramp
        self.networksink_reader = networksink_reader

    @staticmethod
    def setup(sensors, full_conf):
        for name, conf in full_conf['sensors'].items():
            nsr_type = conf['data_reader_type']
            nsr = conf[nsr_type]
            nsr.__init__(**nsr.__dict__)
            sensors.append(SensorInstance(conf['n_samp'], conf['n_ramp'], nsr))

class PalGui:
    """ PalGui creates a Graphical user interface with Qt and pyqtgraph

        In order for the gui to work it uses the class Model
        to do the calculations

        Restrictions
        ____________

        IP : str
        MAX_RANGE : float
        MIN_RANGE : float
        MAX_VELOCITY : float
        MIN_VELOCITY : float
        MAX_ANGLE : float
        MIN_ANGLE : float
            angle is set in degrees
    
        in order for the text fields to work, these floats
        must be set.
    
     """

    #CONSTANTS
    DATA_PLOT_RANGE = [0]*50
    DATA_PLOT_VMAX = [0]*50
    DATA_PLOT_VRCS = [0]*50
    PLOT_VMAX = True
    FILTER_PARAMS = {'maxr': 8.0, 'minr': 0.5, 'maxv': 10.0, 'minv': 1.0, 'maxtheta': 15.0, 'mintheta': -15.0}

    #Restrictions
    MAX_RANGE = 15.0
    MAX_VELOCITY = 10.0
    MAX_ANGEL = 15.0 #Is in degrees

    MIN_RANGE = 1.0
    MIN_VELOCITY = 0.0
    MIN_ANGEL = -15.0 #Is in degrees

    IP = "192.168.0.90"

    #TODO Not Done, see END
    pg.setConfigOption("foreground", "#383838")
    #End
    app = QtGui.QApplication([])
    mw = QtGui.QMainWindow()
    mw.setWindowTitle('Axis RadarDemo')
    mw.resize(5000, 800)
    cw = QtGui.QWidget()
    mw.setCentralWidget(cw)
    layout = QtGui.QVBoxLayout()
    cw.setLayout(layout)

    def __init__(self):
        #Sensor setup radar
        sensors = []
        full_conf = metayaml.read('network_sink_recorder.yml')
        SensorInstance.setup(sensors, full_conf)

        self.model = Model(sensors)
        self.folder_location = QtWidgets.QFileDialog()
        self.timer_for_graph_1 = Timer.create_timer(self.update_range_plot, 600)
        self.timer_for_graph_2 = Timer.create_timer(self.to_be_implemented, 1000)
        self.timer_for_graph_3 = Timer.create_timer(self.update_vmax, 7)
        self.splitter1, self.splitter2 = self.create_splitters()
        self.configuration_tree, self.parameters = self.create_configuration_tree_and_parameter(self.splitter1)
        self.create_actions_for_buttons(self.timer_for_graph_1, self.timer_for_graph_2, self.timer_for_graph_3)
        self.plotwidget1, self.plotwidget2, self.plotwidget3 = self.create_layout(self.splitter2)
        self.mw.show()
        self.P1 = self.plotwidget1.plot()
        self.P2 = self.plotwidget2.plot()
        self.P3 = self.plotwidget3.plot()
        self.P1.setPen(width=4, color='#ffcc33')
        self.P3.setPen(width=4, color='#004966')

        #Start the program in a stopped state
        self.state_stopped()

#Methods
    def create_plot(self, name):
        """Boiler plate to create the type of graph we want"""
        pw = pg.PlotWidget(name=name, background='#ececec')
        pw.setMouseEnabled(x=False, y=False)
        pw.hideButtons()
        pw.setMenuEnabled(False)
        pw.showGrid(True, True, 0.7)
        return pw

    def set_max(self, c):
        if c == 'r':
            gui_max = self.parameters.child('Settings')['Maximum Range']
            if gui_max >= self.MIN_RANGE and gui_max <= self.MAX_RANGE:
                self.FILTER_PARAMS['maxr'] = gui_max
                self.plotwidget1.setXRange(self.FILTER_PARAMS['minr'], gui_max)
            else:
                self.message_box("Maximum range", self.MIN_RANGE, self.MAX_RANGE, gui_max)

        elif c == 'v':
            gui_max = self.parameters.child('Settings')['Maximum Velocity']
            if gui_max >= self.MIN_VELOCITY and gui_max <= self.MAX_VELOCITY:
                self.FILTER_PARAMS['maxv'] = gui_max
                self.plotwidget3.setYRange(self.FILTER_PARAMS['minv'], gui_max)
            else:
                self.message_box("Maximum Velocity",  self.MIN_VELOCITY, self.MAX_VELOCITY, gui_max)

        elif c == 'c':
            gui_max = self.parameters.child('Settings')['Maximum Angle']
            if gui_max >= self.MIN_ANGEL and gui_max <= self.MAX_ANGEL:
                self.FILTER_PARAMS['maxtheta'] = gui_max
            else:
                self.message_box("Maximum Angle", self.MIN_ANGEL, self.MAX_ANGEL, gui_max)

    def set_min(self, c):
        if c == 'r':
            gui_min= self.parameters.child('Settings')['Minimum Range']
            if gui_min>= self.MIN_RANGE and gui_min <= self.MAX_RANGE:
                self.FILTER_PARAMS['minr'] = gui_min
                self.plotwidget1.setXRange(gui_min, self.FILTER_PARAMS['maxr'])
            else:
                self.message_box("Minimum Range", self.MIN_RANGE, self.MAX_RANGE, gui_min)

        elif c == 'v':
            gui_min = self.parameters.child('Settings')['Minimum Velocity']
            if gui_min >= self.MIN_VELOCITY and gui_min <= self.MAX_VELOCITY:
                self.FILTER_PARAMS['minv'] = gui_min
                self.plotwidget3.setYRange(gui_min, self.FILTER_PARAMS['maxv'])
            else:
                self.message_box("Minimum Velocity", self.MIN_VELOCITY, self.MAX_VELOCITY, gui_min)
            
        elif c == 'c':
            gui_min = self.parameters.child('Settings')['Minimum Angle']
            if gui_min >= self.MIN_ANGEL and gui_min <= self.MAX_ANGEL:
                self.FILTER_PARAMS['mintheta'] = gui_min
            else:
                self.message_box("Minimum Angle", self.MIN_ANGEL, self.MAX_ANGEL, gui_min)

    def message_box(self, string, min, max, value):
        msg = QtGui.QMessageBox()
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setText("Requirements not met")
        msg.setInformativeText("Wrong value in input {}".format(string))
        msg.setWindowTitle("PalGui")
        msg.setDetailedText("The value must be between {} and {}, the value entered is {}".format(min, max, value))
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        msg.exec_()
        
    def set_ip(self):
        # TODO check that we only change ip address in a stopped state
        self.IP = self.parameters['IP-address']
        # change the IP in .yml file here? 

    def state_stopped(self):
        """Resets the program to initial state"""
        self.state = State.STOPPED
        self.folder_location = ''
        self.clear_all_graphs()

    def clear_all_graphs(self): #TODO
        Timer.stop_time(self.timer_for_graph_1)
        Timer.stop_time(self.timer_for_graph_2)
        Timer.stop_time(self.timer_for_graph_3)

    def create_actions_for_buttons(self, timer1, timer2, timer3):
        """ Create the action listeners for all the buttons"""
        self.parameters.child('Start Stream').sigActivated.connect(lambda: self.start_stream())
        self.parameters.child('Stop Stream').sigActivated.connect(lambda: self.clear_all_graphs())
        self.parameters.child('Pause/Play').child('Pause/Play Graph 1').sigActivated.connect(lambda: self.toggle_graph(timer1))
        self.parameters.child('Pause/Play').child('Pause/Play Graph 2').sigActivated.connect(lambda: self.toggle_graph(timer2))
        self.parameters.child('Pause/Play').child('Pause/Play Graph 3').sigActivated.connect(lambda: self.toggle_graph(timer3))
        self.parameters.child('Pause/Play').child('Toggle').sigActivated.connect(lambda: self.toggle_v_plot())
        self.parameters.child('Settings').child('Maximum Range').sigValueChanged.connect(lambda: self.set_max('r'))
        self.parameters.child('Settings').child('Minimum Range').sigValueChanged.connect(lambda: self.set_min('r'))
        self.parameters.child('Settings').child('Maximum Velocity').sigValueChanged.connect(lambda: self.set_max('v'))
        self.parameters.child('Settings').child('Minimum Velocity').sigValueChanged.connect(lambda: self.set_min('v'))
        self.parameters.child('Settings').child('Maximum Angle').sigValueChanged.connect(lambda: self.set_max('c'))
        self.parameters.child('Settings').child('Minimum Angle').sigValueChanged.connect(lambda: self.set_min('c'))
        self.parameters.child('IP-address').sigValueChanged.connect(lambda: self.set_ip()) #TODO fix implementation with radar yaml file that we are using
    #End

# Graphs for updating plots
    def update_range_plot(self):
        """Graph the range, used for graph nbr 1"""
        range, rcs = self.model.get_range_rcs(self.FILTER_PARAMS)
        if range and rcs:
            self.P1.setData(y=rcs, x=range)
            self.OLD_RANGE, self.OLD_RCS = range, rcs
        else: 
            self.P1.setData() #y=self.OLD_RCS, x=self.OLD_RANGE
    
    def to_be_implemented(self):
        return
    
    def update_vmax(self):
        vmax, vrcs = self.model.get_velocity(self.FILTER_PARAMS)
        self.DATA_PLOT_VMAX[:-1] = self.DATA_PLOT_VMAX[1:]
        self.DATA_PLOT_VRCS[:-1] = self.DATA_PLOT_VRCS[1:]
        self.DATA_PLOT_VMAX[-1] = vmax
        self.DATA_PLOT_VRCS[-1] = vrcs    
        if self.PLOT_VMAX:
            self.P3.setData(self.DATA_PLOT_VMAX)
            self.P3.setPen(width=4, color='#004966')
        else: 
            self.P3.setData(self.DATA_PLOT_VRCS)
            self.P3.setPen(width=4, color='#FF6347')
#END

    def create_splitters(self):
        """ Creates splitters for window. Used to seperate the graphs and the buttons"""
        splitter = QtGui.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)
        splitter2 = QtGui.QSplitter()
        splitter2.setOrientation(QtCore.Qt.Vertical)
        self.layout.addWidget(splitter)
        splitter.addWidget(splitter2)
        return splitter, splitter2


    def create_layout(self, splitter):
        """Creates the layout for the buttons """
        pw1 = self.create_plot("Plot1")
        pw1.setYRange(-70, 0)
        pw1.setXRange(0, 10)
        splitter.addWidget(pw1)
        pw1.setLabel('left', 'RCS', units='dBsm')
        pw1.setLabel('bottom', 'Range', units='m')

        pw2 = self.create_plot("Plot2")
        splitter.addWidget(pw2)
        pw2.setLabel('left', 'Number of persons')
        pw2.setLabel('bottom', 'Distance', units='m')

        pw3 = self.create_plot("Plot3")
        splitter.addWidget(pw3)
        pw3.setYRange(0, 10)
        pw3.setLabel('left', 'V', units='m/s')
        pw3.setLabel('bottom', 'Time')

        return pw1, pw2, pw3

    def create_configuration_tree_and_parameter(self, splitter):
        """Creates the buttons in a parameter list where a dictionary is used to find specific button"""
        configuration_tree = ParameterTree(showHeader=False)
        splitter.addWidget(configuration_tree)

        params = Parameter.create(name='params', type='group', children=[
            dict(name="IP-address", type='str', value="192.168.0.90"),

            dict(name='Settings', type='group', children=[
            dict(name='Maximum Range', type='float', value=10.0),
            dict(name='Minimum Range', type='float', value=0.5),
            dict(name='Maximum Velocity', type='float', value=10.0),
            dict(name='Minimum Velocity', type='float', value=1.0),
            dict(name='Maximum Angle', type='float', value=15.0),
            dict(name='Minimum Angle', type='float', value=-15.0)]),

            dict(name='Start Stream', type='action'),
            dict(name='Stop Stream', type='action'),
            
            dict(name='Pause/Play', type='group', children=[
            dict(name='Pause/Play Graph 1', type='action'),
            dict(name='Pause/Play Graph 2', type='action'),
            dict(name='Pause/Play Graph 3', type='action'),
            dict(name='Toggle', type='action')])
            ])
        configuration_tree.setParameters(params, showTop=False)
        return configuration_tree, params

    def toggle_graph(self, timer):
        """Toggle between stop and start in graph"""
        timer.stop_time() if timer.timer_counting else timer.start_time()
    
    def toggle_v_plot(self):
        self.PLOT_VMAX = not self.PLOT_VMAX

    #Check if graph will use saved data or use data being streamed
    def start_stream(self):
        """ Starts a radar stream if radar currently is in stopped state """
        if self.state is State.STOPPED:
            #try to set ip address in .yml file
            # start a connection with radar
            # 
            return

      #  self.model.stream_from_radar() if self.state is State.STREAM else self.model.load_from_folder(self.folder_location)
        return

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()

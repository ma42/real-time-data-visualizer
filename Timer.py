from pyqtgraph.Qt import QtGui, QtCore

class Timer(QtCore.QTimer):
    """ Decorator for QTimer with a bool and int"""
    def __init__(self):
        self.timer_counting = True
        self.speed = 0
        QtCore.QTimer.__init__(self)

    def start_time(self):
        """Starts the graph"""
        self.start()
        self.timer_counting = True

    def stop_time(self):
        """Stops the graph"""
        self.stop()
        self.timer_counting = False

    @staticmethod
    def create_timer(function, time):
        """Uses QTimer to call a function every TIME ms.
        The function argument is the function you want to bind to the QTimer"""
        timer = Timer()
        timer.timeout.connect(function)
        timer.start(time)
        timer.speed = time
        return timer

import re
import pickle
import math
import metayaml
import statistics
from collections import deque
from os import listdir

class Model:
    def __init__(self, sensors):
        self.sensors = sensors
        self.files = deque()
        self.filepath = ""

    def get_radar_data(self, filter_params):
        data = self.sensors[0].networksink_reader.await_frame_result()
        d = data['object_list']
        range_data = []
        for (x, y) in zip(d['x'], d['y']):
            range_data.append(self.calculate_range(x, y))
        rcs_in_dBsm = [ self.get_dbsm(rcs) for rcs in d['rcs'] ]
        theta = [ self.get_angle(x,y,sensor) for (x,y,sensor) in zip(d['x'], d['y'], d['sensor_nbr']) ]
        zipped_data = list(zip(d['x'], d['y'], range_data, theta, d['snr'], rcs_in_dBsm, d['velocity'], d['sensor_nbr'])) # Creates list with tuples [(x,y,range,theta,snr,rcs(in dBsm),velocity,sensor_nbr)], every tuple is one point.
        filtered_data = [point for point in zipped_data if filter_params['mintheta'] < point[3] < filter_params['maxtheta'] and not point[7] == 0 ]
        return filtered_data

    def get_range_rcs(self, filter_params):
        """Used for graph 1. Gets the next frame directly from radarstream and make it graphable"""
        range_list = []
        rcs_list = []
        radar_data = self.get_radar_data(filter_params)
        radar_data = sorted(radar_data, key=lambda tup: tup[2])
        for point in radar_data: 
            if filter_params['minr'] < point[2] < filter_params['maxr']:
                range_list.append(point[2])
                rcs_list.append(point[5])
        return range_list, rcs_list

    def get_velocity(self, filter_params):
        vmax_list = []
        filtered_v = []
        radar_data = self.get_radar_data(filter_params)
        for point in radar_data:
            if filter_params['minv'] < point[6] < filter_params['maxv']:
                vmax_list.append(point[6])
                filtered_v.append(point)
        if not len(filtered_v) == 0:
            sorted_v_list = sorted(filtered_v, key=lambda tup: tup[5])
            return max(map(abs, vmax_list)), abs(sorted_v_list[-1][6])
        else: 
            return 0, 0

    @staticmethod
    def calculate_range(x, y):
        return math.sqrt(x**2 + y**2)

    @staticmethod
    def get_angle(x,y,sensor):
        theta = math.degrees(math.atan(y/x))
        return theta + 30 if (sensor == 0) else theta - 30

    @staticmethod
    def get_dbsm(sigma):
        return 10*math.log10(sigma)
    
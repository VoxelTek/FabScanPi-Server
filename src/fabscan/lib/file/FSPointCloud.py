__author__ = "Mario Lukas"
__copyright__ = "Copyright 2017"
__license__ = "GPL v2"
__maintainer__ = "Mario Lukas"
__email__ = "info@mariolukas.de"

import os
import datetime
import fileinput
import logging
import struct
import numpy as np
import gc
from fabscan.FSConfig import ConfigInterface
from fabscan.lib.util.FSInject import inject
from fabscan.FSVersion import __version__


class PointCloudError(Exception):

    def __init__(self):
        Exception.__init__(self, "PointCloudError")


@inject(
    config=ConfigInterface
)
class FSPointCloud():
    #__slots__ = ['points', 'file_name', 'dir_name', 'color', 'config', '_logger', 'file_handler', 'binary', 'file_path', 'line_count']

    def __init__(self, config, filename, postfix, color=True, binary=False):
        self.points = []
        self.texture = np.array([[],[],[]])
        self.file_name = filename
        self._dir_name = None
        self.color = color
        self.config = config
        self._logger = logging.getLogger(__name__)
        self.file_handler = None
        self.binary = binary
        self.file_path = None
        self.line_count = 0

        self.openFile(filename, postfix)

    def get_points(self):
        return self.points

    def to_lines(self, point_cloud, binary=False):
        if binary:
            return [str(struct.pack("<fffBBB", x, y, z, int(r), int(g), int(b))) for x, y, z, b, g, r in point_cloud]
        else:
            return ["{0} {1} {2} {3} {4} {5}\n".format(str(x), str(y), str(z), str(int(r)), str(int(g)), str(int(b))) for x, y, z, b, g, r in point_cloud]

    def append_points(self, points):

        for line in self.to_lines(points):
            self.file_handler.write(line.encode(encoding='UTF-8'))
            self.line_count += 1
        return

    def append_texture(self, texture):
        texture = np.array(texture)
        self.texture = np.hstack((self.texture, texture))

    def get_size(self):
        return len(self.points)

    def writeHeader(self):
        try:
            frame = "ply\n"
            if self.binary:
                frame += "format binary_little_endian 1.0\n"
            else:
                frame += "format ascii 1.0\n"
            frame += "comment Generated by FabScanPi\n"
            frame += "comment version {0}\n".format(__version__)
            frame += "comment {0}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            frame += "element vertex 0\n"
            frame += "property float x\n"
            frame += "property float y\n"
            frame += "property float z\n"
            frame += "property uchar red\n"
            frame += "property uchar green\n"
            frame += "property uchar blue\n"
            frame += "element face 0\n"
            frame += "property list uchar int vertex_indices\n"
            frame += "end_header\n"

            self.file_handler.write(frame.encode(encoding='UTF-8'))
        except IOError as err:
            self._logger.error(err)

    def writePointsToFile(self):
        pass

    def calculateNormals(self):
        pass

    def openFile(self, filename, postfix=''):
        basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self._dir_name = self.config.file.folders.scans+filename

        if(len(str(postfix)) > 0):
            filename = filename + '_' + str(postfix)
        try:
            if not os.path.exists(self._dir_name):
                 os.makedirs(self._dir_name)
            file_name = self._dir_name +'/scan_' +filename + '.ply'
            self.file_path = file_name
            file = open(file_name, 'wb')
            self.file_handler = file
            self.writeHeader()
            self._logger.info('File opened for writing ' + file_name)
            return
        except IOError as err:
            self._logger.error('Error while opening file ' + err)

    def closeFile(self):
        try:
            self.file_handler.close()
            self.modifyHeader()
            self.file_handler = None
            self.file_path = None
        except IOError as err:
            self._logger.error('Error while closing file ' + err)

    def modifyHeader(self):

        for line in fileinput.FileInput(self.file_path, inplace=True):
            if "element vertex 0\n" in line:
                line = line.replace(line, "element vertex {0}\n".format(str(self.line_count)))
            print(line, end='')

    def saveAsFile(self, filename, postfix=''):
        basedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self._dir_name = self.config.file.folders.scans+filename

        if(len(postfix) > 0):
            filename = filename + '_' + postfix

        try:
            if not os.path.exists(self._dir_name):
                 os.makedirs(self._dir_name)

            with open(self._dir_name +'/scan_' +filename + '.ply', 'wb') as f:
                self.save_scene_stream(f)

        except Exception as e:
            self._logger.error(e)

        del self.points[:]
        self.points = None
        self.texture = None

    def save_scene_stream(self, stream, binary=False):

        frame = "ply\n"
        if binary:
            frame += "format binary_little_endian 1.0\n"
        else:
            frame += "format ascii 1.0\n"
        frame += "comment Generated by FabScanPi software\n"
        frame += "element vertex {0}\n".format(str(self.get_size()))
        frame += "property float x\n"
        frame += "property float y\n"
        frame += "property float z\n"
        frame += "property uchar red\n"
        frame += "property uchar green\n"
        frame += "property uchar blue\n"
        frame += "element face 0\n"
        frame += "property list uchar int vertex_indices\n"
        frame += "end_header\n"
        stream.write(frame.encode(encoding='UTF-8'))

        if self.get_size() > 0:
            for point in self.points:
                x, y, z, r, g, b = point

                if binary:
                    frame = str(struct.pack("<fffBBB", x, y, z, int(r), int(g), int(b)))
                else:
                    frame = "{0} {1} {2} {3} {4} {5}\n".format(str(x), str(y), str(z), str(r), str(g), str(b))

                stream.write(frame.encode(encoding='UTF-8'))

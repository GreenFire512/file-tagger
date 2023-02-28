import PyQt5.QtCore

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QListWidget
from PyQt5.QtCore import QThread

class FileListWidget(QListWidget):
    def __init__(self):
        super(FileListWidget, self).__init__()
        self.setUniformItemSizes(True)
        # self.height = 100
        
    def addToList(self, item):
        self.addItem(item)


class QFileListItem(QWidget):
    def __init__(self):
        super(QFileListItem, self).__init__()
        uic.loadUi('qt/ui/filelistitem.ui', self)

    def setFileName(self, text):
        name = text.split('.')
        self.name.setText(name[0])
        self.type.setText(name[1])

    def setTags(self, text):
        self.tag.setText(text)


class AddItemToListThread(QThread):
    def __init__(self):
        super(AddItemToListThread, self).__init__()
        self.stopFlag = False

    def run(self, items):
        for file_name in items:
            if self.stopFlag:
                break
            self.emit(QtCore.SIGNAL('ping(PyQt_PyObject)'), file_name)
            sleep(0.005)
        self.stopFlag = False

    def stop(self):
        self.stopFlag = True
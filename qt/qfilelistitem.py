from PyQt5 import uic
from PyQt5.QtWidgets import QWidget

class QFileListItem(QWidget):
    def __init__(self):
        super(QFileListItem, self).__init__()
        uic.loadUi('qt/filelistitem.ui', self)

    def setFileName(self, text):
        name = text.split('.')
        self.name.setText(name[0])
        self.type.setText(name[1])

    def setTags(self, text):
        self.tag.setText(text)

import os
import shutil
import subprocess
import sys
import threading
import codecs

from database.qt.database import DataBase
from utils import *
from utils.constants import TEMP_DIR, TEMP_FILE_NAME, VLC_PATH
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QFileDialog, QListWidget, QMessageBox, QActionGroup, QAction, QInputDialog, QCompleter,
                             QListView, QListWidgetItem, QTreeWidget, QTreeWidgetItem)
from qt.qfilelistitem import QFileListItem

class App(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        uic.loadUi('qt/ui/mainwindow.ui', self)
        self.files_list = []
        self.tags_list = []
        self.tags_tree = []
        self.tags_name_list = []
        self.temp_file = TEMP_DIR + TEMP_FILE_NAME
        self.settings = app.settings
        self.db = DataBase('mydb.db')
        self.menu_template()
        self.splitter.setSizes([int(self.width() * 0.4), int(self.width() * 0.6)])
        self.splitter.setStyleSheet("border:2px solid rgb(0, 0, 0); ")
        self.leftLayout.setStyleSheet("border:1px solid rgb(0, 0, 0); ")
        self.rightLayout.setStyleSheet("border:1px solid rgb(0, 0, 0); ")
        self.actionAddFiles.triggered.connect(self.add_files_to_db)
        self.completerSearchTags = QCompleter(self.tags_name_list)
        self.completerFilesTags = QCompleter(self.tags_name_list)

        # Files
        self.lineSearchFile.installEventFilter(self)
        self.buttonDeleteFIleFromDb.triggered.connect(self.delete_file_from_db)
        self.button_open.triggered.connect(self.open_vlc)
        self.filesViewer.setSelectionMode(QListWidget.ExtendedSelection)
        self.filesViewer.itemDoubleClicked.connect(self.open_one_file)
        self.filesViewer.selectionModel().selectionChanged.connect(self.refresh_file_tag_list)
        self.filesViewer.installEventFilter(self)
        self.checkFileSorting.clicked.connect(self.set_files_list)
        self.checkTumbnailView.clicked.connect(self.set_files_view)
        self.buttonExport.triggered.connect(self.export_files_to_dir)
        self.buttonClear.triggered.connect(self.delete_not_exsist_files_from_db)
        self.buttonViewNotExist.triggered.connect(self.find_not_exisist_files_from_db)
        self.buttonViewExist.triggered.connect(self.see_exists_files)

        # All tags
        self.get_all_tags_list()
        self.buttonDeleteTagFromDb.triggered.connect(self.delete_tag_from_db)
        self.buttonAddTagToDb.triggered.connect(self.add_tag_to_db)
        self.treeAllTags.installEventFilter(self)
        self.treeAllTags.itemDoubleClicked.connect(self.tag_treeviewdouble_clicked)

        # Tag Search
        self.lineAddTagToSearch.installEventFilter(self)
        self.listSearchTag.setSelectionMode(QListWidget.ExtendedSelection)
        self.buttonDeleteTagFromSearch.clicked.connect(self.delete_tag_from_search)
        self.listSearchTag.itemDoubleClicked.connect(self.delete_tag_from_search)
        self.lineAddTagToFile.setCompleter(self.completerSearchTags)

        # File tags
        self.listFilesTags.setSortingEnabled(True)
        self.lineAddTagToFile.installEventFilter(self)
        self.buttonAddTagToFile.clicked.connect(self.add_tags_to_files)
        self.buttonDeleteTagFromFile.clicked.connect(self.remove_tag_from_files)
        self.lineAddTagToSearch.setCompleter(self.completerSearchTags)
        # END
        self.init_settings()

    def init_settings(self):
        data = self.settings.load_settings()
        templates = self.settings.get_profile_list()
        if data[0] in templates:
            for i in range(0, len(templates)):
                if self.menuProfiles.actions()[i].text() == data[0]:
                    self.menuProfiles.actions()[i].setChecked(True)
                    self.set_template(self.menuProfiles.actions()[i])
        self.checkFileSorting.setChecked(data[1] == 'True')

    # All tags
    def get_all_tags_list(self):
        self.treeAllTags.clear()
        self.tags_name_list.clear()
        self.tags_tree = self.db.Tag.tree()
        self.tags_name_list = self.db.Tag.list()
        self.create_tag_model(self.treeAllTags, self.tags_tree)
        self.refresh_completer()

    def add_tag_to_db(self):
        text, ok = QInputDialog.getText(self, "Tag Window", "Add Tag")
        if ok and text:
            self.db.Tag.add(str_to_tag(text))
            self.get_all_tags_list()

    def delete_tag_from_db(self):
        list_items = self._get_selected_items_from_tree()
        if not list_items:
            return
        qm = QMessageBox()
        result = qm.question(self, 'Delete', "Delete tags?", qm.Yes | qm.No)
        if result == qm.Yes:
            for item in list_items:
                try:
                    tag = self._tree_item_to_list(item)
                    self.db.Tag.delete(tag, False)
                    self._detele_item_from_tree(self.treeAllTags)
                    print(f'INFO: deleted tag: {tag[0]}:{tag[1]}')
                except:
                    print(f"ERROR: cant delete tag: {tag[0]}:{tag[1]}")
            self.db.save()

    def add_group_to_tag(self, tag):
        group, ok = QInputDialog.getText(self, "Group Window", "Add group")
        if ok:
            self.db.Tag.change_group(tag, group)
            self.get_all_tags_list()

    def search_tag_result(self):
        print(f'INFO: NOT IMPLEMENTED')
        # self.treeAllTags.clear()
        # if self.lineSearchTags.text():
        #     for tag in self.tags_name_list:
        #         if self.lineSearchTags.text().lower() in tag.lower():
        #             self.treeAllTags.addItem(tag)
        # else:
        #     self.treeAllTags.addItems(self.tags_name_list)

    # Tag Search
    def add_tag_to_search_from_tags(self):
        if self.treeAllTags.currentItem().text():
            self.listSearchTag.addItem(self.treeAllTags.currentItem().text())
            self.get_files_list()

    def add_tag_to_search_from_line(self):
        if self.lineAddTagToSearch.text():
            self.listSearchTag.addItem(self.lineAddTagToSearch.text())
            self.lineAddTagToSearch.clear()
            self.get_files_list()

    def delete_tag_from_search(self):
        list_items = self.listSearchTag.selectedItems()
        for item in list_items:
            self.listSearchTag.takeItem(self.listSearchTag.row(item))
        self.get_files_list()

    # File tags
    def refresh_file_tag_list(self):
        self.listFilesTags.clear()
        if self.filesViewer.currentItem():
            tag_list = self.db.File.get_tags_list(self.filesViewer.currentItem().text())
            if tag_list:
                for tag in tag_list:
                    if tag:
                        self.listFilesTags.addItem(tag_to_str(tag))
                    else:
                        self.listFilesTags.addItem("???")

    def add_tag_to_files(self):
        files = self.filesViewer.selectedItems()
        file_list = self._item_list_to_list(files)
        self.db.Tag.add_files(str_to_tag(self.lineAddTagToFile.text()), file_list)
        self.lineAddTagToFile.clear()
        self.refresh_file_tag_list()

    def add_tags_to_files(self):
        files = self.filesViewer.selectedItems()
        tags = self._get_selected_items_from_tree()
        for item in files:
            tag_list = self._tree_list_to_list(tags)
            self.db.File.add_tags(item.text(), tag_list, False)
            print(f'INFO: add to file: {item.text()} tags "{tag_list}"')
        self.db.save()
        self.refresh_file_tag_list()

    def remove_tag_from_files(self):
        files = self.filesViewer.selectedItems()
        if files and self.listFilesTags.currentItem():
            file_list = self._item_list_to_list(files)
            for file_name in file_list:
                self.db.Tag.remove_file(str_to_tag(self.listFilesTags.currentItem().text()), file_name, False)
                print(f'INFO: deleted tag "{self.listFilesTags.currentItem().text()}" from files: {file_name}')
            self.db.save()
            self.refresh_file_tag_list()

    def create_tag_model(self, widget, data):
        for group in data:
            if len(data[group]) > 0:
                widget_item = QtWidgets.QTreeWidgetItem(widget, [group])
                self.create_tag_model(widget_item, data[group])
            else:
                widget_item = QtWidgets.QTreeWidgetItem(widget, [group])

    def tag_treeviewdouble_clicked(self, index):
        items = self._get_selected_items_from_tree()
        for item in items:
            data_str = self._tree_item_to_str(item)
            self.listSearchTag.addItem(data_str)
        self.get_files_list()

    # Files
    def get_files_list(self):
        tags_list = []
        for i in range(self.listSearchTag.count()):
            tags_list.append(self.listSearchTag.item(i).text())
        self.files_list.clear()
        self.files_list = self.db.File.get_list_from_tags(tags_list)
        self.set_files_list()

    def thread_view_file(self):
        for file_name in self.files_list:
            item = QListWidgetItem(str(file_name))
            if '.jpg' in file_name or 'png' in file_name or 'jpeg' in file_name:
                item.setIcon(QIcon(QPixmap(self._get_full_path(file_name)).scaled(200, 200, QtCore.Qt.KeepAspectRatio)))
            self.filesViewer.addItem(item)

    def set_files_list(self):
        self.filesViewer.clear()
        self.filesViewer.setSortingEnabled(self.checkFileSorting.isChecked())
        if self.checkTumbnailView.isChecked():
            threading.Thread(target=self.thread_view_file, daemon=True).start()
        else:
            if self.files_list:
                self.filesViewer.addItems(self.files_list)

        # self.testlist.clear()
        # for file_name in self.files_list:
        #     myQListWidget = QFileListItem()
        #     myQListWidget.setFileName(file_name)
        #     myQListWidgetItem = QListWidgetItem(self.testlist)
        #     self.testlist.addItem(myQListWidgetItem)
        #     self.testlist.setItemWidget(myQListWidgetItem, myQListWidget)

    def set_files_view(self):
        if self.checkTumbnailView.isChecked():
            self.filesViewer.setResizeMode(QListView.Adjust)
            self.filesViewer.setViewMode(QListView.IconMode)
            self.filesViewer.setIconSize(QtCore.QSize(150, 150))
        else:
            self.filesViewer.setResizeMode(QListView.Fixed)
            self.filesViewer.setViewMode(QListView.ListMode)
        self.set_files_list()

    def search_file_result(self):
        self.filesViewer.clear()
        if self.lineSearchFile.text():
            for file in self.files_list:
                if self.lineSearchFile.text().lower() in file.lower():
                    self.filesViewer.addItem(file)
        else:
            self.filesViewer.addItems(self.files_list)

    def delete_file_from_db(self):
        list_items = self.filesViewer.selectedItems()
        if not list_items:
            return
        qm = QMessageBox()
        if qm.question(self, 'Delete', f"Delete files?", qm.Yes | qm.No) == qm.Yes:
            for item in list_items:
                self.filesViewer.takeItem(self.filesViewer.row(item))
                self.db.File.delete(item.text(), False)
                file_path = self._get_full_path(item.text())
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    print(f'INFO: deleted file: {item.text()}')
                except ValueError:
                    print(f"ERROR: can't deleted file: {item.text()}")
            self.db.save()

    def delete_not_exsist_files_from_db(self):
        qm = QMessageBox()
        if qm.question(self, 'Clear', f"Clear DB?", qm.Yes | qm.No) == qm.Yes:
            file_list = self.db.File.list()
            for file_name in file_list:
                file_path = self._get_full_path(file_name)
                if not os.path.exists(file_path):
                    self.db.File.delete(file_name, False)
                    print(f'INFO: deleted file: {file_name}')
            self.db.save()

    def find_not_exisist_files_from_db(self):
        self.files_list = []
        file_list = self.db.File.list()
        for file_name in file_list:
            file_path = self._get_full_path(file_name)
            if not os.path.exists(file_path):
                self.files_list.append(file_name)
        self.set_files_list()

    def see_exists_files(self):
        file_list = self.files_list.copy()
        self.files_list = []
        for file_name in file_list:
            file_path = self._get_full_path(file_name)
            if os.path.exists(file_path):
                self.files_list.append(file_name)
        self.set_files_list()

    def open_one_file(self):
        file_name = self.filesViewer.currentItem().text()
        file_path = self._get_full_path(file_name)
        if self._file_exists(file_path):
            subprocess.Popen([VLC_PATH, "file:///" + file_path])
        else:
            print(f'ERROR: file not exists: {file_name}')

    def export_files(self):
        file_list = []
        if self.filesViewer.count() > 0:
            for i in range(self.filesViewer.count()):
                file_list.append(self.filesViewer.item(i).text())
        return file_list

    def export_files_to_dir(self):
        file_list = self.export_files()
        if file_list:
            if not os.path.exists(self.path + '/export/'):
                os.mkdir(self.path + '/export/')
            for i in range(len(file_list)-1):
                if os.path.exists(self.path + '/' + file_list[i]):
                    shutil.move(self.path + '/' + file_list[i], self.path + '/export/' + file_list[i])

    def open_vlc(self):
        file_list = self.export_files()
        if file_list:
            file = codecs.open(self.temp_file, 'w', 'utf-8')
            for i in range(len(file_list)):
                string = self._get_full_path(file_list[i]) + "\n"
                file.write(string)
            file.close()
            subprocess.Popen([VLC_PATH, self.temp_file])

    # Else
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress and source is self.lineAddTagToSearch:
            if event.key() == QtCore.Qt.Key_Return and self.lineAddTagToSearch.hasFocus():
                self.add_tag_to_search_from_line()

        if event.type() == QtCore.QEvent.KeyPress and source is self.lineAddTagToFile:
            if event.key() == QtCore.Qt.Key_Return and self.lineAddTagToFile.hasFocus():
                self.add_tag_to_files()

        if event.type() == QtCore.QEvent.KeyPress and source is self.lineSearchFile:
            if event.key() == QtCore.Qt.Key_Return and self.lineSearchFile.hasFocus():
                self.search_file_result()

        if event.type() == QtCore.QEvent.KeyPress and source is self.filesViewer:
            if event.key() == QtCore.Qt.Key_Delete and self.filesViewer.hasFocus():
                self.delete_file_from_db()

        if event.type() == QtCore.QEvent.ContextMenu and source is self.treeAllTags:
            if self.treeAllTags.currentIndex():
                self.add_group_to_tag(self._tree_item_to_list(self.treeAllTags.currentIndex()))

        return super().eventFilter(source, event)

    def refresh_completer(self):
        self.completerSearchTags.model().setStringList(self.tags_name_list)
        self.completerFilesTags.model().setStringList(self.tags_name_list)

    def change_path(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if path:
            self.path = path

    def add_files_to_db(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if path:
            for file_name in os.listdir(path):
                if os.path.isfile(path + "/" + file_name):
                    try:
                        self.db.File.add(file_name, False)
                        print(f"ADD: file: {file}")
                    except:
                        print(f"ERROR: cant add file: {file_name}")
            self.db.save()

    def menu_template(self):
        templates = self.settings.get_profile_list()
        group = QActionGroup(self.menuProfiles)
        for template in templates:
            a = group.addAction(QAction(template, self.menuProfiles, checkable=True))
            self.menuProfiles.addAction(a)
            group.addAction(a)
        group.setExclusive(True)
        group.triggered.connect(self.set_template)

    def set_template(self, action):
        data = self.settings.get_data_from_profile(action.text())
        self.path = data[0]
        self.get_all_tags_list()
        self.settings.save_settings([action.text(), str(self.checkFileSorting.isChecked())])

    def _build_tree(self, data=None, parent=None):
        for key, value in data.items():
            item = QStandardItem(key)
            item.setText(0, key)
            if isinstance(value, dict):
                build_tree(data=value, parent=item)

    def _tree_to_list(self):
        result = []
        for group in self.tags_tree:
            for tag in group[1]:
                if not group[0]:
                    result.append(tag)
                else:
                    result.append(group[0] + ":" + tag)
        return result

    def _get_full_path(self, file_name) -> str:
        return str(self.path + "/" + file_name)

    def _tree_item_to_str(self, item) -> str:
        if item.parent().data():
            group = item.parent().data() + ':'
        else:
            group = ''
        return group + item.data()

    def _tree_list_to_list(self, item_list) -> list:
        result = []
        for item in item_list:
            result.append(self._tree_item_to_list(item))
        return result

    def _item_list_to_list(self, item_list) -> list:
        result = []
        for item in item_list:
            result.append(item.text())
        return result

    def _tree_item_to_list(self, item) -> list:
        if item.parent().data():
            group = item.parent().data()
        else:
            group = ''
        return [group, item.data()]

    def _tree_item_to_only_tag(self, item) -> str:
        return self._tree_item_to_list(item)[1]

    def _detele_item_from_tree(self, tree):
        root = tree.invisibleRootItem()
        for item in tree.selectedItems():
            (item.parent() or root).removeChild(item)

    def _get_selected_items_from_tree(self):
        return self.treeAllTags.selectedIndexes()

    def _file_exists(self, file_path: str):
        return os.path.exists(file_path)

def start_qt_app(app):
    winApp = QtWidgets.QApplication(sys.argv)
    window = App(app)
    window.show()
    winApp.exec_()
import codecs
import logging
import os
import shutil
import subprocess
import sys
import threading

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QAction, QCursor, QIcon, QPixmap, QStandardItem
from PyQt6.QtWidgets import QCompleter, QFileDialog, QInputDialog, QListView, QListWidgetItem, QMenu, QMessageBox

from database.database import DataBase
# from qt.filewidget import FileListItem
# from qt.tagwidget import *
from utils import str_to_tag, tag_to_str
from utils.constants import EXPORT_DIR, PLAYER_PATH, TEMP_DIR, TEMP_FILE_NAME

from .ui.ui_mainwindow import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, app):
        super().__init__()
        # load gui
        # uic.loadUi('qt/ui/mainwindow.ui', self)
        self.setupUi(self)

        self.file_list_all_type = []
        # self.path = ''
        self.file_type = {}
        self.file_list = []
        self.file_list_filtered = []
        self.tags_list = []
        self.tags_tree = []
        self.tags_name_list = []
        self.temp_file = TEMP_DIR + TEMP_FILE_NAME
        self.settings = app.settings
        self.profile_settings = self.settings.get_data_from_profile('linux')
        self.db = DataBase(self.profile_settings[1])
        self.path = self.profile_settings[0]
        # self.menu_template()
        self.splitter.setSizes([int(self.width() * 0.4), int(self.width() * 0.6)])
        self.splitter.setStyleSheet("border:2px solid rgb(0, 0, 0); ")
        self.leftLayout.setStyleSheet("border:1px solid rgb(0, 0, 0); ")
        self.rightLayout.setStyleSheet("border:1px solid rgb(0, 0, 0); ")
        self.completerSearchTags = QCompleter(self.tags_name_list)
        self.completerFilesTags = QCompleter(self.tags_name_list)

        # Files
        # self.FileListWidget = FileListWidget()
        # self.FileListGrid.addWidget(self.FileListWidget)
        self.lineSearchFile.installEventFilter(self)
        self.actionFilesDelete.triggered.connect(self.delete_file)
        self.actionFilesOpen.triggered.connect(self.open_vlc)
        self.filesViewer.itemDoubleClicked.connect(self.open_one_file)
        self.filesViewer.selectionModel().selectionChanged.connect(self.refresh_file_tag_list)
        self.filesViewer.installEventFilter(self)
        self.checkFileSorting.clicked.connect(self.view_files)
        self.checkThumbnailView.clicked.connect(self.set_files_view)
        self.actionExportFiles.triggered.connect(self.export_files_to_dir)
        self.actionFilesAdd.triggered.connect(self.add_files_to_db)
        self.actionFilesViewAll.triggered.connect(lambda: self.view_files(sort_type='all'))
        self.actionFilesViewExists.triggered.connect(lambda: self.view_files(sort_type='exist'))
        self.actionFilesViewNotExists.triggered.connect(lambda: self.view_files(sort_type='not exist'))
        self.actionAddTypesToFiles.triggered.connect(self.add_type_to_files)
        self.checkBoxImage.clicked.connect(self.get_file_list)
        self.checkBoxUnknown.clicked.connect(self.get_file_list)
        self.checkBoxVideo.clicked.connect(self.get_file_list)

        # All tags
        self.get_all_tags_list()
        self.actionTagsAdd.triggered.connect(self.add_tag_to_db)
        self.actionRename.triggered.connect(self.rename_tag)
        self.actionTagsChangeGroup.triggered.connect(self.add_or_change_group_to_tag)
        self.actionTagsDelete.triggered.connect(self.delete_tag_from_db)
        self.treeAllTags.installEventFilter(self)
        self.treeAllTags.itemDoubleClicked.connect(self.tag_treeviewdouble_clicked)

        # Tag Search
        self.lineAddTagToSearch.installEventFilter(self)
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
        # self.init_settings()
        self.init_file_type()

        self.get_files_list_from_db()

    def init_settings(self):
        data = self.settings.load_settings()
        templates = self.settings.get_profile_list()
        if data[0] in templates:
            for i in range(0, len(templates)):
                if self.menuProfiles.actions()[i].text() == data[0]:
                    # self.menuProfiles.actions()[i].setChecked(True)
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

    def delete_tag_from_db(self):
        list_items = self._get_selected_items_from_tree()
        if not list_items:
            return
        if self._message_box_yes_no('Delete', 'Delete tags?') is False:
            return
        for item in list_items:
            try:
                tag = self._tree_item_to_data(item, return_list=True)
                self.db.Tag.delete(tag, False)
                self._delete_item_from_tree(self.treeAllTags)
                logging.info(f'deleted tag: {tag[0]}:{tag[1]}')
            except:
                logging.error(f'cant delete tag: {tag[0]}:{tag[1]}')
        self.db.save()

    def add_or_change_group_to_tag(self):
        group_str = self._input_dialog('Group Window', 'Add or change group')
        if group_str is None:
            return
        tag = self._tree_item_to_data(self.treeAllTags.currentIndex(), return_list=True)
        self.db.Tag.change_group(tag, group_str)
        self.get_all_tags_list()

    def add_tag_to_db(self):
        tag_name = self._input_dialog('Tag Window', 'Add tag')
        if tag_name is None:
            return
        self.db.Tag.add(str_to_tag(tag_name))
        self.get_all_tags_list()

    def rename_tag(self):
        tag_name = self._input_dialog('Tag Window', 'Rename tag')
        if tag_name is None:
            return
        tag = self._tree_item_to_data(self.treeAllTags.currentIndex(), return_list=True)
        self.db.Tag.rename(tag, tag_name)
        self.get_all_tags_list()

    def search_tag_result(self):
        logging.warning('INFO: NOT IMPLEMENTED')
        # self.treeAllTags.clear()
        # if self.lineSearchTags.text():
        #     for tag in self.tags_name_list:
        #         if self.lineSearchTags.text().lower() in tag.lower():
        #             self.treeAllTags.addItem(tag)
        # else:
        #     self.treeAllTags.addItems(self.tags_name_list)

    # Tag Search
    def add_tag_to_search_from_tags(self):
        if not self.treeAllTags.currentItem().text():
            return
        self.listSearchTag.addItem(self.treeAllTags.currentItem().text())
        self.get_files_list_from_db()

    def add_tag_to_search_from_line(self):
        if not self.lineAddTagToSearch.text():
            return
        self.listSearchTag.addItem(self.lineAddTagToSearch.text())
        self.lineAddTagToSearch.clear()
        self.get_files_list_from_db()

    def delete_tag_from_search(self):
        list_items = self.listSearchTag.selectedItems()
        for item in list_items:
            self.listSearchTag.takeItem(self.listSearchTag.row(item))
        self.get_files_list_from_db()

    # File tags
    def refresh_file_tag_list(self):
        self.listFilesTags.clear()
        if not self.filesViewer.currentItem():
            return
        tag_list = self.db.File.get_tags_list(self.filesViewer.currentItem().text())
        if not tag_list:
            return
        for tag in tag_list:
            name = tag_to_str(tag) if tag else "???"
            self.listFilesTags.addItem(name)

    def add_tag_to_files(self):
        file_list = self._item_list_to_list(self.filesViewer.selectedItems())
        self.db.Tag.add_files(str_to_tag(self.lineAddTagToFile.text()), file_list)
        self.lineAddTagToFile.clear()
        self.refresh_file_tag_list()

    def add_tags_to_files(self):
        files = self.filesViewer.selectedItems()
        tags = self._get_selected_items_from_tree()
        for item in files:
            tag_list = self._tree_list_to_list(tags)
            self.db.File.add_tags(item.text(), tag_list, False)
            logging.info(f'add to file: {item.text()} tags "{tag_list}"')
        self.db.save()
        self.refresh_file_tag_list()

    def remove_tag_from_files(self):
        files = self.filesViewer.selectedItems()
        if not files or not self.listFilesTags.currentItem():
            return
        file_list = self._item_list_to_list(files)
        for file_name in file_list:
            self.db.Tag.remove_file(str_to_tag(self.listFilesTags.currentItem().text()), file_name)
            logging.info(f'deleted tag "{self.listFilesTags.currentItem().text()}" from files: {file_name}')
        self.db.save()
        self.refresh_file_tag_list()

    def create_tag_model(self, widget, data):
        for group in data:
            widget_item = QtWidgets.QTreeWidgetItem(widget, [group])
            if len(data[group]) > 0:
                self.create_tag_model(widget_item, data[group])

    def tag_treeviewdouble_clicked(self, index):
        for item in self._get_selected_items_from_tree():
            data_str = self._tree_item_to_data(item)
            self.listSearchTag.addItem(data_str)
        self.get_files_list_from_db()

    # Files
    def get_files_list_from_db(self):
        tags_list = []
        for i in range(self.listSearchTag.count()):
            tags_list.append(self.listSearchTag.item(i).text())
        if tags_list == []:
            tags_list = ['all']
        self.file_list_all_type.clear()
        self.file_list_all_type = self.db.File.get_list_from_tags(tags_list)
        self.get_file_list()
        self.file_list_filtered = self.file_list.copy()
        self.view_files(sort_type='exist')

    def init_file_type(self):
        files = self.db.File.list()
        for name in files:
            self.file_type[name] = self.db.File.get_type(name)

    def thread_view_file(self):
        for file_name in self.file_list_filtered:
            item = QListWidgetItem(str(file_name))
            if '.jpg' in file_name or 'png' in file_name or 'jpeg' in file_name:
                item.setIcon(QIcon(QPixmap(self._get_full_path(file_name)).scaled(200, 200, QtCore.Qt.KeepAspectRatio)))
            self.filesViewer.addItem(item)

    def get_file_list(self):
        self.file_list = []
        if not self.file_list_all_type:
            return
        file_type = []
        if self.checkBoxImage.isChecked():
            file_type.append('image')
        if self.checkBoxUnknown.isChecked():
            file_type.append('unknown')
        if self.checkBoxVideo.isChecked():
            file_type.append('video')
        self.file_list = []
        if file_type:
            for name in self.file_list_all_type:
                if self.file_type[name] in file_type:
                    self.file_list.append(name)
        else:
            self.file_list = self.file_list_all_type.copy()
        self.view_files(sort_type='exist')

    def view_files(self, sort_type=''):
        self.filesViewer.clear()
        self.filesViewer.setSortingEnabled(self.checkFileSorting.isChecked())

        if sort_type == 'exist':
            self.see_exists_files()
        elif sort_type == 'not exist':
            self.see_not_exists_files()
        elif sort_type == 'all':
            self.see_all_files()

        if self.checkThumbnailView.isChecked():
            threading.Thread(target=self.thread_view_file, daemon=True).start()
        else:
            self.filesViewer.addItems(self.file_list_filtered)

        # test
        # self.FileListWidget.clear()
        # thread = Thread(target=self.add_items_to_test)
        # thread.start()

    @QtCore.pyqtSlot(int)
    def add_items_to_test(self, file_name):
        pass
        # self.addItemToListThread = AddItemToListThread()
        # t = threading.Thread(name='AddToList', target=)
        # t.start()
        # self.connect(self.addItemToListThread, QtCore.SIGNAL("ping(PyQt_PyObject)"), self.FileListWidget.addToList)
        # self.addItemToListThread.run(self.file_list_filtered)
        # for file_name in self.file_list_filtered:
        # widget = FileListItem()
        # widget.setFileName(file_name)
        # item = QListWidgetItem(self.FileListWidget)
        # item.setSizeHint(widget.minimumSizeHint())
        # self.FileListWidget.addItem(item)
        # self.FileListWidget.setItemWidget(item, widget)

    def set_files_view(self):
        if self.checkThumbnailView.isChecked():
            self.filesViewer.setResizeMode(QListView.Adjust)
            self.filesViewer.setViewMode(QListView.IconMode)
            self.filesViewer.setIconSize(QtCore.QSize(150, 150))
        else:
            self.filesViewer.setResizeMode(QListView.Fixed)
            self.filesViewer.setViewMode(QListView.ListMode)
        self.view_files(sort_type='exist')

    def search_file_result(self):
        self.filesViewer.clear()
        self.file_list_filtered = []
        if self.lineSearchFile.text():
            for name in self.file_list:
                if self.lineSearchFile.text().lower() in name.lower():
                    self.file_list_filtered.append(name)
        else:
            self.file_list_filtered = self.file_list.copy()
        self.view_files()

    def delete_file(self, from_db=False):
        list_items = self.filesViewer.selectedItems()
        if not list_items:
            return
        if self._message_box_yes_no("Delete", "Delete files?") is False:
            return
        for item in list_items:
            file_name = item.text()
            self.filesViewer.takeItem(self.filesViewer.row(item))
            if from_db:
                self.db.File.delete(file_name, False)
            else:
                self.db.File.add_tag('deleted', file_name)
            file_path = self._get_full_path(file_name)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                logging.info(f'deleted file: {file_name}')
            except ValueError:
                logging.error(f"can't deleted file: {file_name}")

    def delete_not_exist_files_from_db(self):
        if self._message_box_yes_no('Clear', 'Clear DB?') is False:
            return
        file_list = self.db.File.list()
        for file_name in file_list:
            file_path = self._get_full_path(file_name)
            if not os.path.exists(file_path):
                self.db.File.delete(file_name, False)
                logging.info(f'INFO: deleted file: {file_name}')
        self.db.save()

    def find_not_exists_files_from_db(self):
        self.file_list_all_type = []
        file_list = self.db.File.list()
        for file_name in file_list:
            file_path = self._get_full_path(file_name)
            if not os.path.exists(file_path):
                self.file_list_all_type.append(file_name)
        self.get_file_list()
        self.file_list_filtered = self.file_list
        self.view_files()

    def see_exists_files(self):
        self.file_list_filtered = []
        for file_name in self.file_list:
            file_path = self._get_full_path(file_name)
            if os.path.exists(file_path):
                self.file_list_filtered.append(file_name)

    def see_not_exists_files(self):
        self.file_list_filtered = []
        for file_name in self.file_list:
            file_path = self._get_full_path(file_name)
            if not os.path.exists(file_path):
                self.file_list_filtered.append(file_name)

    def see_all_files(self):
        self.file_list_filtered = self.file_list.copy()

    def open_one_file(self):
        file_name = self.filesViewer.currentItem().text()
        file_path = self._get_full_path(file_name)
        if self._file_exists(file_path):
            subprocess.Popen([PLAYER_PATH, "file:///" + file_path])
        else:
            logging.error(f'file not exists: {file_name}')

    def export_files_to_dir(self):
        if self._message_box_yes_no('Import Files', 'Import Files?') is False:
            return
        file_list = self._export_files()
        if file_list:
            if not os.path.exists(self.path + EXPORT_DIR):
                os.mkdir(self.path + EXPORT_DIR)
            for i in range(len(file_list) - 1):
                if os.path.exists(self.path + '/' + file_list[i]):
                    shutil.move(self.path + '/' + file_list[i], self.path + EXPORT_DIR + file_list[i])

    def open_vlc(self):
        file_list = self._export_files()
        if not file_list:
            return
        file = codecs.open(self.temp_file, 'w', 'utf-8')
        for i in range(len(file_list)):
            string = self._get_full_path(file_list[i]) + "\n"
            file.write(string)
        file.close()
        subprocess.Popen([PLAYER_PATH, self.temp_file])

    def add_type_to_files(self):
        files_list = self.db.File.list()
        for file_name in files_list:
            self.db.File.refresh_type(file_name)
        self.db.save()

    # Else
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source is self.lineAddTagToSearch:
            if event.key() == Qt.Key.Key_Return and self.lineAddTagToSearch.hasFocus():
                self.add_tag_to_search_from_line()

        if event.type() == QEvent.Type.KeyPress and source is self.lineAddTagToFile:
            if event.key() == Qt.Key.Key_Return and self.lineAddTagToFile.hasFocus():
                self.add_tag_to_files()

        if event.type() == QEvent.Type.KeyPress and source is self.lineSearchFile:
            if event.key() == Qt.Key.Key_Return and self.lineSearchFile.hasFocus():
                self.search_file_result()

        if event.type() == QEvent.Type.KeyPress and source is self.filesViewer:
            if event.key() == QtCore.Qt.Key.Key_Delete and self.filesViewer.hasFocus():
                self.delete_file()

        if event.type() == QEvent.Type.ContextMenu and source is self.treeAllTags:
            if self.treeAllTags.currentIndex():
                self.context_menu_event(event)

        return super().eventFilter(source, event)

    def context_menu_event(self, event):
        rename_action = QAction('Rename', self)
        change_action = QAction('Change group', self)
        rename_action.triggered.connect(self.rename_tag)
        change_action.triggered.connect(self.add_or_change_group_to_tag)
        self.tree_all_tags_menu = QMenu(self)
        self.tree_all_tags_menu.addAction(rename_action)
        self.tree_all_tags_menu.addAction(change_action)
        self.tree_all_tags_menu.popup(QCursor.pos())

    def refresh_completer(self):
        self.completerSearchTags.model().setStringList(self.tags_name_list)
        self.completerFilesTags.model().setStringList(self.tags_name_list)

    def change_path(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory", directory=self.path))
        if path:
            self.path = path

    def add_files_to_db(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory", directory=self.path))
        if not path:
            return
        for file_name in os.listdir(path):
            file_path = path + "/" + file_name
            if not os.path.isfile(file_path):
                continue
            try:
                self.db.File.add(file_name, False)
                # new_path = path.parent + "/" + file_name
                # shutil.move(file_path, new_path)
                logging.info(f"add file: {file_name}")
            except:
                logging.error(f"cant add file: {file_name}")
        self.db.save()
        self.init_file_type()

    def menu_template(self):
        templates = self.settings.get_profile_list()
        group = QtWidgets.QMenu(self.menuProfiles)
        for template in templates:
            a = group.addAction(QAction(template, self.menuProfiles, checkable=True))
            self.menuProfiles.addAction(a)
            group.addAction(a)
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
                self._build_tree(data=value, parent=item)

    def _tree_to_list(self) -> list:
        result = []
        for group in self.tags_tree:
            for tag in group[1]:
                if group[0]:
                    tag = group[0] + ":" + tag
                result.append(tag)
        return result

    def _get_full_path(self, file_name) -> str:
        return str(self.path + "/" + file_name)

    def _tree_item_to_data(self, item, return_list=False):
        group = item.parent().data() if item.parent().data() else ''
        if return_list:
            return [group, item.data()]
        return (group + ':' if group else '') + item.data()

    def _tree_list_to_list(self, item_list) -> list:
        result = []
        for item in item_list:
            result.append(self._tree_item_to_data(item, return_list=True))
        return result

    def _item_list_to_list(self, item_list) -> list:
        result = []
        for item in item_list:
            result.append(item.text())
        return result

    def _tree_item_to_only_tag(self, item) -> str:
        return self._tree_item_to_data(item, return_list=True)[1]

    def _delete_item_from_tree(self, tree):
        root = tree.invisibleRootItem()
        for item in tree.selectedItems():
            (item.parent() or root).removeChild(item)

    def _get_selected_items_from_tree(self):
        return self.treeAllTags.selectedIndexes()

    def _file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def _export_files(self) -> list:
        file_list = []
        for i in range(self.filesViewer.count()):
            file_list.append(self.filesViewer.item(i).text())
        return file_list

    def _message_box_yes_no(self, title, message) -> bool:
        if QMessageBox.question(self, title, message) == QMessageBox.StandardButton.Yes:
            return True
        return False

    def _input_dialog(self, title, message) -> str:
        text, yes = QInputDialog.getText(self, title, message)
        if yes:
            return text
        return None


def start_qt_app(app_settings):
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app_settings)
    window.show()

    app.exec()

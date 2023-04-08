import logging
import os
from collections import defaultdict

from utils import str_to_tag


class BaseTable:
    """ Class for base table """
    def __init__(self, database):
        self.db = database

    @classmethod
    def id(self, file_name):
        """ Get id from table in database """
        self.db.search_one(self.TABLE, self.ID, self.NAME, file_name)
        return self.db.fetchone()


class File(BaseTable):
    """ Class of File table """
    TABLE = "File"
    ID = "id"
    NAME = "name"
    TYPE = "type"
    ADDED_DATE = "added_date"
    IMAGE_TYPE = ["jpeg", "jpg", "png", "gif", "jfif", "webp"]
    VIDEO_TYPE = ["mp4", "webm"]

    def create(self):
        """ Create File table in database """
        script = f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE} (
                {self.ID} INTEGER PRIMARY KEY,
                {self.NAME} TEXT NOT NULL UNIQUE,
                {self.TYPE} TEXT(10),
                {self.ADDED_DATE} INTEGER)
            CREATE UNIQUE INDEX File_name_IDX ON File (name,"type");
        """
        self.db.create(script)

    def list(self):
        self.db.select(self.TABLE, self.NAME, order=self.ID)
        return self.db.fetchall()

    def add_tag(self, tag, file_data, one=True):
        if isinstance(tag, int):
            tag_id = tag
        else:
            tag_id = self.db.Tag.id(tag)

        if isinstance(file_data, str):
            file_id = self.db.File.id(file_data)
        else:
            file_id = file_data

        self.db.inserts(TagFile.TABLE, [TagFile.TAG_ID, TagFile.FILE_ID], [tag_id, file_id])
        self.db.save(one)

    def add_tags(self, file_name: str, tag_list, one=True):
        file_id = self.db.File.id(file_name)
        for tag in tag_list:
            tag_id = self.db.Tag.id(tag)
            self.db.File.add_tag(tag_id, file_id, False)
        self.db.save(one)

    def name(self, file_id):
        self.db.search_one(self.TABLE, self.NAME, self.ID, file_id)
        return self.db.fetchone()

    def id(self, file_name):
        """ Get id of file from database """
        self.db.search_one(self.TABLE, self.ID, self.NAME, file_name)
        return self.db.fetchone()

    def add(self, name, one=True):
        file_type = self.db.File.get_file_type(name)
        self.db.inserts(self.TABLE, [self.NAME, self.TYPE], [name, file_type])
        self.db.save(one)

    def get_file_type(self, name):
        file_type = os.path.splitext(name)[1][1:]
        if file_type in self.IMAGE_TYPE:
            file_type = "image"
        elif file_type in self.VIDEO_TYPE:
            file_type = "video"
        else:
            file_type = "unknown"

        return file_type

    def delete(self, data, one=True):
        """ Delete file from database """
        file_id = data if isinstance(data, int) else self.db.File.id(data)
        self.db.delete(self.TABLE, self.ID, file_id)

        tag_list = self.db.File.get_tags_list(file_id)
        for tag in tag_list:
            self.db.File.delete_tag(tag, file_id, False)
        self.db.save(one)

    def get_tags_list(self, data):
        file_id = self.db.File.id(data) if isinstance(data, str) else data
        self.db.select_where(TagFile.TABLE, TagFile.TAG_ID, TagFile.FILE_ID, file_id, TagFile.TAG_ID)
        tag_ids = self.db.fetchall(logic=False)
        result = [self.db.Tag.name(tag_id[0]) for tag_id in tag_ids]
        return result

    def delete_tag(self, tag, file, one=True):
        tag_id = self.db.Tag.id(tag[1], tag[0])
        file_id = self.db.File.id(file)
        if tag_id and file_id:
            self.db.delete_from_tagfile(tag_id, file_id)
            self.db.save(one)

    def get_type(self, name):
        """ Get type of file from database """
        self.db.search_one(self.TABLE, self.TYPE, self.NAME, name)
        return self.db.fetchone()

    def refresh_type(self, name):
        """ Update all type of files in database """
        file_type = self.db.File.get_file_type(name)
        self.db.update_file_type(name, file_type)

    def get_list_from_tags(self, tag_list):
        tags_list = self.db.Tag.list()
        group_list = self.db.Group.list()
        group_and = []
        tag_and = []
        tag_or = []
        tag_not = []
        files_list = set()
        result_and = set()
        result_or = set()
        result_not = set()

        for tag_str in tag_list:
            if tag_str[0] == "+":
                tag = str_to_tag(tag_str[1:])
                if tag[1] in tags_list:
                    tag_or.append(self.db.Tag.id(tag))
            elif tag_str[0] == "-":
                tag = str_to_tag(tag_str[1:])
                if tag[1] in tags_list:
                    tag_not.append(self.db.Tag.id(tag))
            elif tag_str.lower() == "all":
                files_list = self.db.File.list()
            else:
                tag = str_to_tag(tag_str)
                if tag[0] == "" and tag[1] in group_list:
                    group_and.append(self.db.Group.id(tag[0]))
                elif tag[1] in tags_list:
                    tag_and.append(self.db.Tag.id(tag))

        if len(tag_and) == 1:
            tag_id = tag_and[0]
            self.db.cursor.execute(f"""
                SELECT name
                FROM File f
                INNER JOIN
                (
                SELECT file_id
                FROM TagFile tf
                WHERE tag_id = '{tag_id}'
                ORDER BY file_id ASC
                ) t ON f.id = t.file_id;
            """)
            data = self.db.cursor.fetchall()
            if data:
                for tag_id in data:
                    result_and.add(tag_id[0])
        else:
            count = len(tag_and)
            tags_str = ", ".join("'" + str(i) + "'" for i in tag_and)
            self.db.cursor.execute(f"""
                SELECT name
                FROM File f
                INNER JOIN
                (
                SELECT file_id
                FROM TagFile tf
                WHERE tag_id IN ({tags_str})
                GROUP BY file_id
                HAVING COUNT(DISTINCT tag_id) = {count}
                    ) t ON f.id = t.file_id;
            """)
            data = self.db.cursor.fetchall()
            if data:
                for tag_id in data:
                    result_and.add(tag_id[0])

        if len(tag_or) > 0:
            data = tag_or[0] if len(tag_or) == 1 else tuple(tag_or)
            result_or = self.db.Tag.get_file_list(data)
        if len(tag_not) > 0:
            data = tag_not[0] if len(tag_not) == 1 else tuple(tag_not)
            result_not = self.db.Tag.get_file_list(data)

        if result_or or result_and or result_not:
            if result_and or result_or:
                result_and.update(result_or)
                return set(result_and) - set(result_not)
            else:
                files_list = set()
                files_list.update(self.db.File.list())
                return set(files_list) - set(result_not)
        elif files_list:
            return files_list

        return []


class Tag(BaseTable):
    """ Class of Tag table """
    TABLE = "Tag"
    ID = "id"
    NAME = "name"
    GROUP_ID = "group_id"

    def create(self):
        script = f"""CREATE TABLE IF NOT EXISTS {self.TABLE} (
            {self.ID} INTEGER PRIMARY KEY, 
            {self.NAME} TEXT NOT NULL UNIQUE
            {self.GROUP_ID} INTEGER DEFAULT 0 NOT NULL,
            UNIQUE({self.NAME}, {self.GROUP_ID}) ON CONFLICT IGNORE
        ); """
        self.db.create(script)

    def add(self, tag, group_id=0, one=True):
        """ Add tag to the database """
        if isinstance(tag, list):
            tag_name = tag[1]
            group_id = self.db.Group.id(tag[0])
        else:
            tag_name = tag
            if group_id == "":
                group_id = 0

        self.db.inserts(self.TABLE, [self.NAME, self.GROUP_ID], [tag_name, group_id])
        self.db.save()

    def delete(self, tag, one=True, deep_delete=False):
        if isinstance(tag, list):
            tag_id = self.db.Tag.id(tag[1], tag[0])
        else:
            tag_id = tag

        if deep_delete:
            file_list = self.db.Tag.get_file_list(tag_id)
            for file_id in file_list:
                self.db.delete_from_tagfile(tag_id, file_id)

        self.db.delete(self.TABLE, self.ID, tag_id)
        self.db.save(one)

    def remove_file(self, tag, file, one=False, deep_delete=False):
        if isinstance(tag, list):
            tag_id = self.db.Tag.id(tag)
        else:
            tag_id = tag
        if isinstance(file, str):
            file_id = self.db.File.id(file)
        else:
            file_id = file
        self.db.delete_from_tagfile(tag_id, file_id)
        self.db.save(one)

    def id(self, tag, group_name=None):
        if isinstance(tag, list):
            tag_name = tag[1]
            group_id = self.db.Group.id(tag[0])
        else:
            tag_name = tag
            group_id = self.db.Group.id(group_name)
        self.db.select_tag(tag_name, group_id)

        return self.db.fetchone()

    def name(self, tag_id: int):
        try:
            self.db.search_one(self.TABLE, f"{self.NAME}, {self.GROUP_ID}", self.ID, tag_id)
            data = self.db.fetchone(logic=False)
            return [self.db.Group.name(data[1]), data[0]]
        except Exception as exception:
            logging.error("tag: %s, %s", tag_id, exception)
            return None

    def rename(self, tag, tag_name) -> None:
        if isinstance(tag, list) or isinstance(tag, str):
            tag_id = self.db.Tag.id(tag)
        else:
            tag_id = tag
        self.db.update_tag_name(tag_id, tag_name)
        self.db.save()

    def list(self) -> list:
        self.db.select(self.TABLE, self.NAME, self.GROUP_ID)
        return self.db.fetchall()

    def change_group(self, tag, group_id=0):
        if isinstance(group_id, str):
            group_id = self.db.Group.id(group_id)
        if not isinstance(tag[0], int):
            tag[0] = self.db.Group.id(tag[0])
        self.db.update_tag(tag, group_id)
        self.db.save()

    def add_files(self, tag, file_list):
        tag_id = self.db.Tag.get_id(tag[1], tag[0])
        if not tag_id:
            logging.error("Wrong tag: %s", tag)
        for file_name in file_list:
            self.db.File.add_tag(tag_id, file_name, False)
        self.db.save()

    def get_file_list(self, tag_id):
        self.db.select_where(TagFile.TABLE, TagFile.FILE_ID, TagFile.TAG_ID, tag_id)
        result = []
        data = self.db.fetchall()
        for file_id in data:
            result.append(self.db.File.name(file_id))
        return result

    def tree(self):
        self.db.select(self.TABLE, "name, group_id" )
        tags = self.db.fetchall(logic=False)
        if not tags:
            return {}

        tag_map = defaultdict()
        for tag in tags:
            group = self.db.Group.name(tag[1])
            if group:
                if group not in tag_map:
                    tag_map[group] = {}
                tag_map[group].update({tag[0]: {}})
            else:
                tag_map[tag[0]] = {}
        return tag_map


class Group(BaseTable):
    """ Class of Group table """
    TABLE = "Group"
    ID = "id"
    NAME = "name"

    def create(self):
        """ Create Group table in database """
        script = f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE} (
            {self.ID} INTEGER PRIMARY KEY, 
            {self.NAME} TEXT NOT NULL UNIQUE);
        """
        self.db.create(script)

    def add(self, name, one=True):
        self.db.insert(self.TABLE, self.NAME, name)
        self.db.save(one)
        return self.db.fetchone()

    def delete(self, name, one=True):
        self.db.delete(self.TABLE, self.NAME, name)
        self.db.save(one)

    def id(self, group_name: str):
        if group_name == "" or group_name == 0 or group_name is None:
            return 0
        self.db.search_one(self.TABLE, self.ID, self.NAME, group_name)
        result = self.db.fetchone()
        if result:
            return result

        return self.db.Group.add(group_name)

    def name(self, group_id: int):
        self.db.search_one(self.TABLE, self.NAME, self.ID, group_id)
        return self.db.fetchone()

    def list(self):
        self.db.select(self.TABLE, self.NAME)
        return self.db.fetchall()


class TagFile(BaseTable):
    """ Class of TagFile table """
    TABLE = "TagFile"
    ID = "id"
    FILE_ID = "file_id"
    TAG_ID = "tag_id"

    def create(self):
        """ create TagFile table in database """
        script = f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE} (
                {self.ID} INTEGER PRIMARY KEY,
                {self.TAG_ID} INTEGER NOT NULL,
                {self.FILE_ID} INTEGER NOT NULL,
            );
            CREATE UNIQUE INDEX IF NOT EXISTS {self.TABLE}_IDs ON {self.TABLE} ({self.TAG_ID}, {self.FILE_ID}); 
        """
        self.db.create(script)

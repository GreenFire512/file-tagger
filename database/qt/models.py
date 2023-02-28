import logging
import os
from utils import *

class File():
    TABLE = 'File'
    ID = 'id'
    NAME = 'name'
    TYPE = 'type'
    ADDED_DATE = 'added_date'
    IMAGE_TYPE = ['jpeg', 'jpg', 'png', 'gif', 'jfif']
    VIDEO_TYPE = ['mp4', 'webm']
    
    
    def __init__(self, db):
         self.db = db
         
         
    def create(self):
        script = f"""CREATE TABLE IF NOT EXISTS {__class__.TABLE} (
            {__class__.ID} INTEGER PRIMARY KEY, 
            {__class__.NAME} TEXT NOT NULL UNIQUE,
            {__class__.TYPE} TEXT(10),
            {__class__.ADDED_DATE} INTEGER)
            CREATE UNIQUE INDEX File_name_IDX ON File (name,"type");
        """
        self.db._create(script)
    
    def list(self):
        self.db._select(__class__.TABLE, __class__.NAME, order=__class__.ID)
        return self.db._fetchall()

    def add_tag(self, tag, file_data, one=True):
        if isinstance(tag, list):
           tag_id = self.db.Tag.id(tag)
        else:
            tag_id = tag
        if isinstance(file_data, str):
            file_id = self.db.File.id(file_data)
        else:
            file_id = file_data
        self.db._inserts(TagFile.TABLE, [TagFile.TAG_ID, TagFile.FILE_ID], [tag_id, file_id])
        self.db.save(one)
        
    def add_tags(self, file_name: str, tag_list, one=True):
        file_id = self.db.File.id(file_name)
        for tag in tag_list:
            tag_id = self.db.Tag.id(tag)
            self.db.File.add_tag(tag_id, file_id, False)
        self.db.save(one)

    def name(self, file_id):
        self.db._search_one(__class__.TABLE, __class__.NAME, __class__.ID, file_id)
        return self.db._fetchone()

    def id(self, file_name):
        self.db._search_one(__class__.TABLE, __class__.ID, __class__.NAME, file_name)
        return self.db._fetchone()

    def add(self, name, one=True):
        file_type = self.db.File.get_file_tyle(name)
        self.db._inserts(__class__.TABLE, [__class__.NAME, __class__.TYPE], [name, file_type])
        self.db.save(one)
        
    def get_file_tyle(self, name):
        file_type = os.path.splitext(name)[1][1:]
        if file_type in __class__.IMAGE_TYPE:
            file_type = 'image'
        elif file_type in __class__.VIDEO_TYPE:
            file_type = 'video'
        else:
            file_type = 'unknow'
        return file_type
        
    def fill_file_type(self, name):
        file_type = self.db.File.get_file_tyle(name)
        self.db._update_file_type(name, file_type)
        

    def delete(self, data, one=True):
        if isinstance(data, int):
            file_id = data
        else:
            file_id = self.db.File.id(data)
        self.db._delete(__class__.TABLE, __class__.ID, file_id)
        tag_list = self.db.File.get_tags_list(file_id)
        for tag in tag_list:
            self.db.File.delete_tag(tag, file_id, False)
        self.db.save(one)

    def get_tags_list(self, data):
        if isinstance(data, str):
            file_id = self.db.File.id(data)
        else:
            file_id = data
        self.db._select_where(TagFile.TABLE, TagFile.TAG_ID, TagFile.FILE_ID, file_id, TagFile.TAG_ID)
        data = self.db._fetchall(logic=False)
        result = []
        for tag_id in data:
            result.append(self.db.Tag.name(tag_id[0]))
        return result

    def delete_tag(self, tag, file, one=True):
        tag_id = self.db.Tag.id(tag[1], tag[0])
        file_id = self.db.File.id(file)
        if tag_id and file_id:
            self.db._delete_from_tagfile(tag_id, file_id)
            self.db.save(one)
    
    def get_type(self, name):
        self.db._search_one(__class__.TABLE, __class__.TYPE, __class__.NAME, name)
        return self.db._fetchone()

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
            elif tag_str.lower() == 'all':
                files_list = self.db.File.list()
            else:
                tag = str_to_tag(tag_str)
                if tag[0] == '' and tag[1] in group_list:
                    group_and.append(self.db.Group.id(tag[0]))
                elif tag[1] in tags_list:
                    tag_and.append(self.db.Tag.id(tag))

        if len(tag_and) == 1:
            tag_id = tag_and[0]
            self.db.cursor.execute(f"""SELECT name
                                    FROM File f
                                    INNER JOIN
                                    (
                                    SELECT file_id
                                    FROM TagFile tf
                                    WHERE tag_id = '{tag_id}'
                                    ORDER BY file_id ASC
                                    ) t ON f.id = t.file_id; """)
            data = self.db.cursor.fetchall()
            if data:
                for tag_id in data:
                    result_and.add(tag_id[0])
        else:
            count = len(tag_and)
            tags_str = ', '.join("'" + str(i) + "'" for i in tag_and)
            self.db.cursor.execute(f"""SELECT name
                                    FROM File f
                                    INNER JOIN
                                    (
                                    SELECT file_id
                                    FROM TagFile tf
                                    WHERE tag_id IN ({tags_str})
                                    GROUP BY file_id
                                    HAVING COUNT(DISTINCT tag_id) = {count}
                                       ) t ON f.id = t.file_id; """)
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
        else:
            return []


class Tag():
    TABLE = 'Tag'
    ID = 'id'
    NAME = 'name'
    GROUP_ID = 'group_id'
    
    def __init__(self, db):
         self.db = db
        
    def create(self):
        script = f"""CREATE TABLE IF NOT EXISTS {__class__.TABLE} (
            {__class__.ID} INTEGER PRIMARY KEY, 
            {__class__.NAME} TEXT NOT NULL UNIQUE
            {__class__.GROUP_ID} INTEGER DEFAULT 0 NOT NULL,
            UNIQUE({__class__.NAME}, {__class__.GROUP_ID}) ON CONFLICT IGNORE
        ); """
        self.db._create(script)

    
    def add(self, tag, group_id=0, one=True):
        if isinstance(tag, list):
            tag_name = tag[1]
            group_id = self.db.Group.id(tag[0])
        else:
            tag_name = tag
            if group_id == '':
                group_id = 0
        self.db._inserts(__class__.TABLE, [__class__.NAME, __class__.GROUP_ID], [tag_name, group_id])
        self.db.save()

    def delete(self, tag, one=True):
        if isinstance(tag, list):
            tag_id = self.db.Tag.id(tag[1], tag[0])
        else:
            tag_id = tag
        file_list = self.db.Tag.get_file_list(tag_id)
        for file_id in file_list:
            self.db._delete_from_tagfile(tag_id, file_id)
        self.db._delete(__class__.TABLE, __class__.ID, tag_id)
        self.db.save(one)
        
    def remove_file(self, tag, file, one):
        if isinstance(tag, list):
            tag_id = self.db.Tag.id(tag)
        else:
            tag_id = tag
        if isinstance(file, str):
            file_id = self.db.File.id(file)
        else:
            file_id = file
        self.db._delete_from_tagfile(tag_id, file_id)
        self.db.save(one)
        
    def id(self, tag, group_name=None):
        if isinstance(tag, list):
            tag_name = tag[1]
            group_id = self.db.Group.id(tag[0])
        else:
            tag_name = tag
            group_id = self.db.Group.id(group_name)
        self.db._select_tag(tag_name, group_id)
        result =  self.db._fetchone()
        return result

    def name(self, tag_id: int):
        try:
            self.db._search_one(__class__.TABLE, f'{__class__.NAME}, {__class__.GROUP_ID}', __class__.ID, tag_id)
            data = self.db._fetchone(logic=False)
            return [self.db.Group.name(data[1]), data[0]]
        except Exception as e:
            logging.error(f'tag: {tag_id}, {e}')
            return None
        
    def list(self):
        self.db._select(__class__.TABLE, __class__.NAME, __class__.GROUP_ID)
        return self.db._fetchall()

    def change_group(self, tag, group_id=0):
        if isinstance(group_id, str):
            group_id = self.db.Group.id(group_id)
        if not isinstance(tag[0], int):
            tag[0] = self.db.Group.id(tag[0])
        self.db._update_tag(tag, group_id)
        self.db.save()
        
    def add_files(self, tag, file_list):
        tag_id = self.tags.get_id(tag[1], tag[0])
        if not tag_id:
            logging.error(f"wrong tag: {tag}")
        for file_name in file_list:
            self.files.add_tag(tad_id, file_name, False)
        self.save()
        
    def get_file_list(self, tag_id):
        self.db._select_where(TagFile.TABLE, TagFile.FILE_ID, TagFile.TAG_ID, tag_id)
        result = []
        data = self.db._fetchall()
        for file_id in data:
            result.append(self.db.File.name(file_id))
        return result
        

    def tree(self):
        self.db.cursor.execute(f"""SELECT name, group_id FROM Tag; """)
        tags = self.db._fetchall(logic=False)
        tag_map = {}
        if tags:
            for tag in tags:
                group = self.db.Group.name(tag[1])
                if group:
                    if not group in tag_map:
                        tag_map[group] = {}
                    tag_map[group].update({tag[0]: {}})
                else:
                    tag_map[tag[0]] = {}
        return tag_map


class Group():
    TABLE = 'Group'
    ID = 'id'
    NAME = 'name'
    
    def __init__(self, db):
         self.db = db
                
    def create(self):
        script = f"""CREATE TABLE IF NOT EXISTS {__class__.TABLE} (
            {__class__.ID} INTEGER PRIMARY KEY, 
            {__class__.NAME} TEXT NOT NULL UNIQUE); """
        self.db._create(script)
        
    def add(self, name, one=True):
        self.db._insert(__class__.TABLE, __class__.NAME, name)
        self.db.save(one)
        return self.db._fetchone()
    
    def delete(self, name, one=True):
        self.db._delete(__class__.TABLE, __class__.NAME, name)
        self.db.save(one)

    def id(self, group_name: str):
        if group_name == '' or group_name == 0 or group_name == None:
            return 0
        self.db._search_one(__class__.TABLE, __class__.ID, __class__.NAME, group_name)
        result = self.db._fetchone()
        if result:
            return result
        else:
            return self.db.Group.add(group_name)

    def name(self, group_id: int):
        self.db._search_one(__class__.TABLE, __class__.NAME, __class__.ID, group_id)
        return self.db._fetchone()

    def list(self):
        self.db._select(__class__.TABLE, __class__.NAME)
        return self.db._fetchall()
    
class TagFile:
    TABLE = 'TagFile'
    ID = 'id'
    FILE_ID = 'file_id'
    TAG_ID = 'tag_id'
    
    def create():
        script = f"""CREATE TABLE IF NOT EXISTS {__class__.TABLE} (
                        {__class__.ID} INTEGER PRIMARY KEY,
                        {__class__.TAG_ID} INTEGER NOT NULL,
                        {__class__.FILE_ID} INTEGER NOT NULL,
                   );
                   CREATE UNIQUE INDEX IF NOT EXISTS {__class__.TABLE}_IDs ON {__class__.TABLE} ({__class__.TAG_ID}, {__class__.FILE_ID}); 
                """
        self.db._create(script)
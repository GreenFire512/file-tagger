from utils import *

class File():
    TABLE = 'File'
    COLUMN_ID = 'id'
    COLUMN_NAME = 'name'
    
    def __init__(self, db):
         self.db = db
         
         
    def create(self):
        return f"""CREATE TABLE IF NOT EXISTS {__class__.TABLE} (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE); """
    
    def list(self):
        self.db._select(__class__.TABLE, __class__.COLUMN_NAME)
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
        self.db._inserts('TagFile', ['tag_id', 'file_id'], [tag_id, file_id])
        self.db.save(one)
        
    def add_tags(self, file_name: str, tag_list, one=True):
        file_id = self.db.File.id(file_name)
        for tag in tag_list:
            tag_id = self.db.Tag.id(tag)
            self.db.File.add_tag(tag_id, file_id, False)
        self.db.save(one)

    def name(self, file_id):
        self.db._search_one(__class__.TABLE, __class__.COLUMN_NAME, __class__.COLUMN_ID, file_id)
        return self.db._fetchone()

    def id(self, file_name):
        self.db._search_one(__class__.TABLE, __class__.COLUMN_ID, __class__.COLUMN_NAME, file_name)
        return self.db._fetchone()

    def add(self, name, one=True):
        self.db._insert(__class__.TABLE, __class__.COLUMN_NAME, name)
        self.db.save(one)

    def delete(self, data, one=True):
        if isinstance(data, int):
            file_id = self.File.id(data)
        else:
            file_id = data
        self.db._delete(__class__.TABLE, __class__.COLUMN_ID, file_id)
        tag_list = self.db.File.get_tags_list(file_id)
        for tag in tag_list:
            self.db.File.delete_tag(tag, file_id, False)
        self.db.save(one)

    def get_tags_list(self, data):
        if isinstance(data, str):
            file_id = self.db.File.id(data)
        else:
            file_id = data
        self.db._select_where('TagFile', 'tag_id', 'file_id', file_id, 'tag_id')
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

        for tag in tag_list:
            if tag[0] == "+":
                tag = str_to_tag(tag[1:])
                if tag[1] in tags_list:
                    tag_or.append(self.db.Tag.id(tag))
            elif tag[0] == "-":
                tag = str_to_tag(tag[1:])
                if tag[1] in tags_list:
                    tag_not.append(self.db.Tag.id(tag))
            elif tag == 'all':
                files_list = self.db.File.list()
            else:
                tag = str_to_tag(tag)
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
            result_or = self.db.Tag.get_file_list(tag_or)
        if len(tag_not) > 0:
            result_not = self.db.Tag.get_file_list(tag_not)

        if result_or or result_and or result_not:
            if result_and or result_or:
                result_and.update(result_or)
                return result_and - result_not
            else:
                files_list = set()
                files_list.update(self.db.File.list())
                return files_list - result_not
        elif files_list:
            return files_list
        else:
            return ['not found']


class Tag():
    TABLE = 'Tag'
    COLUMN_ID = 'id'
    COLUMN_NAME = 'name'
    
    def __init__(self, db):
         self.db = db
    
    def add(self, tag, group_id=0, one=True):
        if isinstance(tag, list):
            tag_name = tag[1]
            group_id = self.db.Group.id(tag[0])
        else:
            tag_name = tag
            if group_id == '':
                group_id = 0
        self.db._inserts(__class__.TABLE, ['name', 'group_id'], [tag_name, group_id])
        self.db.save()

    def delete(self, tag, one=True):
        if isinstance(tag, list):
            tag_id = self.db.Tag.id(tag[1], tag[0])
        else:
            tag_id = tag
        self._delete(__class__.TABLE, 'id', tag_id)
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
        return self.db._fetchone()

    def name(self, tag_id: int):
        self.db._search_one(__class__.TABLE, 'name, group_id', 'id', tag_id)
        data = self.db._fetchone(logic=False)
        return [self.db.Group.name(data[1]), data[0]]
        
    def list(self):
        self.db._select(__class__.TABLE, "name", "group_id")
        return self.db._fetchall()

    def change_group(self, tag, group_id=0):
        if isinstance(group_id, str):
            group_id = self.db.Group.id(group_id)
        self.db._update_tag(tag, group_id)
        self.db.save()
        
    def add_files(self, tag, file_list):
        tag_id = self.tags.get_id(tag[1], tag[0])
        if not tag_id:
            print(f"ERROR: wrong tag: {tag}")
        for file_name in file_list:
            self.files.add_tag(tad_id, file_name, False)
        self.save()
        
    def get_file_list(self, tag):
        tag_id = seld.db.Tag.id(tag)
        self.db._select_where('TagFile', 'file_id', 'tag_id', tag_id)
        result = self.db._fetchall()
        print('es')
        

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
    
    def __init__(self, db):
         self.db = db
                
    def add(self, name, one=True):
        self.db._insert(__class__.TABLE, 'name', name)
        self.db.save(one)
        return self._fetchone()
    
    def delete(self, name, one=True):
        self.db._delete(__class__.TABLE, 'name', name)
        self.db.save(one)

    def id(self, group_name: str):
        if group_name == '' or group_name == 0:
            return 0
        self.db._search_one(__class__.TABLE, 'id', 'name', group_name)
        result = self.db._fetchone()
        if result:
            return result
        else:
            return self.db.Group.add(group_name)

    def name(self, group_id: int):
        self.db._search_one(__class__.TABLE, 'name', 'id', group_id)
        return self.db._fetchone()

    def list(self):
        self.db._select(__class__.TABLE, 'name')
        return self.db._fetchall()
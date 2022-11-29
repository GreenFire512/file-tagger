import sqlite3
from utils import *
from utils.constants import DB_DIR
from database.qt.models import Tag, File, Group


class DataBase():
    def __init__(self, db_name='database.db'):
        self.Tag = Tag(self)
        self.File = File(self)
        self.Group = Group(self)
        self.db_name = db_name
        self.connect()

    def connect(self, db_name=None):
        if db_name != None:
            self.db_name = db_name
        self.connection = sqlite3.connect(DB_DIR + self.db_name)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        self.connection.close()

    def reconnect(self, db_name=None):
        self.disconnect()
        self.connect(db_name)

    def save(self,one=True, message=False):
        if message:
            print(f"Total {self.cursor.rowcount}")
        if one:
            self.connection.commit()

    def create(self):
        self.db.File.create()
        
        self.connection.executescript("""CREATE TABLE IF NOT EXISTS TagFile (
                                                id INTEGER,
                                                tag_id INTEGER NOT NULL,
                                                file_id INTEGER NOT NULL,
                                                CONSTRAINT tagged_files_PK PRIMARY KEY (id)
                                            );
                                    CREATE UNIQUE INDEX IF NOT EXISTS TagFile_IDs ON TagFile (tag_id,file_id); """)
        self.connection.executescript("""CREATE TABLE IF NOT EXISTS Tag (
                                                id INTEGER PRIMARY KEY,
                                                name TEXT NOT NULL,
                                                group_id INTEGER DEFAULT 0 NOT NULL,
                                                UNIQUE(name, group_id) ON CONFLICT IGNORE
                                         ); """)
        self.connection.executescript("""CREATE TABLE IF NOT EXISTS Group (
                                                id INTEGER PRIMARY KEY,
                                                name TEXT NOT NULL UNIQUE
                                         ); """)
        self.save()

    def _get_file_list_by_tag(self, tag_list):
        tags_str = ', '.join("'" + str(i) + "'" for i in tag_list)
        self.cursor.execute(f"""SELECT name
                                FROM File f
                                INNER JOIN
                                (
                                    SELECT id
                                    FROM TagFile tf
                                    WHERE id IN ({tags_str})
                                    ORDER BY id ASC
                                ) t ON f.id = t.id;
                            """)
        return self._fetchall(is_dict=True)

    # CREATE
    def _create(self, script: str):
        self.connection.executescript(script)

    # FETCH
    def _fetchone(self, logic=True):
        result = self.cursor.fetchone()
        if logic:
            if result:
                return result[0]
        else:
            return result

    def _fetchall(self, is_dict=False, logic=True):
        data = self.cursor.fetchall()
        if logic:
            result = []
            if is_dict:
                result = set()
            for item in data:
                if is_dict:
                    result.add(item[0])
                else:
                    result.append(item[0])
            return result
        else:
            return data


    # DELETE
    def _delete(self, table: str, column: str, what: str):
        try:
            self.connection.execute(f"""DELETE FROM {table} WHERE {column} = '{what}'; """)
            print("Total", self.cursor.rowcount, "Records deleted successfully")
        except sqlite3.Error as error:
            print(f"ERROR: {error}")
                                        
    def _delete_from_tagfile(self, tag_id: int, file_id: int):
        self.connection.execute(f"""DELETE FROM TagFile WHERE TAG_ID = '{tag_id}' AND FILE_ID = '{file_id}'; """)
        
    
    # INSERT
    def _insert(self, table:str, column:str, value:str):
        self.connection.execute(f"""INSERT OR IGNORE INTO {table} ('{column}') VALUES ('{value}') RETURNING id; """)

    def _inserts(self, table:str, colums: list, data: list):
        columns_str = str(colums[0]) + "', '" + str(colums[1])
        values_str = str(data[0]) + "', '" + str(data[1])
        self.connection.execute(f"""INSERT OR IGNORE INTO {table} ('{columns_str}') VALUES ('{values_str}'); """)


    # SEARCH
    def _search_one(self, table: str, columns_select: str, column_where: str, where: str):
        self.cursor.execute(f"""SELECT {columns_select} FROM '{table}' WHERE {column_where} = '{where}'; """)
        
        
    # SELECT
    def _select(self, table: str, columns: str, order=''):
        if order:
            order = f'ORDER by {order} ASC'
        self.cursor.execute(f"""SELECT {columns} FROM '{table}' {order}; """)
        
    def _select_tag(self, tag_name:str, group_id:int):
        self.cursor.execute(f"""SELECT ID FROM Tag WHERE name = '{tag_name}' AND group_id = '{group_id}'; """)
        
    def _select_where(self, table:str, column:str, column_where:str, where:str, order=''):
        if order:
            order = f'ORDER by {order} ASC'
        self.cursor.execute(f"""SELECT {column} FROM '{table}' where {column_where} = '{where}' {order}; """)
        
    # UPDATE
    def _update_tag(self, tag, group_id):
        self.connection.execute("UPDATE tags SET TAG_NAME=?, TAG_GROUP_ID=? WHERE TAG_NAME=? AND TAG_GROUP_ID=?;", \
                                (tag[1], group_id, tag[1], tag[0]))
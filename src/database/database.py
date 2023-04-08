import logging
import sqlite3

from utils.constants import DB_DIR

from .models import File, Group, Tag, TagFile


class DataBaseTest:
    """ DataBase class """
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(DB_DIR + self.db_name)
        cursor = self.connection.cursor()

        return cursor

    def __exit__(self, _type, value, traceback):
        self.connection.commit()
        self.connection.close()


class DataBase:
    """ DataBase class """
    def __init__(self, db_name="database.db"):
        self.Tag = Tag(self)
        self.File = File(self)
        self.Group = Group(self)
        self.TagFile = TagFile(self)
        self.db_name = db_name
        self.connect()

    def connect(self, db_name=None):
        """ Connect to database """
        if db_name is not None:
            self.db_name = db_name
        self.connection = sqlite3.connect(DB_DIR + self.db_name)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        """ Disconnect from database """
        self.connection.close()

    def reconnect(self, db_name=None):
        """ Reconnect to database """
        self.disconnect()
        self.connect(db_name)

    def save(self, save=True, log=False):
        """ Save database state """
        if log:
            print(f"Total {self.cursor.rowcount}")
        if save:
            message = self.cursor.execute("SELECT changes()")
            logging.info(message)
            self.connection.commit()

    def create_db(self):
        """ Create database """
        self.File.create()
        self.Tag.create()
        self.Group.create()
        self.TagFile.create()
        self.save()

    def _get_file_list_by_tag(self, tag_list):
        tags_str = ", ".join("'" + str(i) + "'" for i in tag_list)
        self.cursor.execute(f"""
            SELECT name
            FROM File f
            INNER JOIN
            (
                SELECT id
                FROM TagFile tf
                WHERE id IN ({tags_str})
                ORDER BY id ASC
            ) t ON f.id = t.id;
        """)

        return self.fetchall(is_dict=True)

    # CREATE
    def create(self, script: str):
        """ run script """
        self.connection.executescript(script)

    # FETCH
    def fetchone(self, logic=True):
        """ Fetch one row from database """
        result = self.cursor.fetchone()

        if not logic:
            return result

        if result:
            return result[0]

    def fetchall(self, is_dict=False, logic=True):
        """ Fetch all rows from database """
        fetched_data = self.cursor.fetchall()

        if not logic:
            return fetched_data

        if is_dict:
            result = set()
        else:
            result = []
        for item in fetched_data:
            if is_dict:
                result.add(item[0])
            else:
                result.append(item[0])

        return result

    # DELETE
    def delete(self, table: str, column: str, what):
        """ Delete row in `table` database """
        try:
            self.connection.execute(f"""DELETE FROM '{table}' WHERE {column} = '{what}'; """)
            logging.info("Total %s records deleted successfully", self.cursor.rowcount)
        except sqlite3.Error as error:
            logging.error(error)

    def delete_from_tagfile(self, tag_id: int, file_id: int):
        """ Delete row in TagFile table """
        self.connection.execute(f"""DELETE FROM TagFile WHERE TAG_ID = '{tag_id}' AND FILE_ID = '{file_id}'; """)

    # INSERT
    def insert(self, table: str, column: str, value: str):
        """ Insert row in database """
        self.connection.execute(f"""INSERT OR IGNORE INTO '{table}' ('{column}') VALUES ('{value}') RETURNING id; """)

    def inserts(self, table: str, columns: list, data: list, ignore=True):
        db_ingore = 'OR IGNORE' if ignore else ''
        columns_str = str(columns[0]) + "', '" + str(columns[1])
        values_str = str(data[0]) + "', '" + str(data[1])
        self.connection.execute(
            f"INSERT {db_ingore} INTO '{table}' ('{columns_str}') VALUES ('{values_str}');"
        )

    # SEARCH
    def search_one(self, table: str, columns_select: str, column_where: str, where: str):
        """ Search in `table` by one parameter """
        self.cursor.execute(
            f"SELECT {columns_select} FROM '{table}' WHERE {column_where} = '{where}';"
        )

    # SELECT
    def select(self, table: str, columns: str, order=""):
        if order:
            order = f"ORDER by {order} ASC"
        self.cursor.execute(f"""SELECT {columns} FROM '{table}' {order}; """)

    def select_tag(self, tag_name: str, group_id: int):
        self.cursor.execute(
            f"""SELECT ID FROM Tag WHERE name = '{tag_name}' AND group_id = '{group_id}'; """
        )

    def select_where(self, table: str, column: str, column_where: str, where, order=""):
        """
        The select_where function is used to select a column from a table where the value of another column matches
            the given value. The order parameter can be used to sort the results in ascending order by any other column.
        :param table: str: Specify the table that you want to select from
        :param column: str: Specify which column to select from the table
        :param column_where: str: Specify which column to use in the where clause
        :param where: Filter the results of the query
        :param order: Order the results by a specific column
        """
        if order:
            order = f"ORDER by {order} ASC"
        if isinstance(where, int):
            where = f"('{where}')"
        self.cursor.execute(
            f"""SELECT {column} FROM {table} where {column_where} IN {where} {order}; """
        )

    # UPDATE
    def update_tag_name(self, tag_id, tag_name: str):
        """ Update row in Tag table """
        self.connection.execute(f"""UPDATE Tag SET name='{tag_name}' WHERE id='{tag_id}'; """)

    def update_file_type(self, file_name: str, file_type: str):
        """ Update column `type` in File table """
        self.connection.execute(
            f"""UPDATE File SET name='{file_name}', type='{file_type}' WHERE name='{file_name}'; """
        )

    def update_tag(self, tag: list, group_id: int):
        """
        Update row in Tag table
        :param tag: list of tag and group
        :param group_id: id of updated tag group
        """
        self.connection.execute(
            f"UPDATE Tag SET name='{tag[1]}', group_id={group_id} WHERE name='{tag[1]}' AND group_id={tag[0]};"
        )

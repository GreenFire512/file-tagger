from database.qt.models import *


class DataBase:
    @staticmethod
    def save():
        session.commit()

    @staticmethod
    def get_or_create(session, model, **kwargs):
        instance = session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance, False
        else:
            instance = model(**kwargs)
            session.add(instance)
            return instance, True

class Tags():
    @staticmethod
    def add(tag_list, one=True):
        tag, is_created = DataBase.get_or_create(session, Tag, name=tag_list[1], group_id=Groups.id(tag_list[0]))
        if is_created and one:
            DataBase.save()
        return tag.id

    @staticmethod
    def delete(tag_list, one=True):
        tag = session.query(Tag).filter(Tag.name == tag_list[1], Tag.group_id == Groups.id(tag_list[0])).first()
        if tag:
            session.delete(tag)
            if one:
                DataBase.save()
        return tag.id

    @staticmethod
    def all():
        return session.execute(select(Tag.name)).scalars().all()

    @staticmethod
    def change_group(tag_list, group_name=0):
        if group_name:
            tag_list[0] = Group.get_id(tag_list[0])
            tag = session.query(Tag).filter(Tag.name == tag_list[1], Tag.group_id == tag_list[0]).first()
            tag.group_id = Group.get_id(group_name)
            DataBase.save()

    @staticmethod
    def tree():
        state = session.query(Tag).all()
        tag_map = {}
        if state:
            for tag in state:
                if tag.group_id != 0:
                    group = session.get(Group, tag.group_id).name
                    if not group in tag_map:
                        tag_map[group] = {}
                    tag_map[group].update({tag.name: {}})
                else:
                    tag_map[tag.name] = {}
        return tag_map

    @staticmethod
    def name(id):
        tag = session.query(Tag).filter(Tags.id == id).first()
        return tag.name

    @staticmethod
    def id(tag_list):
        tag = session.query(Tag).filter(Tag.name == tag_list[1], Tag.group_id == Groups.id(tag_list[0])).first()
        return tag.id

    @staticmethod
    def files(tag_id):
        tag = session.query(Tag).filter_by(id=tag_id).first()
        file_list = tag.files
        result = []
        if file_list:
            for file in file_list:
                result.append(file.name)
        return result

    @staticmethod
    def add_files(tag, file_list, one=True):
        tag_id = Tag.get_id(tag)
        tag = session.query(Tag).filter_by(id=tag_id).first()
        for file_name in file_list:
            file = session.query(File).filter_by(name=file_name).first()
            tag.files.append(file)
        if one:
            DataBase.save()
        return file.id

    @staticmethod
    def remove_files(tag, file_list, one=True):
        tag_id = Tags.id(tag)
        tag = session.query(Tag).filter_by(id=tag_id).first()
        for file_name in file_list:
            file = session.query(File).filter_by(name=file_name).first()
            if file in tag.files:
                tag.files.remove(file)
        if one:
            DataBase.save()
        return file.id


class Groups():
    @staticmethod
    def id(group_name):
        if group_name == '' or group_name == 0:
            return 0
        group = session.query(Group).filter(Group.name == group_name).first()
        if group:
            return group.id
        else:
            return Groups.add(group_name)

    @staticmethod
    def add(group_name):
        group, is_created = DataBase.get_or_create(session, Group, name=group_name)
        if is_created:
            DataBase.save()
        return group.id

    @staticmethod
    def delete(group_name):
        group = session.query(Group).filter(Group.name == group_name).first()
        session.delete(group)
        DataBase.save()

    @staticmethod
    def name(id):
        if id == 0 or id == '':
            return ''
        group = session.query(Group).filter(Group.id == id).first()
        if group:
            return group.name

    @staticmethod
    def all():
        return session.execute(select(Group.name)).scalars().all()

class Files():
    @staticmethod
    def add(file_name, one=True):
        state,is_created = DataBase.get_or_create(session, File, name=file_name)
        if is_created and one:
            DataBase.save()
        return state.id

    @staticmethod
    def delete(file_name, one=True):
        state = session.query(File).filter(File.name == file_name).first()
        session.delete(state)
        if one:
            DataBase.save()
        return state.id

    @staticmethod
    def id(file_name):
        return session.query(File).filter(File.name == file_name).first().id

    @staticmethod
    def name(id):
        state = session.query(File).filter(File.id == id).first()
        if state:
            return state.name
        return '???'

    @staticmethod
    def all():
        return session.execute(select(File.name)).scalars().all()

    @staticmethod
    def tags(file_name):
        file = session.query(File).filter_by(name=file_name).first()
        if file:
            tags = file.tags
            result = []
            for tag in tags:
                result.append([Groups.name(tag.group_id), tag.name])
            return result
        else:
            return 'wrong file'

    @staticmethod
    def add_tags(file_name, tag_list, one=True):
        file = session.query(File).filter_by(name=file_name).first()
        for tag in tag_list:
            tag_id = Tags.id(tag)
            tag = session.query(Tag).filter_by(id=tag_id).first()
            file.tags.append(tag)
        if one:
            DataBase.save()
        return file.id

    @staticmethod
    def remove_tags(file_name, tag_list, one=True):
        file = session.query(File).filter_by(name=file_name).first()
        for tag in tag_list:
            tag_id = Tags.id(tag)
            tag = session.query(Tag).filter_by(id=tag_id).first()
            file.tags.remove(tag)
        if one:
            DataBase.save()
        return file.id

    @staticmethod
    def get_by_tags(tags_list):
        all_tags = Tags.all()
        group_list = Groups.all()
        group_and = []
        tag_and = []
        tag_or = []
        tag_not = []
        files_list = set()
        result_and = set()
        result_or = set()
        result_not = set()

        for tag_str in tags_list:
            if tag_str[0] == "+":
                tag_list = str_to_tag(tag_str[1:])
                if tag_list[1] in all_tags:
                    tag_or.append(Tags.id(tag_list))
            elif tag_str[0] == "-":
                tag_list = str_to_tag(tag_str[1:])
                if tag_list[1] in all_tags:
                    tag_not.append(Tags.id(tag_list))
            elif tag_str == 'all':
                files_list = Files.all()
            else:
                tag_list = str_to_tag(tag_str)
                # if tag_list[0] == '' and tag_list[1] in group_list:
                #     group_and.append(Group.get_id(tag_list[0]))
                if tag_list[1] in all_tags:
                    tag_and.append(Tags.id(tag_list))

        if len(tag_and) == 1:
            tag = session.query(Tag).filter_by(id=tag_and[0]).first()
            file_list = tag.files
            if file_list:
                for file in file_list:
                    result_and.add(file.name)

        else:
            count = len(tag_and)
            for tag_id in tag_and:
                tag = session.query(Tag).filter_by(id=tag_id).first()
                file_list = tag.files
                temp = set()
                if file_list:
                    for file in file_list:
                        temp.add(file.name)
                if result_and:
                    result_and = result_and.intersection(temp)
                else:
                    result_and = temp
        if len(tag_or) > 0:
            file_list = session.query(association_table).join(Tag).join(File).filter(Tag.id.in_(tag_and)).all()
            if file_list:
                for file in file_list:
                    result_or.add(Files.get_name(file.file_id))
        if len(tag_not) > 0:
            file_list = session.query(TagFile).filter(TagFile.tag_id.in_(tag_not)).all()
            if file_list:
                for file in file_list:
                    result_not.add(Files.get_name(file.file_id))

        if result_or or result_and or result_not:
            if result_and or result_or:
                result_and.update(result_or)
                return result_and - result_not
            else:
                files_list = set()
                files_list.update(File.get_all())
                return files_list - result_not
        elif files_list:
            return files_list
        else:
            return ['not found']
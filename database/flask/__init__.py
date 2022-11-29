from database.flask.models import *
from utils import *

class Tags:
    @staticmethod
    def get_tree():
        state = Tag.query.all()
        result = {}
        for tag in state:
            if tag.group_id != 0:
                group = Group.query.filter_by(id=tag.group_id).first()
                if group.name not in result:
                    result.update({group.name: {tag.name: ''}})
                else:
                    result[group.name].update({tag.name: ''})
            else:
                result[tag.name] = ''
        return result
    
    @staticmethod
    def id(tag_list):
        tag = Tag.query.filter(Tag.name == tag_list[1], Tag.group_id == Groups.id(tag_list[0])).first()
        return tag.id
    
    @staticmethod
    def all():
        return db.session.execute(db.select(Tag.name)).scalars().all()

class Groups():
    @staticmethod
    def name(id):
        if id == 0 or id == '':
            return ''
        group = Group.query.filter_by(id=id).first()
        if group:
            return group.name
        
    @staticmethod
    def all():
        return db.session.execute(db.select(Group.name)).scalars().all()

class Files:
    @staticmethod
    def all():
        return db.session.execute(db.select(File.name)).scalars().all()
    
    @staticmethod
    def tags(file_name):
        file = File.query.filter_by(name=file_name).first()
        if file:
            tags = file.tags
            result = []
            for tag in tags:
                result.append([Groups.name(tag.group_id), tag.name])
            return result
        else:
            return {'message': 'wrong file'}
        
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
            tag = Tag.query.filter_by(id=tag_and[0]).first()
            file_list = tag.files
            if file_list:
                for file in file_list:
                    result_and.add(file.name)
    
        else:
            count = len(tag_and)
            for tag_id in tag_and:
                tag = Tag.query.filter_by(id=tag_id).first()
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
            file_list = TagFile.query.join(Tag).join(File).filter(Tag.id.in_(tag_and)).all()
            if file_list:
                for file in file_list:
                    result_or.add(Files.get_name(file.file_id))
        if len(tag_not) > 0:
            file_list = TagFile.query.filter(TagFile.tag_id.in_(tag_not)).all()
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
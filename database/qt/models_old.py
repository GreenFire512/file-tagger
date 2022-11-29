from sqlalchemy import Column, String, Integer, ForeignKey, Table, select, UniqueConstraint
from sqlalchemy.orm import relationship, lazyload
from database.qt import *
from utils import *

association_table = Table(
    "TagFile",
    Base.metadata,
    Column("tag_id", ForeignKey("Tag.id")),
    Column("file_id", ForeignKey("File.id")),
    UniqueConstraint('tag_id', 'file_id', name='unique_tag_file')
)

class Tag(Base):
    __tablename__ = 'Tag'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    group_id = Column(Integer, ForeignKey("Group.id"))
    files = relationship("File", secondary=association_table, back_populates="tags")
    __table_args__ = (UniqueConstraint('name', 'group_id', name='unique_name_group'),)


class Group(Base):
    __tablename__ = 'Group'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tags = relationship("Tag", backref="group")


class File(Base):
    __tablename__ = 'File'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tags = relationship("Tag", secondary=association_table, back_populates="files")
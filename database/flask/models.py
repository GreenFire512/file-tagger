from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


association_table = db.Table(
    "TagFile",
    db.Column("tag_id", db.Integer, db.ForeignKey("Tag.id"), primary_key=True),
    db.Column("file_id", db.Integer, db.ForeignKey("File.id"), primary_key=True),
    db.UniqueConstraint('tag_id', 'file_id', name='unique_tag_file')
)


class Tag(db.Model):
    __tablename__ = 'Tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("Group.id"))
    files = db.relationship("File", secondary=association_table, back_populates="tags")
    __table_args__ = (db.UniqueConstraint('name', 'group_id', name='unique_name_group'),)
    
    
class Group(db.Model):
    __tablename__ = 'Group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    tags = db.relationship("Tag", backref="group")
    
    
class File(db.Model):
    __tablename__ = 'File'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    tags = db.relationship("Tag", secondary=association_table, back_populates="files")
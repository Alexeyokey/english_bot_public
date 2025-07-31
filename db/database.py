from peewee import *
import sqlite3
from peewee import Model, SqliteDatabase


db = SqliteDatabase("db/database.sqlite")


class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    id = PrimaryKeyField()
    telegram_id = IntegerField(unique=True)
    name = TextField()


class Word(BaseModel):
    id = PrimaryKeyField()
    en_word = TextField()
    ru_word = TextField()
    count = IntegerField(default=0)
    correct = IntegerField(default=0)


class UserToWords(BaseModel):
    user_id = ForeignKeyField(User, backref='relate')
    word_id = ForeignKeyField(Word, backref='relate')


with db:
    db.create_tables([User, Word, UserToWords])
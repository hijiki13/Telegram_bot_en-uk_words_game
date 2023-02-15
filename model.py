''' Модели в отдельном файле что бы не перемешивать их с основным кодом и можно было повторно использовать как к примеру я в файле utility.py
'''
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    # TODO: в новой версии sqlalchemy если __tablename__ не указывать то название таблицы будет такое же как и имя класса в нижнем регистре т.е. user
    # __tablename__ = "user"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    last_l_u: Mapped[str]
    cur_word: Mapped[str]
    used_words: Mapped[str]

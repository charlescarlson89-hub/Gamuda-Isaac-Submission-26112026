from sqlalchemy import Column, Integer, String

from database import Base, engine


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=False)
    published_year = Column(Integer, nullable=False)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Books table created successfully!")
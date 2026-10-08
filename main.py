import fastapi, uvicorn, asyncio, os
from fastapi import HTTPException, Depends, responses
from sqlalchemy import create_engine, Column, Integer, String, func, ForeignKey,Table
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import URL, create_engine
from sqlalchemy import Boolean
from pydantic import BaseModel

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:1q2w3eT%40@localhost:5432/library",
)

engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()
app = fastapi.FastAPI()

book_author = Table(
    "book_author",
    Base.metadata,
    Column("book_id", ForeignKey("book.id"), primary_key=True),
    Column("author_id", ForeignKey("author.id"), primary_key=True),
)

book_genre = Table(
    "book_genre",
    Base.metadata,
    Column("book_id", ForeignKey("book.id"), primary_key=True),
    Column("genre_id", ForeignKey("genre.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    borrowing = relationship("Borrowing", back_populates="user")

class Author(Base):
  __tablename__ = "author"
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String, nullable=False)
  bio = Column(String)
  books = relationship("Book", secondary=book_author, back_populates="authors")

class Genre(Base):
  __tablename__ = "genre"
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String, nullable=False)
  book = relationship("Book", secondary=book_genre, back_populates="genre")

class Book(Base):
  __tablename__ = "book"
  id = Column(Integer, primary_key=True, autoincrement=True)
  title = Column(String, nullable=False)
  year = Column(Integer, nullable=False)
  description = Column(String, nullable=False)
  borrowing = relationship("Borrowing", back_populates="book")
  authors = relationship("Author", secondary=book_author, back_populates="books")
  genre = relationship("Genre", secondary=book_genre, back_populates="book")

class Borrowing(Base):
  __tablename__ = "borrowing"
  id = Column(Integer, primary_key=True)
  user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  book_id = Column(Integer, ForeignKey("book.id"), nullable=False)
  returned = Column(Boolean, default=False, nullable=False)
  user = relationship("User", back_populates="borrowing")
  book = relationship("Book", back_populates="borrowing")

class UsersIn(BaseModel):
  username: str
  password: str
  email: str

class AuthorIn(BaseModel):
    name: str
    bio: str | None = None

class GenreIn(BaseModel):
    name: str

class BookIn(BaseModel):
    title: str
    year: int
    description: str | None
    author_ids: list[int] = []
    genre_ids: list[int] = []

class BorrowingIn(BaseModel):
    user_id: int
    book_id: int

@app.post("/users")
async def create_users(data: UsersIn):
  user=User(username=data.username, password=data.password, email=data.email)
  session.add(user)
  session.commit()
  return {"message": "Успешный вход"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
  user = session.get(User, user_id)
  if not user:
      raise HTTPException(status_code=404)

  books = (
      session.query(Book)
      .join(Borrowing)
      .filter(Borrowing.user_id == user_id)
      .all())
  return {"user": user.username, "books": [book.title for book in books]}

@app.post("/authors")
async def create_authors(data: AuthorIn):
    author=Author(name=data.name, bio=data.bio)
    session.add(author)
    session.commit()
    return {"name": data.name, "bio": data.bio}

@app.get("/authors")
async def get_authors():
    authors = session.query(Author).all()
    return [{author.name: [b.title for b in author.books]} for author in authors]

@app.get("/authors/{author_id}")
async def get_author(author_id: int):
    author = session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404)
    return {"name": author.name, "bio": author.bio, "books": [book.title for book in author.books]}

@app.post("/genres")
async def create_genres(data: GenreIn):
    genre = Genre(name=data.name)
    session.add(genre)
    session.commit()
    return {"name": genre.name}

@app.get("/genres")
async def get_genres():
    genres = session.query(Genre).all()
    return [{"id": g.id, "name": g.name} for g in genres]

@app.post("/books")
async def create_books(data: BookIn):
    authors = session.query(Author).filter(Author.id.in_(data.author_ids)).all()
    genres = session.query(Genre).filter(Genre.id.in_(data.genre_ids)).all()
    book = Book(title=data.title, year=data.year, description=data.description)
    book.authors.extend(authors)
    book.genre.extend(genres)
    session.add(book)
    session.commit()
    session.refresh(book)
    return {"id": book.id, "authors": [author.name for author in book.authors], "title": book.title, "year": book.year, "description": book.description, "genre": [genre.name for genre in book.genre]}

@app.get("/books")
async def get_books():
    books = session.query(Book).all()
    return [{"id": book.id, "authors": [{"id": a.id, "name": a.name} for a in book.authors], "title": book.title, "year": book.year,"description": book.description, "genres": [{"id": g.id, "name": g.name} for g in book.genre]} for book in books]

@app.get("/books/{book_id}")
async def get_book(book_id: int):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404)
    return {
        "id": book.id,
        "title": book.title,
        "year": book.year,
        "description": book.description,
        "authors": [{"id": a.id, "name": a.name} for a in book.authors],
        "genres": [{"id": g.id, "name": g.name} for g in book.genre]
    }

@app.post("/borrowings/took")
async def took_borrowing(data: BorrowingIn):
    user = session.get(User, data.user_id)
    book = session.get(Book, data.book_id)
    if not user or not book:
        raise HTTPException(404, "User or book not found")

    active = (
        session.query(Borrowing)
        .filter(Borrowing.book_id == data.book_id, Borrowing.returned == False)
        .first()
    )
    if active:
        raise HTTPException(400, "Book is already taken")

    borrowing = Borrowing(user_id=data.user_id, book_id=data.book_id, returned=False)
    session.add(borrowing)
    session.commit()
    session.refresh(borrowing)
    return {"id": borrowing.id, "user_id": borrowing.user_id, "book_id": borrowing.book_id, "returned": borrowing.returned}


@app.post("/borrowings/returned")
async def returned_borrowing(data: BorrowingIn):
    borrowing = (
        session.query(Borrowing)
        .filter(
            Borrowing.book_id == data.book_id,
            Borrowing.user_id == data.user_id,
            Borrowing.returned == False,
        )
        .first()
    )
    if not borrowing:
        raise HTTPException(404, "Active borrowing not found")

    borrowing.returned = True
    session.commit()
    session.refresh(borrowing)
    return {"id": borrowing.id, "returned": borrowing.returned}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
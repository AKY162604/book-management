from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float

from .database import Base
    

class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): The primary key for the user. Automatically generated.
        username (str): The unique username of the user. Cannot be null.
        hashed_password (str): The hashed password of the user. Cannot be null.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Book(Base):
    """
    Represents a book entity in the database.

    Attributes:
        id (int): The primary key identifier for the book.
        title (str): The title of the book.
        author (str): The author of the book.
        genre (str): The genre of the book.
        year_published (int): The year the book was published.
        summary (str, optional): A brief summary or description of the book.
    """
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String)
    genre = Column(String)
    year_published = Column(Integer)
    summary = Column(String, nullable=True)

class Review(Base):
    """
    Represents a review for a book in the database.

    Attributes:
        id (int): The primary key for the review, uniquely identifying each review.
        book_id (int): The foreign key referencing the ID of the book being reviewed.
        user_id (int): The ID of the user who wrote the review.
        review_text (str): The text content of the review.
        rating (float): The rating given to the book by the user.
    """
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"))
    user_id = Column(Integer)
    review_text = Column(String)
    rating = Column(Float)


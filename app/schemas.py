from datetime import date
from pydantic import BaseModel


class UserCreate(BaseModel):
    """
    UserCreate schema for creating a new user.

    Attributes:
        username (str): The username of the user.
        password (str): The password for the user.
    """
    username: str
    password: str

class UserOut(BaseModel):
    """
    UserOut schema represents the output structure for user data.

    Attributes:
        id (int): The unique identifier of the user.
        username (str): The username of the user.

    Config:
        orm_mode (bool): Enables compatibility with ORM objects, allowing
        the schema to work seamlessly with ORM models.
    """
    id: int
    username: str

    class Config:
        orm_mode = True


class BookCreate(BaseModel):
    """
    BookCreate schema for creating a new book entry.

    Attributes:
        title (str): The title of the book.
        author (str): The author of the book.
        genre (str): The genre of the book.
        year_published (int): The year the book was published.
        summary (str, optional): A brief summary of the book. Defaults to None.
    """
    title: str
    author: str
    genre: str
    year_published: int
    summary: str = None

class ReviewCreate(BaseModel):
    """
    ReviewCreate schema for creating a new review.

    Attributes:
        book_id (int): The ID of the book being reviewed.
        user_id (int): The ID of the user creating the review.
        review_text (str): The text content of the review.
        rating (float): The rating given to the book, typically on a scale (e.g., 1.0 to 5.0).
    """
    book_id: int
    user_id: int
    review_text: str
    rating: float

class BookRecommendation(BaseModel):
    """
    BookRecommendation schema for representing a book recommendation.

    Attributes:
        recommend_book (str): The title of the recommended book.
    """
    recommend_book: str

class SummaryRequest(BaseModel):
    """
    SummaryRequest is a Pydantic model that represents the structure of a request
    to summarize book content.

    Attributes:
        book_content (str): The content of the book to be summarized.
    """
    book_content: str


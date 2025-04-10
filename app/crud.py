from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException

from . import models, schemas


async def insert_book_data(db: AsyncSession, book: schemas.BookCreate):
    """
    Inserts a new book record into the database.

    Args:
        db (AsyncSession): The asynchronous database session to use for the operation.
        book (schemas.BookCreate): The book data to be inserted, adhering to the BookCreate schema.

    Returns:
        models.Book: The newly created book record after being committed and refreshed in the database.
    """
    json_compatible_item_data = jsonable_encoder(book)
    db_book = models.Book(**json_compatible_item_data)
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book


async def get_book(db: AsyncSession, book_id: int):
    """
    Retrieve a book from the database by its ID.

    Args:
        db (AsyncSession): The asynchronous database session to use for the query.
        book_id (int): The ID of the book to retrieve.

    Returns:
        models.Book or None: The book object if found, otherwise None.
    """
    query_ = select(models.Book).where(models.Book.id == book_id)
    result = await db.execute(query_)
    books = result.scalars().first()
    return books

async def get_books(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    Retrieve a list of books from the database.

    Args:
        db (AsyncSession): The database session to use for the query.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        List[models.Book]: A list of Book objects retrieved from the database.
    """
    result = await db.execute(select(models.Book))
    return result.scalars().all()

async def update_book_data(db: AsyncSession, book_id: int, book: schemas.BookCreate):
    """
    Update the data of an existing book in the database.

    Args:
        db (AsyncSession): The database session to use for the operation.
        book_id (int): The ID of the book to update.
        book (schemas.BookCreate): The new data for the book, provided as a schema object.

    Returns:
        schemas.Book: The updated book data retrieved from the database.

    Raises:
        HTTPException: If the book with the given ID is not found, raises a 404 error.
    """
    query_ = update(models.Book).where(models.Book.id == book_id).values(**book.dict(exclude_unset=True)).execution_options(synchronize_session="fetch")
    result = await db.execute(query_)
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.commit()
    return await get_book(db=db, book_id=book_id)


async def delete_book_data(db: AsyncSession, book_id: int):
    result = await db.execute(select(models.Book).where(models.Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    query_ = delete(models.Book).where(models.Book.id == book_id)
    await db.execute(query_)
    await db.commit()
    return True
    

async def insert_review_data(db: AsyncSession, review: schemas.ReviewCreate):
    """
    Inserts a new review record into the database.

    Args:
        db (AsyncSession): The asynchronous database session to use for the operation.
        review (schemas.ReviewCreate): The review data to be inserted, adhering to the ReviewCreate schema.

    Returns:
        models.Review: The newly created review record after being committed and refreshed in the database.
    """
    json_compatible_item_data = jsonable_encoder(review)
    db_review = models.Review(**json_compatible_item_data)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    return db_review


async def get_review(db: AsyncSession, book_id: int):
    """
    Retrieve all reviews for a specific book from the database.

    Args:
        db (AsyncSession): The database session to use for the query.
        book_id (int): The ID of the book for which reviews are to be retrieved.

    Returns:
        List[models.Review]: A list of review objects associated with the specified book.

    Raises:
        HTTPException: If no reviews are found for the given book ID, a 404 error is raised.
    """
    query_ = select(models.Review).where(models.Review.book_id == book_id)
    result = await db.execute(query_)
    reviews = result.scalars().all()
    if not reviews:
        raise HTTPException(status_code=404, detail="Review not found")
    return reviews

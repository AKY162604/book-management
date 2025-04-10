import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, FastAPI, HTTPException, Request, Response, Query
from sqlalchemy.orm import Session
from fastapi import status
from . import crud, schemas
from .database import engine, get_db, Base
from langchain_community.llms import LlamaCpp
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
from dotenv import load_dotenv

app = FastAPI()
executor = ThreadPoolExecutor()
load_dotenv()



@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# models.Base.metadata.create_all(bind=engine)

# Callbacks support token-wise streaming
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

llama_file_name = os.getenv("LLMA_FILE_NAME")
llama_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "models", llama_file_name
)
# Make sure the model path is correct for your system!
llm = LlamaCpp(
    model_path=llama_file_path,
    n_ctx=2048,
    n_gpu_layers=20,
    temperature=0.7,
    top_p=0.95,
    verbose=True,
)


async def service_name_identifier(request: Request):
    """
    Extracts the "Service-Name" header from the incoming HTTP request.

    Args:
        request (Request): The incoming HTTP request object.

    Returns:
        str or None: The value of the "Service-Name" header if present, otherwise None.
    """
    service = request.headers.get("Service-Name")
    return service


async def custom_callback(request: Request, response: Response, pexpire: int):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """
    expire = ceil(pexpire / 1000)

    raise HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Too Many Requests. Retry after {expire} seconds.",
        headers={"Retry-After": str(expire)},
    )




def generate(prompt):
    """
    Generates a response based on the given prompt using a language model.

    Args:
        prompt (str): The input text prompt to generate a response for.

    Returns:
        str: The generated response from the language model.
    """
    return llm(prompt)


@app.post("/books/", response_model=schemas.BookCreate)
async def create_book(book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new book entry in the database with a generated summary.

    This endpoint accepts a book object, generates a summary for the book using
    an external function, and saves the book data along with the summary to the database.

    Args:
        book (schemas.BookCreate): The book data to be created, including title and author.
        db (AsyncSession): The database session dependency.

    Returns:
        schemas.BookCreate: The created book object with the generated summary.

    Raises:
        HTTPException: If an error occurs during the summary generation or database operation.
    """
    prompt = f"Summarize book title {book.title} by {book.author} in 150 words."
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(executor, generate, prompt)
        update_book = book.copy(update={"summary": str(response)})
        db_book = await crud.insert_book_data(db=db, book=update_book)
        return db_book
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/books/", response_model=list[schemas.BookCreate])
async def read_books(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a list of books with optional pagination.

    Args:
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.
        db (AsyncSession): The database session dependency.

    Returns:
        list[schemas.BookCreate]: A list of books retrieved from the database.
    """
    books = await crud.get_books(db, skip=skip, limit=limit)
    return books


@app.get("/books/{book_id}", response_model=schemas.BookCreate)
async def read_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to retrieve a book by its ID.

    Args:
        book_id (int): The ID of the book to retrieve.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: A dictionary containing the book details, including:
            - title (str): The title of the book.
            - author (str): The author of the book.
            - genre (str): The genre of the book.
            - year_published (int): The year the book was published.
            - summary (str): A brief summary of the book.

    Raises:
        HTTPException: If the book with the given ID is not found, raises a 404 error with the message "Book not found".
    """
    db_book = await crud.get_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return {
        "title": db_book.title,
        "author": db_book.author,
        "genre": db_book.genre,
        "year_published": db_book.year_published,
        "summary": db_book.summary,
    }


@app.put("/books/{book_id}", response_model=schemas.BookCreate)
async def update_book(book_id: int, book: schemas.BookCreate, db: AsyncSession = Depends(get_db)):
    """
    Updates an existing book in the database.

    Args:
        book_id (int): The ID of the book to update.
        book (schemas.BookCreate): The updated book data.
        db (AsyncSession): The database session dependency.

    Returns:
        schemas.BookCreate: The updated book data.

    Raises:
        HTTPException: If the book with the given ID is not found (404).
    """
    db_book = await crud.get_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    updated_book = await crud.update_book_data(db=db, book=book, book_id=book_id)
    return updated_book


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a book from the database by its ID.

    Args:
        book_id (int): The ID of the book to delete.
        db (AsyncSession): The database session dependency.

    Raises:
        HTTPException: If the book with the given ID is not found, raises a 404 error.

    Returns:
        Response: An HTTP 204 No Content response indicating successful deletion.
    """
    db_book = await crud.get_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    response = await crud.delete_book_data(db=db, book_id=book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/books/{book_id}/reviews", response_model=schemas.ReviewCreate)
async def create_review_for_book(book_id: int, review: schemas.ReviewCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a review for a specific book.

    This endpoint allows users to add a review for a book identified by its `book_id`.
    If the book does not exist, a 404 HTTP exception is raised.

    Args:
        book_id (int): The ID of the book for which the review is being created.
        review (schemas.ReviewCreate): The review data to be added.
        db (AsyncSession): The database session dependency.

    Returns:
        schemas.ReviewCreate: The created review data.

    Raises:
        HTTPException: If the book with the given `book_id` is not found.
    """
    db_book = await crud.get_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db_review = await crud.insert_review_data(db=db, review=review)
    return db_review


@app.get("/books/{book_id}/reviews", response_model=list[schemas.ReviewCreate])
async def read_reviews_for_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieve reviews for a specific book.

    This endpoint fetches all reviews associated with a given book ID. If the book
    does not exist, a 404 HTTP exception is raised.

    Args:
        book_id (int): The ID of the book for which reviews are to be retrieved.
        db (AsyncSession): The database session dependency.

    Returns:
        list[schemas.ReviewCreate]: A list of reviews for the specified book.

    Raises:
        HTTPException: If the book with the given ID is not found.
    """
    db_book = await crud.get_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    reviews = await crud.get_review(db, book_id=book_id)
    return reviews


@app.get("/books/{book_id}/summary", response_model=schemas.BookCreate)
async def read_reviews_for_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Endpoint to retrieve the summary of a specific book by its ID.

    Args:
        book_id (int): The ID of the book to retrieve.
        db (AsyncSession): Database session dependency.

    Returns:
        dict: A dictionary containing the book's details, including:
            - title (str): The title of the book.
            - author (str): The author of the book.
            - genre (str): The genre of the book.
            - year_published (int): The year the book was published.
            - summary (str): A summary of the book.

    Raises:
        HTTPException: If the book with the given ID is not found, raises a 404 error.
    """
    db_book = await crud.get_book(db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return {
        "title": db_book.title,
        "author": db_book.author,
        "genre": db_book.genre,
        "year_published": db_book.year_published,
        "summary": db_book.summary,
    }


@app.get("/recommendations", response_model=dict)
async def recommend_books(prompt: str = Query(...)):
    """
    Endpoint to recommend books based on a given prompt.

    Args:
        prompt (str): A string query provided by the user to generate book recommendations.

    Returns:
        dict: A dictionary containing a list of recommended books under the key "recommend_book".

    Raises:
        HTTPException: If an error occurs during the recommendation generation process, 
                    an HTTP 500 error is raised with the error details.
    """
    prompt_ = f"Recommend 5 books based on: {prompt}"
    try:
        loop = asyncio.get_running_loop()
        recommendations = await loop.run_in_executor(executor, generate, prompt_)
        return {"recommend_book": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

async def summarize_with_llamacpp(content: str) -> str:
    """
    Asynchronously generates a summary for the given content using the LLaMaCPP model.

    Args:
        content (str): The text content to be summarized.

    Returns:
        str: The generated summary as a string. If an error occurs during summarization,
             returns "Summary generation failed."

    Raises:
        Exception: Logs the exception if summarization fails.
    """
    try:
        prompt_ = f"Summarize the following content:\n{content}"
        loop = asyncio.get_running_loop()
        generate_summary = await loop.run_in_executor(executor, generate, prompt_)
        return generate_summary.strip()
    except Exception as e:
        print("Summarization failed:", e)
        return "Summary generation failed."
    

@app.post("/generate-summary")
async def generate_summary(request: schemas.SummaryRequest):
    """
    Handles the POST request to generate a summary for the provided book content.

    Args:
        request (schemas.SummaryRequest): The request body containing the book content to summarize.

    Returns:
        dict: A dictionary containing the generated summary.

    Raises:
        HTTPException: If the summary generation fails, raises a 500 Internal Server Error.
    """
    summary = await summarize_with_llamacpp(request.book_content)
    if summary == "Summary generation failed.":
        raise HTTPException(status_code=500, detail="Failed to generate summary.")
    return {"summary": summary}

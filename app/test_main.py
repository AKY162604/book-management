import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from .main import app
from . import schemas
from .database import get_db

@pytest.fixture
async def test_db():
    """
    Fixture to provide a test database session.
    """
    async with get_db() as db:
        yield db

@pytest.fixture
async def client():
    """
    Fixture to provide an HTTP client for testing.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_book(client, test_db: AsyncSession):
    """
    Test the creation of a book.
    """
    book_data = {
        "title": "Test Book",
        "author": "Test Author",
        "genre": "Fiction",
        "year_published": 2023
    }
    response = await client.post("/books/", json=book_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["author"] == book_data["author"]

@pytest.mark.asyncio
async def test_read_books(client, test_db: AsyncSession):
    """
    Test retrieving a list of books.
    """
    response = await client.get("/books/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_read_book(client, test_db: AsyncSession):
    """
    Test retrieving a single book by ID.
    """
    # Assuming a book with ID 1 exists in the test database
    response = await client.get("/books/1")
    if response.status_code == 404:
        pytest.skip("Book with ID 1 not found in test database.")
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "author" in data

@pytest.mark.asyncio
async def test_update_book(client, test_db: AsyncSession):
    """
    Test updating a book.
    """
    book_data = {
        "title": "Updated Book",
        "author": "Updated Author",
        "genre": "Non-Fiction",
        "year_published": 2022
    }
    # Assuming a book with ID 1 exists in the test database
    response = await client.put("/books/1", json=book_data)
    if response.status_code == 404:
        pytest.skip("Book with ID 1 not found in test database.")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["author"] == book_data["author"]

@pytest.mark.asyncio
async def test_delete_book(client, test_db: AsyncSession):
    """
    Test deleting a book.
    """
    # Assuming a book with ID 1 exists in the test database
    response = await client.delete("/books/1")
    if response.status_code == 404:
        pytest.skip("Book with ID 1 not found in test database.")
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_generate_summary(client):
    """
    Test generating a summary for book content.
    """
    request_data = {"book_content": "This is a test book content."}
    response = await client.post("/generate-summary", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert isinstance(data["summary"], str)

@pytest.mark.asyncio
async def test_recommend_books(client):
    """
    Test recommending books based on a prompt.
    """
    response = await client.get("/recommendations", params={"prompt": "science fiction"})
    assert response.status_code == 200
    data = response.json()
    assert "recommend_book" in data
    assert isinstance(data["recommend_book"], str)
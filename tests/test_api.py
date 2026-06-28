import pytest
from fastapi.testclient import TestClient
from app import app
import io

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_non_pdf():
    fake_file = io.BytesIO(b"this is not a pdf")
    response = client.post(
        "/upload",
        files={"file": ("test.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are accepted" in response.json()["detail"]

def test_upload_empty_file():
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/upload",
        files={"file": ("empty.pdf", empty_file, "application/pdf")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_chat_empty_question():
    response = client.post(
        "/chat",
        json={"question": "", "session_id": "some-session-id"}
    )
    assert response.status_code == 400

def test_chat_missing_session():
    response = client.post(
        "/chat",
        json={"question": "what is this?", "session_id": ""}
    )
    assert response.status_code == 400

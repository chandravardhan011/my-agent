"""
pytest tests for AVR chatbot.
Run with:  pytest tests/test_app.py -v
"""
import pytest
import sys
import os

# Make sure we can import app from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use a test database
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["SECRET_KEY"] = "test-secret"

from app import app, db, User


@pytest.fixture
def client():
    """Create a test client with a fresh in-memory database."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def registered_user(client):
    """Register and return a test user."""
    client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    return {"username": "testuser", "password": "password123"}


# ── Auth tests ────────────────────────────────────────────────────────────────

def test_login_page_loads(client):
    """Login page should return 200."""
    r = client.get("/login")
    assert r.status_code == 200
    assert b"Sign In" in r.data


def test_register_page_loads(client):
    """Register page should return 200."""
    r = client.get("/register")
    assert r.status_code == 200
    assert b"Create Account" in r.data


def test_register_new_user(client):
    """Registering a new user should succeed."""
    r = client.post("/register", json={
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123"
    })
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True


def test_register_duplicate_username(client, registered_user):
    """Registering with duplicate username should fail."""
    r = client.post("/register", json={
        "username": "testuser",
        "email": "other@example.com",
        "password": "password123"
    })
    assert r.status_code == 400
    assert "taken" in r.get_json()["error"].lower()


def test_register_duplicate_email(client, registered_user):
    """Registering with duplicate email should fail."""
    r = client.post("/register", json={
        "username": "newuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert r.status_code == 400
    assert "registered" in r.get_json()["error"].lower()


def test_login_valid(client, registered_user):
    """Valid credentials should log in successfully."""
    r = client.post("/login", json={
        "username": "testuser",
        "password": "password123"
    })
    assert r.status_code == 200
    assert r.get_json()["success"] is True


def test_login_wrong_password(client, registered_user):
    """Wrong password should be rejected."""
    r = client.post("/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert r.status_code == 401
    assert "invalid" in r.get_json()["error"].lower()


def test_login_unknown_user(client):
    """Unknown username should be rejected."""
    r = client.post("/login", json={
        "username": "nobody",
        "password": "anything"
    })
    assert r.status_code == 401


def test_register_missing_fields(client):
    """Missing fields should return 400."""
    r = client.post("/register", json={"username": "bob"})
    assert r.status_code == 400


# ── Protected route tests ─────────────────────────────────────────────────────

def test_home_redirects_unauthenticated(client):
    """Unauthenticated users should be redirected from / to /login."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_chat_requires_auth(client):
    """Unauthenticated users should not be able to POST /chat."""
    r = client.post("/chat", json={"message": "hello"}, follow_redirects=False)
    assert r.status_code == 302


def test_clear_requires_auth(client):
    """Unauthenticated users should not be able to POST /clear."""
    r = client.post("/clear", follow_redirects=False)
    assert r.status_code == 302


# ── User model tests ──────────────────────────────────────────────────────────

def test_password_hashing():
    """Passwords should be hashed and verifiable."""
    with app.app_context():
        user = User(username="hashtest", email="hash@test.com")
        user.set_password("mysecret")
        assert user.password_hash != "mysecret"
        assert user.check_password("mysecret") is True
        assert user.check_password("wrong") is False


def test_user_properties():
    """Flask-Login required properties should work."""
    with app.app_context():
        user = User(username="proptest", email="prop@test.com")
        user.set_password("pass")
        assert user.is_authenticated is True
        assert user.is_active is True
        assert user.is_anonymous is False

# 🤖 AVR – AI Assistant

A full-stack AI chatbot powered by **Llama 3.3 70B** via the Groq API.  
Features user authentication, persistent chat history, web search, and Docker support.

---

## Features

- 🔐 User registration & login (Flask-Login + hashed passwords)
- 🗄️ SQLite database (chat history per user, stored permanently)
- 🌐 Web search via DuckDuckGo
- ♾️ Unlimited questions with smart history summarization
- 📈 Exponential backoff for rate limit handling
- 📋 Logging to file and console
- 🐳 Docker support
- ✅ Pytest test suite

---

## Quick Start

### 1. Clone & install

```bash
git clone <your-repo-url>
cd avr-chatbot
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

Get a free Groq API key at: https://console.groq.com

### 3. Run

```bash
python app.py
```

Open http://localhost:5000 — register an account and start chatting.

---

## Run with Docker

```bash
cp .env.example .env
# Fill in your GROQ_API_KEY in .env

docker compose up --build
```

---

## Run Tests

```bash
pytest tests/test_app.py -v
```

---

## Project Structure

```
avr-chatbot/
├── app.py                  # Main Flask application
├── templates/
│   ├── auth.html           # Login / Register page
│   └── chat.html           # Main chat interface
├── tests/
│   └── test_app.py         # Pytest test suite
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example            # Template for environment variables
├── .gitignore
└── README.md
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (required) |
| `SECRET_KEY` | Flask session secret key (change in production) |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Auth | Flask-Login, Werkzeug |
| Database | SQLite, Flask-SQLAlchemy |
| AI Model | Llama 3.3 70B via Groq API |
| Web Search | DuckDuckGo Search |
| Testing | Pytest |
| Deployment | Docker, Docker Compose |

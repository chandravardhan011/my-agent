import os
import logging
import time
import random
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from groq import Groq
from duckduckgo_search import DDGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.FileHandler("avr.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecretkey123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///avr.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

client = Groq(api_key="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")

SYSTEM_PROMPT = "Your name is AVR. You are a powerful AI assistant. Help with all subjects, coding, math, writing, translation, news, career advice."

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Message", backref="user", lazy=True)
    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)
    @property
    def is_authenticated(self): return True
    @property
    def is_active(self): return True
    @property
    def is_anonymous(self): return False
    def get_id(self): return str(self.id)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        return "\n".join([f"{r['title']}: {r['body']}" for r in results])
    except Exception as e:
        logger.warning(f"Search failed: {e}")
        return "Search failed"

def get_history(user_id):
    msgs = Message.query.filter_by(user_id=user_id).order_by(Message.created_at.desc()).limit(20).all()
    msgs.reverse()
    return [{"role": m.role, "content": m.content} for m in msgs]

def run_agent(question, user_id):
    history = get_history(user_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history
    messages.append({"role": "user", "content": question})
    for attempt in range(10):
        try:
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, max_tokens=8192, temperature=0.7)
        except Exception as e:
            if "429" in str(e):
                wait = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Rate limited. Waiting {wait:.1f}s")
                time.sleep(wait)
                continue
            return f"Error: {str(e)}"
        reply = response.choices[0].message.content
        if "SEARCH:" in reply:
            query = reply.split("SEARCH:")[1].strip().split("\n")[0]
            result = web_search(query)
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": f"Search results: {result}. Now answer."})
        else:
            db.session.add(Message(user_id=user_id, role="user", content=question))
            db.session.add(Message(user_id=user_id, role="assistant", content=reply))
            db.session.commit()
            logger.info(f"User {user_id} message saved")
            return reply
    return "Could not get a response. Please try again."

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        data = request.json
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        if not username or not email or not password:
            return jsonify({"error": "All fields required"}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        logger.info(f"Registered: {username}")
        return jsonify({"success": True})
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            logger.info(f"Login: {username}")
            return jsonify({"success": True})
        return jsonify({"error": "Invalid username or password"}), 401
    return render_template("auth.html", mode="login")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    return render_template("chat.html", username=current_user.username)

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.json
    question = data.get("message", "").strip()
    if not question:
        return jsonify({"reply": "Please enter a message."})
    reply = run_agent(question, current_user.id)
    return jsonify({"reply": reply})

@app.route("/clear", methods=["POST"])
@login_required
def clear():
    Message.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    logger.info("AVR starting at http://localhost:5000")
    app.run(debug=False, port=5000)
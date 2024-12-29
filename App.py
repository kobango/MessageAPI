from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = Flask(__name__)
Base = declarative_base()

# Konfiguracja bazy danych
DATABASE_URL = "sqlite:///messages.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Model użytkownika
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

# Model wiadomości
class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender = Column(String(50), nullable=False)
    recipient = Column(String(50), nullable=False)
    content = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# Rejestracja użytkownika (do testów)
@app.route('/MessageAPI/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    if session.query(User).filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)
    user = User(username=username, password_hash=hashed_password)
    session.add(user)
    session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# Wysyłanie wiadomości
@app.route('/MessageAPI/send', methods=['POST'])
def send_message():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    recipient = data.get('recipient')
    content = data.get('content')
    file = request.files.get('file')

    if not all([login, password, recipient]):
        return jsonify({"error": "Login, password, and recipient are required"}), 400

    user = session.query(User).filter_by(username=login).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid login or password"}), 401

    file_path = None
    if file:
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)

    message = Message(sender=login, recipient=recipient, content=content, file_path=file_path)
    session.add(message)
    session.commit()
    return jsonify({"message": "Message sent successfully"}), 201

# Pobieranie nieprzeczytanych wiadomości
@app.route('/MessageAPI/unread', methods=['POST'])
def get_unread_messages():
    data = request.json
    login = data.get('login')
    password = data.get('password')

    if not all([login, password]):
        return jsonify({"error": "Login and password are required"}), 400

    user = session.query(User).filter_by(username=login).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid login or password"}), 401

    messages = session.query(Message).filter_by(recipient=login, is_read=False).all()
    unread_messages = [{"id": msg.id, "sender": msg.sender, "content": msg.content, "timestamp": msg.timestamp} for msg in messages]
    
    for msg in messages:
        msg.is_read = True
    session.commit()

    return jsonify(unread_messages), 200

# Pobieranie historii wiadomości
@app.route('/MessageAPI/history', methods=['POST'])
def get_message_history():
    data = request.json
    login = data.get('login')
    password = data.get('password')
    page = int(data.get('page', 1))

    if not all([login, password]):
        return jsonify({"error": "Login and password are required"}), 400

    user = session.query(User).filter_by(username=login).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid login or password"}), 401

    PAGE_SIZE = 10
    messages = session.query(Message).filter_by(recipient=login).order_by(Message.timestamp.desc())
    paginated_messages = messages.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE).all()

    history = [{"id": msg.id, "sender": msg.sender, "content": msg.content, "timestamp": msg.timestamp, "file_path": msg.file_path} for msg in paginated_messages]
    return jsonify(history), 200

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)

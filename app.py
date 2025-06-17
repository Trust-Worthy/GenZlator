# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash # Re-added: For password hashing
from dotenv import load_dotenv
from datetime import datetime # Import datetime for timestamps

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Use environment variable for secret key, with a strong default for development
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_super_secret_key_here_generate_a_strong_one_in_production')

# MongoDB Atlas Connection
# Get the connection string from environment variables
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set. Please set it in your .env file or system environment.")

# Initialize client and collections
client = None
db = None
users_collection = None
messages_collection = None

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("genchat_db") # Name your database, e.g., 'genchat_db'
    users_collection = db.get_collection("users") # Collection for users
    messages_collection = db.get_collection("messages") # Collection for messages
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Failed to connect to MongoDB Atlas: {e}")
    flash("Failed to connect to the database. Please try again later.", "error")
    # In a real app, you might want to log this error more formally

# --- Routes ---

@app.route('/')
def index():
    """Redirect to login if not logged in, otherwise go to chat."""
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles both login and signup."""
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')

        if not client:
            flash("Database not connected. Cannot perform login/signup.", "error")
            return render_template('login.html')

        if action == 'signup':
            # Check if user already exists
            existing_user = users_collection.find_one({'username': username})
            if existing_user:
                flash("Username already exists. Please choose a different one.", "error")
            else:
                hashed_pw = generate_password_hash(password) # Re-added: Hash the password before storing
                users_collection.insert_one({'username': username, 'password': hashed_pw})
                flash("Account created successfully! Please log in.", "success")
                # Do not log in automatically after signup; encourage explicit login
                return redirect(url_for('login'))

        elif action == 'login':
            user = users_collection.find_one({'username': username})
            # Re-added: Verify hashed password
            if user and check_password_hash(user['password'], password):
                session['username'] = username # Store username in session
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for('chat'))
            else:
                flash("Invalid username or password.", "error")

    return render_template('login.html')

@app.route('/chat')
def chat():
    """Main chat interface. Must be logged in."""
    if 'username' not in session:
        flash("Please log in to access the chat.", "warning")
        return redirect(url_for('login'))

    current_user = session['username']
    messages = []
    if client:
        # For simplicity, fetching all messages. In a real app, you'd filter by chat room, etc.
        # Ensure to sort messages (e.g., by timestamp) when retrieving.
        messages = list(messages_collection.find().sort("timestamp", 1)) # Assuming 'timestamp' field
    else:
        flash("Database not connected. Cannot load chat messages.", "error")

    return render_template('chat.html', username=current_user, messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        flash("You must be logged in to send messages.", "error")
        return redirect(url_for('login'))

    if not client:
        flash("Database not connected. Cannot send message.", "error")
        return redirect(url_for('chat'))

    sender = session['username'] # Use actual logged-in user from session
    content = request.form.get('message_content')
    
    if content and content.strip(): # Check if content is not empty or just whitespace
        messages_collection.insert_one({
            "sender": sender,
            "content": content,
            "timestamp": datetime.now(),
            "translated_content": "" # Placeholder for AI translation
        })
        flash("Message sent!", "success")
    else:
        flash("Message cannot be empty.", "error")
    return redirect(url_for('chat'))

@app.route('/logout')
def logout():
    """Log the user out and clear session."""
    session.pop('username', None) # Remove username from session
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# === Main ===
if __name__ == '__main__':
    app.run(debug=True)

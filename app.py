# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime

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

# --- MongoDB connection ---
# This block attempts to connect to MongoDB when the Flask app starts.
# Flash messages cannot be used here because there is no active request context yet.
try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("genzlator_db") # Name your database, e.g., 'genchat_db'
    users_collection = db.get_collection("users") # Collection for users
    messages_collection = db.get_collection("messages") # Collection for messages
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Failed to connect to MongoDB Atlas at startup: {e}")
    # Do not use flash() here as there is no request context.
    # The client variable will remain None, and subsequent routes will handle this.

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
            flash("Database not connected. Cannot perform login/signup. Please check server logs.", "error")
            return render_template('login.html')

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template('login.html')

        # Normalize username by stripping whitespace and converting to lowercase
        username = username.strip().lower()

        if action == 'signup':
            # Check if user already exists
            existing_user = users_collection.find_one({'username': username})
            if existing_user:
                flash("Username already exists. Please choose a different one.", "error")
            else:
                hashed_pw = generate_password_hash(password)
                users_collection.insert_one({'username': username, 'password': hashed_pw})
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for('login')) # Redirect to login page after signup

        elif action == 'login':
            user = users_collection.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for('chat')) # Redirect directly to chat on successful login
            else:
                flash("Invalid username or password.", "error")

    return render_template('login.html')
@app.route('/chat')
def chat_home():
    if 'username' not in session:
        flash("Please log in to access chat.", "warning")
        return redirect(url_for('login'))

    current_user = session['username']

    # Step 1: Fetch all messages involving current user
    all_msgs = list(messages_collection.find({
        "$or": [
            {"sender": current_user},
            {"receiver": current_user}
        ]
    }).sort("timestamp", -1))  # newest first

    # Step 2: Build contact => most recent message map
    contact_latest = {}
    for msg in all_msgs:
        contact = msg["receiver"] if msg["sender"] == current_user else msg["sender"]
        if contact not in contact_latest:
            contact_latest[contact] = msg  # first (newest) match wins

    # Step 3: Sort contacts by message timestamp
    sorted_contacts = sorted(contact_latest.items(), key=lambda x: x[1]["timestamp"], reverse=True)

    return render_template("chat_home.html", username=current_user, contact_messages=sorted_contacts)

@app.route('/chat/<contact_username>')
def chat(contact_username):
    if 'username' not in session:
        flash("Please log in to access the chat.", "warning")
        return redirect(url_for('login'))

    current_user = session['username']

    try:
        messages = list(messages_collection.find({
            "$or": [
                {"sender": current_user, "receiver": contact_username},
                {"sender": contact_username, "receiver": current_user}
            ]
        }).sort("timestamp", 1))
    except Exception as e:
        print(f"Error loading messages: {e}")
        messages = []

    return render_template('chat.html',
                           username=current_user,
                           contact_username=contact_username,
                           messages=messages)


@app.route('/send_message', methods=['POST'])
def send_message():
    if 'username' not in session:
        flash("You must be logged in to send messages.", "error")
        return redirect(url_for('login'))

    if not client:
        flash("Database not connected. Cannot send message. Please check server logs.", "error")
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

def get_contacts_from_messages(current_user):
    contacts = set()

    # Find users the current_user has messaged
    sent_to = messages_collection.find({"sender": current_user})
    for msg in sent_to:
        contacts.add(msg["receiver"])

    # Find users who messaged the current_user
    received_from = messages_collection.find({"receiver": current_user})
    for msg in received_from:
        contacts.add(msg["sender"])

    contacts.discard(current_user)  # Just in case

    return sorted(list(contacts))

# === Main ===
if __name__ == '__main__':
    app.run(debug=True)

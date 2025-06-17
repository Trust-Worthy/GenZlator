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
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_super_secret_key_here_generate_a_strong_one_in_production')

# MongoDB Atlas Connection
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set. Please set it in your .env file or system environment.")

client = None
db = None
users_collection = None
messages_collection = None

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("genchat_db") # Changed to genchat_db for consistency with previous discussion
    users_collection = db.get_collection("users")
    messages_collection = db.get_collection("messages")
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Failed to connect to MongoDB Atlas at startup: {e}")
    # Flash messages cannot be used here as there is no request context yet.
    # The client variable will remain None, and subsequent routes will handle this.

# Prevent caching so refresh always goes to server (avoid stale page)
@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def index():
    """Redirect to login if not logged in, otherwise go to chat home."""
    if 'username' in session:
        return redirect(url_for('chat_home'))
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

        username = username.strip().lower()

        if action == 'signup':
            existing_user = users_collection.find_one({'username': username})
            if existing_user:
                flash("Username already exists. Please choose a different one.", "error")
            else:
                hashed_pw = generate_password_hash(password)
                users_collection.insert_one({'username': username, 'password': hashed_pw})
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for('login'))

        elif action == 'login':
            user = users_collection.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for('chat_home')) # Redirect to chat_home on successful login
            else:
                flash("Invalid username or password.", "error")

    return render_template('login.html')

@app.route('/chat')
def chat_home():
    """
    Displays the chat home screen with existing conversations and
    a list of other users to start new conversations with.
    """
    if 'username' not in session:
        flash("Please log in to access chat.", "warning")
        return redirect(url_for('login'))

    current_user = session['username']
    all_users = []
    contact_latest = {}
    sorted_contacts = []

    if client:
        # Fetch all users except current user
        # Exclude _id to simplify JSON for template
        all_users = list(users_collection.find({'username': {'$ne': current_user}}, {'_id': 0, 'username': 1}))
        # Extract just the usernames
        all_users_usernames = [user['username'] for user in all_users]

        # Get existing contacts with messages
        all_msgs = list(messages_collection.find({
            "$or": [
                {"sender": current_user},
                {"receiver": current_user}
            ]
        }).sort("timestamp", -1)) # Sort descending to easily get latest message

        # Build a dictionary of latest message for each contact
        for msg in all_msgs:
            contact = msg["receiver"] if msg["sender"] == current_user else msg["sender"]
            if contact not in contact_latest:
                contact_latest[contact] = msg

        # Sort contacts by their latest message timestamp
        sorted_contacts = sorted(contact_latest.items(), key=lambda x: x[1]["timestamp"], reverse=True)
    else:
        flash("Database not connected. Cannot load chat data. Please check server logs.", "error")

    return render_template(
        "chat_home.html",
        username=current_user,
        contact_messages=sorted_contacts,  # Existing conversations with latest message
        all_users_usernames=all_users_usernames # List of all other usernames
    )

@app.route('/chat/<contact_username>')
def chat_detail(contact_username):
    """Displays the detailed chat conversation with a specific contact."""
    if 'username' not in session:
        flash("Please log in to access the chat.", "warning")
        return redirect(url_for('login'))

    current_user = session['username']

    # Ensure the target contact exists in the database
    target_user_exists = users_collection.find_one({'username': contact_username})
    if not target_user_exists:
        flash(f"User '{contact_username}' not found.", "error")
        return redirect(url_for('chat_home'))

    messages = []
    if client:
        try:
            # Fetch messages between current_user and contact_username
            messages = list(messages_collection.find({
                "$or": [
                    {"sender": current_user, "receiver": contact_username},
                    {"sender": contact_username, "receiver": current_user}
                ]
            }).sort("timestamp", 1)) # Sort ascending for chronological order
        except Exception as e:
            print(f"Error loading messages for {contact_username}: {e}")
            flash("Could not load messages for this conversation. Database error.", "error")
    else:
        flash("Database not connected. Cannot load messages. Please check server logs.", "error")

    return render_template('chat_detail.html',
                           username=current_user,
                           contact_username=contact_username,
                           messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handles sending a new message."""
    if 'username' not in session:
        flash("You must be logged in to send messages.", "error")
        return redirect(url_for('login'))

    if not client:
        flash("Database not connected. Cannot send message. Please check server logs.", "error")
        # Attempt to redirect to the correct chat detail if receiver is available, else home
        receiver_fallback = request.form.get('receiver')
        return redirect(url_for('chat_detail', contact_username=receiver_fallback) if receiver_fallback else url_for('chat_home'))

    sender = session['username']
    content = request.form.get('message_content')
    receiver = request.form.get('receiver') # Get the receiver from the form

    if not receiver:
        flash("Recipient not specified.", "error")
        return redirect(url_for('chat_home'))

    # Ensure receiver exists before attempting to send a message
    if not users_collection.find_one({'username': receiver}):
        flash(f"Recipient '{receiver}' not found.", "error")
        return redirect(url_for('chat_home'))

    if content and content.strip():
        messages_collection.insert_one({
            "sender": sender,
            "receiver": receiver,
            "content": content,
            "timestamp": datetime.now(),
            "translated_content": "" # Placeholder for AI translation
        })
        flash("Message sent!", "success")
    else:
        flash("Message cannot be empty.", "error")
    
    # Redirect back to the specific chat with the receiver
    return redirect(url_for('chat_detail', contact_username=receiver))

@app.route('/logout')
def logout():
    """Log the user out and clear session."""
    session.pop('username', None) # Remove username from session
    session.clear()  # Fully clear session data
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)


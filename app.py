from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'  # Replace in production!


# Now you can access them via os.environ as usual
api_key = os.environ.get('MY_API_KEY')
db_url = os.environ.get('MONGO_STRING')

# === MongoDB Setup ===
client = MongoClient(db_url)  # Use MongoDB Atlas or local
db = client.genchat
users_collection = db.users

# === Routes ===

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

        if action == 'signup':
            existing_user = users_collection.find_one({'username': username})
            if existing_user:
                return "User already exists. Try logging in."
            
            hashed_pw = generate_password_hash(password)
            users_collection.insert_one({'username': username, 'password': hashed_pw})
            session['username'] = username
            return redirect(url_for('chat'))

        elif action == 'login':
            user = users_collection.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                return redirect(url_for('chat'))
            else:
                return "Invalid username or password."

    return render_template('login.html')

@app.route('/chat')
def chat():
    """Main chat interface. Must be logged in."""
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

@app.route('/logout')
def logout():
    """Log the user out and clear session."""
    session.pop('username', None)
    return redirect(url_for('login'))

# === Main ===
if __name__ == '__main__':
    app.run(debug=True)

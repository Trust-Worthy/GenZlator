# app.py
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # Replace with a strong secret key in production

@app.route('/')
def index():
    """Redirects to the login page by default."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login and account creation."""
    if request.method == 'POST':
        # In a real application, you would handle user authentication here.
        # This is a placeholder for frontend demonstration.
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')

        print(f"Action: {action}, Username: {username}, Password: {password}")

        if action == 'login':
            # Dummy login success
            print("Attempting login...")
            return redirect(url_for('chat'))
        elif action == 'signup':
            # Dummy signup success
            print("Attempting signup...")
            return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/chat')
def chat():
    """Renders the main chat interface."""
    # In a real app, ensure user is authenticated before rendering chat.
    return render_template('chat.html')

if __name__ == '__main__':
    # Run the Flask app in debug mode. Set debug=False for production.
    app.run(debug=True)
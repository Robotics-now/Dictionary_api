import os
import uuid
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)

# --- Configuration ---
# Database will store user emails and their generated keys
# Note: On Render's free tier, the .db file resets on every deploy. 
# For permanent storage, use Render's PostgreSQL add-on.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration (using Environment Variables for security)
# Set these in your Render Dashboard under 'Environment'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASS')

db = SQLAlchemy(app)
mail = Mail(app)

# --- Database Model ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    api_key = db.Column(db.String(100), unique=True, nullable=False)

# Initialize database tables
with app.app_context():
    db.create_all()

# Load dictionary data
try:
    df = pd.read_csv('dictionary.csv')
except FileNotFoundError:
    # Fallback for testing if file is missing
    df = pd.DataFrame(columns=['word', 'definition'])

@app.route('/')
def home():
    """Renders the home page where users can register for a key."""
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    """Generates a key, saves it to the DB, and emails the user."""
    email = request.form.get('email')
    
    if not email:
        return "Error: Email is required", 400

    # Check if user already exists in DB
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Generate a unique UUID for the API key
        new_key = str(uuid.uuid4())
        user = User(email=email, api_key=new_key)
        db.session.add(user)
        db.session.commit()
    
    # Send the key via email
    try:
        msg = Message(
            subject="Your Dictionary API Key",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Hello!\n\nYour API key is: {user.api_key}\n\n" \
                   f"Use it like this:\n" \
                   f"{request.host_url}api/{user.api_key}/your-word"
        mail.send(msg)
        return f"Success! A key has been sent to {email}. Check your inbox (and spam folder)."
    except Exception as e:
        return f"Error sending email: {str(e)}", 500

@app.route('/api/<api_key>/<word>')
def get_definition(api_key, word):
    """Protected API route using the key in the URL."""
    
    # 1. Validate the API Key
    user_record = User.query.filter_by(api_key=api_key).first()
    
    if not user_record:
        return jsonify({
            "error": "Invalid API Key",
            "message": "Please register at the home page to receive a valid key."
        }), 401

    # 2. Look up the word (case-insensitive check)
    # Using .lower() ensures better matching if the CSV is lowercase
    word_search = word.lower()
    result = df.loc[df['word'].str.lower() == word_search]

    if result.empty:
        return jsonify({
            "word": word,
            "error": "Definition not found in our records."
        }), 404

    # Get definition (handling potential multiple matches)
    definition = result["definition"].iloc[0]

    return jsonify({
        "word": word,
        "definition": str(definition),
        "status": "authorized",
        "user": user_record.email
    })

if __name__ == '__main__':
    # On Render, the port is usually handled by the environment
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

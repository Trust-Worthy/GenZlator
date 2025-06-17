# Connect to MongoDB Atlas
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
uri = os.getenv("MONGO_URI")

# Initialize MongoDB client
client = MongoClient(uri, server_api=ServerApi('1'))

# Check the connection
try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print("❌ Connection error:", e)

# Choose your database (will be created if it doesn't exist)
db = client["genzlator_db"]

# Create or access collections
users_collection = db["users"]
messages_collection = db["messages"]


# users_collection.insert_one({
#     "username": "grandma_linda",
#     "password": "hashed_or_plaintext_password"
# })

for user in users_collection.find():
    print(user)

# Insert a test message from Grandma Linda
test_message = {
    "sender": "grandma_linda",
    "content": "Hi sweetie! How do I turn on the Wi-Fi again?",
    "timestamp": datetime.now(),
    "translated_content": ""  # You can update this later with AI processing
}

result = messages_collection.insert_one(test_message)
print("✅ Inserted test message with ID:", result.inserted_id)
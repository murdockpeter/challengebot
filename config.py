import os
from dotenv import load_dotenv

load_dotenv()

# Discord Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))

# Firebase Configuration
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_PRIVATE_KEY_ID = os.getenv('FIREBASE_PRIVATE_KEY_ID')
FIREBASE_PRIVATE_KEY = os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
FIREBASE_CLIENT_EMAIL = os.getenv('FIREBASE_CLIENT_EMAIL')
FIREBASE_CLIENT_ID = os.getenv('FIREBASE_CLIENT_ID')
FIREBASE_AUTH_URI = os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth')
FIREBASE_TOKEN_URI = os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token')
FIREBASE_AUTH_PROVIDER_X509_CERT_URL = os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs')
FIREBASE_CLIENT_X509_CERT_URL = os.getenv('FIREBASE_CLIENT_X509_CERT_URL')

# Supported Games
SUPPORTED_GAMES = [
    "Littoral Commander",
    "Battlegroup Clash Baltics",
    "Down Range",
    "Take That Street"
]

# Bot Configuration
COMMAND_PREFIX = "!"

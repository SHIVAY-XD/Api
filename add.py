from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, FloodWait, UsernameNotOccupied
import json
import time

# Bot token from BotFather
bot_token = "6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY"  # Replace with your bot token

# Your API ID and API Hash (from Telegram Developer Portal)
api_id = "12834603"  # Replace with your API ID
api_hash = "84a5daf7ac334a70b3fbd180616a76c6"  # Replace with your API Hash

# A dictionary to store active session indices by user
active_sessions = {}

# Function to display available accounts
def show_accounts():
    return "\n".join([f"{i+1}. Account {i+1}" for i in range(len(active_sessions))])

# Function to read user IDs from a JSON file
def read_user_ids_from_json(json_file):
    try:
        with open(json_file, "r") as file:
            data = json.load(file)
            return data.get("user_ids", [])
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []

# Add Members Function (multiple users)
async def add_members(client, group_chat, user_ids):
    for user_id in user_ids:
        try:
            await client.add_chat_members(group_chat, user_id)
            print(f"Added user {user_id}")
        except UserAlreadyParticipant:
            print(f"User {user_id} is already in the group.")
        except FloodWait as e:
            print(f"Flood wait error: Sleeping for {e.x} seconds.")
            time.sleep(e.x)
        except Exception as e:
            print(f"Error adding user {user_id}: {e}")

# Add a single member (by ID or username)
async def add_single_member(client, group_chat, user_identifier):
    try:
        # Try if it's a numeric user ID
        user_id = int(user_identifier)
    except ValueError:
        # If it's not a valid number, it might be a username
        user_id = None

    # If it's a username, try to resolve it to a user ID
    if user_id is None:
        try:
            user = await client.get_users(user_identifier)
            user_id = user.id
        except UsernameNotOccupied:
            print(f"Username {user_identifier} does not exist.")
            return

    try:
        # Add the user by ID
        await client.add_chat_members(group_chat, user_id)
        print(f"Added user {user_id}")
    except UserAlreadyParticipant:
        print(f"User {user_id} is already in the group.")
    except FloodWait as e:
        print(f"Flood wait error: Sleeping for {e.x} seconds.")
        time.sleep(e.x)
    except Exception as e:
        print(f"Error adding user {user_id}: {e}")

# Handle bot commands and login selection
app = Client("bot_session", bot_token=bot_token, api_id=api_id, api_hash=api_hash)  # Initialize bot client with token

@app.on_message(filters.command('start'))
async def start(client, message):
    # Display instructions
    await message.reply("Welcome to the bot! Please login by providing a unique number to create a session.\n"
                         "Example: /login 1234")

@app.on_message(filters.command('login'))
async def login(client, message):
    try:
        # Get account number from the message
        args = message.text.split()
        if len(args) < 2:
            await message.reply("Please provide a unique number to create a session. Example: /login 1234")
            return
        
        # Extract the account number (used as session name)
        account_number = args[1]
        
        # Check if the account number already exists in active sessions
        if account_number in active_sessions:
            await message.reply(f"Account with number {account_number} is already logged in.")
            return
        
        # Create a new session for the account number
        session_name = f"session_{account_number}"
        
        # Initialize a new client session with the unique number as the session file
        async with Client(session_name, api_id=api_id, api_hash=api_hash) as user_client:
            # Store the session in the active_sessions dictionary
            active_sessions[account_number] = session_name
            
            # Respond to the user
            await message.reply(f"Successfully logged in as {account_number}. You can now add members.")
    
    except Exception as e:
        await message.reply(f"Error: {e}")

@app.on_message(filters.command('add_members'))
async def add_users(client, message):
    try:
        # Get the account number (session) and check if the user is logged in
        args = message.text.splitlines()
        if len(args) < 2:
            await message.reply("Please provide the group chat username (with @) and the JSON file with user IDs.")
            return
        
        group_chat = args[1].strip()  # Extract group chat username (with @)
        
        # User needs to send a document (JSON file with user IDs)
        if message.document is None:
            await message.reply("Please send a JSON file with user IDs.")
            return
        
        json_file = message.document.file_name  # Get JSON file name

        # Download the JSON file
        downloaded_file = await message.document.download()

        # Read the user IDs from the JSON file
        user_ids = read_user_ids_from_json(downloaded_file)

        if not user_ids:
            await message.reply("No user IDs found in the JSON file.")
            return

        # Check if the user is logged in by looking at the active sessions
        if not active_sessions:
            await message.reply("You need to log in first using /login <unique_number>.")
            return
        
        # Use the first session available (for simplicity)
        account_number = list(active_sessions.keys())[0]
        session_name = active_sessions[account_number]

        # Log in to the selected session and add users
        async with Client(session_name, api_id=api_id, api_hash=api_hash) as user_client:
            await add_members(user_client, group_chat, user_ids)
            await message.reply("Users have been added successfully!")

    except Exception as e:
        await message.reply(f"Error: {e}")

@app.on_message(filters.command('add'))
async def add_single(client, message):
    try:
        # Extract the group chat and user ID or username from the message
        args = message.text.split()
        if len(args) < 3:
            await message.reply("Please provide the group chat username (with @) and the user ID or username.")
            return
        
        group_chat = args[1]
        user_identifier = args[2]

        # Check if the user is logged in by looking at the active sessions
        if not active_sessions:
            await message.reply("You need to log in first using /login <unique_number>.")
            return
        
        # Use the first session available (for simplicity)
        account_number = list(active_sessions.keys())[0]
        session_name = active_sessions[account_number]

        # Add the single user
        async with Client(session_name, api_id=api_id, api_hash=api_hash) as user_client:
            await add_single_member(user_client, group_chat, user_identifier)
            await message.reply(f"User {user_identifier} has been added to the group {group_chat}!")

    except Exception as e:
        await message.reply(f"Error: {e}")

# Run the bot
app.run()

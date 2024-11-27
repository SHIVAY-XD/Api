from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, FloodWait, UsernameNotOccupied
import json
import time

# Your bot's token from BotFather
bot_token = "6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY"  # Replace with your bot token

# Define session files for different accounts
session_files = ["account1", "account2", "account3"]  # Replace with your session names

# Function to display available accounts
def show_accounts():
    return "\n".join([f"{i+1}. {session_files[i]}" for i in range(len(session_files))])

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
app = Client("bot_session", bot_token=bot_token)  # Pass bot token here

@app.on_message(filters.command('start'))
async def start(client, message):
    # Display accounts to choose from
    await message.reply("Choose your account to log in:\n" + show_accounts())

@app.on_message(filters.command('login'))
async def login(client, message):
    try:
        # Get account choice from the message (user input)
        choice = int(message.text.split()[1]) - 1  # Get account number, converting to zero-index
        if choice < 0 or choice >= len(session_files):
            await message.reply("Invalid account choice. Please choose a valid account.")
            return
        
        # Log into the chosen account session
        session_name = session_files[choice]
        async with Client(session_name) as user_client:
            # After login, ask for the group to add users
            await message.reply(f"Logged in as {session_name}. Now send the group chat username (with @) and the JSON file.")
            return

    except Exception as e:
        await message.reply(f"Error: {e}")

@app.on_message(filters.command('add_members'))
async def add_users(client, message):
    try:
        # Parse the group chat username
        group_chat = message.text.splitlines()[1].strip()  # Extract group chat username (with @)

        # Get the JSON file with user IDs attached by the user
        json_file = message.document.file_name  # The user needs to send the JSON file with user IDs

        # Download the JSON file
        downloaded_file = await message.document.download()
        
        # Read the user IDs from the JSON file
        user_ids = read_user_ids_from_json(downloaded_file)

        if not user_ids:
            await message.reply("No user IDs found in the JSON file.")
            return

        # Add users to the group using the selected account
        async with Client("selected_account") as user_client:  # Replace with actual client session name
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

        # Add the single user
        async with Client("selected_account") as user_client:  # Replace with actual client session name
            await add_single_member(user_client, group_chat, user_identifier)
            await message.reply(f"User {user_identifier} has been added to the group {group_chat}!")

    except Exception as e:
        await message.reply(f"Error: {e}")

# Run the bot
app.run()

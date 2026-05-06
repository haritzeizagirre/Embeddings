import asyncio
import json
import os
import argparse
from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables from .env file
load_dotenv()

async def main():
    parser = argparse.ArgumentParser(description="Backup Telegram Group Messages")
    parser.add_argument("--topic", type=int, help="Topic ID to filter by")
    parser.add_argument("--limit", type=int, help="Number of messages to backup")
    parser.add_argument("--no-media", action="store_true", help="Skip downloading media")
    args = parser.parse_args()

    print("Welcome to the Telegram Group Backup CLI")
    
    # Obtain credentials from user or environment variables
    api_id = os.environ.get('TG_API_ID') or input("Enter API ID: ")
    api_hash = os.environ.get('TG_API_HASH') or input("Enter API Hash: ")
    phone = os.environ.get('TG_PHONE') or input("Enter Phone Number (e.g., +1234567890): ")
    
    # The first parameter is the session file name
    client = TelegramClient('telegram_backup_session', api_id, api_hash)
    
    await client.start(phone)
    print("Successfully logged in.")
    
    # Retrieve dialogs
    dialogs = await client.get_dialogs()
    
    # Filter only groups/channels
    groups = [dialog for dialog in dialogs if dialog.is_group or dialog.is_channel]
    
    tg_group = os.environ.get('TG_GROUP')
    selected_group = None
    
    if tg_group:
        # Check if they provided an @username
        if tg_group.startswith('@'):
            try:
                selected_group = await client.get_entity(tg_group)
                print(f"\nAutomatically selected group from TG_GROUP: {selected_group.title} (ID: {selected_group.id})")
            except Exception as e:
                print(f"\nGroup from TG_GROUP ('{tg_group}') not found. Error: {e}")
        else:
            for group in groups:
                # Match by exactly ID or exactly name
                if str(group.id) == tg_group or group.name == tg_group:
                    selected_group = group
                    break
            if selected_group:
                print(f"\nAutomatically selected group from TG_GROUP: {selected_group.name} (ID: {selected_group.id})")
            else:
                print(f"\nGroup from TG_GROUP ('{tg_group}') not found.")
            
    if not selected_group:
        print("\nAvailable Groups:")
        for i, group in enumerate(groups):
            print(f"[{i}] {group.name} (ID: {group.id})")
            
        try:
            choice = int(input("\nEnter the number of the group to backup: "))
            selected_group = groups[choice]
        except (ValueError, IndexError):
            print("Invalid choice. Exiting.")
            return

    print(f"\nEvaluating messages from {getattr(selected_group, 'name', getattr(selected_group, 'title', 'Unknown'))}...")
    
    if args.limit is not None:
        limit = args.limit
    else:
        limit_input = os.environ.get('TG_LIMIT')
        if limit_input is None:
            limit_input = input("How many messages do you want to backup? (Press Enter for all): ")
        limit = int(limit_input) if limit_input and limit_input.strip() else None

    # Check topic rules (argparse > env > input)
    if args.topic is not None:
        topic_id = args.topic
    else:
        if 'TG_TOPIC' in os.environ:
            topic_id_raw = os.environ['TG_TOPIC']
        elif 'TG_TOPIC_ID' in os.environ:
            topic_id_raw = os.environ['TG_TOPIC_ID']
        else:
            topic_id_raw = input("Enter Topic ID if it's a forum topic (Press Enter to skip/backup whole group): ")
        topic_id = int(topic_id_raw) if topic_id_raw and str(topic_id_raw).strip() else None

    print("\nStarting backup... This may take a while depending on the group size.")
    messages_data = []
    
    kwargs = {'limit': limit}
    if topic_id:
        kwargs['reply_to'] = topic_id
        print(f"Filtering messages by Topic ID: {topic_id}")
    
    async for message in client.iter_messages(selected_group, **kwargs):
        # We store just the basics. You can expand this dict with more metadata depending on your needs.
        msg_dict = {
            "id": message.id,
            "date": message.date.isoformat() if message.date else None,
            "sender_id": message.sender_id,
            "text": message.text,
            "reply_to_msg_id": message.reply_to_msg_id,
        }
        messages_data.append(msg_dict)
        
        # Log progress every 1000 messages
        if len(messages_data) % 1000 == 0:
            print(f"Backed up {len(messages_data)} messages...")
            
    # Reverse to have them in chronological order
    messages_data.reverse()
    
    os.makedirs('backup', exist_ok=True)
    
    topic_suffix = f"_topic_{topic_id}" if topic_id else ""
    filename = os.path.join("backup", f"backup_{selected_group.id}{topic_suffix}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(messages_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nBackup complete! {len(messages_data)} messages saved to {filename}")

if __name__ == '__main__':
    asyncio.run(main())

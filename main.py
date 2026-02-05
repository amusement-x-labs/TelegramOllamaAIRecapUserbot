import asyncio
import argparse
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient

# --- SETTINGS ---
API_ID = 11111111 # set your APP ID
API_HASH = '0123456789abcdedghiklmnopqrstuvwxyz' # set your API hash
PHONE = '+123456789' # set phone number
SESSION_NAME = 'session_name'
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:1.7b" # make sure that this model is downloaded otherwise set your model

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def get_messages_data(chat_input: str, date_str: str, days: int):
    """Collect messages as a list of JSON dictionaries."""
    try:
        start_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_date = start_date + timedelta(days=days)

        try:
            entity_id = int(chat_input)
        except ValueError:
            entity_id = chat_input

        chat_entity = await client.get_entity(entity_id)
        
        data = {
            "chat_name": getattr(chat_entity, 'title', 'Private Chat'),
            "chat_id": chat_entity.id,
            "period_start": date_str,
            "days_count": days,
            "messages": []
        }

        async for msg in client.iter_messages(chat_entity, limit=None, offset_date=end_date):
            if msg.date < start_date:
                break
            
            sender_name = "Me" if msg.out else (getattr(msg.sender, 'first_name', 'User') if msg.sender else 'User')
            data["messages"].append({
                "timestamp": msg.date.strftime('%Y-%m-%d %H:%M:%S'),
                "sender_id": msg.sender_id,
                "sender_name": sender_name,
                "text": msg.text or "[Media/System]"
            })

        # reverse to make order (from old to new)
        data["messages"].reverse()
        return data, chat_entity
    except Exception as e:
        print(f" Error data receiving: {e}")
        return None, None

def call_ollama(messages_list):
    """Converts a list of messages to text and sends it to Ollama."""
    # Here we form a text canvas for the model
    text_history = "\n".join([f"[{m['timestamp']}] {m['sender_name']}: {m['text']}" for m in messages_list])
    
    prompt = f"""
Analyze the Telegram conversation and create a short recap. Your task is to capture the essence.

Please use this format strictly:

**Topics:**
- [Topic 1]: [Brief: Who said what and the summary]
- [Topic 2]: [Brief: The gist of the discussion]

**Plans:**
(Only if you have: Time, Place, Who. If you don't have any plans, don't write this section.)

**Links:**
(Write down the links, if any. If there are no links, skip this section.)

Answer in English language.

Messages history:
{text_history}
"""
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        return response.json().get('response', 'Нет ответа.')
    except Exception as e:
        return f" Ollama error: {e}"

async def main():
    parser = argparse.ArgumentParser(description='Telegram JSON & Recap Tool')
    subparsers = parser.add_subparsers(dest='command')

    # findchat
    subparsers.add_parser('findchat').add_argument('query')

    # savehistory
    s_p = subparsers.add_parser('savehistory')
    s_p.add_argument('chat')
    s_p.add_argument('date')
    s_p.add_argument('--days', type=int, default=1)

    # recap (live)
    r_p = subparsers.add_parser('recap')
    r_p.add_argument('chat')
    r_p.add_argument('date')
    r_p.add_argument('--days', type=int, default=1)

    # recapfile (based локального on local JSON)
    rf_p = subparsers.add_parser('recapfile')
    rf_p.add_argument('file_path', help='Path to the JSON file with history')

    args = parser.parse_args()

    if args.command == 'recapfile':
        if not os.path.exists(args.file_path):
            print(f" File not found: {args.file_path}")
            return
        
        with open(args.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f" Local file analyzing: {args.file_path}...")
        summary = call_ollama(data['messages'])
        
        print("\n" + "═"*30 + " RECAP (FROM FILE) " + "═"*30)
        print(summary)
        
        recap_name = args.file_path.replace('.json', '_recap.md')
        with open(recap_name, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"\nRecap is saved to: {recap_name}")
        return

    if not args.command:
        parser.print_help()
        return

    await client.start(PHONE)

    if args.command == 'findchat':
        async for dialog in client.iter_dialogs():
            if dialog.title and args.query.lower() in dialog.title.lower():
                print(f"{dialog.title} | ID: {dialog.id}")

    elif args.command == 'savehistory':
        data, entity = await get_messages_data(args.chat, args.date, args.days)
        if data:
            filename = f"history_{entity.id}_{args.date}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f" The histroy is saved to JSON: {filename}")

    elif args.command == 'recap':
        print(f"  Data collecting and analysingn started...")
        data, entity = await get_messages_data(args.chat, args.date, args.days)
        if data and data['messages']:
            summary = call_ollama(data['messages'])
            print("\n" + "═"*30 + " RECAP (LIVE) " + "═"*30)
            print(summary)
            
            recap_name = f"recap_{entity.id}_{args.date}.md"
            with open(recap_name, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"\n Recap is saved to: {recap_name}")
        else:
            print("There are no messages found.")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
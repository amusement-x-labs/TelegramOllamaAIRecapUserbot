# TelegramOllamaAIRecapUserbot

IMPORTANT: Pay attention that you use this user bot on your own risk (I cannot guarantee that your Telegram account will not be blocked by the Telegram)

What this bot does:
* Chat ID Finder: Quickly identify the technical ID of any chat.
```
# main.py findchat "your_chat_name"
```
* Local Archiving: Save chat history to your machine for deep analysis.
```
# main.py savehistory @user_name 2025-11-31
# main.py savehistory -1234567890 2025-11-31
```
* Deep Analysis: Sends history to Ollama to extract topics, links, and action plans. Feel free change prompt as you need
```
# main.py recap @user_name  2026-01-26
# main.py recap -1234567890 2026-01-26
# main.py recapfile history_12345_2026-01-26.json
```
* Instant Recap: Read and summarize active chats "on the fly" without saving files.


## Fullfit demonstration
https://youtu.be/k6oE3rNskyI
# test

```python
import pymongo
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto
from pyrogram.errors import BadRequest

# MongoDB Connection
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["mydatabase"]
collection = db["media"]

# Pyrogram Client
api_id = YOUR_API_ID
api_hash = 'YOUR_API_HASH'
bot_token = 'YOUR_BOT_TOKEN'

app = Client("my_bot", api_id, api_hash, bot_token=bot_token)


# Command to upload photo to Telegraph and save it on MongoDB
@app.on_message(filters.command('upload_photo'))
def upload_photo(client, message):
    try:
        # Upload photo to Telegraph
        telegraph_link = client.upload_media(
            InputMediaPhoto(message.photo.file_id),
            caption=message.caption
        )['link']
        
        # Save data on MongoDB
        collection.insert_one({
            "telegraph_link": telegraph_link,
            "caption": message.caption
        })
        
        # Send response to user
        message.reply_text(f"Your photo was uploaded to Telegraph: {telegraph_link}")
        
    except BadRequest as e:
        message.reply_text(f"Error: {e}")
        

app.run()
```

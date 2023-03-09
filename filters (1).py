import re
from typing import Dict, List, Union
from pyrogram import filters
from ..bot import app,db
from .admin import adminsOnly
from .function import extract_text_and_keyb,ikb

filtersdb = db.filters

async def get_filters_count() -> dict:
    chats_count = 0
    filters_count = 0
    async for chat in filtersdb.find({"chat_id": {"$lt": 0}}):
        filters_name = await get_filters_names(chat["chat_id"])
        filters_count += len(filters_name)
        chats_count += 1
    return {
        "chats_count": chats_count,
        "filters_count": filters_count,
    }

async def _get_filters(chat_id: int) -> Dict[str, int]:
    _filters = await filtersdb.find_one({"chat_id": chat_id})
    if not _filters:
        return {}
    return _filters["filters"]

async def get_filters_names(chat_id: int) -> List[str]:
    _filters = []
    for _filter in await _get_filters(chat_id):
        _filters.append(_filter)
    return _filters

async def get_filter(chat_id: int, name: str) -> Union[bool, dict]:
    name = name.lower().strip()
    _filters = await _get_filters(chat_id)
    if name in _filters:
        return _filters[name]
    return False

async def save_filter(chat_id: int, name: str, _filter: dict):
    name = name.lower().strip()
    _filters = await _get_filters(chat_id)
    _filters[name] = _filter
    await filtersdb.update_one(
        {"chat_id": chat_id},
        {"$set": {"filters": _filters}},
        upsert=True,
    )

async def delete_filter(chat_id: int, name: str) -> bool:
    filtersd = await _get_filters(chat_id)
    name = name.lower().strip()
    if name in filtersd:
        del filtersd[name]
        await filtersdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"filters": filtersd}},
            upsert=True,
        )
        return True
    return False

@app.on_message(filters.command("filter") & ~filters.private)
@adminsOnly("can_change_info")
async def add_filter_handler(_, message):
    if len(message.command) < 2 or not message.reply_to_message:
        return await message.reply_text(
            "**Usage:**\nReply to a text or sticker with /filter filter name to save it."
        )
    if not message.reply_to_message.text and not message.reply_to_message.sticker:
        return await message.reply_text(
            "__**You can only save text or stickers in filters.**__")
    
    name = message.text.split(None, 1)[1].strip()
    if not name:
        return await message.reply_text("**Usage:**\n__/filter filter name__")
    chat_id = message.chat.id
    _type = "text" if message.reply_to_message.text else "sticker"
    _filter = {
        "type": _type,
        "data": message.reply_to_message.text.markdown
        if _type == "text"
        else message.reply_to_message.sticker.file_id,
    }
    await save_filter(chat_id, name, _filter)
    await message.reply_text(f"__**Saved filter {name}.**__")

@app.on_message(filters.command("filters") & ~filters.private)
async def list_filter_handle(_, message):
    _filters = await get_filters_names(message.chat.id)
    if not _filters:
        return await message.reply_text("**No filters in this chat.**")
    _filters.sort()
    msg = f"List of filters in {message.chat.title} :\n"
    for _filter in _filters:
        msg += f"**-** `{_filter}`\n"
    await message.reply_text(msg)

@app.on_message(filters.command("stop") & ~filters.private)
@adminsOnly("can_change_info")
async def delete_filter_handle(_, message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:**\n__/stop filter name__")
    name = message.text.split(None, 1)[1].strip()
    if not name:
        return await message.reply_text("**Usage:**\n__/stop filter name__")
    chat_id = message.chat.id
    deleted = await delete_filter(chat_id, name)
    if deleted:
        await message.reply_text(f"**Deleted filter {name}.**")
    else:
        await message.reply_text("**No such filter.**")

@app.on_message(filters.text & ~filters.private & ~filters.via_bot & ~filters.forwarded,group=1)
async def check_filter_handle(_, message):

    text = message.text.lower().strip()

    if not text:
        return
    
    chat_id = message.chat.id

    list_of_filters = await get_filters_names(chat_id)

    for word in list_of_filters:

        pattern = r"( |^|[^\w])" + re.escape(word) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            _filter = await get_filter(chat_id, word)
            data_type = _filter["type"]
            data = _filter["data"]
            
            if data_type == "text":
                keyb = None
                if re.findall(r"\[.+\,.+\]", data):
                    keyboard = extract_text_and_keyb(ikb, data)
                    if keyboard:
                        data, keyb = keyboard
                if message.reply_to_message:
                    await message.reply_to_message.reply_text(
                        data,
                        reply_markup=keyb,
                        disable_web_page_preview=True)
                    if text.startswith("~"):
                        await message.delete()
                    return
                return await message.reply_text(
                    data,
                    reply_markup=keyb,
                    disable_web_page_preview=True,
                )
            if message.reply_to_message:
                await message.reply_to_message.reply_sticker(data)
                if text.startswith("~"):
                    await message.delete()
                return
            return await message.reply_sticker(data)
        

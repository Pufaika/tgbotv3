from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import Dispatcher
from database import get_item_counts_by_category, get_random_item, mark_item_unavailable
from config import GROUP_ID_NO_PICS, GROUP_ID_WITH_PICS, ADMIN_USER_ID, ALLOWED_GROUP_ID
import logging

CATEGORIES = {
    "coconuts": "🥥",
    "broccoli": "🥦",
    "stars": "⭐",
    "horse": "🐴",
    "painting": "🖼️",
    "mountain": "⛰️"
}

PRICES = {
    "coconuts": {"Small": 50, "Big": 100},
    "broccoli": {"Small": 50, "Big": 100},
    "stars": {"Small": 40, "Big": 75},
    "horse": {"Big": 30},
    "mountain": {"Big": 30},
    "painting": {"Small": 65, "Big": 120}
}

NAMES = ["AZ", "HB", "AA", "SB", "FR", "AC"]
user_data = {}

def register_user_handlers(dp: Dispatcher):
    @dp.message_handler(commands=["start"])
    async def start_command(message: types.Message):
        if not await is_user_allowed(message):
            return
        kb = InlineKeyboardMarkup(row_width=2)
        for cat, emoji in CATEGORIES.items():
            kb.insert(InlineKeyboardButton(f"{emoji} {cat.title()}", callback_data=f"cat:{cat}"))
        await message.answer("Choose a category:", reply_markup=kb)

    @dp.callback_query_handler(lambda c: c.data.startswith("cat:"))
    async def choose_category(callback: types.CallbackQuery):
        if not await is_user_allowed(callback):
            return
        cat = callback.data.split(":")[1]
        user_data[callback.from_user.id] = {"category": cat}
        counts = get_item_counts_by_category(cat)
        kb = InlineKeyboardMarkup()
        small_count = counts.get("Small", 0)
        big_count = counts.get("Big", 0)
        kb.add(InlineKeyboardButton(f"🟢 Small ({small_count})", callback_data="size:Small"))
        kb.add(InlineKeyboardButton(f"🔵 Big ({big_count})", callback_data="size:Big"))
        await callback.message.edit_text(f"Select size for {cat.title()}:", reply_markup=kb)

    @dp.callback_query_handler(lambda c: c.data.startswith("size:"))
    async def choose_size(callback: types.CallbackQuery):
        if not await is_user_allowed(callback):
            return
        size = callback.data.split(":")[1]
        user_data[callback.from_user.id]["size"] = size
        kb = InlineKeyboardMarkup(row_width=3)
        for name in NAMES:
            kb.insert(InlineKeyboardButton(name, callback_data=f"name:{name}"))
        await callback.message.edit_text("Select your name:", reply_markup=kb)

    @dp.callback_query_handler(lambda c: c.data.startswith("name:"))
    async def choose_name(callback: types.CallbackQuery):
        if callback.from_user.id not in user_data:
            await callback.message.answer("❌ Please restart with /start.")
            return
        if not await is_user_allowed(callback):
            return
        name = callback.data.split(":")[1]
        user_data[callback.from_user.id]["name"] = name
        await callback.message.edit_text("Do you want to leave a comment? Type it now or type 'No'.")

    @dp.message_handler(lambda msg: msg.from_user.id in user_data and "comment" not in user_data[msg.from_user.id])
    async def receive_comment(message: types.Message):
        uid = message.from_user.id
        if not await is_user_allowed(message):
            return

        if "size" not in user_data[uid] or "category" not in user_data[uid]:
            await message.answer("❌ Please restart with /start.")
            user_data.pop(uid, None)
            return

        comment = message.text.strip()
        if comment.lower() == "no":
            comment = ""
        user_data[uid]["comment"] = comment
        data = user_data[uid]

        item = get_random_item(data["category"], data["size"])
        logging.info(f"[receive_comment] user={uid}, item={item}")

        if not item:
            await message.answer("🚫 No items available in this category and size.")
            return

        try:
            item_id, cat, size, location, photo_ids = item
            price = PRICES.get(cat, {}).get(size, "Unknown")
            photos = photo_ids.split(",") if photo_ids else []

            msg_text = f"""✅ You received:

📦 Category: {cat.title()}
📏 Size: {size}
📍 Location: {location}
💰 Price: {price}
👤 Name: {data['name']}
🗒 Comment: {comment or 'None'}
🔢 Item ID: {item_id}"""

            if photos:
                for i, pid in enumerate(photos):
                    if i == 0:
                        await message.answer_photo(pid, caption=msg_text)
                    else:
                        await message.answer_photo(pid)
            else:
                await message.answer(msg_text)

            await message.bot.send_message(chat_id=GROUP_ID_NO_PICS, text=msg_text)

            for i, pid in enumerate(photos):
                if i == 0:
                    await message.bot.send_photo(chat_id=GROUP_ID_WITH_PICS, photo=pid, caption=msg_text)
                else:
                    await message.bot.send_photo(chat_id=GROUP_ID_WITH_PICS, photo=pid)

            mark_item_unavailable(item_id)
            user_data.pop(uid, None)

        except Exception as e:
            logging.error(f"❌ Error sending item to user {uid}: {e}")
            await message.answer("❌ Failed to send the item. Please contact the admin.")

async def is_user_allowed(message_or_callback):
    user_id = message_or_callback.from_user.id
    chat_type = message_or_callback.chat.type if hasattr(message_or_callback, 'chat') else message_or_callback.message.chat.type
    if chat_type != "private":
        return False
    if user_id == ADMIN_USER_ID:
        return True
    try:
        member = await message_or_callback.bot.get_chat_member(ALLOWED_GROUP_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

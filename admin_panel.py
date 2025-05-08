from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.dispatcher import Dispatcher
from config import ADMIN_USER_ID, GROUP_ID_WITH_PICS, GROUP_ID_NO_PICS
from database import add_item, delete_item_by_message_id

admin_data = {}

def register_admin_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['add'])
    async def add_start(message: types.Message):
        if message.from_user.id != ADMIN_USER_ID:
            return
        kb = InlineKeyboardMarkup(row_width=2)
        for cat in ["coconuts", "broccoli", "stars", "horse", "painting", "mountain"]:
            kb.insert(InlineKeyboardButton(cat.title(), callback_data=f"admin_cat:{cat}"))
        admin_data[message.from_user.id] = {}
        await message.answer("Choose category:", reply_markup=kb)

    @dp.callback_query_handler(lambda c: c.data.startswith("admin_cat:"))
    async def admin_select_category(callback: CallbackQuery):
        cat = callback.data.split(":")[1]
        admin_data[callback.from_user.id]["category"] = cat
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Small", callback_data="admin_size:Small"))
        kb.add(InlineKeyboardButton("Big", callback_data="admin_size:Big"))
        await callback.message.edit_text(f"Selected: {cat}\nChoose size:", reply_markup=kb)

    @dp.callback_query_handler(lambda c: c.data.startswith("admin_size:"))
    async def admin_select_size(callback: CallbackQuery):
        size = callback.data.split(":")[1]
        admin_data[callback.from_user.id]["size"] = size
        await callback.message.edit_text("Now type the location:")

    @dp.message_handler(lambda m: m.from_user.id == ADMIN_USER_ID and "location" not in admin_data.get(m.from_user.id, {}))
    async def admin_location(message: types.Message):
        admin_data[message.from_user.id]["location"] = message.text
        await message.answer("Send description or type 'No':")

    @dp.message_handler(lambda m: m.from_user.id == ADMIN_USER_ID and "description" not in admin_data.get(m.from_user.id, {}))
    async def admin_description(message: types.Message):
        desc = message.text if message.text.lower() != "no" else ""
        admin_data[message.from_user.id]["description"] = desc
        admin_data[message.from_user.id]["photos"] = []
        await message.answer("Now send photos. Type /d when done.")

    @dp.message_handler(lambda m: m.from_user.id == ADMIN_USER_ID and "photos" in admin_data.get(m.from_user.id, {}), content_types=['photo'])
    async def admin_photo(message: types.Message):
        file_id = message.photo[-1].file_id
        admin_data[message.from_user.id]["photos"].append(file_id)
        await message.answer("✅ Photo added. Send more or type /d.")

    @dp.message_handler(commands=['d'])
    async def admin_finalize(message: types.Message):
        data = admin_data.get(message.from_user.id)
        if not data or not data.get("photos"):
            await message.answer("❌ No item in progress.")
            return

        caption = (
            f"📦 Category: {data['category'].title()}\n"
            f"📏 Size: {data['size']}\n"
            f"📍 Location: {data['location']}\n"
            f"📝 Description: {data['description'] or 'None'}"
        )

        msg = await message.bot.send_photo(
            chat_id=GROUP_ID_WITH_PICS,
            photo=data['photos'][0],
            caption=caption,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("❌ Delete", callback_data="delete_item")
            )
        )

        add_item(
            category=data['category'],
            size=data['size'],
            location=data['location'],
            description=data['description'],
            photo_ids=data['photos'],
            message_id=msg.message_id
        )

        await message.bot.send_message(chat_id=GROUP_ID_NO_PICS, text=caption)
        await message.answer("✅ Item added.")
        del admin_data[message.from_user.id]

    @dp.callback_query_handler(lambda c: c.data == "delete_item")
    async def delete_item_callback(callback: CallbackQuery):
        if callback.from_user.id != ADMIN_USER_ID:
            await callback.answer("Not allowed.", show_alert=True)
            return
        await callback.message.delete()
        delete_item_by_message_id(callback.message.message_id)
        await callback.answer("✅ Deleted.", show_alert=True)

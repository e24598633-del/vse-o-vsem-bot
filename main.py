import asyncio
import logging
import os
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN", "8444507448:AAGpZo6algJ_14_j1klWo_VH7niV3oD_C4k")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        name TEXT,
        info TEXT,
        phone TEXT,
        messenger TEXT,
        place TEXT,
        price TEXT,
        details TEXT,
        author_id INTEGER
    )""")
    conn.commit()
    conn.close()

def add_record(category, name, info, phone, messenger, place, price, details, author_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("""INSERT INTO records 
        (category, name, info, phone, messenger, place, price, details, author_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (category, name, info, phone, messenger, place, price, details, author_id))
    conn.commit()
    conn.close()

def get_records(category):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT id, name, info FROM records WHERE category = ? ORDER BY id DESC", (category,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_record(record_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = c.fetchone()
    conn.close()
    return row

init_db() 
# ===== СОСТОЯНИЯ =====
class AddForm(StatesGroup):
    category = State()
    name = State()
    info = State()
    phone = State()
    messenger = State()
    place = State()
    price = State()

# ===== МЕНЮ =====
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Мастера", callback_data="cat_masters")],
        [InlineKeyboardButton(text="🎯 Желания", callback_data="cat_wishes")],
        [InlineKeyboardButton(text="📦 Аренда", callback_data="cat_rent")],
        [InlineKeyboardButton(text="❤️ Помощь", callback_data="cat_help")],
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add")],
    ])

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Это «Всё обо всём» — бот для Горняка.\n\n"
        "Здесь можно найти мастера, одолжить вещь, попросить о помощи.\n\n"
        "Выбирай:",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "back")
async def back(call: CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())

# ===== КАТЕГОРИИ =====
@dp.callback_query(F.data.startswith("cat_"))
async def show_category(call: CallbackQuery):
    cat = call.data.replace("cat_", "")
    titles = {"masters": "🔧 Мастера", "wishes": "🎯 Желания", "rent": "📦 Аренда", "help": "❤️ Помощь"}
    records = get_records(cat)
    
    if not records:
        text = f"{titles[cat]}\n\nПока пусто. Будь первым — нажми «➕ Добавить»!"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить", callback_data=f"add_{cat}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")],
        ])
    else:
        text = f"{titles[cat]}\n\nНажми на запись, чтобы увидеть контакты:"
        buttons = []
        for r in records:
            buttons.append([InlineKeyboardButton(text=f"{r[1]} — {r[2]}", callback_data=f"rec_{r[0]}")])
        buttons.append([InlineKeyboardButton(text="➕ Добавить", callback_data=f"add_{cat}")])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await call.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("rec_"))
async def show_record(call: CallbackQuery):
    rec_id = int(call.data.replace("rec_", ""))
    r = get_record(rec_id)
    if not r:
        await call.answer("Запись не найдена")
        return
    
    cat = r[1]
    text = f"📋 {r[2]}\n\n"
    if r[3]: text += f"🛠 {r[3]}\n"
    if r[4]: text += f"📞 {r[4]}\n"
    if r[5]: text += f"💬 {r[5]}\n"
    if r[6]: text += f"📍 {r[6]}\n"
    if r[7]: text += f"💰 {r[7]}\n"
    if r[8]: text += f"💬 {r[8]}\n"
    
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{cat}")],
    ])) 
# ===== ДОБАВЛЕНИЕ =====
@dp.callback_query(F.data == "add")
async def add_menu(call: CallbackQuery):
    await call.message.edit_text(
        "➕ Что добавить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔧 Мастера", callback_data="add_masters")],
            [InlineKeyboardButton(text="🎯 Желание", callback_data="add_wishes")],
            [InlineKeyboardButton(text="📦 Аренда", callback_data="add_rent")],
            [InlineKeyboardButton(text="❤️ Помощь", callback_data="add_help")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")],
        ])
    )

@dp.callback_query(F.data.startswith("add_"))
async def add_start(call: CallbackQuery, state: FSMContext):
    cat = call.data.replace("add_", "")
    if cat not in ["masters", "wishes", "rent", "help"]:
        return
    await state.update_data(category=cat)
    await state.set_state(AddForm.name)
    await call.message.edit_text("👤 Как тебя зовут?\n\n(или напиши /cancel, чтобы отменить)")

@dp.message(AddForm.name)
async def form_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    cat = data["category"]
    await state.set_state(AddForm.info)
    if cat == "masters":
        await message.answer("🛠 Что ты делаешь? (сантехник, парикмахер, ремонт электроники)")
    elif cat == "wishes":
        await message.answer("🎯 Что ищешь?")
    elif cat == "rent":
        await message.answer("📦 Что сдаёшь?")
    else:
        await message.answer("❤️ Что нужно?")

@dp.message(AddForm.info)
async def form_info(message: Message, state: FSMContext):
    await state.update_data(info=message.text)
    await state.set_state(AddForm.phone)
    await message.answer("📞 Телефон для связи?")

@dp.message(AddForm.phone)
async def form_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(AddForm.messenger)
    await message.answer("💬 Telegram / WhatsApp? (или напиши «нет»)")

@dp.message(AddForm.messenger)
async def form_messenger(message: Message, state: FSMContext):
    msg = message.text
    if msg.lower() in ["нет", "no", "-"]:
        msg = ""
    await state.update_data(messenger=msg)
    data = await state.get_data()
    if data["category"] == "masters":
        await state.set_state(AddForm.place)
        await message.answer("📍 Горняк или Горняк и рядом?")
    elif data["category"] == "rent":
        await state.set_state(AddForm.price)
        await message.answer("💰 Цена за день? (или «договорная»)")
    elif data["category"] == "wishes":
        await state.set_state(AddForm.price)
        await message.answer("💰 Бюджет? (или «договорная»)")
    else:
        await state.set_state(AddForm.place)
        await message.answer("📍 Где? (Горняк и рядом)")

@dp.message(AddForm.place)
async def form_place(message: Message, state: FSMContext):
    await state.update_data(place=message.text, price="", details="")
    await finish_form(message, state)

@dp.message(AddForm.price)
async def form_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text, place="Горняк и рядом", details="")
    await finish_form(message, state)

async def finish_form(message: Message, state: FSMContext):
    data = await state.get_data()
    add_record(
        data["category"], data["name"], data["info"],
        data["phone"], data.get("messenger", ""),
        data.get("place", ""), data.get("price", ""),
        data.get("details", ""), message.from_user.id
    )
    await state.clear()
    await message.answer("✅ Запись добавлена!\n\nПосмотреть — в главном меню.", reply_markup=main_menu())

@dp.message(F.text == "/cancel")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())

async def main():
    print("Бот запущен! 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

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

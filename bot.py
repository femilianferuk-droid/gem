import os
import time
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from google import genai

# Получаем токены из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Убедитесь, что переменные окружения BOT_TOKEN и GEMINI_API_KEY установлены!")

# Инициализация нового клиента Gemini API
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = 'gemini-2.0-flash' # Рекомендую использовать 2.0-flash, она новее и умнее

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я ИИ-бот на базе Gemini. Напиши мне любой вопрос, и я постараюсь ответить.")

@dp.message(F.text)
async def ai_handler(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        # 1. Отправляем сообщение-заглушку
        bot_msg = await message.reply("⏳ Думаю...")
        
        # 2. Запускаем генерацию в потоковом режиме через новый асинхронный клиент (client.aio)
        response = await client.aio.models.generate_content_stream(
            model=MODEL_ID,
            contents=message.text
        )
        
        full_text = ""
        last_edit_time = 0
        
        # 3. Асинхронно получаем куски текста
        async for chunk in response:
            if chunk.text: # Проверяем, что текст в чанке не пустой
                full_text += chunk.text
                current_time = time.time()
                
                # Обновляем сообщение не чаще 1 раза в секунду
                if current_time - last_edit_time > 1.0:
                    try:
                        await bot_msg.edit_text(full_text)
                        last_edit_time = current_time
                    except Exception:
                        pass # Игнорируем ошибки (например, Message is not modified)
                    
        # 4. Финальное обновление сообщения
        try:
            if full_text.strip():
                await bot_msg.edit_text(full_text)
            else:
                await bot_msg.edit_text("Извините, ответ получился пустым.")
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"Ошибка при обращении к Gemini API: {e}")
        await message.reply(f"Извините, произошла ошибка: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот с новым SDK запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")

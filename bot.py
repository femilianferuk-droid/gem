import os
import time
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import google.generativeai as genai

# Получаем токены из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Убедитесь, что переменные окружения BOT_TOKEN и GEMINI_API_KEY установлены!")

# Настройка Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
        # 1. Отправляем сообщение-заглушку, которое будем редактировать
        bot_msg = await message.reply("⏳ Думаю...")
        
        # 2. Запускаем генерацию в потоковом режиме (stream=True)
        response = await model.generate_content_async(message.text, stream=True)
        
        full_text = ""
        last_edit_time = 0
        
        # 3. Асинхронно получаем куски текста по мере их генерации
        async for chunk in response:
            full_text += chunk.text
            current_time = time.time()
            
            # Обновляем сообщение не чаще 1 раза в секунду, чтобы не словить бан от Telegram
            if current_time - last_edit_time > 1.0:
                try:
                    await bot_msg.edit_text(full_text)
                    last_edit_time = current_time
                except Exception:
                    # Игнорируем ошибки (например, если текст не изменился)
                    pass
                    
        # 4. Финальное обновление сообщения, когда генерация полностью завершена
        try:
            if full_text.strip():
                await bot_msg.edit_text(full_text)
            else:
                await bot_msg.edit_text("Извините, ответ получился пустым.")
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"Ошибка при обращении к Gemini API: {e}")
        await message.reply("Извините, произошла ошибка при генерации ответа. Попробуйте еще раз позже.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот со стримингом запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")

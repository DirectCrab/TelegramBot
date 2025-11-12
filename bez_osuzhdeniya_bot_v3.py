#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
БезОсужденияBot - Бот для сбора анонимных историй
Версия 3.0 - с кнопками и улучшенным интерфейсом
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

# ============================================================================
# НАСТРОЙКИ (ЗАГРУЖАЮТСЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ-
# ============================================================================

# Configure logging first
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load and validate environment variables
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

logger.info("Environment variables loaded:")
logger.info(f"BOT_TOKEN exists: {bool(TOKEN)}")

# Parse admin IDs with error handling
admin_ids_str = os.getenv("ADMIN_IDS", "")
try:
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
except ValueError as e:
    logger.error(f"Error parsing ADMIN_IDS: {e}")
    ADMIN_IDS = []

CHANNEL_ID = os.getenv("CHANNEL_ID")
if not CHANNEL_ID:
    raise ValueError("No CHANNEL_ID found in environment variables!")

# 🔧 АВТОПУБЛИКАЦИЯ: True - публикует автоматически, False - только через /post
AUTO_POST = True  # Измените на False для ручной модерации

# ============================================================================
# ХРАНИЛИЩЕ ДАННЫХ
# ============================================================================

STORIES_FILE = "stories.jsonl"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ
# ============================================================================

def load_stories():
    """Загрузить все истории из файла"""
    stories = []
    if os.path.exists(STORIES_FILE):
        try:
            with open(STORIES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        stories.append(json.loads(line))
        except Exception as e:
            logger.error(f"Ошибка при загрузке историй: {e}")
    return stories


def save_story(user_id: int, username: Optional[str], text: str) -> int:
    """Сохранить новую историю в файл"""
    stories = load_stories()
    
    # Генерируем новый ID
    new_id = max([s.get('id', 0) for s in stories], default=0) + 1
    
    story = {
        'id': new_id,
        'ts': datetime.now().isoformat(),
        'user_id': user_id,
        'username': username,
        'text': text
    }
    
    try:
        with open(STORIES_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(story, ensure_ascii=False) + '\n')
        logger.info(f"История #{new_id} сохранена от пользователя {user_id}")
        return new_id
    except Exception as e:
        logger.error(f"Ошибка при сохранении истории: {e}")
        return -1


def get_story_by_id(story_id: int):
    """Получить историю по ID"""
    stories = load_stories()
    for story in stories:
        if story.get('id') == story_id:
            return story
    return None


def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


# ============================================================================
# ОБРАБОТЧИКИ КОМАНД
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с кнопками"""
    
    welcome_text = """
💖 Привет, подружка!

Я — твоя Анонимная Подружка 💬

Здесь можно просто быть собой 🌷

Если хочешь — напиши свою историю.

Я сохраню её анонимно 💌
"""
    
    # Создаём кнопки
    keyboard = [
        [InlineKeyboardButton("📖 Как отправить историю?", callback_data='how_to')],
        [InlineKeyboardButton("❓ Частые вопросы.", callback_data='faq')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'how_to':
        how_to_text = """
<b>📖 Инструкция: Как отправить историю</b>

<b>Шаг 1:</b> Напишите свою историю
Просто начните печатать в этом чате. Расскажите то, что у вас на душе.

<b>Шаг 2:</b> Отправьте сообщение
Нажмите кнопку "Отправить" (или Enter). Всё готово!

<b>Шаг 3:</b> Получите подтверждение
Бот подтвердит, что история получена и опубликована.

<b>💡 Советы:</b>
• Пишите всю историю одним сообщением
• Будьте искренни
• Не волнуйтесь — это полностью анонимно!

<i>Готовы? Напишите свою историю прямо сейчас!</i>
"""
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            how_to_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    elif query.data == 'faq':
        faq_text = """
<b>❓ Частые вопросы</b>

<b>Q: Это действительно анонимно?</b>
A: Да! Ваше имя и контакты никогда не публикуются.

<b>Q: Кто увидит мою историю?</b>
A: История будет опубликована анонимно, никто не узнает автора.

<b>Q: Можно ли удалить историю?</b>
A: Напишите администратору после публикации.

<b>Q: Как быстро публикуется история?</b>
A: Мгновенно! Бот автоматически публикует после отправки.

<b>Q: Можно отправить несколько историй?</b>
A: Да, отправляйте сколько угодно историй!

<b>Q: Что если я случайно отправил не то?</b>
A: Свяжитесь с администратором.
"""
        keyboard = [
            [InlineKeyboardButton("◀️ Назад", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            faq_text,
            parse_mode='HTML',
            reply_markup=reply_markup
        )
    
    elif query.data == 'back_to_start':
        welcome_text = """
💖 Привет, подружка!

Я — твоя Анонимная Подружка 💬

Здесь можно просто быть собой 🌷

Если хочешь — напиши свою историю.

Я сохраню её анонимно 💌
"""
        keyboard = [
            [InlineKeyboardButton("📖 Как отправить историю?", callback_data='how_to')],
            [InlineKeyboardButton("❓ Частые вопросы", callback_data='faq')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup
        )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /list N - показать последние N историй (только для админов)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return  # Молча игнорируем не-админов
    
    # Получаем количество историй (по умолчанию 10)
    try:
        count = int(context.args[0]) if context.args else 10
    except (ValueError, IndexError):
        count = 10
    
    stories = load_stories()
    
    if not stories:
        await update.message.reply_text("📭 Нет сохранённых историй.")
        return
    
    # Берём последние N историй
    recent_stories = stories[-count:]
    recent_stories.reverse()  # Показываем от новых к старым
    
    response = f"📋 Последние {len(recent_stories)} историй:\n\n"
    
    for story in recent_stories:
        story_id = story.get('id')
        text = story.get('text', '')
        preview = text[:100] + '...' if len(text) > 100 else text
        ts = story.get('ts', '')
        
        response += f"ID: {story_id} | {ts[:16]}\n"
        response += f"📝 {preview}\n\n"
    
    response += "\nИспользуйте /post ID для публикации истории."
    
    # Отправляем длинное сообщение (может быть несколько сообщений)
    if len(response) > 4000:
        # Разбиваем на части
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(response)


async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /post ID - опубликовать историю (только для админов)"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return  # Молча игнорируем не-админов
    
    if not context.args:
        await update.message.reply_text("❌ Укажите ID истории: /post ID")
        return
    
    try:
        story_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом.")
        return
    
    story = get_story_by_id(story_id)
    
    if not story:
        await update.message.reply_text(f"❌ История #{story_id} не найдена.")
        return
    
    # Формируем текст для публикации
    post_text = f"📝 История №{story_id}\n\n{story['text']}"
    
    try:
        # Публикуем
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=post_text
        )
        await update.message.reply_text(
            f"✅ История #{story_id} опубликована!"
        )
        logger.info(f"История #{story_id} опубликована админом {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при публикации: {e}")
        await update.message.reply_text(
            "❌ Не могу опубликовать. Проверьте CHANNEL_ID и права бота."
        )


async def handle_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений - приём историй"""
    # Игнорируем пустые сообщения
    if not update.message.text or not update.message.text.strip():
        return
    
    user_id = update.effective_user.id
    username = update.effective_user.username
    text = update.message.text.strip()
    
    # Сохраняем историю
    story_id = save_story(user_id, username, text)
    
    if story_id > 0:
        # Проверяем настройку автопубликации
        if AUTO_POST:
            # 🤖 АВТОМАТИЧЕСКАЯ ПУБЛИКАЦИЯ
            post_text = f"📝 История №{story_id}\n\n{text}"
            
            try:
                # Публикуем
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post_text
                )
                logger.info(f"История #{story_id} автоматически опубликована")
                
                # Создаём кнопку для отправки ещё одной истории
                keyboard = [
                    [InlineKeyboardButton("📝 Отправить ещё историю", callback_data='back_to_start')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "✅ <b>История принята и опубликована!</b>\n\n"
                    "💬 Ваша история опубликована. Спасибо за доверие!\n\n"
                    "📖 Хотите поделиться ещё одной историей? Просто напишите её следующим сообщением.",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Ошибка при публикации: {e}")
                await update.message.reply_text(
                    "💌 История принята и сохранена, но не удалось опубликовать. "
                    "Администратор сможет опубликовать её позже."
                )
        else:
            # 👤 РУЧНАЯ МОДЕРАЦИЯ
            await update.message.reply_text(
                "💌 <b>История принята!</b>\n\n"
                "Спасибо! Ваша история сохранена анонимно и будет рассмотрена для публикации.",
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при сохранении истории. Попробуйте позже."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ -
# ============================================================================

def main():
    """Запуск бота"""
    try:
        logger.info("Starting bot initialization...")
        
        # Print all environment variables (without sensitive data)
        logger.info("Environment check:")
        logger.info(f"BOT_TOKEN configured: {'Yes' if TOKEN else 'No'}")
        logger.info(f"ADMIN_IDS configured: {ADMIN_IDS}")
        logger.info(f"CHANNEL_ID configured: {CHANNEL_ID}")
        
        # Создаём приложение
        application = Application.builder().token(TOKEN).build()
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        raise
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("post", post_command))
    
    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Обработчик текстовых сообщений (приём историй)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_story)
    )
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 БезОсужденияBot запущен!")
    print(f"📊 Админы: {ADMIN_IDS}")
    print(f"📢 Канал: {CHANNEL_ID}")
    print(f"🔧 Автопубликация: {'✅ ВКЛЮЧЕНА' if AUTO_POST else '❌ ВЫКЛЮЧЕНА (ручная модерация)'}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

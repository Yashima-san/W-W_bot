import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import pandas as pd
import io
import os

# Токен вашего бота
TELEGRAM_BOT_TOKEN = '7825742740:AAF8yrh-fB_kvZFfoB3075RbDwOpkq4mjx4'

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для преобразования XLSX в CSV и сохранения его в той же директории
def convert_xlsx_to_csv(xlsx_path, csv_path):
    if os.path.exists(csv_path):
        logger.info("Такой файл уже есть!")
        return

    try:
        # Считываем файл XLSX
        df = pd.read_excel(xlsx_path)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {xlsx_path}: {e}")
        raise Exception(f"Ошибка при чтении файла {xlsx_path}: {e}")

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    try:
        # Сохраняем файл CSV
        with open(csv_path, 'w', encoding='utf-8') as csv_file:
            csv_file.write(csv_buffer.getvalue())
    except Exception as e:
        logger.error(f"Ошибка при записи файла {csv_path}: {e}")
        raise Exception(f"Ошибка при записи файла {csv_path}: {e}")

# Преобразование и сохранение файла Rice11.xlsx в Rice11.csv в той же директории
try:
    xlsx_path = 'Rice11.xlsx'  # Путь к вашему XLSX файлу в локальной директории
    csv_path = 'Rice11.csv'     # Путь к вашему CSV файлу в локальной директории

    # Логирование текущей рабочей директории
    current_directory = os.getcwd()
    logger.info(f"Текущая рабочая директория: {current_directory}")

    convert_xlsx_to_csv(xlsx_path, csv_path)
    logger.info("Файл Rice11.xlsx успешно преобразован и сохранён как Rice11.csv")
except Exception as e:
    logger.error(f"Ошибка при преобразовании и сохранении файла: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("1 курс", callback_data='1')],
        [InlineKeyboardButton("2 курс", callback_data='2')],
        [InlineKeyboardButton("3 курс", callback_data='3')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Выберите курс:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data in ['2', '3']:
        await query.edit_message_text(text="На стадии разработки!")
    elif query.data == '1':
        keyboard = [
            [InlineKeyboardButton("ИС24-02", callback_data='ИС24-02')],
            # Добавьте остальные группы здесь
            [InlineKeyboardButton("<-- Назад", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text='Выберите группу:', reply_markup=reply_markup)

async def group_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    group = query.data
    keyboard = [
        [InlineKeyboardButton("Понедельник", callback_data=f'{group}_Monday')],
        [InlineKeyboardButton("Вторник", callback_data=f'{group}_Tuesday')],
        [InlineKeyboardButton("Среда", callback_data=f'{group}_Wednesday')],
        [InlineKeyboardButton("Четверг", callback_data=f'{group}_Thursday')],
        [InlineKeyboardButton("Пятница", callback_data=f'{group}_Friday')],
        [InlineKeyboardButton("Полное расписание", callback_data=f'{group}_Full')],
        [InlineKeyboardButton("<-- Назад", callback_data=f'{group}_back_to_groups')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Выберите день недели:', reply_markup=reply_markup)

async def schedule_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    group = data[0]
    day = data[1]

    # Путь к CSV файлу
    csv_path = 'Rice11.csv'  # Путь к вашему CSV файлу в локальной директории

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        await query.edit_message_text(text=f"Ошибка при чтении файла: {e}")
        return

    if day == 'Full':
        filtered_df = df[df['Группа'] == group][['День недели', 'Время', group]]
    else:
        filtered_df = df[(df['Группа'] == group) & (df['День недели'] == day)][['День недели', 'Время', group]]

    # Формируем текст для вывода
    if filtered_df.empty:
        schedule = "Расписание на выбранный день недели отсутствует."
    else:
        schedule = filtered_df.to_string(index=False)

    keyboard = [
        [InlineKeyboardButton("<-- Назад", callback_data=f'{group}_back_to_days')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=schedule, reply_markup=reply_markup)

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("1 курс", callback_data='1')],
        [InlineKeyboardButton("2 курс", callback_data='2')],
        [InlineKeyboardButton("3 курс", callback_data='3')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Выберите курс:', reply_markup=reply_markup)

async def back_to_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("ИС24-02", callback_data='ИС24-02')],
        # Добавьте остальные группы здесь
        [InlineKeyboardButton("<-- Назад", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Выберите группу:', reply_markup=reply_markup)

async def back_to_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split('_')
    group = data[0]

    keyboard = [
        [InlineKeyboardButton("Понедельник", callback_data=f'{group}_Monday')],
        [InlineKeyboardButton("Вторник", callback_data=f'{group}_Tuesday')],
        [InlineKeyboardButton("Среда", callback_data=f'{group}_Wednesday')],
        [InlineKeyboardButton("Четверг", callback_data=f'{group}_Thursday')],
        [InlineKeyboardButton("Пятница", callback_data=f'{group}_Friday')],
        [InlineKeyboardButton("Полное расписание", callback_data=f'{group}_Full')],
        [InlineKeyboardButton("Назад", callback_data=f'{group}_back_to_groups')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Выберите день недели:', reply_markup=reply_markup)

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern='^[123]$'))
    application.add_handler(CallbackQueryHandler(group_button, pattern='^ИС24-02$'))  # Добавьте остальные группы здесь
    application.add_handler(CallbackQueryHandler(schedule_button, pattern='^(ИС24-02)_[A-Za-z]+$'))  # Добавьте остальные группы здесь
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    application.add_handler(CallbackQueryHandler(back_to_groups, pattern='^(ИС24-02)_back_to_groups$'))  # Добавьте остальные группы здесь
    application.add_handler(CallbackQueryHandler(back_to_days, pattern='^(ИС24-02)_back_to_days$'))  # Добавьте остальные группы здесь

    application.run_polling()

if __name__ == '__main__':
    main()
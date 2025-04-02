import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import pandas as pd
import os

# Токен вашего бота
TELEGRAM_BOT_TOKEN = '7825742740:AAF8yrh-fB_kvZFfoB3075RbDwOpkq4mjx4'

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к XLSX файлу
xlsx_path = 'Rice11.xlsx'  # Путь к вашему XLSX файлу в локальной директории

# Функция для получения списка групп из XLSX файла
def get_groups_from_xlsx(xlsx_path):
    try:
        df = pd.read_excel(xlsx_path)
        groups = df.columns[2:].tolist()  # Предполагаем, что первые две колонки - День недели и Время
        return groups
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {xlsx_path}: {e}")
        return []

# Получаем список групп
groups = get_groups_from_xlsx(xlsx_path)

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
            [InlineKeyboardButton(group, callback_data=group)] for group in groups[:13]  # Сокращаем до ИС24-01-1П включительно
        ] + [
            [InlineKeyboardButton("<-- Назад", callback_data='back_to_start')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text='Выберите группу:', reply_markup=reply_markup)

async def group_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    group = query.data
    keyboard = [
        [InlineKeyboardButton(day, callback_data=f'{group}_{day}') for day in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']],
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

    # Проверка наличия файла XLSX
    if not os.path.exists(xlsx_path):
        await query.edit_message_text(text="Файл Rice11.xlsx не найден. Попробуйте позже.")
        return

    try:
        # Считываем файл XLSX
        df = pd.read_excel(xlsx_path)
    except Exception as e:
        await query.edit_message_text(text=f"Ошибка при чтении файла: {e}")
        return

    if day == 'Full':
        # Формируем полное расписание
        full_schedule = f"————————————————————————\nГруппа: {group}\nПолное расписание\n————————————————————————\n"
        days_of_week = df['День недели'].unique()
        for d in days_of_week:
            day_schedule = df[(df['День недели'] == d) & (df[group].notna())][['Время', group]]
            if not day_schedule.empty:
                full_schedule += f"\n————————————————————————\n{d}\n————————————————————————\n"
                for _, row in day_schedule.iterrows():
                    full_schedule += f"⏰ {row['Время']} ┆ {row[group]}\n"
        schedule = full_schedule
    else:
        # Формируем расписание для конкретного дня
        filtered_df = df[(df['День недели'] == day) & (df[group].notna())][['Время', group]]
        if filtered_df.empty:
            schedule = "Расписание на выбранный день недели отсутствует."
        else:
            schedule = f"Группа: {group}\nДень: {day}\n————————————————————————\n"
            for _, row in filtered_df.iterrows():
                schedule += f"⏰ {row['Время']} ┆ {row[group]}\n"

    logger.info(f"Расписание для группы {group} на {day}:\n{schedule}")

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
        [InlineKeyboardButton(group, callback_data=group)] for group in groups[:13]  # Сокращаем до ИС24-01-1П включительно
    ] + [
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
        [InlineKeyboardButton(day, callback_data=f'{group}_{day}') for day in ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']],
        [InlineKeyboardButton("Полное расписание", callback_data=f'{group}_Full')],
        [InlineKeyboardButton("<-- Назад", callback_data=f'{group}_back_to_groups')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text='Выберите день недели:', reply_markup=reply_markup)

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern='^[123]$'))
    application.add_handler(CallbackQueryHandler(group_button, pattern='^(' + '|'.join(groups[:13]) + ')$'))  # Сокращаем до ИС24-01-1П включительно
    application.add_handler(CallbackQueryHandler(schedule_button, pattern='^(' + '|'.join(groups[:13]) + ')_[А-Яа-я]+$'))  # Сокращаем до ИС24-01-1П включительно
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    application.add_handler(CallbackQueryHandler(back_to_groups, pattern='^(' + '|'.join(groups[:13]) + ')_back_to_groups$'))  # Сокращаем до ИС24-01-1П включительно
    application.add_handler(CallbackQueryHandler(back_to_days, pattern='^(' + '|'.join(groups[:13]) + ')_back_to_days$'))  # Сокращаем до ИС24-01-1П включительно

    application.run_polling()

if __name__ == '__main__':
    main()
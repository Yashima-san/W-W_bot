import os
import requests
import pandas as pd
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

# Константы
TELEGRAM_BOT_TOKEN = "7825742740:AAF8yrh-fB_kvZFfoB3075RbDwOpkq4mjx4"
YANDEX_CLIENT_ID = "2e36052ca2af4d5190cf9e31ce7c1991"  # Замените на ваш реальный Client ID
YANDEX_CLIENT_SECRET = "fbce49b7b109497596fcf2d579650834"  # Замените на ваш реальный Client Secret
YANDEX_REDIRECT_URI = "https://oauth.yandex.ru/suggest/token"  # Замените на ваш реальный Redirect URI
YANDEX_AUTH_URL = "https://oauth.yandex.ru/authorize"
YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_FILE_PATH = "disk:/Rice/Rice_11.xlsx"
LOCAL_EXCEL_FILE = "Rice_11.xlsx"
LOCAL_CSV_FILE = "schedule.csv"
LOCAL_JSON_FILE = "schedule.json"
USER_LOGS_FILE = "user_logs.json"

def get_yandex_disk_token(client_id, client_secret, redirect_uri):
    auth_url = f"{YANDEX_AUTH_URL}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    print(f"Перейдите по ссылке для авторизации: {auth_url}")
    code = input("Введите код из URL: ")

    token_url = YANDEX_TOKEN_URL
    token_params = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }

    try:
        response = requests.post(token_url, data=token_params)
        response.raise_for_status()
        token_info = response.json()
        return token_info['access_token']
    except Exception as e:
        print(f"Произошла ошибка при получении токена: {e}")
        raise

# Получение OAuth-токена
try:
    YANDEX_DISK_TOKEN = get_yandex_disk_token(YANDEX_CLIENT_ID, YANDEX_CLIENT_SECRET, YANDEX_REDIRECT_URI)
except Exception as e:
    print(f"Ошибка при получении токена: {e}")
    exit(1)

def check_file_exists(token, file_path):
    url = "https://disk.yandex.ru/d/fd5cVHTtcFGn1Q"
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": file_path}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        print(f"Файл {file_path} существует.")
    except Exception as e:
        print(f"Файл {file_path} не существует или нет доступа: {e}")
        raise

# Проверка существования файла
try:
    check_file_exists(YANDEX_DISK_TOKEN, YANDEX_FILE_PATH)
except Exception as e:
    print(f"Ошибка при проверке существования файла: {e}")
    exit(1)

def download_file_yandex(token, file_path, local_path):
    url = "https://disk.yandex.ru/d/ueMmvEhxy4OuDw"
    headers = {"Authorization": f"OAuth {token}"}
    params = {"path": file_path}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        response_json = response.json()
        download_url = response_json.get("href")
        if not download_url:
            raise ValueError(f"Не удалось получить URL для скачивания файла. Ответ: {response_json}")
        
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Файл успешно скачан и сохранён как {local_path}")
    except Exception as e:
        print(f"Произошла ошибка при скачивании файла: {e}")
        raise

def excel_to_csv(excel_file, csv_file):
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        # Убедитесь, что у вас есть нужные столбцы
        required_columns = ['Группа', 'День недели', 'Номер пары', 'Дисциплина', 'Преподаватель', 'Кабинет']
        if not all(column in df.columns for column in required_columns):
            raise ValueError("Не хватает необходимых столбцов в Excel файле")

        df['Дисциплина'] = df.apply(lambda row: 'Дисциплина - ПП' if row['Дисциплина'] == 'ПП' else row['Дисциплина'], axis=1)
        df['Кабинет'] = df.apply(lambda row: '' if row['Дисциплина'] == 'ПП' else row['Кабинет'], axis=1)
        df['Преподаватель'] = df.apply(lambda row: '' if row['Дисциплина'] == 'ПП' else row['Преподаватель'], axis=1)
        
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"Файл успешно сохранён как {csv_file}")
        return df
    except Exception as e:
        print(f"Произошла ошибка при преобразовании Excel в CSV: {e}")
        return None

def save_to_json(data, json_file):
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data.to_dict(orient='records'), f, ensure_ascii=False, indent=4)
        print(f"Данные успешно сохранены в {json_file}")
    except Exception as e:
        print(f"Произошла ошибка при сохранении данных в JSON: {e}")
        raise

def log_user_request(user_id, group, timestamp=None):
    try:
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        user_log = {
            "user_id": user_id,
            "group": group,
            "timestamp": timestamp
        }
        
        if os.path.exists(USER_LOGS_FILE):
            with open(USER_LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(user_log)
        
        with open(USER_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
        print(f"Запрос пользователя {user_id} сохранён в {USER_LOGS_FILE}")
    except Exception as e:
        print(f"Произошла ошибка при сохранении логов пользователя: {e}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Введите группу для получения расписания (например: ИС23-02)')

async def get_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    group = update.message.text.strip().upper()
    user_id = update.effective_user.id
    if not group:
        await update.message.reply_text('Пожалуйста, введите корректную группу.')
        return
    
    try:
        # Сохранение лога запроса пользователя
        log_user_request(user_id, group)
        
        download_file_yandex(YANDEX_DISK_TOKEN, YANDEX_FILE_PATH, LOCAL_EXCEL_FILE)
        
        # Преобразование Excel в CSV
        df = excel_to_csv(LOCAL_EXCEL_FILE, LOCAL_CSV_FILE)
        if df is None:
            await update.message.reply_text("Произошла ошибка при преобразовании файла Excel в CSV.")
            return
        
        # Сохранение данных в JSON
        save_to_json(df, LOCAL_JSON_FILE)

        # Фильтрация данных по группе
        filtered_df = df[df['Группа'] == group]
        
        if filtered_df.empty:
            await update.message.reply_text(f'Расписание для группы {group} не найдено.')
            return
        
        response = f"Расписание для группы {group}:\n"
        for _, row in filtered_df.iterrows():
            response += f"{row['День недели']}.\n--------------------\n"
            response += f"{row['Номер пары']}  {row['Дисциплина']}  {row['Преподаватель']} || {row['Кабинет']}\n"
        
        await update.message.reply_text(response)
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при получении расписания: {e}")
        print(f"Ошибка при получении расписания: {e}")

def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_schedule))
    
    application.run_polling()

if __name__ == '__main__':
    main()
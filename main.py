import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict

# --- Настройка логов ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

# --- Подключение к Google Sheets ---
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Finance Tracker").sheet1

# --- Функция добавления транзакции ---
def add_transaction(update, context):
    text = update.message.text.strip()
    user = update.message.from_user.username or str(update.message.from_user.id)
    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    if text.startswith('+') or text.startswith('-'):
        parts = text.split(' ', 1)
        amount = parts[0]
        category = parts[1] if len(parts) > 1 else 'Без категории'

        try:
            float(amount)  # проверка числа
        except ValueError:
            update.message.reply_text("Сумма должна быть числом, например: -100 еда")
            return

        # Запись в Google Sheets
        sheet.append_row([date, user, amount, category])
        update.message.reply_text(f"✅ Добавлено: {amount} на {category}")
    else:
        update.message.reply_text("Введите в формате: `-100 кафе` или `+500 зарплата`")

# --- Команда /summary - итог за все время ---
def summary(update, context):
    user = update.message.from_user.username or str(update.message.from_user.id)
    rows = sheet.get_all_values()[1:]  # пропускаем заголовок
    total = 0
    for row in rows:
        if row[1] == user:
            try:
                total += float(row[2])
            except:
                pass
    update.message.reply_text(f"Итоговый баланс: {total:.2f} руб.")

# --- Команда /today - отчет за сегодня ---
def today_report(update, context):
    user = update.message.from_user.username or str(update.message.from_user.id)
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    rows = sheet.get_all_values()[1:]
    total = 0
    cat_sum = defaultdict(float)

    for row in rows:
        date, u, amount, category = row
        if u == user and date.startswith(today_str):
            try:
                val = float(amount)
                total += val
                cat_sum[category] += val
            except:
                pass

    report = f"Отчет за сегодня ({today_str}):\nИтог: {total:.2f} руб.\n"
    report += "По категориям:\n"
    for cat, val in cat_sum.items():
        report += f" - {cat}: {val:.2f} руб.\n"

    update.message.reply_text(report)

# --- Команда /week - отчет за последние 7 дней ---
def week_report(update, context):
    user = update.message.from_user.username or str(update.message.from_user.id)
    now = datetime.datetime.now()
    week_ago = now - datetime.timedelta(days=7)
    rows = sheet.get_all_values()[1:]
    total = 0
    cat_sum = defaultdict(float)

    for row in rows:
        date_str, u, amount, category = row
        if u != user:
            continue
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        except:
            continue

        if date >= week_ago:
            try:
                val = float(amount)
                total += val
                cat_sum[category] += val
            except:
                pass

    report = f"Отчет за последние 7 дней:\nИтог: {total:.2f} руб.\n"
    report += "По категориям:\n"
    for cat, val in cat_sum.items():
        report += f" - {cat}: {val:.2f} руб.\n"

    update.message.reply_text(report)

# --- Основная функция запуска бота ---
def main():
    # Вставьте сюда токен вашего бота
    TOKEN = '7926562743:AAGb86OAy_mFv7qgzmRdRqKHLIXrFx-cuIw'

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, add_transaction))
    dp.add_handler(CommandHandler("summary", summary))
    dp.add_handler(CommandHandler("today", today_report))
    dp.add_handler(CommandHandler("week", week_report))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

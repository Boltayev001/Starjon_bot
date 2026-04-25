import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = "8285361555:AAEC1rMpMzt_TSfmgcgNZUTH62pGqAtWHuw"
FILE = "words.json"

# user_id -> [[uz, en]]
user_words = {}

# user_id -> current index
current = {}


# ---------------- LOAD / SAVE ----------------
def load_words():
    global user_words
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            # eski format bo‘lsa tozalab yuboramiz
            if isinstance(data, dict):
                user_words = data
            else:
                user_words = {}

    except:
        user_words = {}


def save_words_to_file():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(user_words, f, ensure_ascii=False)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom 👋\n\n"
        "/add - so‘z qo‘shish\n"
        "/quiz - test\n"
        "/list - so‘zlar\n"
        "/stats - statistika\n"
        "/remove - hammasini o‘chirish"
    )


# ---------------- ADD ----------------
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "So‘zlarni yubor:\n\nolma-apple\nkitob-book"
    )
    context.user_data["adding"] = True


# ---------------- QUIZ ----------------
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    words_list = user_words.get(user_id, [])

    if not words_list:
        await update.message.reply_text("Avval so‘z qo‘sh /add 😕")
        return

    current[user_id] = 0
    uz, en = words_list[0]

    context.user_data["quiz"] = True
    context.user_data["answer"] = en

    await update.message.reply_text(f"Tarjima qil:\n\n{uz}")


# ---------------- REMOVE ----------------
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    user_words[user_id] = []
    current[user_id] = 0

    save_words_to_file()
    context.user_data.clear()

    await update.message.reply_text("Sizning so‘zlaringiz o‘chirildi 🗑️")


# ---------------- LIST ----------------
async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    words_list = user_words.get(user_id, [])

    if not words_list:
        await update.message.reply_text("So‘z yo‘q 😕")
        return

    text = "📚 So‘zlar:\n\n"
    for i, (uz, en) in enumerate(words_list, 1):
        text += f"{i}. {uz} - {en}\n"

    await update.message.reply_text(text)


# ---------------- STATS ----------------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    total = len(user_words.get(user_id, []))

    await update.message.reply_text(
        f"📊 Statistika:\n\n🔢 Jami so‘zlar: {total}"
    )


# ---------------- MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)

    # -------- ADD --------
    if context.user_data.get("adding"):
        if user_id not in user_words:
            user_words[user_id] = []

        lines = text.split("\n")

        for line in lines:
            if "-" in line:
                uz, en = line.split("-", 1)
                user_words[user_id].append((uz.strip(), en.strip()))

        save_words_to_file()
        context.user_data["adding"] = False

        await update.message.reply_text(
            f"{len(user_words[user_id])} ta so‘z saqlandi ✅"
        )
        return

    # -------- QUIZ --------
    if context.user_data.get("quiz"):
        words_list = user_words.get(user_id, [])

        if not words_list:
            await update.message.reply_text("So‘z yo‘q 😕")
            return

        user_answer = text.lower()
        correct = context.user_data["answer"].lower()

        index = current.get(user_id, 0)

        if user_answer == correct:
            index += 1
            current[user_id] = index

            if index >= len(words_list):
                await update.message.reply_text("Tugadi 🎉")
                context.user_data["quiz"] = False
                return

            uz, en = words_list[index]
            context.user_data["answer"] = en

            await update.message.reply_text("To‘g‘ri ✅")
            await update.message.reply_text(f"Keyingi:\n\n{uz}")

        else:
            await update.message.reply_text("Noto‘g‘ri ❌ Qaytadan urin")


# ---------------- MAIN ----------------
load_words()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(CommandHandler("remove", remove))
app.add_handler(CommandHandler("list", list_words))
app.add_handler(CommandHandler("stats", stats))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
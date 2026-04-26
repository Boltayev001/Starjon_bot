import json
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = "8285361555:AAEC1rMpMzt_TSfmgcgNZUTH62pGqAtWHuw"
FILE = "words.json"

words = []
current = {}
quiz_order = {}


# -------- LOAD / SAVE --------
def load_words():
    global words
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            words = data if isinstance(data, list) else []
    except:
        words = []

def save_words():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom 👋\n\n"
        "Quizni boshlash uchun /quiz ni bosing 🎯"
    )


# -------- MAKE --------
async def make(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "So‘zlarni yubor:\n\nolma-apple\nkitob-book"
    )
    context.user_data["adding"] = True


# -------- QUIZ --------
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if not words:
        await update.message.reply_text("Hali so‘z yo‘q 😕")
        return

    order = list(range(len(words)))
    random.shuffle(order)

    quiz_order[user_id] = order
    current[user_id] = 0

    index = order[0]
    uz, en = words[index]

    context.user_data["quiz"] = True
    context.user_data["answer"] = en
    context.user_data[f"retry_{user_id}"] = False

    await update.message.reply_text(f"Tarjima qil:\n\n{uz}")


# -------- REMOVE --------
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words.clear()
    save_words()

    current.clear()
    quiz_order.clear()
    context.user_data.clear()

    await update.message.reply_text("Barcha so‘zlar o‘chirildi 🗑️")


# -------- MESSAGE HANDLER --------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)

    # --- ADD WORDS ---
    if context.user_data.get("adding"):
        for line in text.split("\n"):
            if "-" in line:
                uz, en = line.split("-", 1)
                words.append((uz.strip(), en.strip()))

        save_words()
        context.user_data["adding"] = False

        await update.message.reply_text("So‘zlar saqlandi ✅")
        return

    # --- QUIZ MODE ---
    if context.user_data.get("quiz"):
        order = quiz_order.get(user_id, [])

        if not words or not order:
            await update.message.reply_text("So‘z yo‘q 😕")
            return

        user_answer = text.lower().strip()
        correct = context.user_data["answer"].lower()

        retry_key = f"retry_{user_id}"
        retry = context.user_data.get(retry_key, False)

        pos = current.get(user_id, 0)

        # ---------------- CORRECT ----------------
        if user_answer == correct:
            context.user_data[retry_key] = False

            pos += 1
            current[user_id] = pos

            if pos >= len(order):
                await update.message.reply_text(
                    "Tugadi 🎉 Sen uddalading!\n\n"
                    "Testni qayta boshlash uchun /quiz ni bosing 🎯"
                )
                context.user_data["quiz"] = False
                return

            index = order[pos]
            uz, en = words[index]
            context.user_data["answer"] = en

            await update.message.reply_text("To‘g‘ri ✅")
            await update.message.reply_text(f"Keyingi:\n\n{uz}")
            return

        # ---------------- FIRST WRONG ----------------
        if not retry:
            context.user_data[retry_key] = True
            await update.message.reply_text("Noto‘g‘ri ❌ Yana bir marta urinib ko‘r")
            return

        # ---------------- SECOND WRONG ----------------
        context.user_data[retry_key] = False

        await update.message.reply_text(f"❌ To‘g‘ri javob: {correct}")

        pos += 1
        current[user_id] = pos

        if pos >= len(order):
            await update.message.reply_text(
                "Tugadi 🎉\n\n"
                "Testni qayta boshlash uchun /quiz ni bosing 🎯"
            )
            context.user_data["quiz"] = False
            return

        index = order[pos]
        uz, en = words[index]
        context.user_data["answer"] = en

        await update.message.reply_text(f"Keyingi:\n\n{uz}")
        return

    # --- DEFAULT ---
    await update.message.reply_text(
        "Testni boshlash uchun /quiz ni bosing 🎯"
    )


# -------- MAIN --------
load_words()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("make", make))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(CommandHandler("remove", remove))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()

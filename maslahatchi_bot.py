import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import anthropic

# =============================================
#  SOZLAMALAR — Railway Variables bo'limiga
#  TELEGRAM_TOKEN va ANTHROPIC_KEY kiriting
# =============================================
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_KEY  = os.environ["ANTHROPIC_KEY"]

# =============================================
#  Logging
# =============================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =============================================
#  Anthropic klienti
# =============================================
ai = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SYSTEM_PROMPT = """Siz "Maslahatchi" nomli professional va jiddiy AI yordamchisiz.
Faqat o'zbek tilida javob bering.
Qisqa, aniq va amaliy maslahatlar bering.
Har bir javob tushunarli, ishonchli va konstruktiv bo'lsin.
Ortiqcha so'z ishlatmang."""

# Foydalanuvchi suhbat tarixi (xotira)
# { chat_id: [ {role, content}, ... ] }
conversation_history: dict[int, list[dict]] = {}


def get_ai_response(chat_id: int, user_text: str) -> str:
    """Anthropic API ga so'rov yuboradi va javob qaytaradi."""
    history = conversation_history.setdefault(chat_id, [])
    history.append({"role": "user", "content": user_text})

    # Oxirgi 20 ta xabarni yuboramiz (context window tejash uchun)
    response = ai.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=history[-20:],
    )

    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    return reply


# =============================================
#  /start komandasi
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    # Yangi suhbat boshlanganda tarixni tozalaymiz
    conversation_history[chat_id] = []
    await update.message.reply_text(
        f"Salom, {user.first_name}! 👋\n\n"
        "Men — *Maslahatchi*, sizning professional AI yordamchingiz.\n\n"
        "Biznes, ta'lim, texnologiya yoki hayotning istalgan sohasida "
        "savolingizni yozing — aniq javob beraman.\n\n"
        "📌 Foydali komandalar:\n"
        "/start — yangi suhbat boshlash\n"
        "/help  — yordam\n"
        "/clear — suhbat tarixini tozalash",
        parse_mode="Markdown",
    )


# =============================================
#  /help komandasi
# =============================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Maslahatchi bot — qo'llanma*\n\n"
        "Menga istalgan savolingizni yozing. Men:\n"
        "• Biznes va startup maslahatlar beraman\n"
        "• Ta'lim va ko'nikma rivojlantirishda yordam beraman\n"
        "• Texnologiya va dasturlash savollariga javob beraman\n"
        "• Hayotiy vaziyatlarda qo'llab-quvvatlayman\n\n"
        "Suhbat tarixini eslab qolaman, shuning uchun davomli suhbat qilish mumkin.\n\n"
        "/clear — tarixni tozalash uchun",
        parse_mode="Markdown",
    )


# =============================================
#  /clear komandasi
# =============================================
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    conversation_history[chat_id] = []
    await update.message.reply_text("✅ Suhbat tarixi tozalandi. Yangi suhbat boshlashingiz mumkin!")


# =============================================
#  Oddiy xabarlarni qayta ishlash
# =============================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_text = update.message.text

    # "Yozmoqda..." ko'rsatamiz
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        reply = get_ai_response(chat_id, user_text)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Xato: {e}")
        await update.message.reply_text(
            "⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )


# =============================================
#  Botni ishga tushirish
# =============================================
def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()

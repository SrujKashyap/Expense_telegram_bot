import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from db import init_db, log_expense
from expense_parser import parse_expense
from alerts import check_budget_alerts
from handlers import (
    handle_total,
    handle_summary,
    handle_budget_set,
    handle_undo,
    handle_expenses,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8080))


# ── Command handlers ────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Expense Tracker*\n\n"
        "Log an expense — just type:\n"
        "  `500 lunch`\n"
        "  `1200 groceries big shop`\n"
        "  `1.5k rent`\n\n"
        "*Commands*\n"
        "  /total — this month's total\n"
        "  /summary — breakdown by category\n"
        "  /summary last — last month\n"
        "  /budget 20000 — set monthly budget\n"
        "  /budget food 5000 — set category budget\n"
        "  /expenses — last 10 entries\n"
        "  /expenses food — entries in a category\n"
        "  /undo — remove last entry",
        parse_mode="Markdown",
    )


async def total_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = handle_total(update.effective_user.id)
    await update.message.reply_text(reply, parse_mode="Markdown")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    last = "last" in (context.args or [])
    reply = handle_summary(update.effective_user.id, last_month=last)
    await update.message.reply_text(reply, parse_mode="Markdown")


async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = handle_budget_set(update.effective_user.id, context.args)
    await update.message.reply_text(reply)


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = handle_undo(update.effective_user.id)
    await update.message.reply_text(reply)


async def expenses_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = handle_expenses(update.effective_user.id, context.args)
    await update.message.reply_text(reply, parse_mode="Markdown")


# ── Message handler (expense logging) ───────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    try:
        amount, category, note = parse_expense(text)
    except ValueError:
        await update.message.reply_text(
            "❓ Couldn't parse that.\n"
            "Try: `500 lunch` or `1200 groceries`",
            parse_mode="Markdown",
        )
        return

    log_expense(user_id, amount, category, note)

    reply = f"✅ Logged: ₹{amount:,.0f} — {category}"
    if note:
        reply += f" ({note})"

    alert = check_budget_alerts(user_id)
    if alert:
        reply += f"\n\n{alert}"

    await update.message.reply_text(reply)


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")

    init_db()
    logger.info("Database initialised")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("total", total_command))
    app.add_handler(CommandHandler("summary", summary_command))
    app.add_handler(CommandHandler("budget", budget_command))
    app.add_handler(CommandHandler("undo", undo_command))
    app.add_handler(CommandHandler("expenses", expenses_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    if WEBHOOK_URL:
        # Production — Railway provides a public HTTPS URL
        logger.info(f"Starting webhook on port {PORT}")
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            url_path="/webhook",
        )
    else:
        # Local development — polling, no URL needed
        logger.info("No WEBHOOK_URL set — running in polling mode (local dev)")
        app.run_polling()


if __name__ == "__main__":
    main()
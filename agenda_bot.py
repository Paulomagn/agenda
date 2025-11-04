from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Substitua pelo seu token
TOKEN = "8593565188:AAFc1gvWDk6njaay3cmgOqhCg1oljJaHqv4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envia uma mensagem de boas-vindas e o ID do chat."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"Olá! Eu sou o agendapaulobot. Seu ID de chat é: `{chat_id}`\n"
        "Use este ID para configurar seus alertas na agenda web.",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Envia uma mensagem de ajuda."""
    await update.message.reply_text(
        "Comandos disponíveis:\n"
        "/start - Inicia o bot e mostra seu ID de chat.\n"
        "/help - Mostra esta mensagem de ajuda."
    )

def main():
    """Inicia o bot."""
    # Cria o Application e passa o token do bot
    application = ApplicationBuilder().token(TOKEN).build()

    # Adiciona handlers para comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Inicia o Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

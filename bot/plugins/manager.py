from pyrogram import Client, filters
from pyrogram.types import Message

from bot.utils import scripts
from bot.utils.logger import logger
from bot.utils.emojis import StaticEmoji
from bot.utils.launcher import tg_clients, run_tasks


@Client.on_message(filters.me & filters.chat("me") & filters.command("help", prefixes="/"))
async def send_help(_: Client, message: Message):
    help_text = scripts.get_help_text()

    # Логируем попытку отправки помощи
    logger.info("Received /help command.")
    
    # Проверяем, что message не пустое
    if message and message.text:
        logger.info("Editing message to send help text.")
        await message.edit(text=help_text)
    else:
        logger.error("Message is not provided or is empty for editing.")


@Client.on_message(filters.me & filters.chat("me") & filters.command("tap", prefixes="/"))
@scripts.with_args("<b>This command does not work without arguments\n"
                   "Type <code>/tap on</code> to start or <code>/tap off</code> to stop</b>")
async def launch_tapper(client: Client, message: Message):
    logger.info("Received /tap command.")

    # Проверяем наличие аргументов команды
    flag = scripts.get_command_args(message, "tap")
    logger.info(f"Command flag: {flag}")

    flags_to_start = ["on", "start"]
    flags_to_stop = ["off", "stop"]

    if flag in flags_to_start:
        logger.info(f"The tapper is being launched with the command /tap {flag}")

        if tg_clients:  # Проверяем, что tg_clients определён и не пустой
            logger.info(f"tg_clients found: {len(tg_clients)} clients available.")
            
            if message and message.text:
                logger.info("Editing message to confirm tapper launch.")
                await message.edit(
                    text=f"<b>{StaticEmoji.ACCEPT} Tapper launched! {StaticEmoji.START}</b>"
                )
            else:
                logger.error("Message is not provided or is empty for editing during tapper launch.")

            logger.info("Starting run_tasks...")
            await run_tasks(tg_clients=tg_clients)
        else:
            logger.warning("No tg_clients found to launch tapper.")
            
            if message and message.text:
                logger.info("Editing message to notify that no clients found.")
                await message.edit(
                    text=f"<b>{StaticEmoji.DENY} No active clients found to launch the tapper.</b>"
                )
            else:
                logger.error("Message is not provided or is empty for editing during client check.")

    elif flag in flags_to_stop:
        logger.info(f"Tapper is being stopped with /tap command {flag}")

        await scripts.stop_tasks(client=client)

        if message and message.text:
            logger.info("Editing message to confirm tapper stop.")
            await message.edit(
                text=f"<b>{StaticEmoji.ACCEPT} Tapper stopped! {StaticEmoji.STOP}</b>"
            )
        else:
            logger.error("Message is not provided or is empty for editing during tapper stop.")
    else:
        logger.warning(f"Received an invalid argument: {flag}")
        
        if message and message.text:
            logger.info("Editing message to inform about invalid argument.")
            await message.edit(
                text=f"<b>{StaticEmoji.DENY} This command only accepts the following arguments: on/off | start/stop</b>"
            )
        else:
            logger.error("Message is not provided or is empty for editing during invalid argument.")
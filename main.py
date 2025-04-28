import os
import discord
from discord import app_commands
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

AUTHORIZED_ROLE_ID = 1366100715033858190
CUSTOMER_ROLE_ID = 1366095881912193026

def generate_oauth_link(client_id):
    base_url = "https://discord.com/api/oauth2/authorize"
    redirect_uri = "http://localhost"
    scope = "bot"
    permissions = "8"  # Administrator permission for simplicity, adjust as needed.
    return f"{base_url}?client_id={client_id}&permissions={permissions}&scope={scope}"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents, activity=discord.Activity(type=discord.ActivityType.playing, name="Commands"))
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    logger.info(f'Bot is ready. Logged in as {bot.user}')
    await tree.sync()

@bot.event
async def on_message(message):
    # Log all received messages for debugging
    logger.info(f"Received message: '{message.content}' from {message.author} in {message.guild}")
    logger.info(f"Author roles: {[role.name for role in message.author.roles]}")
    
    # Ignore messages from the bot itself
    if message.author == bot.user:
        logger.info("Ignoring message from self")
        return
    
    # Check if the message starts with .customer or .cus
    if not (message.content.startswith('.customer') or message.content.startswith('.cus')):
        logger.info("Message does not match command pattern")
        return
    
    # Check if the user has the authorized role
    author_roles = [role.id for role in message.author.roles]
    if AUTHORIZED_ROLE_ID not in author_roles:
        logger.warning(f"User {message.author} lacks authorized role {AUTHORIZED_ROLE_ID}")
        await message.reply("❌ You don't have permission to use this command!")
        return
    
    # Check if a user was mentioned
    if not message.mentions:
        logger.info("No user mentioned in command")
        await message.reply("❌ Please mention a user to assign the customer role to!")
        return
    
    target_user = message.mentions[0]
    customer_role = message.guild.get_role(CUSTOMER_ROLE_ID)
    
    if not customer_role:
        logger.error(f"Customer role {CUSTOMER_ROLE_ID} not found in guild")
        await message.reply("❌ Customer role not found! Please check the role ID.")
        return
    
    try:
        await target_user.add_roles(customer_role)
        logger.info(f"Successfully assigned customer role to {target_user}")
        await message.reply(f"✅ Successfully assigned customer role to {target_user.mention}!")
    except discord.Forbidden:
        logger.error("Bot lacks permission to assign roles")
        await message.reply("❌ I don't have permission to assign roles!")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        await message.reply(f"❌ An error occurred: {str(e)}")

async def keep_bot_alive(token):
    while True:
        try:
            # Reconnect if bot is disconnected
            if not bot.is_ready():
                logger.warning("Bot disconnected. Attempting to reconnect...")
                await bot.close()
                await bot.start(token)
        except Exception as e:
            logger.error(f"Error in keep_bot_alive: {e}")
        await asyncio.sleep(300)  # Check every 5 minutes

def main():
    client_id = os.environ.get('CLIENT_ID')
    bot_token = os.environ.get('BOT_TOKEN')
    
    if not client_id and not bot_token:
        logger.error("🚨 Oops! Both CLIENT_ID 🆔 and BOT_TOKEN 🔑 environment variables are missing. 🚨")
        return
    elif not client_id:
        logger.error("🚨 Oops! The CLIENT_ID 🆔 environment variable is missing. 🚨")
        return
    elif not bot_token:
        logger.error("🚨 Oops! The BOT_TOKEN 🔑 environment variable is missing. 🚨")
        return
    
    oauth_link = generate_oauth_link(client_id)
    logger.info(f"🔗 Click this link to invite your Discord bot to your server 👉 {oauth_link}")
    
    # Run the bot with a keep-alive mechanism
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(keep_bot_alive(bot_token))
        bot.run(bot_token)
    except Exception as e:
        logger.error(f"Fatal error running bot: {e}")

if __name__ == "__main__":
    main()

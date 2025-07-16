import discord
from discord.ext import commands
from datetime import datetime

#config
intents = discord.Intents.default().all()
intents.members = True
bot = commands.Bot(command_prefix='+', intents=intents)
bot.remove_command('help')
TOKEN = ''
log_channel_id = int('')


async def send_log(channel, title, description, color, footer, thumbnail_url=None):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=footer)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    await channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(log_channel_id)
    if channel:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        description = f'Участник {member.mention} присоединился к серверу'
        footer = f'ID: {member.id}  •  {current_time}'
        await send_log(channel, 'Участник присоединился', description, discord.Color.green(), footer, member.display_avatar.url)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(log_channel_id)
    if channel:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        description = f'Участник {member.mention} покинул сервер'
        footer = f'ID: {member.id}  •  {current_time}'
        await send_log(channel, 'Участник покинул сервер', description, discord.Color.red(), footer, member.display_avatar.url)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    channel = bot.get_channel(log_channel_id)
    if channel:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        description = (f'Автор: {message.author.mention}\n'
                       f'Канал: {message.channel.mention}\n'
                       f'Содержание: {message.content}')
        footer = f'ID: {message.author.id}  •  {current_time}'
        await send_log(channel, 'Сообщение удалено', description, discord.Color.red(), footer, message.author.display_avatar.url)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return

    channel = bot.get_channel(log_channel_id)
    if channel:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        description = (f'Автор: {before.author.mention}\n'
                       f'Канал: {before.channel.mention}\n'
                       f'Изменено: {before.content}\n'
                       f'На: {after.content}')
        footer = f'ID: {before.author.id}  •  {current_time}'
        await send_log(channel, 'Сообщение изменено', description, discord.Color.gold(), footer, before.author.display_avatar.url)

@bot.event
async def on_member_update(before, after):
    channel = bot.get_channel(log_channel_id)
    if channel:
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles:
                description = f'{after.mention} получил следующие роли:\n' + '\n'.join([f'- {role.mention}' for role in added_roles])
                footer = f'ID: {after.id}  •  {current_time}'
                await send_log(channel, 'Добавлены роли', description, discord.Color.green(), footer, after.display_avatar.url)

            if removed_roles:
                description = f'{after.mention} потерял следующие роли:\n' + '\n'.join([f'- {role.mention}' for role in removed_roles])
                footer = f'ID: {after.id}  •  {current_time}'
                await send_log(channel, 'Удалены роли', description, discord.Color.red(), footer, after.display_avatar.url)

bot.run(TOKEN)

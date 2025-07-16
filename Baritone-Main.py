import asyncio
import discord
from discord.ext import commands
import psutil
import os
import json
import random

# config
intents = discord.Intents.default().all()
intents.members = True
bot = commands.Bot(command_prefix='+', intents=intents)
bot.remove_command('help')
TOKEN = ''
SERVER_ID = int('')
PUNISHMENTS_FILE = 'punishments.json'

# punishments file
def load_punishments():
    if os.path.exists(PUNISHMENTS_FILE):
        with open(PUNISHMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_punishments(data):
    with open(PUNISHMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def is_punishment_expired(end_time):
    return end_time and end_time < asyncio.get_event_loop().time()

async def apply_punishment(member, role_name, action):
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        if action == 'add':
            await member.add_roles(role)
        elif action == 'remove':
            await member.remove_roles(role)

# administrator commands
@bot.command()
@commands.has_role('Baritone Moderator')
async def spam(ctx, count: int, *, message):
    """Отправка сообщения несколько раз в чат."""
    for _ in range(count):
        await ctx.send(message)
    await ctx.message.delete()

@bot.command()
@commands.has_role('Baritone Moderator')
async def mute(ctx, member: discord.Member, duration: int, *, reason: str):
    """Временный мут пользователя."""
    await apply_punishment(member, 'Muted', 'add')
    await ctx.send(embed=discord.Embed(
        description=f'**{member.mention} был замучен на {duration} минут по причине: {reason}.**',
        color=0x00ff12
    ))
    punishments = load_punishments()
    punishments[str(member.id)] = {
        'type': 'mute',
        'reason': reason,
        'end_time': asyncio.get_event_loop().time() + duration * 60
    }
    save_punishments(punishments)

    await asyncio.sleep(duration * 60)
    await apply_punishment(member, 'Muted', 'remove')
    await ctx.send(embed=discord.Embed(
        description=f'**{member.mention} был размучен.**',
        color=0x00ff12
    ))
    punishments.pop(str(member.id), None)
    save_punishments(punishments)

@bot.command()
@commands.has_role('Baritone Moderator')
async def unmute(ctx, member: discord.Member):
    """Размут пользователя."""
    await apply_punishment(member, 'Muted', 'remove')
    await ctx.send(embed=discord.Embed(
        description=f'**{member.mention} был размучен.**',
        color=0x00ff12
    ))
    punishments = load_punishments()
    punishments.pop(str(member.id), None)
    save_punishments(punishments)

@bot.command()
@commands.has_role('Baritone Moderator')
async def clear(ctx, amount: int):
    """Очистка сообщений в чате."""
    await ctx.channel.purge(limit=amount)
    await ctx.send(embed=discord.Embed(
        description=f'**Очищено {amount} сообщений.**',
        color=0x00ff12
    ), delete_after=5)

# бан
@bot.command()
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(embed = discord.Embed(description = f'** {ctx.author.name}, участник {member} был забанен по причине: {reason}.**', color=0x00ff12))
    await ctx.message.delete()

    punishments = load_punishments()
    punishments[str(member.id)] = {
        'type': 'ban',
        'reason': reason
    }
    save_punishments(punishments)

    punishments = load_punishments()
    punishments.pop(str(member.id), None)
    save_punishments(punishments)


# give a random happy image
@bot.command()
async def happyimg(ctx):
    try:
        with open('happyImages.txt', 'r') as file:
            links = [line.strip() for line in file.readlines()]
        if links:
            random_link = random.choice(links)
            embed = discord.Embed(title='Смешные картинки! xD', color=0x00ff12)
            embed.set_image(url=random_link)
            await ctx.send(embed=embed)
        else:
            await ctx.send('Нет доступных ссылок для отображения.')
    except FileNotFoundError:
        await ctx.send('Файл с изображениями не найден.')
    except Exception as e:
        print(f'Ошибка: {e}')

@bot.command()
@commands.has_role('Baritone Moderator')
async def embedSend(ctx, *, title: str, message: str, value: str, channelID: int, color: str):
    channel = bot.get_channel(channelID)
    titleEmbed = title
    valueEmbed = value
    colorEmbed = color
    messageEmbed = message
    embed = discord.Embed(title=titleEmbed, color=colorEmbed)
    embed.add_field(name=messageEmbed, value=valueEmbed, inline=False)
    embed.set_footer(
        text="2025 Senator  •  Баритон"
    )
    await channel.send(embed=embed)
    await ctx.message.delete()

# help
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="List commands", color=discord.Colour.from_rgb(0, 255, 18))
    embed.add_field(name="`+embedSend [title] [message] [подпись] [ID канала] [цвет]`", value='Отправка Embed сообщения от лица Баритона', inline=False)
    embed.add_field(name="`+happyimg`", value='Веселые картинки для заряда позитивом!', inline=False)
    embed.add_field(name="`+spam [кол-во сообщений] [сообщение]`", value="Флуд в чат", inline=False)
    embed.add_field(name="`+spamls [кол-во сообщений] [ID получателя] [сообщение]`", value="Флуд в DM пользователю", inline=False)
    embed.add_field(name="`+mute [пользователь] [время в минутах] [причина]`", value="Замутить пользователя.", inline=False)
    embed.add_field(name="`+unmute [пользователь]`", value="Размутить пользователя.", inline=False)
    embed.add_field(name="`+ban [пользователь] [причина]`", value="Забанить пользователя.", inline=False)
    embed.add_field(name="`+unban [пользователь]`", value="Разбанить пользователя.", inline=False)
    embed.add_field(name="`+kick [пользователь] [причина]`", value="Выгнать пользователя.", inline=False)
    embed.add_field(name="`+clear [количество]`", value="Очистить чат.", inline=False)
    embed.set_author(
        name="Help for Baritone Bot",
        url="https://discord.gg/jDxJmBgP8K",
        icon_url="https://i.imgur.com/tg2vL3K.png",
    )
    embed.set_footer(
        text="2025 Senator",
        icon_url="https://i.imgur.com/tg2vL3K.png",
    )
    embed.set_thumbnail(url="https://i.imgur.com/tg2vL3K.png")
    await ctx.send(embed=embed)
    await ctx.message.delete()

# error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(
            description=f'**{ctx.author.name}, у вас нет доступа к этой команде.**',
            color=0x00ff12
        ))
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(embed=discord.Embed(
            description=f'**{ctx.author.name}, данной команды не существует.**',
            color=0x00ff12
        ))

# start
@bot.event
async def on_ready():
    print('Бот успешно запущен!')

    punishments = load_punishments()
    for user_id, punishment in list(punishments.items()):
        guild = bot.get_guild(SERVER_ID)
        member = guild.get_member(int(user_id))
        if member and is_punishment_expired(punishment.get('end_time')):
            if punishment['type'] == 'mute':
                await apply_punishment(member, 'Muted', 'remove')
                print(f'Размут пользователя {member}.')
            punishments.pop(user_id, None)
    save_punishments(punishments)

bot.run(TOKEN)

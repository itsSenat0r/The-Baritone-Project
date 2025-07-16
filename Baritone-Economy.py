import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
import json
import os

# config
intents = discord.Intents.default().all()
intents.message_content = True
bot = commands.Bot(command_prefix='+', intents=intents)
bot.remove_command('help')
TOKEN = ''
currentDirectory = os.path.dirname(os.path.abspath(__file__))
json_file = os.path.join(currentDirectory, 'economyDataBase.json')
messageIdFile = os.path.join(currentDirectory, 'messageEconomyId.json')

# load files
def load_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json_file(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка записи данных в файл {file_path}: {e}")

# balance functions
def get_user_balance(user_id):
    data = load_json_file(json_file)
    return data.get(str(user_id), 0)

def update_user_balance(user_id, amount):
    data = load_json_file(json_file)
    user_id = str(user_id)
    data[user_id] = data.get(user_id, 0) + amount
    save_json_file(json_file, data)

def deduct_user_balance(user_id, amount):
    data = load_json_file(json_file)
    user_id = str(user_id)
    if data.get(user_id, 0) < amount:
        return False
    data[user_id] -= amount
    save_json_file(json_file, data)
    return True

# handing over candy
class HandingCandyModal(Modal):
    def __init__(self):
        super().__init__(title="Передача конфет")

        self.recipient_id = TextInput(
            label="ID получателя",
            placeholder="Введите ID получателя",
            required=True
        )
        self.add_item(self.recipient_id)

        self.amount = TextInput(
            label="Количество конфет",
            placeholder="Введите количество конфет",
            required=True
        )
        self.add_item(self.amount)

    async def on_submit(self, interaction: discord.Interaction):
        recipient_id = int(self.recipient_id.value)
        amount = int(self.amount.value)

        if deduct_user_balance(interaction.user.id, amount):
            update_user_balance(recipient_id, amount)
            await interaction.response.send_message(f"Вы успешно передали {amount} конфет пользователю с ID {recipient_id}.", ephemeral=True)
        else:
            await interaction.response.send_message("У вас недостаточно конфет для передачи.", ephemeral=True)

# creating a role for candy
async def create_role(guild, user_id, role_name, color):
    try:
        role_color = discord.Color(int(color.lstrip('#'), 16))
        member = await guild.fetch_member(user_id)
        role = await guild.create_role(name=role_name, color=role_color)
        await member.add_roles(role)
        return True
    except Exception as e:
        print(f"Ошибка при создании роли: {e}")
        return False

# buy already created role for candy
class BuyRoleModal(Modal):
    def __init__(self):
        super().__init__(title="Введите параметры покраса")

        self.role_name = TextInput(
            label="Название роли",
            placeholder="Введите название роли",
            required=True
        )
        self.add_item(self.role_name)

        self.role_color = TextInput(
            label="Цвет (Hex-код цвета без #)",
            placeholder="Например: FF5733",
            required=True
        )
        self.add_item(self.role_color)

    async def on_submit(self, interaction: discord.Interaction):
        role_name = self.role_name.value
        role_color = self.role_color.value

        if deduct_user_balance(interaction.user.id, 4000):
            success = await create_role(interaction.guild, interaction.user.id, role_name, role_color)
            if success:
                await interaction.response.send_message(f"Роль '{role_name}' успешно создана и назначена вам!", ephemeral=True)
            else:
                await interaction.response.send_message("Произошла ошибка при создании роли.", ephemeral=True)
        else:
            await interaction.response.send_message("У вас недостаточно конфет для покупки.", ephemeral=True)

# dropdown menu 
class CommandSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Приобрести товар", value="BuyElement"),
            discord.SelectOption(label="Показать баланс", value="Balance"),
            discord.SelectOption(label="Информация", value="Information"),
        ]
        super().__init__(placeholder="Выберите команду", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        command = self.values[0]

        if command == 'BuyElement':
            modal = BuyRoleModal()
            await interaction.response.send_modal(modal)

        elif command == 'Balance':
            balance = get_user_balance(interaction.user.id)
            await interaction.response.send_message(f"Ваш баланс: {balance}CND", ephemeral=True)

        elif command == 'Information':
            await interaction.response.send_message(
                'Добро пожаловать в магазин Баритона. Вот что вы можете сделать:\n'
                '1. Купить покрас за 4000CND.\n'
                '2. Проверить баланс.\n'
                '3. Передать конфеты другому пользователю. \n'
                '\n*CND - денежная единица Баритона.', ephemeral=True)

        elif command == 'PayCandies':
            modal = HandingCandyModal()
            await interaction.response.send_modal(modal)
# control panel
class CommandPanel(View):
    def __init__(self):
        super().__init__()
        self.add_item(CommandSelect())

# spawn control panel
@bot.command()
@commands.has_permissions(administrator=True)
async def shopPanel(ctx):
    try:
        embed = discord.Embed(
            title='Магазин Баритона',
            description="Выберите пункт меню ниже.",
            color=0x00ff12
        )
        view = CommandPanel()
        message = await ctx.send(embed=embed, view=view)
        save_json_file(messageIdFile, {"channel_id": ctx.channel.id, "message_id": message.id})
    except Exception as e:
        print(e)

# load a panel after restart
@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    message_info = load_json_file(messageIdFile)
    if message_info:
        try:
            channel = bot.get_channel(message_info["channel_id"])
            message = await channel.fetch_message(message_info["message_id"])
            view = CommandPanel()
            await message.edit(view=view)
            print("Панель восстановлена.")
        except Exception as e:
            print(f"Ошибка восстановления панели: {e}")

# save user activity
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    update_user_balance(message.author.id, 1)
    await bot.process_commands(message)

bot.run(TOKEN)

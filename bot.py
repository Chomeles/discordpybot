import discord
from discord.ext import commands, tasks
import aiosqlite
import random
import time
import math
import os

ACTION_LIMIT = 10
DAILY_REWARD_INTERVAL = 86400  # 24 Stunden in Sekunden
JAIL_TIME = 3  # Gefängniszeit in Stunden
LOTTERY_JACKPOT_RESET = 50
LOTTERY_JACKPOT_MULTIPLIER = 1.7

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)

async def ensure_db_structure():
    async with aiosqlite.connect('game.db') as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS players (
                                id INTEGER PRIMARY KEY,
                                balance INTEGER DEFAULT 100,
                                actions INTEGER DEFAULT 0,
                                last_action REAL DEFAULT 0,
                                jailed INTEGER DEFAULT 0,
                                jail_time REAL DEFAULT 0,
                                last_daily REAL DEFAULT 0,
                                level INTEGER DEFAULT 1,
                                xp INTEGER DEFAULT 0
                            )''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS lottery (
                                id INTEGER PRIMARY KEY,
                                jackpot REAL DEFAULT 50
                            )''')
        await conn.commit()

async def load_player(user_id):
    async with aiosqlite.connect('game.db') as conn:
        async with conn.execute("SELECT * FROM players WHERE id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "balance": row[1],
                    "actions": row[2],
                    "last_action": row[3],
                    "jailed": row[4],
                    "jail_time": row[5],
                    "last_daily": row[6],
                    "level": row[7],
                    "xp": row[8]
                }
            return None

async def save_player(user_id, player_data):
    async with aiosqlite.connect('game.db') as conn:
        await conn.execute('''REPLACE INTO players (id, balance, actions, last_action, jailed, jail_time, last_daily, level, xp)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (user_id, player_data['balance'], player_data['actions'], player_data['last_action'], 
                           player_data['jailed'], player_data['jail_time'], player_data['last_daily'], 
                           player_data['level'], player_data['xp']))
        await conn.commit()

async def get_lottery_jackpot():
    async with aiosqlite.connect('game.db') as conn:
        async with conn.execute("SELECT jackpot FROM lottery WHERE id=1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else LOTTERY_JACKPOT_RESET

async def update_lottery_jackpot(new_jackpot):
    async with aiosqlite.connect('game.db') as conn:
        await conn.execute("REPLACE INTO lottery (id, jackpot) VALUES (1, ?)", (new_jackpot,))
        await conn.commit()

def check_jail(user_data):
    if user_data['jailed'] > 0:
        time_passed = time.time() - user_data['jail_time']
        rounds_passed = int(time_passed // 3600)
        if rounds_passed > 0:
            user_data['jailed'] = max(0, user_data['jailed'] - rounds_passed)

def calculate_xp_to_level(level):
    return math.ceil(100 * (1.5 ** (level - 1)))

@bot.command()
async def join(ctx):
    user_id = ctx.author.id
    player_data = await load_player(user_id)
    if not player_data:
        player_data = {
            "balance": 100, "actions": 0, "last_action": 0, "jailed": 0,
            "jail_time": 0, "last_daily": 0, "level": 1, "xp": 0
        }
        await save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention} hat dem Spiel erfolgreich beigetreten! Dein Startguthaben beträgt 100.")
    else:
        await ctx.send(f"{ctx.author.mention} du bist bereits im Spiel!")

@bot.command()
async def work(ctx):
    user_id = ctx.author.id
    player_data = await load_player(user_id)
    if player_data:
        check_jail(player_data)
        if player_data['jailed'] > 0:
            await ctx.send(f"{ctx.author.mention} du bist im Gefängnis und kannst nicht arbeiten! Du musst noch {player_data['jailed']} Runde(n) warten.")
            return

        if player_data['actions'] >= ACTION_LIMIT:
            await ctx.send(f"{ctx.author.mention} du hast das stündliche Aktionslimit erreicht. Warte eine Stunde.")
            return

        level = player_data['level']
        earned = random.randint(10, 20) * level
        player_data['balance'] += earned
        player_data['actions'] += 1
        player_data['last_action'] = time.time()
        await save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention} du hast gearbeitet und {earned} verdient! Dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.command()
async def steal(ctx, target: discord.Member = None):
    user_id = ctx.author.id
    if target is None:
        await ctx.send(f"{ctx.author.mention} du musst angeben, von wem du stehlen möchtest. Benutze `!steal @Benutzer`.")
        return

    target_id = target.id
    player_data = await load_player(user_id)
    target_data = await load_player(target_id)
    if player_data and target_data:
        check_jail(player_data)
        if player_data['jailed'] > 0:
            await ctx.send(f"{ctx.author.mention} du bist im Gefängnis und kannst nicht stehlen! Du musst noch {player_data['jailed']} Runde(n) warten.")
            return

        if player_data['actions'] >= ACTION_LIMIT:
            await ctx.send(f"{ctx.author.mention} du hast das stündliche Aktionslimit erreicht. Warte eine Stunde.")
            return

        if random.random() < 0.5:
            stolen_amount = random.randint(10, 30)
            if target_data['balance'] < stolen_amount:
                stolen_amount = target_data['balance']

            target_data['balance'] -= stolen_amount
            player_data['balance'] += stolen_amount
            await ctx.send(f"{ctx.author.mention} hat erfolgreich {stolen_amount} von {target.mention} gestohlen!")
        else:
            lost_amount = random.randint(10, 20)
            player_data['balance'] -= lost_amount
            player_data['jailed'] = JAIL_TIME
            player_data['jail_time'] = time.time()
            await ctx.send(f"{ctx.author.mention} wurde beim Stehlen erwischt und hat {lost_amount} verloren! Du bist für {JAIL_TIME} Runden (Stunden) im Gefängnis.")

        player_data['actions'] += 1
        player_data['last_action'] = time.time()
        await save_player(user_id, player_data)
        await save_player(target_id, target_data)

@bot.command()
async def wheel(ctx, bet: int):
    user_id = ctx.author.id
    player_data = await load_player(user_id)
    if player_data:
        check_jail(player_data)
        if player_data['jailed'] > 0:
            await ctx.send(f"{ctx.author.mention} du bist im Gefängnis und kannst das Glücksrad nicht drehen! Du musst noch {player_data['jailed']} Runde(n) warten.")
            return

        if player_data['actions'] >= ACTION_LIMIT:
            await ctx.send(f"{ctx.author.mention} du hast das stündliche Aktionslimit erreicht. Warte eine Stunde.")
            return

        if bet > player_data['balance']:
            await ctx.send(f"{ctx.author.mention}, du hast nicht genug Guthaben für diesen Einsatz! Dein aktuelles Guthaben beträgt {player_data['balance']}.")
            return

        wheel_outcomes = [
            (0, "Niete"),              # 40% Chance
            (bet * 0.5, "0.5x Einsatz"),  # 20% Chance
            (bet, "1x Einsatz"),       # 15% Chance
            (bet * 2, "2x Einsatz"),   # 10% Chance
            (bet * 5, "5x Einsatz"),   # 8% Chance
            (bet * 10, "10x Einsatz"), # 5% Chance
            (bet * 50, "50x Einsatz")  # 2% Chance
        ]

        outcome, description = random.choices(
            wheel_outcomes, 
            weights=[40, 20, 15, 10, 8, 5, 2], 
            k=1
        )[0]

        player_data['balance'] += outcome - bet
        player_data['actions'] += 1
        player_data['last_action'] = time.time()
        await save_player(user_id, player_data)

        if outcome == 0:
            await ctx.send(f"{ctx.author.mention}, du hast leider nichts gewonnen und deinen Einsatz von {bet} verloren! Dein aktuelles Guthaben beträgt {player_data['balance']}.")
        else:
            await ctx.send(f"{ctx.author.mention}, du hast das Glücksrad gedreht und {description} gewonnen! Dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    player_data = await load_player(user_id)
    if player_data:
        current_time = time.time()
        if current_time - player_data['last_daily'] < DAILY_REWARD_INTERVAL:
            await ctx.send(f"{ctx.author.mention} du hast deine tägliche Belohnung bereits erhalten. Bitte warte 24 Stunden.")
            return

        player_data['balance'] += 10
        player_data['last_daily'] = current_time
        await save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention} hat die tägliche Belohnung von 10 erhalten! Dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.command()
async def levelup(ctx):
    user_id = ctx.author.id
    player_data = await load_player(user_id)
    if player_data:
        if player_data['actions'] >= ACTION_LIMIT:
            await ctx.send(f"{ctx.author.mention} du hast das stündliche Aktionslimit erreicht. Warte eine Stunde.")
            return

        xp_gained = random.randint(5, 15)
        player_data['xp'] += xp_gained

        xp_to_level = calculate_xp_to_level(player_data['level'])

        if player_data['xp'] >= xp_to_level:
            player_data['level'] += 1
            player_data['xp'] -= xp_to_level
            await ctx.send(f"{ctx.author.mention} hat ein neues Level erreicht! Du bist jetzt Level {player_data['level']}.")

        player_data['actions'] += 1
        await save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention} hat {xp_gained} XP durch das Lernen erhalten. Dein aktuelles Level ist {player_data['level']}, mit {player_data['xp']} XP. Du benötigst {calculate_xp_to_level(player_data['level'])} XP, um das nächste Level zu erreichen.")

@bot.command(aliases=['bal'])
async def balance(ctx):
    user_id = ctx.author.id
    player_data = await load_player(user_id)
    if player_data:
        await ctx.send(f"{ctx.author.mention}, dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.command()
async def level(ctx):
    user_id = ctx.author.id
    player_data = await load_player(user_id)
    if player_data:
        xp_to_level = calculate_xp_to_level(player_data['level'])
        await ctx.send(f"{ctx.author.mention}, dein aktuelles Level ist {player_data['level']} mit {player_data['xp']} XP. Du benötigst {xp_to_level} XP, um das nächste Level zu erreichen.")

@bot.command(name="commands")
async def commands_command(ctx):
    help_text = """
    **Verfügbare Befehle:**

    `!join` - Tritt dem Spiel bei.
    `!work` - Arbeite, um Geld zu verdienen.
    `!steal @Benutzer` - Versuche, von einem anderen Spieler zu stehlen.
    `!wheel <Einsatz>` - Drehe das Glücksrad mit einem Einsatz für eine Chance auf einen Gewinn.
    `!daily` - Erhalte deine tägliche Belohnung (einmal alle 24 Stunden).
    `!balance` oder `!bal` - Zeigt dein aktuelles Guthaben an.
    `!levelup` - Lerne, um XP zu verdienen und im Level aufzusteigen.
    `!level` - Zeigt dein aktuelles Level und deine XP an.
    """
    await ctx.send(help_text)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"{ctx.author.mention}, es fehlt ein erforderliches Argument. Überprüfe den Befehl und versuche es erneut.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{ctx.author.mention}, dieser Befehl existiert nicht. Verwende `!commands`, um eine Liste der verfügbaren Befehle zu sehen.")
    else:
        await ctx.send(f"{ctx.author.mention}, ein Fehler ist aufgetreten: {error}")

@tasks.loop(hours=6)
async def lottery_event():
    async with aiosqlite.connect('game.db') as conn:
        async with conn.execute("SELECT id FROM players") as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]
    
    if user_ids:
        jackpot = await get_lottery_jackpot()
        winner_id = random.choice(user_ids) if random.random() <= 0.18 else None

        if winner_id:
            player_data = await load_player(winner_id)
            if player_data:
                player_data['balance'] += jackpot
                await save_player(winner_id, player_data)
                user = bot.get_user(winner_id)
                if user:
                    await user.send(f"Glückwunsch {user.mention}! Du hast die Lotterie gewonnen und {jackpot} erhalten. Dein neues Guthaben beträgt {player_data['balance']}.")
            await update_lottery_jackpot(LOTTERY_JACKPOT_RESET)  # Reset the jackpot to 50
        else:
            new_jackpot = jackpot * LOTTERY_JACKPOT_MULTIPLIER
            await update_lottery_jackpot(new_jackpot)
            await bot.get_channel(your_channel_id_here).send(f"Leider hat niemand die Lotterie gewonnen. Der Jackpot steigt auf {new_jackpot:.2f} für das nächste Event!")

@tasks.loop(minutes=random.randint(5, 60))
async def random_rewards():
    async with aiosqlite.connect('game.db') as conn:
        async with conn.execute("SELECT id FROM players") as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]
    if user_ids:
        user_id = random.choice(user_ids)
        reward = random.randint(14, 26)
        player_data = await load_player(user_id)
        if player_data:
            player_data['balance'] += reward
            await save_player(user_id, player_data)
            user = bot.get_user(user_id)
            if user:
                await user.send(f"Du hast zufällig eine Belohnung von {reward} erhalten! Dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.event
async def on_ready():
    await ensure_db_structure()
    random_rewards.start()
    lottery_event.start()
    print(f'Bot ist bereit und eingeloggt als {bot.user}')

bot.run(os.getenv('DISCORD_TOKEN'))

import discord
from discord.ext import commands, tasks
import random
import time
import math
import general
import databank
import aiosqlite

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None, case_insensitive=True)

@bot.command()
async def join(ctx):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    if not player_data:
        player_data = {
            "balance": 100, "actions": [], "jailed": 0, "jail_time": 0, 
            "last_daily": 0, "level": 1, "xp": 0, "job": None, "last_job_change": 0
        }
        await databank.save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention} hat dem Spiel erfolgreich beigetreten! Dein Startguthaben beträgt 100.")
    else:
        await ctx.send(f"{ctx.author.mention} du bist bereits im Spiel!")

@bot.command()
async def work(ctx):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    
    if player_data:
        general.check_jail(player_data)
        if player_data['jailed'] > 0:
            await ctx.send(f"{ctx.author.mention}, du bist im Gefängnis und kannst nicht arbeiten! Du musst noch {player_data['jailed']} Runde(n) warten.")
            return

        if not await general.check_action_limit(ctx, player_data, 1):
            return

        cost = 1  # Cost for work action before level 10
        earnings = 0
        base_earnings = 10 * (2 ** (player_data['level'] - 1))  # Exponentiell steigender Grundverdienst basierend auf dem Level

        if player_data['level'] >= 10:
            job = player_data['job'] if player_data['job'] else "Banker"  # Standardjob ist Banker, wenn keiner gewählt wurde
            job_info = JOBS[job]
            cost = job_info["cost"]

            if not await general.check_action_limit(ctx, player_data, cost):
                return

            if job == "Investor":
                if random.random() < job_info["loss_chance"]:
                    earnings = -base_earnings * job_info["max_loss_multiplier"]
                else:
                    earnings = base_earnings * job_info["win_multiplier"]
            elif job == "Selbstständiger":
                option = random.choices(job_info["earnings"], weights=[e["chance"] for e in job_info["earnings"]], k=1)[0]
                earnings = base_earnings * option["multiplier"]
            else:
                earnings = base_earnings * job_info["multiplier"]
                if job_info.get("bonus_chance") and random.random() < job_info["bonus_chance"]:
                    earnings += earnings * job_info["bonus_multiplier"]
        else:
            earnings = base_earnings  # Earnings without job multiplier for levels < 10

        player_data['balance'] += earnings
        player_data['actions'].extend([time.time()] * cost)
        await databank.save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention}, du hast gearbeitet und insgesamt {earnings:.2f} verdient! Dein aktuelles Guthaben beträgt {player_data['balance']:.2f}.")


@bot.command()
async def bail(ctx):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    
    if player_data:
        general.check_jail(player_data)
        if player_data['jailed'] > 0 and player_data['balance'] >= 1500:
            player_data['balance'] -= 1500
            player_data['jailed']  = 0
            player_data['jail_time'] = 0
            await ctx.send(f"{ctx.author.mention} du hast dich aus dem Gefängnis freigekauft! Deine jail time beträgt jetzt {player_data['jailed']}")
            await databank.save_player(user_id, player_data)
            return
        else:
            await ctx.send(f"{ctx.author.mention} du bist nicht im Gefängnis und kannst dich auch nicht freikaufen. Das ist doch irgendwie klar du IDIOT!!! Ganz ehrlich, wie kann man so DUMM sein?")
            return

@bot.command()
async def gift(ctx, ammount: int, target: discord.Member = None):
    user_id = ctx.author.id
    if target is None or target.id == user_id:
        await ctx.send(f"{ctx.author.mention} du musst einen anderen Spieler angeben, dem du Geld schicken möchtest.")
        return

    target_id = target.id
    player_data = await databank.load_player(user_id)
    target_data = await databank.load_player(target_id)
    
    if player_data and target_data:
        general.check_jail(player_data)
        if player_data['jailed'] > 0:
            await ctx.send(f"{ctx.author.mention} du bist im Gefängnis und kannst nichts verschenken! Du musst noch {player_data['jailed']} Runde(n) warten.")
            return
    if player_data['balance'] >= ammount: 
        target_data['balance'] += ammount
        player_data['balance'] -= ammount 
        await databank.save_player(target_id, target_data)
        await databank.save_player(user_id, player_data)
        return

@bot.command()
async def steal(ctx, target: discord.Member = None):
    user_id = ctx.author.id
    if target is None or target.id == user_id:
        await ctx.send(f"{ctx.author.mention} du musst einen anderen Spieler angeben, von dem du stehlen möchtest. Benutze !steal @Benutzer.")
        return

    target_id = target.id
    player_data = await databank.load_player(user_id)
    target_data = await databank.load_player(target_id)
    
    if player_data and target_data:
        general.check_jail(player_data)
        if player_data['jailed'] > 0:
            await ctx.send(f"{ctx.author.mention} du bist im Gefängnis und kannst nicht stehlen! Du musst noch {player_data['jailed']} Runde(n) warten.")
            return

        job = player_data['job'] if player_data['job'] else "Dieb"  # Standardjob ist Dieb, wenn keiner gewählt wurde
        job_info = general.JOBS[job]
        cost = job_info["cost"]

        if not await general.check_action_limit(ctx, player_data, cost):
            return

        if random.random() < job_info["jail_chance"]:
            lost_amount = random.randint(10, 20)
            player_data['balance'] -= lost_amount
            player_data['jailed'] = JAIL_TIME
            player_data['jail_time'] = time.time()
            await ctx.send(f"{ctx.author.mention} wurde beim Stehlen erwischt und hat {lost_amount} verloren! Du bist für {JAIL_TIME} Runden (Stunden) im Gefängnis.")
        else:
            stolen_amount = random.randint(10, 30)
            if target_data['balance'] < stolen_amount:
                stolen_amount = target_data['balance']

            target_data['balance'] -= stolen_amount
            player_data['balance'] += stolen_amount
            await ctx.send(f"{ctx.author.mention} hat erfolgreich {stolen_amount} von {target.mention} gestohlen!")

        player_data['actions'].extend([time.time()] * cost)
        await databank.save_player(user_id, player_data)
        await databank.save_player(target_id, target_data)

@bot.command()
async def wheel(ctx, bet: int):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    
    if player_data:
        general.check_jail(player_data)
        if player_data['jailed'] > 0:
            await ctx.send(f"{ctx.author.mention} du bist im Gefängnis und kannst das Glücksrad nicht drehen! Du musst noch {player_data['jailed']} Runde(n) warten.")
            return

        if not await general.check_action_limit(ctx, player_data, 1):  # Cost is 1 action point
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
        player_data['actions'].append(time.time())
        await databank.save_player(user_id, player_data)

        if outcome == 0:
            await ctx.send(f"{ctx.author.mention}, du hast leider nichts gewonnen und deinen Einsatz von {bet} verloren! Dein aktuelles Guthaben beträgt {player_data['balance']}.")
        else:
            await ctx.send(f"{ctx.author.mention}, du hast das Glücksrad gedreht und {description} gewonnen! Dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.command()
async def daily(ctx):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    if player_data:
        current_time = time.time()
        if current_time - player_data['last_daily'] < DAILY_REWARD_INTERVAL:
            await ctx.send(f"{ctx.author.mention} du hast deine tägliche Belohnung bereits erhalten. Bitte warte 24 Stunden.")
            return

        if not await general.check_action_limit(ctx, player_data, 1):
            return

        player_data['balance'] += 10
        player_data['last_daily'] = current_time
        player_data['actions'].append(time.time())
        await databank.save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention} hat die tägliche Belohnung von 10 erhalten! Dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.command()
async def levelup(ctx):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    if player_data:
        if not await general.check_action_limit(ctx, player_data, 1):
            return

        xp_gained = random.randint(15, 65)
        player_data['xp'] += xp_gained

        xp_to_level = general.calculate_xp_to_level(player_data['level'])

        if player_data['xp'] >= xp_to_level:
            player_data['level'] += 1
            player_data['xp'] -= xp_to_level
            await ctx.send(f"{ctx.author.mention} hat ein neues Level erreicht! Du bist jetzt Level {player_data['level']}.")

        player_data['actions'].append(time.time())
        await databank.save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention} hat {xp_gained} XP durch das Lernen erhalten. Dein aktuelles Level ist {player_data['level']}, mit {player_data['xp']} XP. Du benötigst {general.calculate_xp_to_level(player_data['level'])} XP, um das nächste Level zu erreichen.")

@bot.command(aliases=['bal'])
async def balance(ctx):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    if player_data:
        await ctx.send(f"{ctx.author.mention}, dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.command()
async def level(ctx):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    if player_data:
        xp_to_level = general.calculate_xp_to_level(player_data['level'])
        await ctx.send(f"{ctx.author.mention}, dein aktuelles Level ist {player_data['level']} mit {player_data['xp']} XP. Du benötigst {xp_to_level} XP, um das nächste Level zu erreichen.")

@bot.command()
async def jobs(ctx):
    job_list = "**Verfügbare Jobs:**\n"
    for job_name, job_info in JOBS.items():
        job_list += f"**{job_name}:**\n"
        job_list += f" - Kostet {job_info['cost']} Aktionspunkte pro Arbeit.\n"
        job_list += f" - Einkommen-Multiplikator: {job_info.get('multiplier', 'Varies')}x.\n"
        job_list += f" - Jail-Chance: {int(job_info.get('jail_chance', 0) * 100)}%.\n"
        if job_name == "Investor":
            job_list += f"Chance auf Verlust: {int(job_info['loss_chance'] * 100)}%. "
            job_list += f"Maximaler Verlust: {int(job_info['max_loss_multiplier'] * 100)}%. "
            job_list += f"Gewinn-Multiplikator: {job_info['win_multiplier']}.\n"
        elif job_name == "Selbstständiger":
            job_list += "Einkommens-Optionen:\n"
            for option in job_info["earnings"]:
                job_list += f" - {int(option['chance'] * 100)}% Chance auf {option['multiplier']}x Einkommen.\n"
        elif job_name == "Händler":
            job_list += f"Bonus-Chance: {int(job_info['bonus_chance'] * 100)}%. "
            job_list += f"Bonus-Multiplikator: {job_info['bonus_multiplier']}.\n"
        job_list += "\n"
    
    await ctx.send(job_list)

@bot.command()
async def getjob(ctx, job_name: str):
    user_id = ctx.author.id
    player_data = await databank.load_player(user_id)
    if player_data:
        if player_data['level'] < 10:
            await ctx.send(f"{ctx.author.mention}, du musst Level 10 erreichen, bevor du einen Job wählen kannst.")
            return

        if job_name not in JOBS:
            await ctx.send(f"{ctx.author.mention}, dieser Job existiert nicht.")
            return

        current_time = time.time()
        if current_time - player_data['last_job_change'] < DAILY_REWARD_INTERVAL:
            await ctx.send(f"{ctx.author.mention}, du kannst deinen Job erst in 24 Stunden wieder wechseln.")
            return

        player_data['job'] = job_name
        player_data['last_job_change'] = current_time
        await databank.save_player(user_id, player_data)
        await ctx.send(f"{ctx.author.mention}, du hast jetzt den Job **{job_name}**. Du kannst diesen Job erst in 24 Stunden wieder wechseln.")

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
    `!gift <amount> @Benutzer` - sende einem Spieler Geld.
    `!levelup` - Lerne, um XP zu verdienen und im Level aufzusteigen.
    `!level` - Zeigt dein aktuelles Level und deine XP an.
    `!jobs` - Zeigt eine Liste der verfügbaren Jobs an.
    `!getjob <Jobname>` - Wähle einen Job, den du haben möchtest.
    `!bail` - Kauf dich aus dem Gefängnis für 1500
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
    async with aiosqlite.connect('../game.db') as conn:
        async with conn.execute("SELECT id FROM players") as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]
    
    if user_ids:
        jackpot = await databank.get_lottery_jackpot()
        winner_id = random.choice(user_ids) if random.random() <= 0.18 else None

        if winner_id:
            player_data = await databank.load_player(winner_id)
            if player_data:
                player_data['balance'] += jackpot
                await databank.save_player(winner_id, player_data)
                user = bot.get_user(winner_id)
                if user:
                    await user.send(f"Glückwunsch {user.mention}! Du hast die Lotterie gewonnen und {jackpot} erhalten. Dein neues Guthaben beträgt {player_data['balance']}.")
            await databank.update_lottery_jackpot(general.LOTTERY_JACKPOT_RESET)  # Reset the jackpot to 50
        else:
            new_jackpot = jackpot * general.LOTTERY_JACKPOT_MULTIPLIER
            await databank.update_lottery_jackpot(new_jackpot)
            await bot.get_channel(1275206295280029771).send(f"Leider hat niemand die Lotterie gewonnen. Der Jackpot steigt auf {new_jackpot:.2f} für das nächste Event!")   # channel id needs to be changed TODO

@tasks.loop(minutes=random.randint(5, 60))
async def random_rewards():
    async with aiosqlite.connect('../game.db') as conn:
        async with conn.execute("SELECT id FROM players") as cursor:
            user_ids = [row[0] for row in await cursor.fetchall()]
    if user_ids:
        user_id = random.choice(user_ids)
        reward = random.randint(14, 26)
        player_data = await databank.load_player(user_id)
        if player_data:
            player_data['balance'] += reward
            await databank.save_player(user_id, player_data)
            user = bot.get_user(user_id)
            if user:
                await user.send(f"Du hast zufällig eine Belohnung von {reward} erhalten! Dein aktuelles Guthaben beträgt {player_data['balance']}.")

@bot.event
async def on_ready():
    await databank.ensure_db_structure()
    random_rewards.start()
    lottery_event.start()
    print(f'Bot ist bereit und eingeloggt als {bot.user}')
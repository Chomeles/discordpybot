import math
import time

ACTION_LIMIT = 12
DAILY_REWARD_INTERVAL = 86400  # 24 Stunden in Sekunden
JAIL_TIME = 2  # Gefängniszeit in Stunden
LOTTERY_JACKPOT_RESET = 50
LOTTERY_JACKPOT_MULTIPLIER = 1.7
COOLDOWN_DURATION = 3600  # 1 Stunde in Sekunden

JOBS = {
    "Banker": {
        "cost": 2,
        "multiplier": 2,
        "jail_chance": 0
    },
    "Dieb": {
        "cost": 1,
        "multiplier": 2,
        "jail_chance": 0.3
    },
    "Investor": {
        "cost": 3,
        "multiplier": 5,
        "jail_chance": 0,
        "loss_chance": 0.4,  # 40% Chance auf Verlust
        "max_loss_multiplier": 0.5,  # Maximaler Verlust bis zu 50% des Einkommens
        "win_multiplier": 2.0  # Wenn gewonnen, wird der Gewinn verdoppelt
    },
    "Selbstständiger": {
        "cost": 1,
        "jail_chance": 0.05,
        "earnings": [
            {"chance": 0.4, "multiplier": 0.5},  # 40% Chance auf halbes Einkommen
            {"chance": 0.4, "multiplier": 1.0},  # 40% Chance auf normales Einkommen
            {"chance": 0.15, "multiplier": 2.0},  # 15% Chance auf doppeltes Einkommen
            {"chance": 0.05, "multiplier": 5.0}  # 5% Chance auf sehr hohes Einkommen
        ]
    },
    "Händler": {
        "cost": 2,
        "multiplier": 1.8,
        "jail_chance": 0,
        "bonus_chance": 0.2,
        "bonus_multiplier": 1.5  # 20% Chance auf 50% zusätzlichen Gewinn
    }
}


def check_jail(user_data):
    if user_data['jailed'] > 0:
        time_passed = time.time() - user_data['jail_time']
        rounds_passed = int(time_passed // 3600)
        if rounds_passed > 0:
            user_data['jailed'] = max(0, user_data['jailed'] - rounds_passed)

def calculate_xp_to_level(level):
    return math.ceil(100 * (1.65 ** (level - 1)))

async def check_action_limit(ctx, player_data, cost):
    current_time = time.time()
    player_data['actions'] = [ts for ts in player_data['actions'] if current_time - ts < COOLDOWN_DURATION]

    if len(player_data['actions']) + cost > ACTION_LIMIT:
        earliest_reset_time = player_data['actions'][0] + COOLDOWN_DURATION
        remaining_time = earliest_reset_time - current_time
        minutes_left = int(remaining_time // 60)
        seconds_left = int(remaining_time % 60)
        await ctx.send(f"{ctx.author.mention}, du hast das Limit von {ACTION_LIMIT} Aktionen erreicht. Warte noch {minutes_left} Minuten und {seconds_left} Sekunden.")
        return False

    return True

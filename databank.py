import aiosqlite

async def ensure_db_structure():
    async with aiosqlite.connect('../game.db') as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS players (
                                id INTEGER PRIMARY KEY,
                                balance INTEGER DEFAULT 100,
                                actions TEXT DEFAULT '[]',
                                jailed INTEGER DEFAULT 0,
                                jail_time REAL DEFAULT 0,
                                last_daily REAL DEFAULT 0,
                                level INTEGER DEFAULT 1,
                                xp INTEGER DEFAULT 0,
                                job TEXT DEFAULT NULL,
                                last_job_change REAL DEFAULT 0
                            )''')
        await conn.execute('''CREATE TABLE IF NOT EXISTS lottery (
                                id INTEGER PRIMARY KEY,
                                jackpot REAL DEFAULT 50
                            )''')
        await conn.commit()

async def load_player(user_id):
    async with aiosqlite.connect('../game.db') as conn:
        async with conn.execute("SELECT * FROM players WHERE id=?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "balance": row[1],
                    "actions": eval(row[2]),
                    "jailed": row[3],
                    "jail_time": row[4],
                    "last_daily": row[5],
                    "level": row[6],
                    "xp": row[7],
                    "job": row[8],
                    "last_job_change": row[9]
                }
            return None

async def save_player(user_id, player_data):
    async with aiosqlite.connect('../game.db') as conn:
        await conn.execute('''REPLACE INTO players (id, balance, actions, jailed, jail_time, last_daily, level, xp, job, last_job_change)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (user_id, player_data['balance'], str(player_data['actions']), player_data['jailed'], 
                           player_data['jail_time'], player_data['last_daily'], player_data['level'], player_data['xp'], 
                           player_data['job'], player_data['last_job_change']))
        await conn.commit()

async def get_lottery_jackpot():
    async with aiosqlite.connect('../game.db') as conn:
        async with conn.execute("SELECT jackpot FROM lottery WHERE id=1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else LOTTERY_JACKPOT_RESET

async def update_lottery_jackpot(new_jackpot):
    async with aiosqlite.connect('../game.db') as conn:
        await conn.execute("REPLACE INTO lottery (id, jackpot) VALUES (1, ?)", (new_jackpot,))
        await conn.commit()

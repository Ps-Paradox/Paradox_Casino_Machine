import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
import os
import sqlite3
import json
from flask import Flask, request, jsonify
import threading
import logging
import time
import math
import requests  # For making API requests
import html      # For decoding HTML entities
import aiohttp

bot_start_time = datetime.utcnow()

# --- Constants ---

# General Constants
MAX_LINES = 3
MAX_BET = 1000
MIN_BET = 10
DAILY_REWARD = 500
JACKPOT_SYMBOL = '7️⃣'
JACKPOT_MULTIPLIER = 5
STARTING_BALANCE = 7000
LOTTERY_TICKET_PRICE = 50
TOURNAMENT_ENTRY_FEE = 500
BANK_INTEREST_RATE = 0.02  # 2% daily interest

# Slot Machine Constants
SLOTS = ['🍒', '🍋', '🍇', '🔔', '💎', '7️⃣']
WIN_MESSAGES = [
    "You're on a hot streak! 🔥", "Luck is on your side! 🍀", "Money in the bank! 💰",
    "Winner takes all! 🍗", "Defying the odds! ✨", "Jackpot dreams come true! ⚡",
    "Fortune favors the bold! 🌟"
]
LOSS_MESSAGES = [
    "Next time’s the charm! 🎲", "So close yet so far! 📏", "The house edges out! 🤔",
    "Paradox strikes again! 😤", "Keep spinning! ✨", "Break the streak! 🔄"
]

# Roulette Constants
RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
GREEN_NUMBERS = [0]
ROULETTE_BETS = {
    "number": {"payout": 35, "validator": lambda x: x.isdigit() and 0 <= int(x) <= 36},
    "color": {"payout": 1, "validator": lambda x: x.lower() in ["red", "black"]},
    "parity": {"payout": 1, "validator": lambda x: x.lower() in ["even", "odd"]},
    "range": {"payout": 1, "validator": lambda x: x.lower() in ["high", "low"]},
    "dozen": {"payout": 2, "validator": lambda x: x.lower() in ["first", "second", "third"]},
    "column": {"payout": 2, "validator": lambda x: x.isdigit() and 1 <= int(x) <= 3}
}

# Poker Constants
CARD_SUITS = ['♠', '♣', '♥', '♦']
CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
POKER_PAYOUTS = {
    "royal_flush": 250,
    "straight_flush": 50,
    "four_of_a_kind": 25,
    "full_house": 9,
    "flush": 6,
    "straight": 4,
    "three_of_a_kind": 3,
    "two_pair": 2,
    "pair": 1,
    "high_card": 0
}

# Blackjack Constants
BLACKJACK_PAYOUT = 1.5
DECK = [f"{rank}{suit}" for suit in CARD_SUITS for rank in CARD_RANKS] * 4

# Wheel of Fortune Constants
WHEEL_PRIZES = [0, 50, 100, 200, 500, 1000, "Jackpot"]

# Scratch Card Constants
SCRATCH_PRIZES = [0, 10, 25, 50, 100, 500]
SCRATCH_PRICE = 20

# Bingo Constants
BINGO_NUMBERS = list(range(1, 76))
BINGO_CARD_SIZE = 5

# Economy Constants
SHOP_ITEMS = {
    "profile_bg1": {"name": "Cosmic Background", "description": "A starry night sky", "price": 1000},
    "profile_bg2": {"name": "Golden Vault", "description": "Shimmering gold backdrop", "price": 1000},
    "title_gambler": {"name": "Gambler", "description": "For risk-takers", "price": 500},
    "title_highroller": {"name": "High Roller", "description": "For big spenders", "price": 750},
    "daily_boost": {"name": "Daily Boost", "description": "Doubles daily reward for 24h", "price": 200},
    "xp_boost": {"name": "XP Boost", "description": "Doubles XP gain for 24h", "price": 300},
    "loan_pass": {"name": "Loan Pass", "description": "Allows taking a loan", "price": 100},
    "tournament_ticket": {"name": "Tournament Ticket", "description": "Entry to a tournament", "price": 500},
    "crafting_kit": {"name": "Crafting Kit", "description": "Unlocks crafting recipes", "price": 800}
}

CRAFTING_RECIPES = {
    "lucky_charm": {
        "ingredients": {"gold_coin": 5, "four_leaf_clover": 1},
        "description": "Increases win chance by 5% for 1 hour",
        "duration": "1h"
    },
    "mega_jackpot": {
        "ingredients": {"gold_bar": 3, "diamond": 2},
        "description": "Triples jackpot winnings once",
        "uses": 1
    }
}

ITEM_DROP_TABLE = {
    "gold_coin": {"chance": 0.5, "source": "slots"},
    "four_leaf_clover": {"chance": 0.1, "source": "roulette"},
    "gold_bar": {"chance": 0.05, "source": "poker"},
    "diamond": {"chance": 0.02, "source": "blackjack"}
}

# Achievements
ACHIEVEMENTS = {
    "first_win": {"name": "Paradox Novice", "description": "Win your first slot game", "emoji": "🏆"},
    "big_winner": {"name": "Paradox Master", "description": "Win over 1000 coins", "emoji": "💎"},
    "daily_streak": {"name": "Consistent Player", "description": "Claim daily reward 7 days in a row", "emoji": "📅"},
    "tournament_champ": {"name": "Tournament King", "description": "Win a tournament", "emoji": "👑"}
}

# Missions
MISSIONS = {
    "daily": [
        {"id": "play_slots", "name": "Slot Enthusiast", "description": "Play 5 slot games", "requirements": {"slot_plays": 5}, "rewards": {"coins": 100, "xp": 50}},
        {"id": "win_roulette", "name": "Roulette Pro", "description": "Win a roulette bet", "requirements": {"roulette_wins": 1}, "rewards": {"coins": 150, "xp": 75}}
    ],
    "weekly": [
        {"id": "big_spender", "name": "Big Spender", "description": "Spend 5000 coins", "requirements": {"spent": 5000}, "rewards": {"coins": 1000, "xp": 500}}
    ],
    "one-time": [
        {"id": "first_level", "name": "Level Up", "description": "Reach level 2", "requirements": {"level": 2}, "rewards": {"coins": 200, "xp": 100}}
    ]
}

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('casino_bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger('ParadoxCasinoBot')

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- Flask Setup ---
app = Flask(__name__)
start_time = time.time()

@app.route('/')
def home():
    return "Paradox Casino Bot is operational!"

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "uptime": time.time() - start_time}), 200

@app.route('/<path:path>')
def catch_all(path):
    return f"Error: Path '{path}' not found!", 404

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- Database Helpers ---

def init_db():
    """Initialize the SQLite database with all necessary tables."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()

        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        balance INTEGER DEFAULT 7000,
                        bank_balance INTEGER DEFAULT 0,
                        winnings INTEGER DEFAULT 0,
                        xp INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        achievements TEXT DEFAULT '[]',
                        inventory TEXT DEFAULT '{}',
                        loans TEXT DEFAULT '{}',
                        lottery_tickets INTEGER DEFAULT 0,
                        daily_claim TEXT,
                        streaks TEXT DEFAULT '{"daily": 0}',
                        rps_wins INTEGER DEFAULT 0,
                        blackjack_wins INTEGER DEFAULT 0,
                        craps_wins INTEGER DEFAULT 0,
                        crafting_items TEXT DEFAULT '{}',
                        active_effects TEXT DEFAULT '{}',
                        missions TEXT DEFAULT '{}'
                    )''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_id ON users (id)')

        # Lottery table
        c.execute('''CREATE TABLE IF NOT EXISTS lottery (
                        jackpot INTEGER DEFAULT 1000
                    )''')
        c.execute('INSERT OR IGNORE INTO lottery (rowid, jackpot) VALUES (1, 1000)')

        # Tournaments table
        c.execute('''CREATE TABLE IF NOT EXISTS tournaments (
                        channel_id INTEGER PRIMARY KEY,
                        game_type TEXT,
                        players TEXT DEFAULT '{}',
                        scores TEXT DEFAULT '{}',
                        rounds INTEGER DEFAULT 3,
                        current_round INTEGER DEFAULT 0,
                        active INTEGER DEFAULT 0,
                        prize_pool INTEGER DEFAULT 0
                    )''')

        # Items table
        c.execute('''CREATE TABLE IF NOT EXISTS items (
                        item_id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        price INTEGER
                    )''')
        for item_id, item in SHOP_ITEMS.items():
            c.execute('INSERT OR IGNORE INTO items (item_id, name, description, price) VALUES (?, ?, ?, ?)',
                      (item_id, item['name'], item['description'], item['price']))

        # Trade offers table
        c.execute('''CREATE TABLE IF NOT EXISTS trade_offers (
                        offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender_id INTEGER,
                        receiver_id INTEGER,
                        offered_items TEXT,
                        requested_items TEXT,
                        status TEXT DEFAULT 'pending'
                    )''')

        # Announcement settings table (already present, no change needed)
        c.execute('''CREATE TABLE IF NOT EXISTS announcement_settings (
                        guild_id INTEGER PRIMARY KEY,
                        channel_id INTEGER,
                        message TEXT
                    )''')

        conn.commit()
        logger.info("Database initialized with all necessary tables.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        conn.close()

def get_user_data(user_id):
    """Retrieve user data from the database, initializing if not present."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (id, balance) VALUES (?, ?)', (user_id, STARTING_BALANCE))
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        data = c.fetchone()
        conn.commit()
        keys = ['id', 'balance', 'bank_balance', 'winnings', 'xp', 'level', 'achievements', 'inventory', 'loans',
                'lottery_tickets', 'daily_claim', 'streaks', 'rps_wins', 'blackjack_wins', 'craps_wins',
                'crafting_items', 'active_effects', 'missions']
        return dict(zip(keys, data))
    except sqlite3.Error as e:
        logger.error(f"Database error in get_user_data: {e}")
        return None
    finally:
        conn.close()

def update_user_data(user_id, updates):
    """Update user data in the database."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        query = 'UPDATE users SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE id = ?'
        values = list(updates.values()) + [user_id]
        c.execute(query, values)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error in update_user_data: {e}")
    finally:
        conn.close()

def get_lottery_jackpot():
    """Get the current lottery jackpot."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT jackpot FROM lottery WHERE rowid = 1')
        return c.fetchone()[0]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_lottery_jackpot: {e}")
        return 1000
    finally:
        conn.close()

def update_lottery_jackpot(amount):
    """Update the lottery jackpot by adding the specified amount."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('UPDATE lottery SET jackpot = jackpot + ? WHERE rowid = 1', (amount,))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error in update_lottery_jackpot: {e}")
    finally:
        conn.close()

def get_tournament_data(channel_id):
    """Retrieve tournament data for a channel."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT * FROM tournaments WHERE channel_id = ?', (channel_id,))
        data = c.fetchone()
        if data:
            keys = ['channel_id', 'game_type', 'players', 'scores', 'rounds', 'current_round', 'active', 'prize_pool']
            return dict(zip(keys, data))
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error in get_tournament_data: {e}")
        return None
    finally:
        conn.close()

def update_tournament_data(channel_id, updates):
    """Update or insert tournament data."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO tournaments (channel_id) VALUES (?)', (channel_id,))
        query = 'UPDATE tournaments SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE channel_id = ?'
        values = list(updates.values()) + [channel_id]
        c.execute(query, values)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error in update_tournament_data: {e}")
    finally:
        conn.close()

# New announcement helpers
def set_announcement_settings(guild_id, channel_id, message=None):
    """Set the announcement channel and optional message for a guild."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO announcement_settings (guild_id, channel_id, message) VALUES (?, ?, ?)',
                  (guild_id, channel_id, message))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error in set_announcement_settings: {e}")
    finally:
        conn.close()

def get_announcement_settings(guild_id):
    """Get the announcement channel and message for a guild."""
    try:
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT channel_id, message FROM announcement_settings WHERE guild_id = ?', (guild_id,))
        result = c.fetchone()
        return {'channel_id': result[0], 'message': result[1]} if result else None
    except sqlite3.Error as e:
        logger.error(f"Database error in get_announcement_settings: {e}")
        return None
    finally:
        conn.close()


# --- Utility Commands ---

@bot.command()
@commands.has_permissions(administrator=True)
async def setannouncement(ctx, channel: discord.TextChannel = None, *, message: str = None):
    """Set the daily shop reset announcement channel and optional message. Usage: !setannouncement [#channel] [message]"""
    channel = channel or ctx.channel  # Default to current channel
    set_announcement_settings(ctx.guild.id, channel.id, message)
    embed = discord.Embed(
        title="📢 Shop Reset Announcement Settings Updated",
        description=f"Daily shop reset announcements will be sent to {channel.mention}.\n" +
                    (f"Custom message set: '{message}'" if message else "Using default: 'Daily shop is reset thx for gambling with us Regards Time_Walker.inc'"),
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    """Display the help menu."""
    embed = discord.Embed(title="🎰 Paradox Casino Help", description="Welcome to the Paradox Casino Machine!", color=0x3498db)
    embed.add_field(
        name="Utility",
        value="`!setannouncement [#channel] [message]` - Set daily shop reset channel/message",
        inline=False
    )
    # Add other sections (e.g., Gambling Games) as needed based on your existing commands
    embed.set_footer(text="Paradox Casino Machine | Powered by Luck")
    await ctx.send(embed=embed)        

# --- Game Functions ---

def spin_slots(lines):
    """Generate slot machine results."""
    return [[random.choice(SLOTS) for _ in range(3)] for _ in range(lines)]

def check_win(slots):
    """Check slot machine results for winnings."""
    winnings = 0
    jackpot_win = False
    winning_lines = []
    for i, line in enumerate(slots):
        if line[0] == line[1] == line[2]:
            multiplier = JACKPOT_MULTIPLIER if line[0] == JACKPOT_SYMBOL else 1
            line_win = 100 * multiplier
            winnings += line_win
            winning_lines.append((i, line_win))
            if line[0] == JACKPOT_SYMBOL:
                jackpot_win = True
    return winnings, jackpot_win, winning_lines

def format_slot_display(slots, winning_lines):
    """Format the slot display for output."""
    winning_dict = dict(winning_lines)
    display = []
    for i, line in enumerate(slots):
        if i in winning_dict:
            display.append(f"▶️ {' '.join(line)} ◀️ +${winning_dict[i]}")
        else:
            display.append(f"   {' '.join(line)}")
    return '\n'.join(display)

def get_roulette_color(number):
    """Determine the color of a roulette number."""
    if number in RED_NUMBERS:
        return "red"
    elif number in BLACK_NUMBERS:
        return "black"
    else:
        return "green"

def validate_roulette_bet(bet_type, bet_value):
    """Validate roulette bet type and value."""
    if bet_type not in ROULETTE_BETS:
        return False
    return ROULETTE_BETS[bet_type]["validator"](bet_value)

def calculate_roulette_payout(bet_type, bet_value, spun_number):
    """Calculate roulette payout based on bet."""
    color = get_roulette_color(spun_number)
    if bet_type == "number":
        return ROULETTE_BETS[bet_type]["payout"] if spun_number == int(bet_value) else 0
    elif bet_type == "color":
        return ROULETTE_BETS[bet_type]["payout"] if color == bet_value.lower() else 0
    elif bet_type == "parity":
        if spun_number == 0:
            return 0
        return ROULETTE_BETS[bet_type]["payout"] if (spun_number % 2 == 0) == (bet_value.lower() == "even") else 0
    elif bet_type == "range":
        if spun_number == 0:
            return 0
        return ROULETTE_BETS[bet_type]["payout"] if (spun_number > 18) == (bet_value.lower() == "high") else 0
    elif bet_type == "dozen":
        ranges = {"first": range(1, 13), "second": range(13, 25), "third": range(25, 37)}
        return ROULETTE_BETS[bet_type]["payout"] if spun_number in ranges[bet_value.lower()] else 0
    elif bet_type == "column":
        column = int(bet_value)
        return ROULETTE_BETS[bet_type]["payout"] if spun_number % 3 == column - 1 else 0
    return 0

def deal_poker_hand():
    """Deal a 5-card poker hand."""
    deck = DECK.copy()
    random.shuffle(deck)
    return deck[:5]

def evaluate_poker_hand(hand):
    """Evaluate a poker hand and return the best combination."""
    ranks = [card[:-1] for card in hand]
    suits = [card[-1] for card in hand]
    rank_counts = {rank: ranks.count(rank) for rank in set(ranks)}
    sorted_ranks = sorted([CARD_RANKS.index(r) for r in ranks], reverse=True)
    is_flush = len(set(suits)) == 1
    is_straight = all(sorted_ranks[i] - sorted_ranks[i + 1] == 1 for i in range(4)) or (sorted_ranks == [12, 3, 2, 1, 0])

    if is_flush and sorted_ranks == [12, 11, 10, 9, 8]:
        return "royal_flush"
    elif is_flush and is_straight:
        return "straight_flush"
    elif 4 in rank_counts.values():
        return "four_of_a_kind"
    elif 3 in rank_counts.values() and 2 in rank_counts.values():
        return "full_house"
    elif is_flush:
        return "flush"
    elif is_straight:
        return "straight"
    elif 3 in rank_counts.values():
        return "three_of_a_kind"
    elif list(rank_counts.values()).count(2) == 2:
        return "two_pair"
    elif 2 in rank_counts.values() and max(CARD_RANKS.index(r) for r, c in rank_counts.items() if c == 2) >= 9:
        return "pair"
    else:
        return "high_card"

def blackjack_value(cards):
    """Calculate the value of a blackjack hand."""
    value = 0
    aces = 0
    for card in cards:
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']:
            value += 10
        elif rank == 'A':
            aces += 1
        else:
            value += int(rank)
    for _ in range(aces):
        if value + 11 <= 21:
            value += 11
        else:
            value += 1
    return value

def roll_dice(n=2):
    """Roll n dice and return the sum."""
    return sum(random.randint(1, 6) for _ in range(n))

def baccarat_hand(cards):
    """Calculate the value of a Baccarat hand."""
    value = sum(10 if card[:-1] in ['10', 'J', 'Q', 'K'] else 1 if card[:-1] == 'A' else int(card[:-1]) for card in cards) % 10
    return value

def generate_bingo_card():
    """Generate a 5x5 bingo card."""
    card = []
    for col, letter in enumerate('BINGO'):
        if letter == 'N':
            numbers = random.sample(range(col * 15 + 1, col * 15 + 16), 4)
            card.append(numbers[:2] + [None] + numbers[2:])
        else:
            card.append(random.sample(range(col * 15 + 1, col * 15 + 16), 5))
    return list(zip(*card))

def check_bingo_win(card, called_numbers):
    """Check if a bingo card has a winning line."""
    for row in card:
        if all(num in called_numbers for num in row if num is not None):
            return True
    for col in zip(*card):
        if all(num in called_numbers for num in col if num is not None):
            return True
    if all(card[i][i] in called_numbers for i in range(5) if card[i][i] is not None):
        return True
    if all(card[i][4 - i] in called_numbers for i in range(5) if card[i][4 - i] is not None):
        return True
    return False

# --- Economy Functions ---

def add_item_drop(user_id, game):
    """Add a random item drop based on game played."""
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    for item_id, info in ITEM_DROP_TABLE.items():
        if info['source'] == game and random.random() < info['chance']:
            inventory[item_id] = inventory.get(item_id, 0) + 1
            update_user_data(user_id, {'inventory': json.dumps(inventory)})
            return item_id
    return None

def can_craft(user_id, recipe_id):
    """Check if a user can craft an item."""
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    recipe = CRAFTING_RECIPES.get(recipe_id)
    if not recipe:
        return False
    return all(inventory.get(item, 0) >= qty for item, qty in recipe['ingredients'].items())

def craft_item(user_id, recipe_id):
    """Craft an item and update inventory."""
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    recipe = CRAFTING_RECIPES[recipe_id]
    for item, qty in recipe['ingredients'].items():
        inventory[item] -= qty
    inventory[recipe_id] = inventory.get(recipe_id, 0) + 1
    update_user_data(user_id, {'inventory': json.dumps(inventory)})

# --- Utility Functions ---

def add_xp(user_id, amount):
    """Add XP to a user and handle leveling."""
    user_data = get_user_data(user_id)
    xp = user_data['xp'] + amount
    level = user_data['level']
    while xp >= 100 * level:
        xp -= 100 * level
        level += 1
        # Add level-up bonus
        update_user_data(user_id, {'balance': user_data['balance'] + 100})
    update_user_data(user_id, {'xp': xp, 'level': level})

def update_mission_progress(user_id, mission_type, progress_key, amount=1):
    """Update mission progress for a user."""
    user_data = get_user_data(user_id)
    missions = json.loads(user_data['missions']) or {}
    if mission_type not in missions:
        missions[mission_type] = {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS[mission_type]}
    for mission in MISSIONS[mission_type]:
        mission_id = mission["id"]
        if mission_id in missions[mission_type] and not missions[mission_type][mission_id]["completed"]:
            if progress_key in mission["requirements"]:
                missions[mission_type][mission_id]["progress"] += amount
                if missions[mission_type][mission_id]["progress"] >= mission["requirements"][progress_key]:
                    missions[mission_type][mission_id]["completed"] = True
                    for key, value in mission["rewards"].items():
                        if key == "coins":
                            update_user_data(user_id, {'balance': user_data['balance'] + value})
                        elif key == "xp":
                            add_xp(user_id, value)
    update_user_data(user_id, {'missions': json.dumps(missions)})

# --- Bot Events ---

@bot.event
async def on_ready():
    """Handle bot startup."""
    logger.info(f'Bot logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="!help"))
    init_db()

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Command on cooldown. Retry in {error.retry_after:.1f}s.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing argument! Use `!help` for details.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument! Use `!help` for details.")
    else:
        await ctx.send(f"❌ Error: {str(error)}")
        logger.error(f"Command error: {error}")

# --- Commands ---

## Gambling Commands

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet(ctx, amount: int, lines: int = 1):
    """Spin the slot machine. Usage: !bet <amount> [lines]"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    total_bet = amount * lines

    if not (MIN_BET <= amount <= MAX_BET and 1 <= lines <= MAX_LINES and total_bet <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}, lines 1-{MAX_LINES}. Balance: ${user_data['balance']}")
        return

    slots = spin_slots(lines)
    winnings, jackpot_win, winning_lines = check_win(slots)
    user_data['balance'] -= total_bet
    user_data['balance'] += winnings
    updates = {
        'balance': user_data['balance'],
        'winnings': user_data.get('winnings', 0) + winnings
    }
    update_user_data(user_id, updates)
    add_xp(user_id, total_bet // 10)
    update_mission_progress(user_id, "daily", "slot_plays")
    item_drop = add_item_drop(user_id, "slots")

    embed = discord.Embed(
        title="🎰 Slot Result",
        description=f"Bet: ${total_bet} | {'Won' if winnings > 0 else 'Lost'}: ${winnings if winnings > 0 else total_bet}",
        color=0x2ecc71 if winnings > 0 else 0xe74c3c
    )
    embed.add_field(name="Spin", value=f"```\n{format_slot_display(slots, winning_lines)}\n```", inline=False)
    embed.add_field(name="Balance", value=f"${user_data['balance']}", inline=True)
    if item_drop:
        embed.add_field(name="Item Drop", value=f"You found a {SHOP_ITEMS.get(item_drop, {'name': item_drop})['name']}!", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def roulette(ctx, bet_type: str, bet_value: str, amount: int):
    """Play roulette. Usage: !roulette <bet_type> <bet_value> <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if amount <= 0 or amount > user_data['balance']:
        await ctx.send("❌ Invalid bet amount!")
        return

    if not validate_roulette_bet(bet_type, bet_value):
        await ctx.send("❌ Invalid bet type or value! Use: number (0-36), color (red/black), parity (even/odd), range (high/low), dozen (first/second/third), column (1-3)")
        return

    spun_number = random.randint(0, 36)
    payout = calculate_roulette_payout(bet_type, bet_value, spun_number)
    net_gain = payout * amount if payout > 0 else -amount
    new_balance = user_data['balance'] + net_gain
    updates = {'balance': new_balance}
    if net_gain > 0:
        updates['winnings'] = user_data.get('winnings', 0) + net_gain
        update_mission_progress(user_id, "daily", "roulette_wins")
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)
    item_drop = add_item_drop(user_id, "roulette")

    color = get_roulette_color(spun_number)
    embed = discord.Embed(
        title="🎡 Roulette Result",
        description=f"Spun: {spun_number} ({color})\nBet: {bet_type} {bet_value} (${amount})\n{'Won' if net_gain > 0 else 'Lost'}: ${abs(net_gain)}",
        color=0x2ecc71 if net_gain > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    if item_drop:
        embed.add_field(name="Item Drop", value=f"You found a {SHOP_ITEMS.get(item_drop, {'name': item_drop})['name']}!", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def poker(ctx, amount: int):
    """Play video poker. Usage: !poker <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    hand = deal_poker_hand()
    combination = evaluate_poker_hand(hand)
    payout = POKER_PAYOUTS[combination] * amount
    new_balance = user_data['balance'] - amount + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)
    item_drop = add_item_drop(user_id, "poker")

    embed = discord.Embed(
        title="🃏 Poker Result",
        description=f"Bet: ${amount}\nHand: {' '.join(hand)}\nResult: {combination.replace('_', ' ').title()}\n{'Won' if payout > 0 else 'Lost'}: ${payout if payout > 0 else amount}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    if item_drop:
        embed.add_field(name="Item Drop", value=f"You found a {SHOP_ITEMS.get(item_drop, {'name': item_drop})['name']}!", inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def blackjack(ctx, amount: int):
    """Play blackjack against the dealer. Usage: !blackjack <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    deck = DECK.copy()
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    embed = discord.Embed(
        title="♠️ Blackjack",
        description=f"Your hand: {' '.join(player_hand)} (Value: {blackjack_value(player_hand)})\nDealer's hand: {dealer_hand[0]} ?",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")  # Hit
    await msg.add_reaction("❌")  # Stand

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

    while blackjack_value(player_hand) < 21:
        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) == "✅":
                player_hand.append(deck.pop())
                embed.description = f"Your hand: {' '.join(player_hand)} (Value: {blackjack_value(player_hand)})\nDealer's hand: {dealer_hand[0]} ?"
                await msg.edit(embed=embed)
            else:
                break
        except asyncio.TimeoutError:
            break

    player_value = blackjack_value(player_hand)
    if player_value > 21:
        result = "bust"
        payout = -amount
    else:
        while blackjack_value(dealer_hand) < 17:
            dealer_hand.append(deck.pop())
        dealer_value = blackjack_value(dealer_hand)
        if dealer_value > 21 or player_value > dealer_value:
            result = "win"
            payout = int(amount * (BLACKJACK_PAYOUT if player_value == 21 and len(player_hand) == 2 else 1))
            update_user_data(user_id, {'blackjack_wins': user_data['blackjack_wins'] + 1})
        elif player_value == dealer_value:
            result = "push"
            payout = 0
        else:
            result = "lose"
            payout = -amount

    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)
    item_drop = add_item_drop(user_id, "blackjack")

    embed = discord.Embed(
        title="♠️ Blackjack Result",
        description=f"Your hand: {' '.join(player_hand)} (Value: {player_value})\nDealer's hand: {' '.join(dealer_hand)} (Value: {dealer_value})\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    if item_drop:
        embed.add_field(name="Item Drop", value=f"You found a {SHOP_ITEMS.get(item_drop, {'name': item_drop})['name']}!", inline=False)
    await msg.edit(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def craps(ctx, amount: int, bet: str):
    """Play a simplified game of craps. Usage: !craps <amount> <pass/dont_pass>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    bet = bet.lower()

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return
    if bet not in ["pass", "dont_pass"]:
        await ctx.send("❌ Bet must be 'pass' or 'dont_pass'!")
        return

    roll = roll_dice()
    if roll in [7, 11]:
        result = "win" if bet == "pass" else "lose"
    elif roll in [2, 3, 12]:
        result = "lose" if bet == "pass" else "win"
    else:
        point = roll
        while True:
            roll = roll_dice()
            if roll == point:
                result = "win" if bet == "pass" else "lose"
                break
            elif roll == 7:
                result = "lose" if bet == "pass" else "win"
                break

    payout = amount if result == "win" else -amount
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
        updates['craps_wins'] = user_data['craps_wins'] + 1
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🎲 Craps Result",
        description=f"Initial Roll: {roll}\nBet: {bet} (${amount})\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def baccarat(ctx, amount: int, bet: str):
    """Play baccarat. Usage: !baccarat <amount> <player/banker/tie>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    bet = bet.lower()

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return
    if bet not in ["player", "banker", "tie"]:
        await ctx.send("❌ Bet must be 'player', 'banker', or 'tie'!")
        return

    deck = DECK.copy()
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    banker_hand = [deck.pop(), deck.pop()]
    player_value = baccarat_hand(player_hand)
    banker_value = baccarat_hand(banker_hand)

    if player_value > banker_value:
        result = "player"
        payout = amount if bet == "player" else -amount
    elif banker_value > player_value:
        result = "banker"
        payout = int(amount * 0.95) if bet == "banker" else -amount  # 5% commission
    else:
        result = "tie"
        payout = amount * 8 if bet == "tie" else -amount

    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🎴 Baccarat Result",
        description=f"Player: {' '.join(player_hand)} (Value: {player_value})\nBanker: {' '.join(banker_hand)} (Value: {banker_value})\nBet: {bet} (${amount})\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def rps(ctx, choice: str, amount: int):
    """Play Rock-Paper-Scissors. Usage: !rps <rock/paper/scissors> <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    choice = choice.lower()

    if choice not in ["rock", "paper", "scissors"]:
        await ctx.send("❌ Choice must be 'rock', 'paper', or 'scissors'!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    bot_choice = random.choice(["rock", "paper", "scissors"])
    if choice == bot_choice:
        result = "tie"
        payout = 0
    elif (choice == "rock" and bot_choice == "scissors") or (choice == "paper" and bot_choice == "rock") or (choice == "scissors" and bot_choice == "paper"):
        result = "win"
        payout = amount
    else:
        result = "lose"
        payout = -amount

    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
        updates['rps_wins'] = user_data['rps_wins'] + 1
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="✊ Rock-Paper-Scissors",
        description=f"You chose: {choice}\nBot chose: {bot_choice}\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def hangman(ctx, amount: int):
    """Play Hangman for coins. Usage: !hangman <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    words = ["casino", "jackpot", "roulette", "blackjack"]
    word = random.choice(words)
    guessed = set()
    display = ["_" for _ in word]
    attempts = 6

    embed = discord.Embed(
        title="🔮 Hangman",
        description=f"Word: {' '.join(display)}\nAttempts left: {attempts}\nGuess a letter!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)

    while attempts > 0 and "_" in display:
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()

        try:
            guess = await bot.wait_for("message", timeout=30.0, check=check)
            letter = guess.content.lower()
            await guess.delete()
            if letter in guessed:
                embed.description = f"Word: {' '.join(display)}\nAttempts left: {attempts}\nYou've already guessed '{letter}'!"
            elif letter in word:
                guessed.add(letter)
                for i, char in enumerate(word):
                    if char == letter:
                        display[i] = letter
                embed.description = f"Word: {' '.join(display)}\nAttempts left: {attempts}\nGood guess!"
            else:
                guessed.add(letter)
                attempts -= 1
                embed.description = f"Word: {' '.join(display)}\nAttempts left: {attempts}\n'{letter}' not in word!"
            await msg.edit(embed=embed)
        except asyncio.TimeoutError:
            embed.description = f"Word: {' '.join(display)}\nAttempts left: {attempts}\nTime's up!"
            await msg.edit(embed=embed)
            break

    if "_" not in display:
        payout = amount * 2
        result = "win"
    else:
        payout = -amount
        result = "lose"
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🔮 Hangman Result",
        description=f"Word was: {word}\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await msg.edit(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def guess(ctx, amount: int, number: int):
    """Guess a number between 1 and 100. Usage: !guess <amount> <number>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return
    if not (1 <= number <= 100):
        await ctx.send("❌ Number must be between 1 and 100!")
        return

    target = random.randint(1, 100)
    if number == target:
        payout = amount * 10
        result = "win"
    else:
        payout = -amount
        result = "lose"
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🔢 Number Guessing",
        description=f"Your guess: {number}\nNumber was: {target}\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

# Local fallback questions in case API fails
LOCAL_TRIVIA = [
    {
        "question": "What is the capital of France?",
        "options": ["Paris", "London", "Berlin", "Madrid"],
        "correct": "Paris",
        "difficulty": "easy"
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Venus", "Mars", "Jupiter", "Saturn"],
        "correct": "Mars",
        "difficulty": "medium"
    },
    {
        "question": "What is the powerhouse of the cell?",
        "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi Apparatus"],
        "correct": "Mitochondria",
        "difficulty": "hard"
    }
]

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def trivia(ctx, amount: int, difficulty: str = "medium"):
    """Answer a trivia question with varying difficulty. Usage: !trivia <amount> [easy|medium|hard]"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    # Validate bet amount
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    # Validate difficulty
    difficulty = difficulty.lower()
    if difficulty not in ["easy", "medium", "hard"]:
        await ctx.send("❌ Difficulty must be 'easy', 'medium', or 'hard'. Defaulting to 'medium'.")
        difficulty = "medium"

    # Multiplier based on difficulty
    difficulty_multipliers = {"easy": 1.5, "medium": 2, "hard": 3}
    multiplier = difficulty_multipliers[difficulty]

    # Try fetching from API
    question_data = None
    try:
        async with aiohttp.ClientSession() as session:
            asyncA with session.get(
                f"https://opentdb.com/api.php?amount=1&type=multiple&difficulty={difficulty}",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['response_code'] == 0:
                        q = data['results'][0]
                        question_data = {
                            "question": html.unescape(q['question']),
                            "options": [html.unescape(ans) for ans in q['incorrect_answers'] + [q['correct_answer']]],
                            "correct": html.unescape(q['correct_answer'])
                        }
                        random.shuffle(question_data["options"])
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning(f"Trivia API failed: {e}. Using local question.")
        # Fallback to local question
        question_data = random.choice([q for q in LOCAL_TRIVIA if q["difficulty"] == difficulty])

    if not question_data:
        await ctx.send("❌ Failed to load a trivia question. Please try again later.")
        return

    question = question_data["question"]
    options = question_data["options"]
    correct_answer = question_data["correct"]
    correct_index = options.index(correct_answer) + 1  # 1-based index

    # Present question and options
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    embed = discord.Embed(
        title=f"❓ Trivia Challenge ({difficulty.capitalize()})",
        description=f"Question: {question}\n\n**Options:**\n{options_text}\n\nBet: ${amount} | Multiplier: x{multiplier}\nAnswer with a number (1-4) within 30 seconds!",
        color=0x3498db
    )
    embed.set_footer(text="Type your answer directly in the channel.")
    msg = await ctx.send(embed=embed)

    # Check for user's response
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= 4

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
        answer = int(response.content)
        await response.delete()  # Clean up the user's answer
        if answer == correct_index:
            payout = int(amount * multiplier)  # Win based on difficulty multiplier
            result = "win"
        else:
            payout = -amount
            result = "lose"
    except asyncio.TimeoutError:
        payout = -amount
        result = "lose"
        answer = "Time's up!"

    # Update user data
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, int(amount * (multiplier / 2)))  # XP scales with difficulty

    # Show result
    result_embed = discord.Embed(
        title=f"❓ Trivia Result ({difficulty.capitalize()})",
        description=f"Question: {question}\nYour answer: {options[answer-1] if isinstance(answer, int) else answer}\nCorrect answer: {correct_answer}\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    result_embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    result_embed.add_field(name="XP Gained", value=f"+{int(amount * (multiplier / 2))}", inline=True)
    await msg.edit(embed=result_embed)

    
@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def coinflip(ctx, choice: str, amount: int):
    """Flip a coin. Usage: !coinflip <heads/tails> <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    choice = choice.lower()

    if choice not in ["heads", "tails"]:
        await ctx.send("❌ Choice must be 'heads' or 'tails'!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    result = random.choice(["heads", "tails"])
    payout = amount if choice == result else -amount
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🪙 Coinflip",
        description=f"You chose: {choice}\nResult: {result}\n{'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def dice(ctx, amount: int, prediction: int):
    """Roll two dice and predict the sum. Usage: !dice <amount> <prediction>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return
    if not (2 <= prediction <= 12):
        await ctx.send("❌ Prediction must be between 2 and 12!")
        return

    roll = roll_dice()
    payout = amount * 5 if roll == prediction else -amount
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=f"Your prediction: {prediction}\nRoll: {roll}\n{'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def wheel(ctx, amount: int):
    """Spin the Wheel of Fortune. Usage: !wheel <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    prize = random.choice(WHEEL_PRIZES)
    if prize == "Jackpot":
        winnings = get_lottery_jackpot()
        update_lottery_jackpot(-winnings + 1000)
    else:
        winnings = prize
    new_balance = user_data['balance'] - amount + winnings
    updates = {'balance': new_balance}
    if winnings > 0:
        updates['winnings'] = user_data.get('winnings', 0) + winnings
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🎡 Wheel of Fortune",
        description=f"Bet: ${amount}\nPrize: {prize if prize != 'Jackpot' else f'${winnings} Jackpot'}\n{'Won' if winnings > 0 else 'Lost'}: ${winnings if winnings > 0 else amount}",
        color=0x2ecc71 if winnings > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def scratch(ctx):
    """Buy and scratch a card for a prize. Usage: !scratch"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if SCRATCH_PRICE > user_data['balance']:
        await ctx.send(f"❌ Scratch card costs ${SCRATCH_PRICE}. Balance: ${user_data['balance']}")
        return

    prizes = random.choices(SCRATCH_PRIZES, k=3)
    winnings = sum(1 for p in prizes if p > 0) >= 2 and max(prizes) or 0
    new_balance = user_data['balance'] - SCRATCH_PRICE + winnings
    updates = {'balance': new_balance}
    if winnings > 0:
        updates['winnings'] = user_data.get('winnings', 0) + winnings
    update_user_data(user_id, updates)
    add_xp(user_id, SCRATCH_PRICE // 10)

    embed = discord.Embed(
        title="🎟️ Scratch Card",
        description=f"Cost: ${SCRATCH_PRICE}\nScratched: {', '.join(map(str, prizes))}\n{'Won' if winnings > 0 else 'Lost'}: ${winnings if winnings > 0 else SCRATCH_PRICE}",
        color=0x2ecc71 if winnings > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def bingo(ctx, amount: int):
    """Play a game of bingo. Usage: !bingo <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    card = generate_bingo_card()
    called_numbers = set()
    embed = discord.Embed(
        title="🎱 Bingo",
        description=f"Your card:\n```\n{' '.join(str(n).rjust(2) if n else ' X' for row in card for n in row)}\n```\nBet: ${amount}\nNumbers called: None",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)

    for _ in range(10):  # Simulate 10 calls
        await asyncio.sleep(3)
        number = random.choice([n for n in BINGO_NUMBERS if n not in called_numbers])
        called_numbers.add(number)
        embed.description = f"Your card:\n```\n{' '.join(str(n).rjust(2) if n else ' X' for row in card for n in row)}\n```\nBet: ${amount}\nNumbers called: {', '.join(map(str, called_numbers))}"
        await msg.edit(embed=embed)
        if check_bingo_win(card, called_numbers):
            break

    if check_bingo_win(card, called_numbers):
        payout = amount * 5
        result = "win"
    else:
        payout = -amount
        result = "lose"
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🎱 Bingo Result",
        description=f"Your card:\n```\n{' '.join(str(n).rjust(2) if n else ' X' for row in card for n in row)}\n```\nNumbers called: {', '.join(map(str, called_numbers))}\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await msg.edit(embed=embed)


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def highlow(ctx, amount: int, guess: str):
    """Guess if the next card is higher or lower. Usage: !highlow <amount> <high/low>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    guess = guess.lower()

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return
    if guess not in ["high", "low"]:
        await ctx.send("❌ Guess must be 'high' or 'low'!")
        return

    deck = DECK.copy()
    random.shuffle(deck)
    current_card = deck.pop()
    next_card = deck.pop()
    current_value = CARD_RANKS.index(current_card[:-1]) + 2  # 2-14 scale
    next_value = CARD_RANKS.index(next_card[:-1]) + 2

    if (guess == "high" and next_value > current_value) or (guess == "low" and next_value < current_value):
        payout = amount
        result = "win"
    elif next_value == current_value:
        payout = 0
        result = "tie"
    else:
        payout = -amount
        result = "lose"

    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🎴 High-Low",
        description=f"Current card: {current_card} ({current_value})\nNext card: {next_card} ({next_value})\nGuess: {guess}\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.channel)
async def slotrace(ctx, amount: int):
    """Start a slot race with others. Usage: !slotrace <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    embed = discord.Embed(
        title="🏁 Slot Race",
        description=f"Bet: ${amount}\nJoin with ✅ within 15 seconds!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check(reaction, user):
        return str(reaction.emoji) == "✅" and reaction.message.id == msg.id and user != bot.user

    players = {user_id: user_data}
    try:
        async with asyncio.timeout(15):
            while True:
                reaction, user = await bot.wait_for("reaction_add", check=check)
                if user.id not in players and MIN_BET <= amount <= MAX_BET and get_user_data(user.id)['balance'] >= amount:
                    players[user.id] = get_user_data(user.id)
                    await ctx.send(f"{user.mention} joined the race!")
    except asyncio.TimeoutError:
        pass

    if len(players) < 2:
        await ctx.send("❌ Not enough players joined the race!")
        return

    results = {}
    for player_id in players:
        slots = spin_slots(1)
        winnings, _, _ = check_win(slots)
        results[player_id] = {"winnings": winnings, "slots": slots[0]}
        update_user_data(player_id, {'balance': players[player_id]['balance'] - amount})

    winner_id = max(results, key=lambda x: results[x]["winnings"])
    prize = amount * len(players)
    new_balance = players[winner_id]['balance'] - amount + prize
    update_user_data(winner_id, {
        'balance': new_balance,
        'winnings': players[winner_id].get('winnings', 0) + prize
    })
    for player_id in players:
        add_xp(player_id, amount // 10)

    embed = discord.Embed(title="🏁 Slot Race Results", color=0x2ecc71)
    for player_id, data in results.items():
        embed.add_field(
            name=f"<@{player_id}>",
            value=f"{' '.join(data['slots'])} (+${data['winnings']}) {'🏆' if player_id == winner_id else ''}",
            inline=False
        )
    embed.add_field(name="Winner", value=f"<@{winner_id}> wins ${prize}!", inline=False)
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def tictactoe(ctx, opponent: discord.Member, amount: int):
    """Play Tic-Tac-Toe against another user. Usage: !tictactoe <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't play against yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="⭕ Tic-Tac-Toe Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} for ${amount}!\n{opponent.mention}, accept with ✅ within 30 seconds!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    board = [" " for _ in range(9)]
    players = {user_id: "X", opponent_id: "O"}
    turn = user_id

    def display_board():
        return f"```\n{board[0]} | {board[1]} | {board[2]}\n---------\n{board[3]} | {board[4]} | {board[5]}\n---------\n{board[6]} | {board[7]} | {board[8]}\n```"

    embed = discord.Embed(
        title="⭕ Tic-Tac-Toe",
        description=f"{display_board()}\n<@{turn}>'s turn (X). Move: 1-9",
        color=0x3498db
    )
    game_msg = await ctx.send(embed=embed)

    def check_win():
        wins = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        return any(board[a] == board[b] == board[c] != " " for a, b, c in wins)

    while " " in board:
        def check(m):
            return m.author.id == turn and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= 9

        try:
            move = await bot.wait_for("message", timeout=30.0, check=check)
            pos = int(move.content) - 1
            await move.delete()
            if board[pos] == " ":
                board[pos] = players[turn]
                embed.description = f"{display_board()}\n{'<@' + str(turn) + '> wins!' if check_win() else 'Tie!' if ' ' not in board else '<@' + str(opponent_id if turn == user_id else user_id) + '>’s turn (' + players[opponent_id if turn == user_id else user_id] + ')'}"
                await game_msg.edit(embed=embed)
                if check_win() or " " not in board:
                    break
                turn = opponent_id if turn == user_id else user_id
            else:
                await ctx.send(f"<@{turn}>, that spot is taken!", delete_after=5)
        except asyncio.TimeoutError:
            await ctx.send(f"<@{turn}> took too long! Game forfeited.")
            turn = opponent_id if turn == user_id else user_id
            break

    winner_id = turn if check_win() else None
    payout = amount * 2 if winner_id else 0
    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed.color = 0x2ecc71 if winner_id else 0xe74c3c
    embed.description += f"\nResult: {'<@' + str(winner_id) + '> wins $' + str(payout) if winner_id else 'Tie! No payout.'}"
    await game_msg.edit(embed=embed)



@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def cardmatch(ctx, amount: int):
    """Match pairs of cards. Usage: !cardmatch <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    cards = ["A♠", "A♠", "K♥", "K♥", "Q♦", "Q♦"]  # 3 pairs
    random.shuffle(cards)
    display = ["🂠" for _ in cards]
    matches = 0

    embed = discord.Embed(
        title="🃏 Card Match",
        description=f"Cards: {' '.join(display)}\nBet: ${amount}\nPick two positions (1-6) with `1 2` within 30s!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)

    def check(m):
        return (m.author == ctx.author and m.channel == ctx.channel and
                len(m.content.split()) == 2 and all(x.isdigit() and 1 <= int(x) <= 6 for x in m.content.split()))

    for _ in range(3):  # 3 attempts
        try:
            guess = await bot.wait_for("message", timeout=30.0, check=check)
            pos1, pos2 = [int(x) - 1 for x in guess.content.split()]
            await guess.delete()
            if pos1 == pos2 or display[pos1] != "🂠" or display[pos2] != "🂠":
                embed.description = f"Cards: {' '.join(display)}\nInvalid move! Try again."
                await msg.edit(embed=embed)
                continue
            display[pos1] = cards[pos1]
            display[pos2] = cards[pos2]
            embed.description = f"Cards: {' '.join(display)}\nFlipped {pos1+1} and {pos2+1}. {'Match!' if cards[pos1] == cards[pos2] else 'No match.'}"
            await msg.edit(embed=embed)
            if cards[pos1] == cards[pos2]:
                matches += 1
            else:
                await asyncio.sleep(2)
                display[pos1] = display[pos2] = "🂠"
                embed.description = f"Cards: {' '.join(display)}\nPick again!"
                await msg.edit(embed=embed)
        except asyncio.TimeoutError:
            break

    payout = amount * matches - amount if matches > 0 else -amount
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🃏 Card Match Result",
        description=f"Matches: {matches}/3\nResult: {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await msg.edit(embed=embed)


@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def crash(ctx, amount: int):
    """Bet on a multiplier before it crashes. Usage: !crash <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    multiplier = 1.0
    crashed = False
    embed = discord.Embed(
        title="💥 Crash",
        description=f"Bet: ${amount}\nMultiplier: {multiplier:.2f}x\nCash out with ✅ or wait...",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    async def update_multiplier():
        nonlocal multiplier, crashed
        while not crashed:
            await asyncio.sleep(1)
            multiplier += random.uniform(0.1, 0.5)
            if random.random() < 0.15:  # 15% chance to crash each second
                crashed = True
            embed.description = f"Bet: ${amount}\nMultiplier: {multiplier:.2f}x\n{'Crashed!' if crashed else 'Cash out with ✅ or wait...'}"
            await msg.edit(embed=embed)

    bot.loop.create_task(update_multiplier())
    try:
        await bot.wait_for("reaction_add", timeout=15.0, check=check)
        if not crashed:
            payout = int(amount * multiplier) - amount
            result = "win"
        else:
            payout = -amount
            result = "lose"
    except asyncio.TimeoutError:
        payout = -amount if crashed else int(amount * multiplier) - amount
        result = "lose" if crashed else "win"

    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="💥 Crash Result",
        description=f"Final Multiplier: {multiplier:.2f}x\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await msg.edit(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def diceduel(ctx, opponent: discord.Member, amount: int):
    """Challenge another player to a dice duel. Usage: !diceduel <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't duel yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="🎲 Dice Duel Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} to a dice duel for ${amount}!\n{opponent.mention}, accept with ✅ within 30 seconds!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    user_roll = roll_dice(2)
    opponent_roll = roll_dice(2)
    if user_roll > opponent_roll:
        winner_id = user_id
        payout = amount * 2
        result = f"{ctx.author.mention} wins!"
    elif opponent_roll > user_roll:
        winner_id = opponent_id
        payout = amount * 2
        result = f"{opponent.mention} wins!"
    else:
        winner_id = None
        payout = 0
        result = "It's a tie!"

    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="🎲 Dice Duel Result",
        description=f"{ctx.author.mention} rolled: {user_roll}\n{opponent.mention} rolled: {opponent_roll}\n{result}\n{'Won' if winner_id else 'Payout'}: ${payout}",
        color=0x2ecc71 if winner_id else 0xe74c3c
    )
    embed.add_field(name="Your New Balance", value=f"${get_user_data(user_id)['balance']}", inline=True)
    embed.add_field(name="Opponent's New Balance", value=f"${get_user_data(opponent_id)['balance']}", inline=True)
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def slotstreak(ctx, amount: int):
    """Try for consecutive slot wins. Usage: !slotstreak <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    streak = 0
    total_payout = -amount
    embed = discord.Embed(
        title="🎰 Slot Streak",
        description=f"Bet: ${amount}\nStreak: {streak}\nSpin with ✅ or stop with ❌ (30s timeout)",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

    while True:
        slots = spin_slots(1)
        winnings, _, _ = check_win(slots)
        if winnings > 0:
            streak += 1
            total_payout += winnings
        else:
            break

        embed.description = f"Bet: ${amount}\nSpin: {' '.join(slots[0])}\nStreak: {streak}\nWinnings: ${total_payout + amount}\nSpin again with ✅ or stop with ❌"
        embed.color = 0x2ecc71
        await msg.edit(embed=embed)

        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) == "❌":
                break
        except asyncio.TimeoutError:
            break

    new_balance = user_data['balance'] + total_payout
    updates = {'balance': new_balance}
    if total_payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + total_payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10 * (streak + 1))

    embed = discord.Embed(
        title="🎰 Slot Streak Result",
        description=f"Final Streak: {streak}\nTotal {'Won' if total_payout > 0 else 'Lost'}: ${abs(total_payout)}",
        color=0x2ecc71 if total_payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await msg.edit(embed=embed)


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def treasurehunt(ctx, amount: int):
    """Dig for treasure with a bet. Usage: !treasurehunt <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    treasures = {
        "💎 Diamond": amount * 5,
        "🥇 Gold": amount * 2,
        "🥈 Silver": amount,
        "💣 Trap": -amount * 2,
        "🪨 Nothing": -amount
    }
    weights = [0.05, 0.15, 0.30, 0.20, 0.30]  # Probabilities
    result = random.choices(list(treasures.keys()), weights=weights, k=1)[0]
    payout = treasures[result]
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="⛏️ Treasure Hunt",
        description=f"Bet: ${amount}\nFound: {result}\n{'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def war(ctx, amount: int):
    """Play a card war against the bot. Usage: !war <amount>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return

    deck = DECK.copy()
    random.shuffle(deck)
    player_card = deck.pop()
    bot_card = deck.pop()
    player_value = CARD_RANKS.index(player_card[:-1]) + 2  # 2-14 scale
    bot_value = CARD_RANKS.index(bot_card[:-1]) + 2

    if player_value > bot_value:
        payout = amount
        result = "win"
    elif bot_value > player_value:
        payout = -amount
        result = "lose"
    else:
        payout = 0
        result = "tie"

    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="⚔️ Card War",
        description=f"Your card: {player_card} ({player_value})\nBot's card: {bot_card} ({bot_value})\nResult: {result.title()} | {'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def jackpotguess(ctx, amount: int, guess: int):
    """Guess a number to win a jackpot multiplier. Usage: !jackpotguess <amount> <1-50>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Balance: ${user_data['balance']}")
        return
    if not (1 <= guess <= 50):
        await ctx.send("❌ Guess must be between 1 and 50!")
        return

    jackpot = random.randint(1, 50)
    difference = abs(guess - jackpot)
    if difference == 0:
        multiplier = 10  # Perfect guess
    elif difference <= 5:
        multiplier = 3   # Close guess
    elif difference <= 10:
        multiplier = 1   # Near miss
    else:
        multiplier = 0   # Too far

    payout = amount * multiplier - amount if multiplier > 0 else -amount
    new_balance = user_data['balance'] + payout
    updates = {'balance': new_balance}
    if payout > 0:
        updates['winnings'] = user_data.get('winnings', 0) + payout
    update_user_data(user_id, updates)
    add_xp(user_id, amount // 10)

    embed = discord.Embed(
        title="🎯 Jackpot Guess",
        description=f"Bet: ${amount}\nYour guess: {guess}\nJackpot: {jackpot}\nMultiplier: {multiplier}x\n{'Won' if payout > 0 else 'Lost'}: ${abs(payout)}",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def roulettespinoff(ctx, opponent: discord.Member, amount: int):
    """Challenge another player to a roulette spin-off. Usage: !roulettespinoff <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't challenge yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="🎡 Roulette Spin-Off Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} to a roulette spin-off for ${amount}!\n{opponent.mention}, accept with ✅ within 30 seconds!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    user_spin = random.randint(0, 36)
    opponent_spin = random.randint(0, 36)
    user_color = get_roulette_color(user_spin)
    opponent_color = get_roulette_color(opponent_spin)

    if user_spin > opponent_spin:
        winner_id = user_id
        payout = amount * 2
        result = f"{ctx.author.mention} wins!"
    elif opponent_spin > user_spin:
        winner_id = opponent_id
        payout = amount * 2
        result = f"{opponent.mention} wins!"
    else:
        winner_id = None
        payout = 0
        result = "It's a tie!"

    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="🎡 Roulette Spin-Off Result",
        description=f"{ctx.author.mention} spun: {user_spin} ({user_color})\n{opponent.mention} spun: {opponent_spin} ({opponent_color})\n{result}\n{'Won' if winner_id else 'Payout'}: ${payout}",
        color=0x2ecc71 if winner_id else 0xe74c3c
    )
    embed.add_field(name="Your New Balance", value=f"${get_user_data(user_id)['balance']}", inline=True)
    embed.add_field(name="Opponent's New Balance", value=f"${get_user_data(opponent_id)['balance']}", inline=True)
    await ctx.send(embed=embed)



@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def emojibomb(ctx, opponent: discord.Member, amount: int):
    """Place bombs to outsmart your opponent. Usage: !emojibomb <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't play against yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="💣 Emoji Bomb Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} for ${amount}!\n{opponent.mention}, accept with ✅ within 30s!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check_reaction(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    board = [["⬜" for _ in range(3)] for _ in range(3)]
    players = {user_id: "💣", opponent_id: "💥"}
    turn = user_id

    def display_board():
        return "\n".join(" ".join(row) for row in board)

    def check_boom():
        for i in range(3):
            if board[i].count("💣") == 3 or board[i].count("💥") == 3: return True
            if [board[j][i] for j in range(3)].count("💣") == 3 or [board[j][i] for j in range(3)].count("💥") == 3: return True
        if [board[i][i] for i in range(3)].count("💣") == 3 or [board[i][i] for i in range(3)].count("💥") == 3: return True
        if [board[i][2-i] for i in range(3)].count("💣") == 3 or [board[i][2-i] for i in range(3)].count("💥") == 3: return True
        return False

    embed = discord.Embed(title="💣 Emoji Bomb", color=0x3498db)
    while True:
        embed.description = f"{display_board()}\n<@{turn}>'s turn ({players[turn]}). Place bomb (e.g., '1 1') within 30s!"
        await msg.edit(embed=embed)

        def check_msg(m):
            return m.author.id == turn and m.channel == ctx.channel and len(m.content.split()) == 2 and all(x.isdigit() and 1 <= int(x) <= 3 for x in m.content.split())

        try:
            move = await bot.wait_for("message", timeout=30.0, check=check_msg)
            x, y = [int(n) - 1 for n in move.content.split()]
            await move.delete()
            if board[x][y] == "⬜":
                board[x][y] = players[turn]
                if check_boom():
                    winner_id = opponent_id if turn == user_id else user_id  # Opponent wins if current player triggers
                    break
                turn = opponent_id if turn == user_id else user_id
            else:
                await ctx.send(f"<@{turn}>, that spot is taken!", delete_after=5)
        except asyncio.TimeoutError:
            await ctx.send(f"<@{turn}> took too long! Forfeit!")
            winner_id = opponent_id if turn == user_id else user_id
            break
        if all(cell != "⬜" for row in board for cell in row):
            winner_id = None  # Tie
            break

    payout = amount * 2 if winner_id else 0
    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="💣 Emoji Bomb Result",
        description=f"{display_board()}\n{'<@' + str(winner_id) + '> wins $' + str(payout) if winner_id else 'Tie! No payout.'}",
        color=0x2ecc71 if winner_id else 0xe74c3c
    )
    await msg.edit(embed=embed)

    
@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def crystalclash(ctx, opponent: discord.Member, amount: int):
    """Clash crystals with hidden powers. Usage: !crystalclash <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't clash with yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="💎 Crystal Clash Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} for ${amount}!\n{opponent.mention}, accept with ✅ within 30s!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check_reaction(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    crystals = {"🔴": 3, "🟢": 5, "🔵": 7}  # Red: 3, Green: 5, Blue: 7
    options = "Pick a crystal in DM: `red` (🔴), `green` (🟢), or `blue` (🔵)"

    for player in [ctx.author, opponent]:
        await player.send(embed=discord.Embed(title="💎 Crystal Clash", description=options, color=0x3498db))

    def check_dm(m):
        return m.channel.type == discord.ChannelType.private and m.content.lower() in ["red", "green", "blue"]

    try:
        user_task = bot.wait_for("message", timeout=30.0, check=lambda m: m.author == ctx.author and check_dm(m))
        opp_task = bot.wait_for("message", timeout=30.0, check=lambda m: m.author == opponent and check_dm(m))
        user_msg, opp_msg = await asyncio.gather(user_task, opp_task)
        user_choice = {"red": "🔴", "green": "🟢", "blue": "🔵"}[user_msg.content.lower()]
        opp_choice = {"red": "🔴", "green": "🟢", "blue": "🔵"}[opp_msg.content.lower()]
    except asyncio.TimeoutError:
        await ctx.send("❌ One or both players didn’t choose in time!")
        return

    user_power = crystals[user_choice] * (2 if random.random() < 0.1 else 1)  # 10% crit chance
    opp_power = crystals[opp_choice] * (2 if random.random() < 0.1 else 1)

    if user_power > opp_power:
        winner_id = user_id
        payout = amount * 2
        result = f"{ctx.author.mention} wins!"
    elif opp_power > user_power:
        winner_id = opponent_id
        payout = amount * 2
        result = f"{opponent.mention} wins!"
    else:
        winner_id = None
        payout = 0
        result = "Tie!"

    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="💎 Crystal Clash Result",
        description=f"{ctx.author.mention}: {user_choice} ({user_power})\n{opponent.mention}: {opp_choice} ({opp_power})\n{result}\n{'Won' if winner_id else 'Payout'}: ${payout}",
        color=0x2ecc71 if winner_id else 0xe74c3c
    )
    await ctx.send(embed=embed)

    
@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def pirateplunder(ctx, opponent: discord.Member, amount: int):
    """Plunder treasure until a trap is hit. Usage: !pirateplunder <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't plunder against yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="🏴‍☠️ Pirate Plunder Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} for ${amount}!\n{opponent.mention}, accept with ✅ within 30s!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check_reaction(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    pile = [amount * i for i in [0.5, 1, 1.5, 2, 0]] * 2  # 10 items: loot + 2 traps (0)
    random.shuffle(pile)
    user_loot = 0
    opp_loot = 0
    turn = user_id

    embed = discord.Embed(title="🏴‍☠️ Pirate Plunder", color=0x3498db)
    while pile:
        embed.description = f"Pile: {len(pile)} treasures left\n{ctx.author.mention}: ${user_loot}\n{opponent.mention}: ${opp_loot}\n<@{turn}> plunders with ✅ or passes with ❌ (30s)"
        await msg.edit(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user.id == turn and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

        try:
            reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
            await msg.clear_reactions()
            if str(reaction.emoji) == "✅":
                loot = pile.pop()
                if loot == 0:
                    embed.description += f"\n<@{turn}> hit a trap! Game over!"
                    break
                if turn == user_id:
                    user_loot += loot
                else:
                    opp_loot += loot
            turn = opponent_id if turn == user_id else user_id
        except asyncio.TimeoutError:
            embed.description += f"\n<@{turn}> took too long! Game over!"
            break

    winner_id = user_id if user_loot > opp_loot else opponent_id if opp_loot > user_loot else None
    payout = amount * 2 if winner_id else 0
    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="🏴‍☠️ Pirate Plunder Result",
        description=f"{ctx.author.mention}: ${user_loot}\n{opponent.mention}: ${opp_loot}\n{'<@' + str(winner_id) + '> wins $' + str(payout) if winner_id else 'Tie! No payout.'}",
        color=0x2ecc71 if winner_id else 0xe74c3c
    )
    await msg.edit(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def spellduel(ctx, opponent: discord.Member, amount: int):
    """Duel with magical spells. Usage: !spellduel <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't duel yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="✨ Spell Duel Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} for ${amount}!\n{opponent.mention}, accept with ✅ within 30s!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check_reaction(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    spells = {"🔥": 3, "❄️": 2, "⚡": 4}  # Damage values
    user_hp = 10
    opp_hp = 10
    turn = user_id

    embed = discord.Embed(title="✨ Spell Duel", color=0x3498db)
    while user_hp > 0 and opp_hp > 0:
        embed.description = f"{ctx.author.mention}: {user_hp} HP\n{opponent.mention}: {opp_hp} HP\n<@{turn}>'s turn. Cast in DM: `fire` (🔥), `ice` (❄️), `lightning` (⚡) (30s)"
        await msg.edit(embed=embed)
        await bot.get_user(turn).send(embed=discord.Embed(title="✨ Cast Your Spell", description="Reply with `fire`, `ice`, or `lightning`", color=0x3498db))

        def check_dm(m):
            return m.channel.type == discord.ChannelType.private and m.author.id == turn and m.content.lower() in ["fire", "ice", "lightning"]

        try:
            spell_msg = await bot.wait_for("message", timeout=30.0, check=check_dm)
            spell = {"fire": "🔥", "ice": "❄️", "lightning": "⚡"}[spell_msg.content.lower()]
            damage = spells[spell] * (2 if random.random() < 0.1 else 1)  # 10% crit chance
            if turn == user_id:
                opp_hp -= damage
                action = f"{ctx.author.mention} casts {spell} for {damage} damage!"
            else:
                user_hp -= damage
                action = f"{opponent.mention} casts {spell} for {damage} damage!"
            embed.description = f"{ctx.author.mention}: {user_hp} HP\n{opponent.mention}: {opp_hp} HP\n{action}"
            turn = opponent_id if turn == user_id else user_id
        except asyncio.TimeoutError:
            await ctx.send(f"<@{turn}> took too long! Forfeit!")
            winner_id = opponent_id if turn == user_id else user_id
            break
    else:
        winner_id = user_id if opp_hp <= 0 else opponent_id if user_hp <= 0 else None

    payout = amount * 2 if winner_id else 0
    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="✨ Spell Duel Result",
        description=f"{ctx.author.mention}: {user_hp} HP\n{opponent.mention}: {opp_hp} HP\n{'<@' + str(winner_id) + '> wins $' + str(payout) if winner_id else 'Tie! No payout.'}",
        color=0x2ecc71 if winner_id else 0xe74c3c
    )
    await msg.edit(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def auctionfrenzy(ctx, opponent: discord.Member, amount: int):
    """Bid on mystery items in an auction. Usage: !auctionfrenzy <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't auction against yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="📦 Auction Frenzy Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} for ${amount}!\n{opponent.mention}, accept with ✅ within 30s!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check_reaction(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    items = [("💍 Ring", amount * 2), ("🖼️ Painting", amount * 1.5), ("🗿 Statue", amount), ("📜 Scroll", amount * 0.5)]
    user_total = 0
    opp_total = 0
    turn = user_id

    embed = discord.Embed(title="📦 Auction Frenzy", color=0x3498db)
    for item, value in items:
        user_bid = 0
        opp_bid = 0
        for player_id in [user_id, opponent_id]:
            embed.description = f"Item: {item} (Value: ??)\n{ctx.author.mention}: ${user_total}\n{opponent.mention}: ${opp_total}\n<@{player_id}>, bid 0-{amount} in DM (30s)"
            await msg.edit(embed=embed)
            await bot.get_user(player_id).send(embed=discord.Embed(title="📦 Place Your Bid", description=f"Bid 0-{amount} for {item}", color=0x3498db))

            def check_dm(m):
                return m.channel.type == discord.ChannelType.private and m.author.id == player_id and m.content.isdigit() and 0 <= int(m.content) <= amount

            try:
                bid_msg = await bot.wait_for("message", timeout=30.0, check=check_dm)
                bid = int(bid_msg.content)
                if player_id == user_id:
                    user_bid = bid
                else:
                    opp_bid = bid
            except asyncio.TimeoutError:
                pass

        if user_bid > opp_bid:
            user_total += value
            result = f"{ctx.author.mention} wins {item}!"
        elif opp_bid > user_bid:
            opp_total += value
            result = f"{opponent.mention} wins {item}!"
        else:
            result = f"Tie! {item} goes to no one."
        embed.description = f"Item: {item}\n{ctx.author.mention} bid: ${user_bid}\n{opponent.mention} bid: ${opp_bid}\n{result}"
        await msg.edit(embed=embed)
        await asyncio.sleep(2)

    winner_id = user_id if user_total > opp_total else opponent_id if opp_total > user_total else None
    payout = amount * 2 if winner_id else 0
    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    if winner_id:
        update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="📦 Auction Frenzy Result",
        description=f"{ctx.author.mention}: ${user_total}\n{opponent.mention}: ${opp_total}\n{'<@' + str(winner_id) + '> wins $' + str(payout) if winner_id else 'Tie! No payout.'}",
        color=0x2ecc71 if winner_id else 0xe74c3c
    )
    await msg.edit(embed=embed)


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def timebomb(ctx, opponent: discord.Member, amount: int):
    """Pass a ticking bomb until it explodes. Usage: !timebomb <@opponent> <amount>"""
    user_id = ctx.author.id
    opponent_id = opponent.id
    user_data = get_user_data(user_id)
    opponent_data = get_user_data(opponent_id)

    if user_id == opponent_id:
        await ctx.send("❌ You can't play against yourself!")
        return
    if not (MIN_BET <= amount <= MAX_BET and amount <= user_data['balance'] and amount <= opponent_data['balance']):
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}. Your balance: ${user_data['balance']}, Opponent's: ${opponent_data['balance']}")
        return

    embed = discord.Embed(
        title="⏰ Time Bomb Challenge",
        description=f"{ctx.author.mention} challenges {opponent.mention} to a Time Bomb duel for ${amount}!\n{opponent.mention}, accept with ✅ within 30 seconds!",
        color=0x3498db
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check_reaction(reaction, user):
        return user == opponent and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")
        return

    timer = 25  # Starting timer reduced for faster games
    turn = user_id
    fuse_boost_used = False  # One-time random boost flag

    embed = discord.Embed(title="⏰ Time Bomb", color=0x3498db)
    while timer > 0:
        embed.description = f"Timer: {timer}s\nHeld by: <@{turn}>\nSubtract 1-5 seconds (e.g., `3`) within 30s!"
        await msg.edit(embed=embed)

        def check_msg(m):
            return m.author.id == turn and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= min(5, timer)

        try:
            move = await bot.wait_for("message", timeout=30.0, check=check_msg)
            subtract = int(move.content)
            await move.delete()

            # Random fuse boost: 20% chance to add 5-10s (once per game)
            if not fuse_boost_used and random.random() < 0.2:
                boost = random.randint(5, 10)
                timer += boost
                fuse_boost_used = True
                embed.description = f"Timer: {timer}s\nFuse boost! +{boost}s added!\n<@{turn}> subtracted {subtract}s."
            else:
                embed.description = f"Timer: {timer}s\n<@{turn}> subtracted {subtract}s."

            timer -= subtract
            turn = opponent_id if turn == user_id else user_id
            await msg.edit(embed=embed)
            await asyncio.sleep(1)  # Brief pause for readability
        except asyncio.TimeoutError:
            embed.description = f"Timer: {timer}s\n<@{turn}> took too long! Bomb explodes!"
            await msg.edit(embed=embed)
            break

    winner_id = opponent_id if turn == user_id else user_id  # Winner is the one not holding it
    payout = amount * 2
    update_user_data(user_id, {'balance': user_data['balance'] - amount + (payout if winner_id == user_id else 0)})
    update_user_data(opponent_id, {'balance': opponent_data['balance'] - amount + (payout if winner_id == opponent_id else 0)})
    update_user_data(winner_id, {'winnings': get_user_data(winner_id)['winnings'] + payout})
    add_xp(user_id, amount // 10)
    add_xp(opponent_id, amount // 10)

    embed = discord.Embed(
        title="⏰ Time Bomb Result",
        description=f"Bomb exploded on <@{turn}> after reaching {timer}s!\n<@{winner_id}> wins ${payout}!",
        color=0x2ecc71
    )
    embed.add_field(name="Your New Balance", value=f"${get_user_data(user_id)['balance']}", inline=True)
    embed.add_field(name="Opponent's New Balance", value=f"${get_user_data(opponent_id)['balance']}", inline=True)
    await msg.edit(embed=embed)


# can add more  mini games  here line 2448


@bot.command()
async def lottery(ctx, tickets: int):
    """Buy lottery tickets. Usage: !lottery <tickets>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if tickets <= 0 or tickets * LOTTERY_TICKET_PRICE > user_data['balance']:
        await ctx.send(f"❌ Invalid number of tickets! Cost: ${LOTTERY_TICKET_PRICE} per ticket. Balance: ${user_data['balance']}")
        return

    cost = tickets * LOTTERY_TICKET_PRICE
    new_balance = user_data['balance'] - cost
    update_user_data(user_id, {
        'balance': new_balance,
        'lottery_tickets': user_data['lottery_tickets'] + tickets
    })
    update_lottery_jackpot(cost // 2)

    embed = discord.Embed(
        title="🎰 Lottery",
        description=f"Purchased {tickets} ticket(s) for ${cost}\nCurrent jackpot: ${get_lottery_jackpot()}\nYour tickets: {user_data['lottery_tickets'] + tickets}",
        color=0x3498db
    )
    embed.add_field(name="New Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)

## Economy Commands

@bot.command()
async def shop(ctx):
    """View available shop items. Usage: !shop"""
    embed = discord.Embed(title="🛒 Paradox Shop", color=0x3498db)
    for item_id, item in SHOP_ITEMS.items():
        embed.add_field(
            name=f"{item['name']} (${item['price']})",
            value=item['description'],
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, item_id: str):
    """Buy an item from the shop. Usage: !buy <item_id>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    item = SHOP_ITEMS.get(item_id.lower())

    if not item:
        await ctx.send("❌ Item not found!")
        return
    if user_data['balance'] < item['price']:
        await ctx.send(f"❌ Insufficient funds! Need ${item['price']}, have ${user_data['balance']}")
        return

    inventory = json.loads(user_data['inventory'])
    inventory[item_id] = inventory.get(item_id, 0) + 1
    update_user_data(user_id, {
        'balance': user_data['balance'] - item['price'],
        'inventory': json.dumps(inventory)
    })
    update_mission_progress(user_id, "weekly", "spent", item['price'])
    embed = discord.Embed(
        title="🛒 Purchase",
        description=f"Purchased {item['name']} for ${item['price']}!",
        color=0x2ecc71
    )
    embed.add_field(name="New Balance", value=f"${user_data['balance'] - item['price']}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx):
    """View your inventory. Usage: !inventory"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    if not inventory:
        await ctx.send("❌ Your inventory is empty!")
        return
    embed = discord.Embed(title="🎒 Inventory", color=0x3498db)
    for item_id, qty in inventory.items():
        item = SHOP_ITEMS.get(item_id, {"name": item_id})
        embed.add_field(name=item['name'], value=f"Quantity: {qty}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def craft(ctx, recipe_id: str):
    """Craft an item. Usage: !craft <recipe_id>"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    recipe_id = recipe_id.lower()

    if recipe_id not in CRAFTING_RECIPES:
        await ctx.send("❌ Invalid recipe! Available: " + ", ".join(CRAFTING_RECIPES.keys()))
        return
    if not can_craft(user_id, recipe_id):
        recipe = CRAFTING_RECIPES[recipe_id]
        reqs = ", ".join(f"{qty} {SHOP_ITEMS.get(item, {'name': item})['name']}" for item, qty in recipe['ingredients'].items())
        await ctx.send(f"❌ You need: {reqs}")
        return

    craft_item(user_id, recipe_id)
    embed = discord.Embed(
        title="🔨 Crafting",
        description=f"Crafted a {recipe_id.replace('_', ' ').title()}!",
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

@bot.command()
async def trade(ctx, member: discord.Member, offer: str, request: str):
    """Offer a trade to another user. Usage: !trade <@user> <offer> <request>"""
    user_id = ctx.author.id
    receiver_id = member.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])

    offer_items = dict(item.split(':') for item in offer.split(','))
    request_items = dict(item.split(':') for item in request.split(','))
    for item, qty in offer_items.items():
        qty = int(qty)
        if inventory.get(item, 0) < qty:
            await ctx.send(f"❌ You don't have enough {item}!")
            return

    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT INTO trade_offers (sender_id, receiver_id, offered_items, requested_items) VALUES (?, ?, ?, ?)',
              (user_id, receiver_id, json.dumps(offer_items), json.dumps(request_items)))
    offer_id = c.lastrowid
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="🤝 Trade Offer",
        description=f"{ctx.author.mention} offers {offer} to {member.mention} for {request}\nAccept with `!accept {offer_id}` or decline with `!decline {offer_id}`",
        color=0x3498db
    )
    await ctx.send(embed=embed)

@bot.command()
async def accept(ctx, offer_id: int):
    """Accept a trade offer. Usage: !accept <offer_id>"""
    user_id = ctx.author.id
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM trade_offers WHERE offer_id = ? AND receiver_id = ? AND status = "pending"', (offer_id, user_id))
    trade = c.fetchone()
    if not trade:
        await ctx.send("❌ Invalid or expired trade offer!")
        conn.close()
        return

    sender_id, _, offered_items, requested_items, _ = trade[1:]
    offered_items = json.loads(offered_items)
    requested_items = json.loads(requested_items)

    sender_data = get_user_data(sender_id)
    receiver_data = get_user_data(user_id)
    sender_inventory = json.loads(sender_data['inventory'])
    receiver_inventory = json.loads(receiver_data['inventory'])

    if not all(sender_inventory.get(item, 0) >= int(qty) for item, qty in offered_items.items()) or \
       not all(receiver_inventory.get(item, 0) >= int(qty) for item, qty in requested_items.items()):
        await ctx.send("❌ One or both parties no longer have the required items!")
        c.execute('UPDATE trade_offers SET status = "declined" WHERE offer_id = ?', (offer_id,))
        conn.commit()
        conn.close()
        return

    for item, qty in offered_items.items():
        qty = int(qty)
        sender_inventory[item] -= qty
        receiver_inventory[item] = receiver_inventory.get(item, 0) + qty
    for item, qty in requested_items.items():
        qty = int(qty)
        receiver_inventory[item] -= qty
        sender_inventory[item] = sender_inventory.get(item, 0) + qty

    update_user_data(sender_id, {'inventory': json.dumps(sender_inventory)})
    update_user_data(user_id, {'inventory': json.dumps(receiver_inventory)})
    c.execute('UPDATE trade_offers SET status = "accepted" WHERE offer_id = ?', (offer_id,))
    conn.commit()
    conn.close()

    embed = discord.Embed(
        title="🤝 Trade Accepted",
        description=f"Trade {offer_id} between {ctx.author.mention} and <@{sender_id}> completed!",
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

@bot.command()
async def decline(ctx, offer_id: int):
    """Decline a trade offer. Usage: !decline <offer_id>"""
    user_id = ctx.author.id
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM trade_offers WHERE offer_id = ? AND receiver_id = ? AND status = "pending"', (offer_id, user_id))
    if not c.fetchone():
        await ctx.send("❌ Invalid or expired trade offer!")
    else:
        c.execute('UPDATE trade_offers SET status = "declined" WHERE offer_id = ?', (offer_id,))
        conn.commit()
        embed = discord.Embed(
            title="🤝 Trade Declined",
            description=f"Trade {offer_id} declined by {ctx.author.mention}.",
            color=0xe74c3c
        )
        await ctx.send(embed=embed)
    conn.close()

@bot.command()
async def bank(ctx, action: str, amount: int = None):
    """Manage your bank account. Usage: !bank <deposit|withdraw|balance> [amount]"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    bank_balance = user_data.get('bank_balance', 0)

    if action == "deposit" and amount:
        if amount <= 0 or amount > user_data['balance']:
            await ctx.send("❌ Invalid deposit amount!")
            return
        update_user_data(user_id, {
            'balance': user_data['balance'] - amount,
            'bank_balance': bank_balance + amount
        })
        embed = discord.Embed(
            title="🏦 Bank Deposit",
            description=f"Deposited ${amount} into your bank.",
            color=0x2ecc71
        )
        embed.add_field(name="Bank Balance", value=f"${bank_balance + amount}", inline=True)
        embed.add_field(name="Cash Balance", value=f"${user_data['balance'] - amount}", inline=True)
        await ctx.send(embed=embed)
    elif action == "withdraw" and amount:
        if amount <= 0 or amount > bank_balance:
            await ctx.send("❌ Invalid withdraw amount!")
            return
        update_user_data(user_id, {
            'balance': user_data['balance'] + amount,
            'bank_balance': bank_balance - amount
        })
        embed = discord.Embed(
            title="🏦 Bank Withdrawal",
            description=f"Withdrew ${amount} from your bank.",
            color=0x2ecc71
        )
        embed.add_field(name="Bank Balance", value=f"${bank_balance - amount}", inline=True)
        embed.add_field(name="Cash Balance", value=f"${user_data['balance'] + amount}", inline=True)
        await ctx.send(embed=embed)
    elif action == "balance":
        embed = discord.Embed(
            title="🏦 Bank Balance",
            description=f"Your bank balance: ${bank_balance}\nCash balance: ${user_data['balance']}",
            color=0x3498db
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Invalid action! Use 'deposit', 'withdraw', or 'balance'.")

## Social Commands

@bot.command()
@commands.cooldown(1, 60, commands.BucketType.channel)
async def tournament(ctx, game: str):
    """Start a tournament. Usage: !tournament <game>"""
    channel_id = ctx.channel.id
    game = game.lower()
    if game not in ["slots", "coinflip"]:
        await ctx.send("❌ Only 'slots' and 'coinflip' tournaments supported!")
        return
    tournament_data = get_tournament_data(channel_id)
    if tournament_data and tournament_data['active']:
        await ctx.send("❌ A tournament is already active!")
        return
    update_tournament_data(channel_id, {
        'game_type': game,
        'players': json.dumps({}),
        'scores': json.dumps({}),
        'rounds': 3,
        'current_round': 0,
        'active': 1,
        'prize_pool': 0
    })
    embed = discord.Embed(
        title=f"🏆 {game.capitalize()} Tournament",
        description="Join with `!join`. Starts in 60 seconds!",
        color=0x3498db
    )
    await ctx.send(embed=embed)
    await asyncio.sleep(60)
    await run_tournament(ctx.channel)

@bot.command()
async def join(ctx):
    """Join an active tournament. Usage: !join"""
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    tournament = get_tournament_data(channel_id)
    if not tournament or not tournament['active'] or tournament['current_round'] > 0:
        await ctx.send("❌ No active tournament or it has already started!")
        return
    if user_data['balance'] < TOURNAMENT_ENTRY_FEE:
        await ctx.send(f"❌ Entry fee is ${TOURNAMENT_ENTRY_FEE}. Balance: ${user_data['balance']}")
        return

    players = json.loads(tournament['players'])
    if str(user_id) in players:
        await ctx.send("❌ You’ve already joined!")
        return
    players[str(user_id)] = 0
    update_tournament_data(channel_id, {
        'players': json.dumps(players),
        'prize_pool': tournament['prize_pool'] + TOURNAMENT_ENTRY_FEE
    })
    update_user_data(user_id, {'balance': user_data['balance'] - TOURNAMENT_ENTRY_FEE})
    embed = discord.Embed(
        title="🏆 Tournament",
        description=f"{ctx.author.mention} joined the {tournament['game_type']} tournament!\nPrize pool: ${tournament['prize_pool'] + TOURNAMENT_ENTRY_FEE}",
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

async def run_tournament(channel):
    """Run the tournament rounds and determine the winner."""
    tournament = get_tournament_data(channel.id)
    if not tournament or len(json.loads(tournament['players'])) < 2:
        await channel.send("❌ Tournament cancelled: Not enough players!")
        update_tournament_data(channel.id, {'active': 0})
        return

    game_type = tournament['game_type']
    rounds = tournament['rounds']
    for round_num in range(1, rounds + 1):
        players = json.loads(tournament['players'])
        scores = json.loads(tournament['scores'])
        embed = discord.Embed(
            title=f"🏆 {game_type.capitalize()} Tournament - Round {round_num}",
            description="Results:",
            color=0x3498db
        )
        for player_id in players:
            if game_type == "slots":
                slots = spin_slots(1)
                winnings, _, _ = check_win(slots)
                scores[player_id] = scores.get(player_id, 0) + winnings
                embed.add_field(name=f"<@{player_id}>", value=f"{' '.join(slots[0])} (+${winnings})", inline=False)
            elif game_type == "coinflip":
                result = random.choice([True, False])
                score = 100 if result else 0
                scores[player_id] = scores.get(player_id, 0) + score
                embed.add_field(name=f"<@{player_id}>", value=f"{'Heads' if result else 'Tails'} (+${score})", inline=False)
        update_tournament_data(channel.id, {
            'scores': json.dumps(scores),
            'current_round': round_num
        })
        await channel.send(embed=embed)
        await asyncio.sleep(5)

    scores = json.loads(tournament['scores'])
    winner_id = max(scores, key=scores.get)
    prize = tournament['prize_pool']
    winner_data = get_user_data(int(winner_id))
    update_user_data(int(winner_id), {
        'balance': winner_data['balance'] + prize,
        'winnings': winner_data['winnings'] + prize
    })
    embed = discord.Embed(
        title=f"🏆 {game_type.capitalize()} Tournament Ended",
        description=f"Winner: <@{winner_id}> with {scores[winner_id]} points!\nPrize: ${prize}",
        color=0x2ecc71
    )
    for player_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        embed.add_field(name=f"<@{player_id}>", value=f"Score: {score}", inline=False)
    await channel.send(embed=embed)
    update_tournament_data(channel.id, {'active': 0})

## Utility Commands

@bot.command()
async def daily(ctx):
    """Claim your daily reward. Usage: !daily"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    now = datetime.utcnow()
    last_claim = user_data['daily_claim']

    if not last_claim or (datetime.fromisoformat(last_claim) + timedelta(days=1)) <= now:
        reward = DAILY_REWARD
        streaks = json.loads(user_data['streaks'])
        streaks['daily'] = streaks.get('daily', 0) + 1
        if streaks['daily'] >= 7 and "daily_streak" not in json.loads(user_data['achievements']):
            achievements = json.loads(user_data['achievements'])
            achievements.append("daily_streak")
            update_user_data(user_id, {'achievements': json.dumps(achievements)})
        update_user_data(user_id, {
            'balance': user_data['balance'] + reward,
            'daily_claim': now.isoformat(),
            'streaks': json.dumps(streaks)
        })
        embed = discord.Embed(
            title="💰 Daily Reward",
            description=f"Claimed ${reward}! Daily streak: {streaks['daily']}",
            color=0x2ecc71
        )
        embed.add_field(name="New Balance", value=f"${user_data['balance'] + reward}", inline=True)
        await ctx.send(embed=embed)
    else:
        time_left = (datetime.fromisoformat(last_claim) + timedelta(days=1)) - now
        await ctx.send(f"⏳ Wait {time_left.seconds // 3600}h {(time_left.seconds % 3600) // 60}m")

@bot.command()
async def profile(ctx, member: discord.Member = None):
    """View your or another user's profile. Usage: !profile [@user]"""
    user_id = member.id if member else ctx.author.id
    user_data = get_user_data(user_id)
    user = member or ctx.author
    embed = discord.Embed(
        title=f"👤 {user.name}'s Profile",
        description=f"Level: {user_data['level']}\nXP: {user_data['xp']}/{100 * user_data['level']}\nBalance: ${user_data['balance']}\nBank: ${user_data['bank_balance']}\nWinnings: ${user_data['winnings']}",
        color=0x3498db
    )
    achievements = json.loads(user_data['achievements'])
    if achievements:
        embed.add_field(name="Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} {ACHIEVEMENTS[a]['name']}" for a in achievements), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def balance(ctx, member: discord.Member = None):
    """Check your or another user's balance. Usage: !balance [@user]"""
    user_id = member.id if member else ctx.author.id
    user_data = get_user_data(user_id)
    user = member or ctx.author
    embed = discord.Embed(
        title=f"💰 {user.name}'s Balance",
        description=f"Cash: ${user_data['balance']}\nBank: ${user_data['bank_balance']}",
        color=0x3498db
    )
    await ctx.send(embed=embed)

@bot.command()
async def top(ctx):
    """View the top 10 players by balance. Usage: !top"""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT id, balance + bank_balance AS total FROM users ORDER BY total DESC LIMIT 10')
    leaderboard = c.fetchall()
    conn.close()

    embed = discord.Embed(title="🏅 Leaderboard", color=0x3498db)
    for i, (user_id, total) in enumerate(leaderboard, 1):
        user = await bot.fetch_user(user_id)
        embed.add_field(name=f"{i}. {user.name}", value=f"${total}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def achievements(ctx):
    """View all possible achievements. Usage: !achievements"""
    embed = discord.Embed(title="🏆 Achievements", color=0x3498db)
    for ach_id, ach in ACHIEVEMENTS.items():
        embed.add_field(name=f"{ach['emoji']} {ach['name']}", value=ach['description'], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def give(ctx, member: discord.Member, amount: int):
    """Transfer coins to another user. Usage: !give <@user> <amount>"""
    user_id = ctx.author.id
    receiver_id = member.id
    user_data = get_user_data(user_id)
    receiver_data = get_user_data(receiver_id)

    if amount <= 0 or amount > user_data['balance']:
        await ctx.send(f"❌ Invalid amount! Balance: ${user_data['balance']}")
        return
    if user_id == receiver_id:
        await ctx.send("❌ You can't give coins to yourself!")
        return

    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    update_user_data(receiver_id, {'balance': receiver_data['balance'] + amount})
    embed = discord.Embed(
        title="💸 Coin Transfer",
        description=f"{ctx.author.mention} gave ${amount} to {member.mention}!",
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

@bot.command()
async def missions(ctx):
    """View your active missions. Usage: !missions"""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    missions = json.loads(user_data['missions']) or {}
    embed = discord.Embed(title="📜 Missions", color=0x3498db)

    for mission_type in MISSIONS:
        if mission_type not in missions:
            missions[mission_type] = {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS[mission_type]}
        for mission in MISSIONS[mission_type]:
            mission_id = mission["id"]
            progress = missions[mission_type][mission_id]["progress"]
            completed = missions[mission_type][mission_id]["completed"]
            req = list(mission["requirements"].items())[0]
            embed.add_field(
                name=f"{mission['name']} ({mission_type.capitalize()})",
                value=f"{mission['description']}\nProgress: {progress}/{req[1]} {'✅' if completed else ''}",
                inline=False
            )
    update_user_data(user_id, {'missions': json.dumps(missions)})
    await ctx.send(embed=embed)

# --- Utility Commands ---

@bot.command()
async def paradox(ctx, action: str = None, channel: discord.TextChannel = None, *, message: str = None):
    """Main command for Paradox Casino Machine. Usage: !paradox [action] [#channel] [message]"""
    # Bot uptime
    uptime = datetime.utcnow() - bot_start_time  # Assume bot_start_time is set globally at startup
    uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"

    # User data
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    # Base embed
    embed = discord.Embed(
        title="🎰 Paradox Casino Machine",
        description="Welcome to the ultimate casino experience!",
        color=0x3498db
    )
    embed.set_footer(text=f"Uptime: {uptime_str} | Guilds: {len(bot.guilds)}")

    if action is None:
        # Default view: Overview
        embed.add_field(
            name="Your Stats",
            value=f"Balance: ${user_data['balance']}\nXP: {user_data['xp']}\nWinnings: ${user_data['winnings']}",
            inline=True
        )
        embed.add_field(
            name="Solo Games",
            value="`!bet` - Slots\n"
                  "`!slotstreak <amount>` - Streak slots\n"
                  "`!treasurehunt <amount>` - Dig for treasure\n"
                  "`!war <amount>` - Card war vs bot\n"
                  "`!jackpotguess <amount> <1-50>` - Guess the jackpot",
            inline=True
        )
        embed.add_field(
            name="PvP Games",
            value="`!diceduel <@opponent> <amount>` - Dice duel\n"
                  "`!roulettespinoff <@opponent> <amount>` - Roulette duel\n"
                  "`!emojibomb <@opponent> <amount>` - Place bombs\n"
                  "`!crystalclash <@opponent> <amount>` - Clash crystals\n"
                  "`!pirateplunder <@opponent> <amount>` - Plunder treasure\n"
                  "`!spellduel <@opponent> <amount>` - Spell duel\n"
                  "`!auctionfrenzy <@opponent> <amount>` - Bid on items\n"
                  "`!timebomb <@opponent> <amount>` - Pass a bomb",
            inline=True
        )
        embed.add_field(
            name="Commands",
            value="`!paradox settings [#channel] [message]` - Set shop reset announcement (admin)\n"
                  "`!help` - Full command list",
            inline=False
        )
    elif action.lower() == "settings":
        # Announcement settings (admin only)
        if not ctx.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only administrators can configure announcement settings.",
                color=0xe74c3c
            )
        else:
            channel = channel or ctx.channel  # Default to current channel
            set_announcement_settings(ctx.guild.id, channel.id, message)
            embed = discord.Embed(
                title="📢 Shop Reset Announcement Settings Updated",
                description=f"Daily shop reset announcements will be sent to {channel.mention}.\n" +
                            (f"Custom message set: '{message}'" if message else "Using default: 'Daily shop is reset thx for gambling with us Regards Time_Walker.inc'"),
                color=0x2ecc71
            )
    else:
        embed = discord.Embed(
            title="❌ Invalid Action",
            description="Use `!paradox` for overview or `!paradox settings [#channel] [message]` to configure announcements.",
            color=0xe74c3c
        )

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def setannouncement(ctx, channel: discord.TextChannel = None, *, message: str = None):
    """Set the daily shop reset announcement channel and optional message. Usage: !setannouncement [#channel] [message]"""
    channel = channel or ctx.channel  # Default to current channel
    set_announcement_settings(ctx.guild.id, channel.id, message)
    embed = discord.Embed(
        title="📢 Shop Reset Announcement Settings Updated",
        description=f"Daily shop reset announcements will be sent to {channel.mention}.\n" +
                    (f"Custom message set: '{message}'" if message else "Using default: 'Daily shop is reset thx for gambling with us Regards Time_Walker.inc'"),
        color=0x2ecc71
    )
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    """Display the help menu."""
    embed = discord.Embed(title="🎰 Paradox Casino Help", description="Welcome to the Paradox Casino Machine!", color=0x3498db)
    embed.add_field(
        name="Utility",
        value="`!paradox` - Casino overview and settings\n"
              "`!setannouncement [#channel] [message]` - Set daily shop reset channel/message (admin)",
        inline=False
    )
    embed.add_field(
        name="Solo Games",
        value="`!bet` - Slots\n"
              "`!slotstreak <amount>` - Streak slots\n"
              "`!treasurehunt <amount>` - Dig for treasure\n"
              "`!war <amount>` - Card war vs bot\n"
              "`!jackpotguess <amount> <1-50>` - Guess the jackpot",
        inline=True
    )
    embed.add_field(
        name="PvP Games",
        value="`!diceduel <@opponent> <amount>` - Dice duel\n"
              "`!roulettespinoff <@opponent> <amount>` - Roulette duel\n"
              "`!emojibomb <@opponent> <amount>` - Place bombs\n"
              "`!crystalclash <@opponent> <amount>` - Clash crystals\n"
              "`!pirateplunder <@opponent> <amount>` - Plunder treasure\n"
              "`!spellduel <@opponent> <amount>` - Spell duel\n"
              "`!auctionfrenzy <@opponent> <amount>` - Bid on items\n"
              "`!timebomb <@opponent> <amount>` - Pass a bomb",
        inline=True
    )
    embed.set_footer(text="Paradox Casino Machine | Powered by Luck")
    await ctx.send(embed=embed)

uptime = datetime.utcnow() - bot_start_time
uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"    

# --- Background Tasks ---

async def casino_announcements():
    """Send periodic casino announcements."""
    await bot.wait_until_ready()
    announcements = [
        {"title": "🎰 Slot Frenzy!", "description": f"Spin `!bet` for a chance at the {JACKPOT_SYMBOL} jackpot!"},
        {"title": "🏆 Tournament Time!", "description": "Start a tournament with `!tournament slots` or `!tournament coinflip`!"},
        {"title": "🎱 Bingo Bash!", "description": "Play `!bingo` for big wins!"},
        {"title": "🎟️ Lottery Draw!", "description": f"Buy tickets with `!lottery`! Current jackpot: ${get_lottery_jackpot()}"}
    ]
    index = 0
    while not bot.is_closed():
        for guild in bot.guilds:
            channel = guild.system_channel or discord.utils.get(guild.text_channels, name='general')
            if channel and channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(**announcements[index], color=0xf1c40f)
                embed.set_footer(text="Paradox Casino Machine | Powered by Luck")
                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to send announcement to {guild.name}: {e}")
        index = (index + 1) % len(announcements)
        await asyncio.sleep(3600 * 6)  # Every 6 hours

async def daily_shop_reset():
    """Announce daily shop reset at midnight UTC."""
    await bot.wait_until_ready()
    default_message = "Daily shop is reset thx for gambling with us Regards Time_Walker.inc"
    while not bot.is_closed():
        now = datetime.utcnow()
        next_reset = (now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
        await asyncio.sleep((next_reset - now).total_seconds())  # Sleep until midnight UTC
        for guild in bot.guilds:
            settings = get_announcement_settings(guild.id)
            channel = (bot.get_channel(settings['channel_id']) if settings and settings['channel_id'] else
                       guild.system_channel or discord.utils.get(guild.text_channels, name='general'))
            if channel and channel.permissions_for(guild.me).send_messages:
                message = settings['message'] if settings and settings['message'] else default_message
                embed = discord.Embed(
                    title="🛒 Daily Shop Reset",
                    description=message,
                    color=0xf1c40f
                )
                embed.set_footer(text="Paradox Casino Machine | Powered by Luck")
                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to send shop reset announcement to {guild.name}: {e}")

async def lottery_draw_task():
    """Handle daily lottery draws."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(86400)  # Daily draw
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT id, lottery_tickets FROM users WHERE lottery_tickets > 0')
        players = c.fetchall()
        if players:
            total_tickets = sum(p[1] for p in players)
            winner_id = random.choices([p[0] for p in players], weights=[p[1] for p in players], k=1)[0]
            jackpot = get_lottery_jackpot()
            user_data = get_user_data(winner_id)
            update_user_data(winner_id, {
                'balance': user_data['balance'] + jackpot,
                'lottery_tickets': 0,
                'winnings': user_data['winnings'] + jackpot
            })
            c.execute('UPDATE users SET lottery_tickets = 0')
            c.execute('UPDATE lottery SET jackpot = 1000 WHERE rowid = 1')
            conn.commit()
            for guild in bot.guilds:
                channel = guild.system_channel
                if channel and channel.permissions_for(guild.me).send_messages:
                    embed = discord.Embed(
                        title="🎉 Lottery Winner!",
                        description=f"<@{winner_id}> has won the jackpot of ${jackpot}!",
                        color=0x2ecc71
                    )
                    await channel.send(embed=embed)
        conn.close()

async def bank_interest_task():
    """Apply daily interest to bank balances."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(86400)  # Daily
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT id, bank_balance FROM users WHERE bank_balance > 0')
        users = c.fetchall()
        for user_id, bank_balance in users:
            interest = int(bank_balance * BANK_INTEREST_RATE)
            c.execute('UPDATE users SET bank_balance = bank_balance + ? WHERE id = ?', (interest, user_id))
        conn.commit()
        conn.close()
        logger.info("Bank interest applied to all users.")

async def mission_reset_task():
    """Reset daily missions."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(86400)  # Daily
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT id, missions FROM users')
        users = c.fetchall()
        for user_id, missions_json in users:
            missions = json.loads(missions_json) or {}
            missions['daily'] = {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS['daily']}
            c.execute('UPDATE users SET missions = ? WHERE id = ?', (json.dumps(missions), user_id))
        conn.commit()
        conn.close()
        logger.info("Daily missions reset for all users.")


# --- Bot Startup ---

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot.loop.create_task(casino_announcements())
    bot.loop.create_task(daily_shop_reset())
    bot.loop.create_task(lottery_draw_task())
    bot.loop.create_task(bank_interest_task())
    bot.loop.create_task(mission_reset_task())
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))

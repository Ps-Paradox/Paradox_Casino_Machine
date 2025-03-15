# Import required libraries for bot functionality, database management, and threading
import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
import os
import sqlite3
import json
from flask import Flask, request
import threading
import logging
import time
import math

# --- Flask Setup for Uptime Monitoring ---
app = Flask(__name__)

@app.route('/')
def home():
    """Root endpoint to confirm the bot is operational."""
    return "Paradox Casino Bot is fully operational and ready for action!"

@app.route('/health')
def health_check():
    """Endpoint to perform a health check on the bot's status."""
    return json.dumps({"status": "healthy", "uptime": time.time() - start_time}), 200

@app.route('/<path:path>')
def catch_all(path):
    """Catch-all endpoint to handle invalid paths with a custom message."""
    print(f"Received request for invalid path: {path}")
    return f"Error: Path '{path}' not found, but the server remains active!", 404

def run_flask():
    """Run the Flask server in a separate thread to ensure bot uptime monitoring."""
    port = int(os.environ.get('PORT', 8080))
    try:
        print(f"Initializing Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask server encountered an error: {e}")

start_time = time.time()
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('casino_bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger('ParadoxCasinoBot')

# --- Bot Configuration ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# --- Game Constants ---
MAX_LINES = 3
MAX_BET = 1000
MIN_BET = 10
DAILY_REWARD = 500
JACKPOT_SYMBOL = '7️⃣'
JACKPOT_MULTIPLIER = 5
STARTING_BALANCE = 7000
LOTTERY_TICKET_PRICE = 50
TOURNAMENT_ENTRY_FEE = 500

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

# --- Roulette Constants ---
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

# --- Poker Constants ---
POKER_CARDS = [f"{rank}{suit}" for suit in "♠♥♦♣" for rank in "23456789TJQKA"]
POKER_HANDS = {
    "Royal Flush": 250, "Straight Flush": 50, "Four of a Kind": 25, "Full House": 9,
    "Flush": 6, "Straight": 4, "Three of a Kind": 3, "Two Pair": 2, "One Pair": 1,
    "High Card": 0
}

# --- Blackjack Constants ---
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
BLACKJACK_CARDS = [f"{rank}{suit}" for suit in "♠♥♦♣" for rank in "23456789TJQKA"]

# --- Craps Constants ---
CRAPS_PASS_LINE = {"win": [7, 11], "lose": [2, 3, 12], "point": [4, 5, 6, 8, 9, 10]}
CRAPS_DONT_PASS = {"win": [2, 3], "lose": [7, 11], "push": [12], "point": [4, 5, 6, 8, 9, 10]}

# --- Baccarat Constants ---
BACCARAT_BETS = {
    "player": 1, "banker": 0.95, "tie": 8
}

# --- Economy Constants ---
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

# --- Achievements Dictionary ---
ACHIEVEMENTS = {
    "first_win": {"name": "Paradox Novice", "description": "Win your first slot game", "emoji": "🏆"},
    "big_winner": {"name": "Paradox Master", "description": "Win over 1000 coins", "emoji": "💎"},
    "jackpot": {"name": "Paradox Breaker", "description": "Hit the jackpot", "emoji": "🎯"},
    "broke": {"name": "Rock Bottom", "description": "Lose all your money", "emoji": "📉"},
    "comeback": {"name": "Phoenix Rising", "description": "Win with less than 100 coins", "emoji": "🔄"},
    "high_roller": {"name": "Paradox Whale", "description": "Bet the maximum amount", "emoji": "💵"},
    "daily_streak": {"name": "Time Traveler", "description": "Claim rewards for 7 days", "emoji": "⏰"},
    "legendary": {"name": "Legendary Gambler", "description": "Win 5 times in a row", "emoji": "👑"},
    "rps_master": {"name": "RPS Master", "description": "Win 5 RPS games in a row", "emoji": "🪨"},
    "blackjack_pro": {"name": "Blackjack Pro", "description": "Win 3 Blackjack games in a row", "emoji": "♠"},
    "roulette_master": {"name": "Roulette Master", "description": "Win a number bet in Roulette", "emoji": "🎡"},
    "poker_pro": {"name": "Poker Pro", "description": "Win a Poker game", "emoji": "🃏"},
    "craps_winner": {"name": "Craps Winner", "description": "Win a Craps game", "emoji": "🎲"},
    "baccarat_champ": {"name": "Baccarat Champ", "description": "Win a Baccarat game", "emoji": "🎴"},
    "shopaholic": {"name": "Shopaholic", "description": "Buy 10 items from the shop", "emoji": "🛍️"},
    "vip_member": {"name": "VIP Member", "description": "Reach VIP status (Level 5)", "emoji": "👑"},
    "debt_free": {"name": "Debt Free", "description": "Pay off a loan", "emoji": "💸"},
    "tournament_champ": {"name": "Tournament Champ", "description": "Win a tournament", "emoji": "🏅"},
    "craftsman": {"name": "Craftsman", "description": "Craft your first item", "emoji": "🔨"},
    "trader": {"name": "Trader", "description": "Complete a trade with another player", "emoji": "🤝"}
}

# --- Mission Constants ---
MISSIONS = {
    "daily": [
        {"id": "play_slots", "name": "Slot Enthusiast", "description": "Play 5 slot games", "requirements": {"slot_plays": 5}, "rewards": {"coins": 100}},
        {"id": "win_games", "name": "Winner", "description": "Win 3 games", "requirements": {"wins": 3}, "rewards": {"coins": 150}},
    ],
    "weekly": [
        {"id": "slot_master", "name": "Slot Master", "description": "Win 10 slot games", "requirements": {"slot_wins": 10}, "rewards": {"coins": 500}},
    ],
    "one-time": [
        {"id": "level_5", "name": "Level Up", "description": "Reach level 5", "requirements": {"level": 5}, "rewards": {"coins": 1000}},
        {"id": "jackpot", "name": "Jackpot Hunter", "description": "Win the jackpot", "requirements": {"jackpot_wins": 1}, "rewards": {"coins": 2000}},
    ]
}

# --- SQLite Database Initialization ---
def init_db():
    """Initialize the SQLite database with comprehensive tables for users, games, items, and announcements."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    
    # Users table for storing player data with missions column
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 7000,
                    winnings INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    achievements TEXT DEFAULT '[]',
                    inventory TEXT DEFAULT '{}',
                    loans TEXT DEFAULT '{}',
                    lottery_tickets INTEGER DEFAULT 0,
                    daily_claim TEXT,
                    streaks TEXT DEFAULT '{}',
                    rps_wins INTEGER DEFAULT 0,
                    blackjack_wins INTEGER DEFAULT 0,
                    craps_wins INTEGER DEFAULT 0,
                    crafting_items TEXT DEFAULT '{}',
                    active_effects TEXT DEFAULT '{}',
                    missions TEXT DEFAULT '{}'
                )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_users_id ON users (id)')
    
    # Lottery table for managing the jackpot
    c.execute('''CREATE TABLE IF NOT EXISTS lottery (
                    jackpot INTEGER DEFAULT 1000
                )''')
    c.execute('INSERT OR IGNORE INTO lottery (rowid, jackpot) VALUES (1, 1000)')
    
    # Tournaments table for multiplayer events
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
    
    # Items table for shop inventory
    c.execute('''CREATE TABLE IF NOT EXISTS items (
                    item_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    price INTEGER
                )''')
    for item_id, item in SHOP_ITEMS.items():
        c.execute('INSERT OR IGNORE INTO items (item_id, name, description, price) VALUES (?, ?, ?, ?)',
                  (item_id, item['name'], item['description'], item['price']))
    
    # Trade offers table for player trading
    c.execute('''CREATE TABLE IF NOT EXISTS trade_offers (
                    offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    receiver_id INTEGER,
                    offered_items TEXT,
                    requested_items TEXT,
                    status TEXT DEFAULT 'pending'
                )''')
    
    # Announcement settings table for daily announcements
    c.execute('''CREATE TABLE IF NOT EXISTS announcement_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message TEXT
                )''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized with all necessary tables.")

init_db()

# --- Database Helper Functions ---
def get_user_data(user_id):
    """Retrieve user data from the database, initializing if not present."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (id, balance) VALUES (?, ?)', (user_id, STARTING_BALANCE))
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    data = c.fetchone()
    conn.commit()
    conn.close()
    keys = ['id', 'balance', 'winnings', 'xp', 'level', 'achievements', 'inventory', 'loans',
            'lottery_tickets', 'daily_claim', 'streaks', 'rps_wins', 'blackjack_wins', 'craps_wins',
            'crafting_items', 'active_effects', 'missions']
    return dict(zip(keys, data))

def update_user_data(user_id, updates):
    """Update user data in the database with provided key-value pairs."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    query = 'UPDATE users SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE id = ?'
    values = list(updates.values()) + [user_id]
    c.execute(query, values)
    conn.commit()
    conn.close()
    logger.debug(f"User data updated for ID {user_id}: {updates}")

def get_lottery_jackpot():
    """Retrieve the current lottery jackpot amount."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT jackpot FROM lottery WHERE rowid = 1')
    jackpot = c.fetchone()[0]
    conn.close()
    return jackpot

def update_lottery_jackpot(amount):
    """Update the lottery jackpot by adding or subtracting the specified amount."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('UPDATE lottery SET jackpot = jackpot + ? WHERE rowid = 1', (amount,))
    conn.commit()
    conn.close()
    logger.debug(f"Lottery jackpot adjusted by {amount}")

def get_tournament_data(channel_id):
    """Retrieve tournament data for a specific channel."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tournaments WHERE channel_id = ?', (channel_id,))
    data = c.fetchone()
    conn.close()
    if data:
        keys = ['channel_id', 'game_type', 'players', 'scores', 'rounds', 'current_round', 'active', 'prize_pool']
        return dict(zip(keys, data))
    return None

def update_tournament_data(channel_id, updates):
    """Update or insert tournament data in the database."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO tournaments (channel_id) VALUES (?)', (channel_id,))
    query = 'UPDATE tournaments SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE channel_id = ?'
    values = list(updates.values()) + [channel_id]
    c.execute(query, values)
    conn.commit()
    conn.close()
    logger.debug(f"Tournament data updated for channel {channel_id}: {updates}")

def get_item_data(item_id):
    """Retrieve item data from the items table."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM items WHERE item_id = ?', (item_id,))
    data = c.fetchone()
    conn.close()
    if data:
        keys = ['item_id', 'name', 'description', 'price']
        return dict(zip(keys, data))
    return None

def create_trade_offer(sender_id, receiver_id, offered_items, requested_items):
    """Create a new trade offer between two players."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('''INSERT INTO trade_offers (sender_id, receiver_id, offered_items, requested_items)
                 VALUES (?, ?, ?, ?)''', (sender_id, receiver_id, json.dumps(offered_items), json.dumps(requested_items)))
    offer_id = c.lastrowid
    conn.commit()
    conn.close()
    return offer_id

def get_trade_offer(offer_id):
    """Retrieve details of a specific trade offer."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM trade_offers WHERE offer_id = ?', (offer_id,))
    data = c.fetchone()
    conn.close()
    if data:
        keys = ['offer_id', 'sender_id', 'receiver_id', 'offered_items', 'requested_items', 'status']
        return dict(zip(keys, data))
    return None

def update_trade_offer(offer_id, updates):
    """Update the status or details of a trade offer."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    query = 'UPDATE trade_offers SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE offer_id = ?'
    values = list(updates.values()) + [offer_id]
    c.execute(query, values)
    conn.commit()
    conn.close()

# --- Mission Helper Functions ---
def get_user_missions(user_id):
    """Retrieve user's mission progress from the database."""
    user_data = get_user_data(user_id)
    return json.loads(user_data['missions'])

def update_user_missions(user_id, missions):
    """Update user's mission progress in the database."""
    update_user_data(user_id, {'missions': json.dumps(missions)})

def initialize_missions(user_id):
    """Initialize mission progress for a user if not already set."""
    missions = {
        "daily": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["daily"]},
        "weekly": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["weekly"]},
        "one-time": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["one-time"]}
    }
    update_user_missions(user_id, missions)

def reset_missions(user_id, mission_type):
    """Reset mission progress for a specific type (daily/weekly)."""
    missions = get_user_missions(user_id)
    if mission_type in missions:
        missions[mission_type] = {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS[mission_type]}
        update_user_missions(user_id, missions)

# --- Slot Machine Functions ---
def spin_slots(lines):
    """Generate a slot machine spin result for the specified number of lines."""
    result = []
    for _ in range(lines):
        line = [random.choice(SLOTS) for _ in range(3)]
        result.append(line)
    return result

def check_win(slots):
    """Check slot spin for wins and calculate total winnings with jackpot detection."""
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

def format_animated_slots(slots, revealed_columns):
    """Format slot display for animation with specified columns revealed."""
    display_lines = []
    for line in slots:
        line_display = []
        for i, symbol in enumerate(line):
            if i in revealed_columns:
                line_display.append(symbol)
            else:
                line_display.append('🎰')
        display_lines.append(' '.join(line_display))
    return '\n'.join(display_lines)

def format_slot_display(slots, winning_lines=None):
    """Format slot machine display with highlighted winning lines."""
    if winning_lines is None:
        winning_lines = []
    winning_line_indices = {line[0]: line[1] for line in winning_lines}
    display_lines = []
    for i, line in enumerate(slots):
        if i in winning_line_indices:
            display_lines.append(f"▶️ {' '.join(line)} ◀️ +${winning_line_indices[i]}")
        else:
            display_lines.append(f"   {' '.join(line)}")
    return '\n'.join(display_lines)

# --- Roulette Functions ---
def get_roulette_color(number):
    """Determine the color of a roulette number based on predefined lists."""
    if number in RED_NUMBERS:
        return "red"
    elif number in BLACK_NUMBERS:
        return "black"
    else:
        return "green"

def validate_roulette_bet(bet_type, bet_value):
    """Validate the type and value of a roulette bet."""
    if bet_type not in ROULETTE_BETS:
        return False
    return ROULETTE_BETS[bet_type]["validator"](bet_value)

def calculate_roulette_payout(bet_type, bet_value, spun_number):
    """Calculate the payout for a roulette bet based on the spun number."""
    color = get_roulette_color(spun_number)
    if bet_type == "number":
        return ROULETTE_BETS[bet_type]["payout"] if spun_number == int(bet_value) else 0
    elif bet_type == "color":
        return ROULETTE_BETS[bet_type]["payout"] if color == bet_value.lower() else 0
    elif bet_type == "parity":
        if spun_number == 0:
            return 0
        parity = "even" if spun_number % 2 == 0 else "odd"
        return ROULETTE_BETS[bet_type]["payout"] if parity == bet_value.lower() else 0
    elif bet_type == "range":
        if spun_number == 0:
            return 0
        range_type = "low" if 1 <= spun_number <= 18 else "high"
        return ROULETTE_BETS[bet_type]["payout"] if range_type == bet_value.lower() else 0
    elif bet_type == "dozen":
        dozens = {"first": (1, 12), "second": (13, 24), "third": (25, 36)}
        if spun_number == 0:
            return 0
        for dozen, (low, high) in dozens.items():
            if low <= spun_number <= high and dozen == bet_value.lower():
                return ROULETTE_BETS[bet_type]["payout"]
        return 0
    elif bet_type == "column":
        columns = {
            1: [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34],
            2: [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            3: [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
        }
        if spun_number == 0:
            return 0
        return ROULETTE_BETS[bet_type]["payout"] if spun_number in columns[int(bet_value)] else 0
    return 0

# --- Poker Functions ---
def deal_poker_hand():
    """Deal a 5-card poker hand from a shuffled deck."""
    deck = POKER_CARDS.copy()
    random.shuffle(deck)
    return deck[:5]

def evaluate_poker_hand(hand):
    """Evaluate a poker hand and return its rank and payout multiplier."""
    ranks = sorted([card[:-1].replace('T', '10').replace('J', '11').replace('Q', '12').replace('K', '13').replace('A', '14') for card in hand], key=int, reverse=True)
    suits = [card[-1] for card in hand]
    rank_values = [int(r) for r in ranks]
    is_flush = len(set(suits)) == 1
    is_straight = all(rank_values[i] - 1 == rank_values[i + 1] for i in range(4)) or (ranks == ['14', '5', '4', '3', '2'])
    
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    count_values = sorted(counts.values(), reverse=True)
    
    if is_flush and is_straight and ranks[0] == '14':
        return "Royal Flush", POKER_HANDS["Royal Flush"]
    elif is_flush and is_straight:
        return "Straight Flush", POKER_HANDS["Straight Flush"]
    elif count_values[0] == 4:
        return "Four of a Kind", POKER_HANDS["Four of a Kind"]
    elif count_values == [3, 2]:
        return "Full House", POKER_HANDS["Full House"]
    elif is_flush:
        return "Flush", POKER_HANDS["Flush"]
    elif is_straight:
        return "Straight", POKER_HANDS["Straight"]
    elif count_values[0] == 3:
        return "Three of a Kind", POKER_HANDS["Three of a Kind"]
    elif count_values == [2, 2, 1]:
        return "Two Pair", POKER_HANDS["Two Pair"]
    elif count_values[0] == 2:
        return "One Pair", POKER_HANDS["One Pair"]
    else:
        return "High Card", POKER_HANDS["High Card"]

# --- Blackjack Functions ---
def deal_blackjack_hand():
    """Deal a 2-card blackjack hand from a shuffled deck."""
    deck = BLACKJACK_CARDS.copy()
    random.shuffle(deck)
    return deck[:2]

def calculate_blackjack_score(hand):
    """Calculate the score of a blackjack hand, adjusting for aces."""
    score = 0
    aces = 0
    for card in hand:
        value = CARD_VALUES[card[:-1]]
        if value == 11:
            aces += 1
        score += value
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

# --- Craps Functions ---
def roll_dice():
    """Roll two six-sided dice and return their values."""
    return random.randint(1, 6), random.randint(1, 6)

def play_craps(bet_type, amount, user_id):
    """Play a round of Craps with pass or don't pass bets."""
    user_data = get_user_data(user_id)
    if amount <= 0 or amount > user_data['balance']:
        return "Invalid bet amount!", None, user_data['balance']
    
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    dice1, dice2 = roll_dice()
    total = dice1 + dice2
    
    if bet_type == "pass":
        if total in CRAPS_PASS_LINE["win"]:
            payout = amount
        elif total in CRAPS_PASS_LINE["lose"]:
            payout = -amount
        else:
            point = total
            while True:
                dice1, dice2 = roll_dice()
                total = dice1 + dice2
                if total == point:
                    payout = amount
                    break
                elif total == 7:
                    payout = -amount
                    break
    elif bet_type == "dont_pass":
        if total in CRAPS_DONT_PASS["win"]:
            payout = amount
        elif total in CRAPS_DONT_PASS["lose"]:
            payout = -amount
        elif total in CRAPS_DONT_PASS["push"]:
            payout = 0
        else:
            point = total
            while True:
                dice1, dice2 = roll_dice()
                total = dice1 + dice2
                if total == point:
                    payout = -amount
                    break
                elif total == 7:
                    payout = amount
                    break
    else:
        return "Invalid bet type!", None, user_data['balance']
    
    new_balance = user_data['balance'] - amount + (payout if payout > 0 else 0)
    update_user_data(user_id, {'balance': new_balance})
    return f"Rolled {dice1} + {dice2} = {total}. You {'win' if payout > 0 else 'lose'} ${abs(payout)}!", payout, new_balance

# --- Baccarat Functions ---
def deal_baccarat_hands():
    """Deal two-card hands for player and banker in Baccarat."""
    deck = BLACKJACK_CARDS.copy()  # Reuse blackjack deck for simplicity
    random.shuffle(deck)
    return deck[:2], deck[2:4]

def calculate_baccarat_score(hand):
    """Calculate Baccarat score (sum modulo 10)."""
    score = sum(CARD_VALUES[card[:-1]] for card in hand) % 10
    return score

def determine_baccarat_winner(player_score, banker_score):
    """Determine the winner of a Baccarat round."""
    if player_score > banker_score:
        return "player"
    elif banker_score > player_score:
        return "banker"
    else:
        return "tie"

# --- XP and Leveling System ---
def add_xp(user_id, amount):
    """Add XP to a user, handle level-ups, award achievements, and update missions."""
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    boosts = inventory.get('boosts', {})
    xp_multiplier = 2 if 'xp_boost' in boosts and datetime.fromisoformat(boosts['xp_boost']) > datetime.utcnow() else 1
    xp = user_data['xp'] + amount * xp_multiplier
    level = user_data['level']
    levels_gained = 0
    earned_achievements = []
    
    while xp >= 100 * level:
        xp -= 100 * level
        level += 1
        levels_gained += 1
        if level == 5 and "vip_member" not in json.loads(user_data['achievements']):
            earned_achievements.append("vip_member")
    
    # Update one-time mission for reaching level 5
    missions = get_user_missions(user_id)
    if not missions:
        initialize_missions(user_id)
        missions = get_user_missions(user_id)
    for m in MISSIONS["one-time"]:
        if m["id"] == "level_5" and level >= m["requirements"]["level"] and not missions["one-time"][m["id"]]["completed"]:
            missions["one-time"][m["id"]]["completed"] = True
            missions["one-time"][m["id"]]["progress"] = level
            reward = m["rewards"]["coins"]
            user_data['balance'] += reward
            earned_achievements.append(f"Completed mission '{m['name']}' for ${reward}!")
    
    update_user_data(user_id, {
        'xp': xp,
        'level': level,
        'balance': user_data['balance'] + 500 * levels_gained,
        'achievements': json.dumps(json.loads(user_data['achievements']) + [a for a in earned_achievements if a in ACHIEVEMENTS]),
        'missions': json.dumps(missions)
    })
    return levels_gained, earned_achievements

# --- Achievements System ---
def check_achievements(user_id, bet_amount, win_amount, jackpot_win, balance, streaks, game_type=None):
    """Check and award achievements based on user activity and game outcomes, update missions."""
    user_data = get_user_data(user_id)
    achievements = json.loads(user_data['achievements'])
    earned = []
    streaks = json.loads(streaks) if isinstance(streaks, str) else streaks

    # Update missions based on game outcomes
    missions = get_user_missions(user_id)
    if not missions:
        initialize_missions(user_id)
        missions = get_user_missions(user_id)

    if game_type == "slots":
        if "play_slots" in missions["daily"]:
            missions["daily"]["play_slots"]["progress"] += 1
            if (missions["daily"]["play_slots"]["progress"] >= MISSIONS["daily"][0]["requirements"]["slot_plays"] and 
                not missions["daily"]["play_slots"]["completed"]):
                missions["daily"]["play_slots"]["completed"] = True
                reward = MISSIONS["daily"][0]["rewards"]["coins"]
                user_data['balance'] += reward
                earned.append(f"Completed mission 'Slot Enthusiast' for ${reward}!")
        
        if win_amount > 0:
            if "win_games" in missions["daily"]:
                missions["daily"]["win_games"]["progress"] += 1
                if (missions["daily"]["win_games"]["progress"] >= MISSIONS["daily"][1]["requirements"]["wins"] and 
                    not missions["daily"]["win_games"]["completed"]):
                    missions["daily"]["win_games"]["completed"] = True
                    reward = MISSIONS["daily"][1]["rewards"]["coins"]
                    user_data['balance'] += reward
                    earned.append(f"Completed mission 'Winner' for ${reward}!")
            
            if "slot_master" in missions["weekly"]:
                missions["weekly"]["slot_master"]["progress"] += 1
                if (missions["weekly"]["slot_master"]["progress"] >= MISSIONS["weekly"][0]["requirements"]["slot_wins"] and 
                    not missions["weekly"]["slot_master"]["completed"]):
                    missions["weekly"]["slot_master"]["completed"] = True
                    reward = MISSIONS["weekly"][0]["rewards"]["coins"]
                    user_data['balance'] += reward
                    earned.append(f"Completed mission 'Slot Master' for ${reward}!")
            
            if jackpot_win and "jackpot" in missions["one-time"]:
                missions["one-time"]["jackpot"]["progress"] += 1
                if (missions["one-time"]["jackpot"]["progress"] >= MISSIONS["one-time"][1]["requirements"]["jackpot_wins"] and 
                    not missions["one-time"]["jackpot"]["completed"]):
                    missions["one-time"]["jackpot"]["completed"] = True
                    reward = MISSIONS["one-time"][1]["rewards"]["coins"]
                    user_data['balance'] += reward
                    earned.append(f"Completed mission 'Jackpot Hunter' for ${reward}!")

    # Standard achievement checks
    if win_amount > 0 and "first_win" not in achievements:
        earned.append("first_win")
    if win_amount >= 1000 and "big_winner" not in achievements:
        earned.append("big_winner")
    if jackpot_win and "jackpot" not in achievements:
        earned.append("jackpot")
    if balance == 0 and "broke" not in achievements:
        earned.append("broke")
    if balance <= 100 and win_amount > 0 and "comeback" not in achievements:
        earned.append("comeback")
    if bet_amount == MAX_BET and "high_roller" not in achievements:
        earned.append("high_roller")
    if streaks.get('daily', 0) >= 7 and "daily_streak" not in achievements:
        earned.append("daily_streak")
    if streaks.get('wins', 0) >= 5 and "legendary" not in achievements:
        earned.append("legendary")
    if game_type == "rps" and win_amount > 0 and streaks.get('rps_wins', 0) >= 5 and "rps_master" not in achievements:
        earned.append("rps_master")
    if game_type == "blackjack" and win_amount > 0 and streaks.get('blackjack_wins', 0) >= 3 and "blackjack_pro" not in achievements:
        earned.append("blackjack_pro")
    if game_type == "roulette" and win_amount > 0 and "roulette_master" not in achievements:
        earned.append("roulette_master")
    if game_type == "poker" and win_amount > 0 and "poker_pro" not in achievements:
        earned.append("poker_pro")
    if game_type == "craps" and win_amount > 0 and "craps_winner" not in achievements:
        earned.append("craps_winner")
    if game_type == "baccarat" and win_amount > 0 and "baccarat_champ" not in achievements:
        earned.append("baccarat_champ")

    achievements.extend([a for a in earned if a in ACHIEVEMENTS])
    update_user_data(user_id, {
        'achievements': json.dumps(achievements),
        'missions': json.dumps(missions),
        'balance': user_data['balance']
    })
    return earned

# --- Crafting System ---
def check_crafting_eligibility(user_id, recipe_id):
    """Check if a user has the required items to craft a recipe."""
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    crafting_items = json.loads(user_data['crafting_items'])
    recipe = CRAFTING_RECIPES.get(recipe_id)
    
    if not recipe or 'crafting_kit' not in inventory:
        return False, "You need a crafting kit to craft items!"
    
    for item, qty in recipe['ingredients'].items():
        if crafting_items.get(item, 0) < qty:
            return False, f"Not enough {item}!"
    return True, "Eligible"

def craft_item(user_id, recipe_id):
    """Craft an item using the specified recipe."""
    eligible, message = check_crafting_eligibility(user_id, recipe_id)
    if not eligible:
        return message
    
    user_data = get_user_data(user_id)
    crafting_items = json.loads(user_data['crafting_items'])
    recipe = CRAFTING_RECIPES[recipe_id]
    
    # Deduct ingredients
    for item, qty in recipe['ingredients'].items():
        crafting_items[item] -= qty
    
    # Add crafted item effect
    active_effects = json.loads(user_data['active_effects'])
    if recipe_id == "lucky_charm":
        active_effects[recipe_id] = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    elif recipe_id == "mega_jackpot":
        active_effects[recipe_id] = 1  # One-time use
    
    # Update achievements
    achievements = json.loads(user_data['achievements'])
    if "craftsman" not in achievements:
        achievements.append("craftsman")
    
    update_user_data(user_id, {
        'crafting_items': json.dumps(crafting_items),
        'active_effects': json.dumps(active_effects),
        'achievements': json.dumps(achievements)
    })
    return f"Successfully crafted {recipe_id}! {recipe['description']}"

# --- Trading System ---
def award_drop(user_id, game_type):
    """Award a random crafting item drop based on game type."""
    user_data = get_user_data(user_id)
    crafting_items = json.loads(user_data['crafting_items'])
    for item, details in ITEM_DROP_TABLE.items():
        if details['source'] == game_type and random.random() < details['chance']:
            crafting_items[item] = crafting_items.get(item, 0) + 1
            update_user_data(user_id, {'crafting_items': json.dumps(crafting_items)})
            return f"Dropped {item}!"
    return None

# --- Bot Events ---
@bot.event
async def on_ready():
    """Handle bot startup, set presence, and start background tasks."""
    logger.info(f'Bot logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="!paradox for commands"))
    bot.loop.create_task(casino_announcements())
    bot.loop.create_task(lottery_draw_task())
    bot.loop.create_task(save_data_periodically())
    bot.loop.create_task(daily_announcement_task())
    bot.loop.create_task(reset_missions_task())
    logger.info("Bot is fully operational and tasks scheduled.")

async def casino_announcements():
    """Periodically send themed announcements to guild channels."""
    await bot.wait_until_ready()
    announcements = [
        {"title": "🎰 Slot Frenzy!", "description": f"Spin `!bet` for a chance at the {JACKPOT_SYMBOL} jackpot!"},
        {"title": "🎡 Roulette Royale", "description": "Place your bets with `!roulette`!"},
        {"title": "🃏 Poker Night", "description": "Show your skills with `!poker`!"},
        {"title": "🛒 Shop Specials", "description": "Check out `!shop` for exclusive items!"},
        {"title": "🎲 Craps Craze", "description": "Roll the dice with `!craps`!"},
        {"title": "♠ Blackjack Blitz", "description": "Beat the dealer with `!blackjack`!"},
        {"title": "🎴 Baccarat Battle", "description": "Play `!baccarat` for high stakes!"}
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
        await asyncio.sleep(3600 * 6)  # Announce every 6 hours

async def lottery_draw_task():
    """Conduct daily lottery draws and award the jackpot."""
    while True:
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
                'lottery_tickets': 0
            })
            c.execute('UPDATE users SET lottery_tickets = 0')
            c.execute('UPDATE lottery SET jackpot = 1000 WHERE rowid = 1')
            conn.commit()
            for guild in bot.guilds:
                channel = guild.system_channel
                if channel:
                    await channel.send(f"🎉 <@{winner_id}> has won the lottery jackpot of ${jackpot}!")
        conn.close()

async def save_data_periodically():
    """Periodically log a data save checkpoint."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        logger.info("Periodic data checkpoint saved.")

async def daily_announcement_task():
    """Send daily announcements to configured guild channels at 12:00 PM UTC."""
    while True:
        now = datetime.utcnow()
        next_announcement = (now + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_announcement - now).total_seconds())
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT guild_id, channel_id, message FROM announcement_settings')
        settings = c.fetchall()
        for guild_id, channel_id, message in settings:
            guild = bot.get_guild(guild_id)
            if guild:
                channel = guild.get_channel(channel_id)
                if channel:
                    try:
                        await channel.send(message)
                    except Exception as e:
                        logger.error(f"Failed to send announcement to {guild.name}: {e}")
        conn.close()

async def reset_missions_task():
    """Periodically reset daily and weekly missions for all users."""
    while True:
        now = datetime.utcnow()
        # Reset daily missions at midnight UTC
        next_daily_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_daily_reset - now).total_seconds())
        conn = sqlite3.connect('casino.db')
        c = conn.cursor()
        c.execute('SELECT id FROM users')
        users = c.fetchall()
        for user in users:
            reset_missions(user[0], "daily")
        conn.close()
        logger.info("Daily missions reset for all users.")
        
        # Reset weekly missions every Monday at midnight UTC
        days_until_monday = (7 - now.weekday()) % 7 or 7
        next_weekly_reset = (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_weekly_reset - now).total_seconds())
        for user in users:
            reset_missions(user[0], "weekly")
        logger.info("Weekly missions reset for all users.")

# --- Core Commands ---
@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet(ctx, amount: int, lines: int = 1):
    """Spin the slot machine with an animated reveal and update missions."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    total_bet = amount * lines
    
    # Validate bet amount and lines
    if amount < MIN_BET or amount > MAX_BET or lines < 1 or lines > MAX_LINES or total_bet > user_data['balance']:
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET}, lines 1-{MAX_LINES}. You have ${user_data['balance']}.")
        return
    
    # Initialize missions if not present
    if not get_user_missions(user_id):
        initialize_missions(user_id)
    
    # Contribute to lottery jackpot
    update_lottery_jackpot(int(total_bet * 0.05))
    slots = spin_slots(lines)
    winnings, jackpot_win, winning_lines = check_win(slots)
    
    # Apply crafting effects
    active_effects = json.loads(user_data['active_effects'])
    if jackpot_win and "mega_jackpot" in active_effects and active_effects["mega_jackpot"] > 0:
        winnings *= 3
        active_effects["mega_jackpot"] -= 1
        if active_effects["mega_jackpot"] == 0:
            del active_effects["mega_jackpot"]
    elif "lucky_charm" in active_effects and datetime.fromisoformat(active_effects["lucky_charm"]) > datetime.utcnow():
        winnings = int(winnings * 1.05)  # 5% boost
    
    # Handle jackpot winnings
    if jackpot_win:
        jackpot_amount = get_lottery_jackpot()
        winnings += jackpot_amount
        update_lottery_jackpot(-jackpot_amount + 1000)
    
    # Initial embed for animation
    embed = discord.Embed(title="🎰 Spinning the Reels...", color=0x3498db)
    embed.add_field(name="Your Spin", value=f"```\n{format_animated_slots(slots, [])} \n```", inline=False)
    message = await ctx.send(embed=embed)
    
    # Animate slot reveal
    for i in range(3):
        await asyncio.sleep(0.8)
        embed.set_field_at(0, name="Your Spin", value=f"```\n{format_animated_slots(slots, list(range(i + 1)))}\n```")
        await message.edit(embed=embed)
    
    # Update user data
    user_data['balance'] -= total_bet
    user_data['balance'] += winnings
    user_data['winnings'] += winnings
    streaks = json.loads(user_data['streaks'])
    if winnings > 0:
        streaks['wins'] = streaks.get('wins', 0) + 1
        streaks['losses'] = 0
    else:
        streaks['losses'] = streaks.get('losses', 0) + 1
        streaks['wins'] = 0
    
    earned_achievements = check_achievements(user_id, amount, winnings, jackpot_win, user_data['balance'], streaks, "slots")
    update_user_data(user_id, {
        'balance': user_data['balance'],
        'winnings': user_data['winnings'],
        'streaks': json.dumps(streaks),
        'active_effects': json.dumps(active_effects)
    })
    
    # Final embed with results
    embed.title = "🎰 Jackpot!" if jackpot_win else "🎰 Spin Result"
    embed.description = f"{random.choice(WIN_MESSAGES if winnings > 0 else LOSS_MESSAGES)}\nBet: ${total_bet} | {'Won' if winnings > 0 else 'Lost'}: ${winnings if winnings > 0 else total_bet}"
    embed.set_field_at(0, name="Your Spin", value=f"```\n{format_slot_display(slots, winning_lines)}\n```")
    embed.add_field(name="Balance", value=f"${user_data['balance']}", inline=True)
    if earned_achievements:
        embed.add_field(name="🏆 New Achievements & Missions", value="\n".join(
            f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}**" if a in ACHIEVEMENTS else a 
            for a in earned_achievements), inline=False)
    embed.color = 0x2ecc71 if winnings > 0 else 0xe74c3c
    await message.edit(embed=embed)
    
    # Award XP and drops
    levels_gained, level_achievements = add_xp(user_id, 10)
    drop_message = award_drop(user_id, "slots")
    if levels_gained:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to {get_user_data(user_id)['level']}! +${500 * levels_gained}")
    if level_achievements:
        await ctx.send(f"🏆 {ctx.author.mention} earned: " + ", ".join(
            f"**{ACHIEVEMENTS[a]['name']}**" if a in ACHIEVEMENTS else a for a in level_achievements))
    if drop_message:
        await ctx.send(drop_message)

@bot.command()
async def daily(ctx):
    """Claim a daily reward with streak bonuses and potential boosts."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    boosts = inventory.get('boosts', {})
    now = datetime.utcnow()
    last_claim = user_data['daily_claim']
    
    if not last_claim or (datetime.fromisoformat(last_claim) + timedelta(days=1)) <= now:
        base_reward = DAILY_REWARD * (1.5 if user_data['level'] >= 5 else 1)
        daily_boost = 2 if 'daily_boost' in boosts and datetime.fromisoformat(boosts['daily_boost']) > now else 1
        streaks = json.loads(user_data['streaks'])
        daily_streak = streaks.get('daily', 0)
        
        if last_claim and (datetime.fromisoformat(last_claim) + timedelta(days=2)) > now:
            daily_streak += 1
        else:
            daily_streak = 1
        
        streak_bonus = min(daily_streak * 50, DAILY_REWARD) if daily_streak < 7 else DAILY_REWARD
        total_reward = int((base_reward + streak_bonus) * daily_boost)
        user_data['balance'] += total_reward
        streaks['daily'] = daily_streak
        
        earned_achievements = check_achievements(user_id, 0, total_reward, False, user_data['balance'], streaks)
        update_user_data(user_id, {
            'balance': user_data['balance'],
            'daily_claim': now.isoformat(),
            'streaks': json.dumps(streaks)
        })
        
        embed = discord.Embed(title="💸 Daily Reward Claimed!", description=f"You received ${total_reward}!", color=0x2ecc71)
        embed.add_field(name="Streak", value=f"{daily_streak} days (+${streak_bonus})", inline=True)
        if daily_boost > 1:
            embed.add_field(name="Boost", value="2x Reward!", inline=True)
        embed.add_field(name="New Balance", value=f"${user_data['balance']}", inline=True)
        if earned_achievements:
            embed.add_field(name="🏆 Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements), inline=False)
        await ctx.send(embed=embed)
    else:
        time_left = (datetime.fromisoformat(last_claim) + timedelta(days=1)) - now
        await ctx.send(f"⏳ Next claim in {time_left.seconds // 3600}h {(time_left.seconds % 3600) // 60}m")

@bot.command()
async def profile(ctx, member: discord.Member = None):
    """Display a user's profile with detailed stats and inventory."""
    user = member or ctx.author
    user_id = user.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    loans = json.loads(user_data['loans'])
    crafting_items = json.loads(user_data['crafting_items'])
    active_effects = json.loads(user_data['active_effects'])
    
    embed = discord.Embed(
        title=f"👤 {user.name}'s Casino Profile",
        description=f"Level: {user_data['level']} | XP: {user_data['xp']}/{100 * user_data['level']}\nBalance: ${user_data['balance']}\nWinnings: ${user_data['winnings']}",
        color=0x3498db
    )
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    # Inventory details
    owned_bgs = ', '.join(inventory.get('owned_bgs', [])) or "None"
    owned_titles = ', '.join(inventory.get('owned_titles', [])) or "None"
    embed.add_field(name="Inventory", value=f"Backgrounds: {owned_bgs}\nTitles: {owned_titles}\nTickets: {inventory.get('tournament_tickets', 0)}", inline=False)
    
    # Crafting items
    crafting_display = '\n'.join(f"{k}: {v}" for k, v in crafting_items.items()) or "None"
    embed.add_field(name="Crafting Items", value=crafting_display, inline=True)
    
    # Active effects
    effects_display = '\n'.join(f"{k}: {v}" for k, v in active_effects.items()) or "None"
    embed.add_field(name="Active Effects", value=effects_display, inline=True)
    
    # Loans
    if loans:
        embed.add_field(name="Loans", value=f"Amount: ${loans.get('amount', 0)}\nDue: {loans.get('due_date', 'N/A')}", inline=True)
    
    # Achievements
    achievements = json.loads(user_data['achievements'])
    if achievements:
        embed.add_field(name="Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} {ACHIEVEMENTS[a]['name']}" for a in achievements), inline=False)
    
    await ctx.send(embed=embed)

# --- Mission Command ---
@bot.command()
async def missions(ctx):
    """Display the user's current mission progress."""
    user_id = ctx.author.id
    user_missions = get_user_missions(user_id)
    if not user_missions:
        initialize_missions(user_id)
        user_missions = get_user_missions(user_id)
    
    embed = discord.Embed(title="🎯 Your Missions", description="Complete missions to earn rewards!", color=0x3498db)
    for mission_type in ["daily", "weekly", "one-time"]:
        embed.add_field(name=f"{mission_type.capitalize()} Missions", value="\u200b", inline=False)
        for m in MISSIONS[mission_type]:
            progress = user_missions[mission_type][m["id"]]["progress"]
            completed = user_missions[mission_type][m["id"]]["completed"]
            req_value = list(m["requirements"].values())[0]
            status = "✅ Completed" if completed else f"Progress: {progress}/{req_value}"
            embed.add_field(name=f"{m['name']} - ${m['rewards']['coins']}", value=f"{m['description']}\n{status}", inline=False)
    await ctx.send(embed=embed)

# --- Daily Announcement Commands ---
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setdailyannouncement(ctx, channel: discord.TextChannel, *, message: str):
    """Set a daily announcement for the guild in a specific channel."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO announcement_settings (guild_id, channel_id, message) VALUES (?, ?, ?)', 
              (ctx.guild.id, channel.id, message))
    conn.commit()
    conn.close()
    await ctx.send(f"📢 Daily announcement set for {channel.mention} with message: '{message}'")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def unsetdailyannouncement(ctx):
    """Unset the daily announcement for the guild."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('DELETE FROM announcement_settings WHERE guild_id = ?', (ctx.guild.id,))
    conn.commit()
    conn.close()
    await ctx.send("📢 Daily announcement unset.")

# --- Casino Games ---
@bot.command()
async def roulette(ctx, bet_type: str, bet_value: str, amount: int):
    """Play a round of Roulette with various betting options."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    bet_type = bet_type.lower()
    
    if not validate_roulette_bet(bet_type, bet_value):
        await ctx.send("❌ Invalid bet! Use: number (0-36), color (red/black), parity (even/odd), range (high/low), dozen (first/second/third), column (1-3)")
        return
    if amount < MIN_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet must be ${MIN_BET} or more and within your balance (${user_data['balance']})!")
        return
    
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    spun_number = random.randint(0, 36)
    payout_multiplier = calculate_roulette_payout(bet_type, bet_value, spun_number)
    payout = amount * payout_multiplier
    new_balance = user_data['balance'] - amount + payout
    
    embed = discord.Embed(
        title="🎡 Roulette Wheel Spins!",
        description=f"The ball lands on **{spun_number} ({get_roulette_color(spun_number)})**",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="Your Bet", value=f"{bet_type.capitalize()} {bet_value}: ${amount}", inline=False)
    embed.add_field(name="Outcome", value=f"You {'win' if payout > 0 else 'lose'}! Payout: ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    
    update_user_data(user_id, {'balance': new_balance})
    if payout > 0:
        earned_achievements = check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "roulette")
        drop_message = award_drop(user_id, "roulette")
        if earned_achievements:
            await ctx.send(f"🏆 {ctx.author.mention} earned: " + ", ".join(f"**{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements))
        if drop_message:
            await ctx.send(drop_message)
    add_xp(user_id, 5)

@bot.command()
async def poker(ctx, amount: int):
    """Play a simplified Poker game against the bot."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET} and within your balance (${user_data['balance']})!")
        return
    
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    player_hand = deal_poker_hand()
    bot_hand = deal_poker_hand()
    player_rank, player_multiplier = evaluate_poker_hand(player_hand)
    bot_rank, bot_multiplier = evaluate_poker_hand(bot_hand)
    
    player_score = list(POKER_HANDS.keys()).index(player_rank) * 100 + player_multiplier
    bot_score = list(POKER_HANDS.keys()).index(bot_rank) * 100 + bot_multiplier
    win = player_score > bot_score
    payout = amount * player_multiplier if win else 0
    new_balance = user_data['balance'] - amount + payout
    
    embed = discord.Embed(
        title="🃏 Poker Showdown",
        description=f"**Your Hand**: {' '.join(player_hand)} ({player_rank})\n**Bot Hand**: {' '.join(bot_hand)} ({bot_rank})",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Result", value=f"You {'win' if win else 'lose'}! Payout: ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    
    update_user_data(user_id, {'balance': new_balance})
    if win:
        earned_achievements = check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "poker")
        drop_message = award_drop(user_id, "poker")
        if earned_achievements:
            await ctx.send(f"🏆 {ctx.author.mention} earned: " + ", ".join(f"**{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements))
        if drop_message:
            await ctx.send(drop_message)
    add_xp(user_id, 10)

@bot.command()
async def blackjack(ctx, amount: int):
    """Play a simplified Blackjack game against the bot."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet must be ${MIN_BET}-${MAX_BET} and within your balance (${user_data['balance']})!")
        return
    
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    player_hand = deal_blackjack_hand()
    dealer_hand = deal_blackjack_hand()
    
    player_score = calculate_blackjack_score(player_hand)
    dealer_score = calculate_blackjack_score(dealer_hand)
    
    while dealer_score < 17:
        dealer_hand.append(random.choice(BLACKJACK_CARDS))
        dealer_score = calculate_blackjack_score(dealer_hand)
    
    win = (player_score <= 21 and (player_score > dealer_score or dealer_score > 21))
    payout = amount * 2 if win else 0
    new_balance = user_data['balance'] - amount + payout
    
    embed = discord.Embed(
        title="♠ Blackjack Table",
        description=f"**Your Hand**: {' '.join(player_hand)} ({player_score})\n**Dealer Hand**: {' '.join(dealer_hand)} ({dealer_score})",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Result", value=f"You {'win' if win else 'lose'}! Payout: ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    
    update_user_data(user_id, {'balance': new_balance})
    if win:
        earned_achievements = check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "blackjack")
        drop_message = award_drop(user_id, "blackjack")
        if earned_achievements:
            await ctx.send(f"🏆 {ctx.author.mention} earned: " + ", ".join(f"**{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements))
        if drop_message:
            await ctx.send(drop_message)
    add_xp(user_id, 8)

@bot.command()
async def craps(ctx, bet_type: str, amount: int):
    """Play a round of Craps with pass or don't pass bets."""
    user_id = ctx.author.id
    bet_type = bet_type.lower()
    
    if bet_type not in ["pass", "dont_pass"]:
        await ctx.send("❌ Bet type must be 'pass' or 'dont_pass'!")
        return
    
    result, payout, new_balance = play_craps(bet_type, amount, user_id)
    await ctx.send(embed=discord.Embed(
        title="🎲 Craps Roll",
        description=result,
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    ).add_field(name="Balance", value=f"${new_balance}", inline=True))
    
    if payout > 0:
        earned_achievements = check_achievements(user_id, amount, payout, False, new_balance, get_user_data(user_id)['streaks'], "craps")
        if earned_achievements:
            await ctx.send(f"🏆 {ctx.author.mention} earned: " + ", ".join(f"**{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements))
    add_xp(user_id, 7)

@bot.command()
async def baccarat(ctx, bet_type: str, amount: int):
    """Play a round of Baccarat with player, banker, or tie bets."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    bet_type = bet_type.lower()
    
    if bet_type not in BACCARAT_BETS:
        await ctx.send("❌ Bet type must be 'player', 'banker', or 'tie'!")
        return
    if amount < MIN_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet must be ${MIN_BET} or more and within your balance (${user_data['balance']})!")
        return
    
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    player_hand, banker_hand = deal_baccarat_hands()
    player_score = calculate_baccarat_score(player_hand)
    banker_score = calculate_baccarat_score(banker_hand)
    result = determine_baccarat_winner(player_score, banker_score)
    payout = int(amount * BACCARAT_BETS[bet_type]) if result == bet_type else 0
    new_balance = user_data['balance'] - amount + payout
    
    embed = discord.Embed(
        title="🎴 Baccarat Round",
        description=f"**Player**: {' '.join(player_hand)} ({player_score})\n**Banker**: {' '.join(banker_hand)} ({banker_score})",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="Your Bet", value=f"{bet_type.capitalize()}: ${amount}", inline=False)
    embed.add_field(name="Result", value=f"{'Win' if payout > 0 else 'Loss'}! Payout: ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    
    update_user_data(user_id, {'balance': new_balance})
    if payout > 0:
        earned_achievements = check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "baccarat")
        if earned_achievements:
            await ctx.send(f"🏆 {ctx.author.mention} earned: " + ", ".join(f"**{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements))
    add_xp(user_id, 6)

# --- Economy Commands ---
@bot.command()
async def shop(ctx):
    """Display the shop with all available items."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT item_id, name, description, price FROM items')
    items = c.fetchall()
    conn.close()
    
    embed = discord.Embed(title="🛒 Paradox Casino Shop", description="Purchase with `!buy [item_id]`", color=0x3498db)
    for item_id, name, desc, price in items:
        embed.add_field(name=f"{name} - ${price} ({item_id})", value=desc, inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, item_id: str):
    """Purchase an item from the shop and update inventory."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    item = get_item_data(item_id)
    
    if not item:
        await ctx.send("❌ Item not found in the shop!")
        return
    if user_data['balance'] < item['price']:
        await ctx.send(f"❌ You need ${item['price']}, but you only have ${user_data['balance']}!")
        return
    
    inventory = json.loads(user_data['inventory'])
    if item_id.startswith("profile_bg"):
        owned_bgs = inventory.get("owned_bgs", [])
        if item_id in owned_bgs:
            await ctx.send("❌ You already own this background!")
            return
        owned_bgs.append(item_id)
        inventory["owned_bgs"] = owned_bgs
        if "selected_bg" not in inventory:
            inventory["selected_bg"] = item_id
    elif item_id.startswith("title"):
        owned_titles = inventory.get("owned_titles", [])
        if item_id in owned_titles:
            await ctx.send("❌ You already own this title!")
            return
        owned_titles.append(item_id)
        inventory["owned_titles"] = owned_titles
        if "selected_title" not in inventory:
            inventory["selected_title"] = item_id
    elif item_id in ["daily_boost", "xp_boost"]:
        boosts = inventory.get("boosts", {})
        if item_id in boosts and datetime.fromisoformat(boosts[item_id]) > datetime.utcnow():
            await ctx.send(f"❌ You already have an active {item['name']}!")
            return
        boosts[item_id] = (datetime.utcnow() + timedelta(days=1)).isoformat()
        inventory["boosts"] = boosts
    elif item_id == "loan_pass":
        if "loan_pass" in inventory:
            await ctx.send("❌ You already own a loan pass!")
            return
        inventory["loan_pass"] = True
    elif item_id == "tournament_ticket":
        inventory["tournament_tickets"] = inventory.get("tournament_tickets", 0) + 1
    elif item_id == "crafting_kit":
        if "crafting_kit" in inventory:
            await ctx.send("❌ You already own a crafting kit!")
            return
        inventory["crafting_kit"] = True
    
    update_user_data(user_id, {
        'balance': user_data['balance'] - item['price'],
        'inventory': json.dumps(inventory)
    })
    await ctx.send(f"🛍️ Purchased **{item['name']}** for ${item['price']}!")
    
    # Check shopaholic achievement
    purchases = len(inventory.get("owned_bgs", [])) + len(inventory.get("owned_titles", [])) + len(inventory.get("boosts", {}))
    if purchases >= 10 and "shopaholic" not in json.loads(user_data['achievements']):
        achievements = json.loads(user_data['achievements'])
        achievements.append("shopaholic")
        update_user_data(user_id, {'achievements': json.dumps(achievements)})
        await ctx.send(f"🏆 {ctx.author.mention} earned **Shopaholic**!")

@bot.command()
async def setbg(ctx, bg_id: str):
    """Set your profile background from owned items."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    owned_bgs = inventory.get("owned_bgs", [])
    
    if bg_id not in owned_bgs:
        await ctx.send("❌ You don’t own this background!")
        return
    inventory["selected_bg"] = bg_id
    update_user_data(user_id, {'inventory': json.dumps(inventory)})
    await ctx.send(f"🎨 Profile background set to **{bg_id}**!")

@bot.command()
async def settitle(ctx, title_id: str):
    """Set your profile title from owned items."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    owned_titles = inventory.get("owned_titles", [])
    
    if title_id not in owned_titles:
        await ctx.send("❌ You don’t own this title!")
        return
    inventory["selected_title"] = title_id
    update_user_data(user_id, {'inventory': json.dumps(inventory)})
    await ctx.send(f"🏷️ Profile title set to **{title_id}**!")

@bot.command()
async def loan(ctx, amount: int):
    """Take out a loan with 10% interest, requiring a loan pass."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    
    if "loan_pass" not in inventory:
        await ctx.send("❌ You need a Loan Pass from the shop to take a loan!")
        return
    loans = json.loads(user_data['loans'])
    if loans:
        await ctx.send("❌ You already have an active loan!")
        return
    if amount < 100 or amount > 5000:
        await ctx.send("❌ Loan amount must be between 100 and 5000 coins!")
        return
    
    due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
    interest = int(amount * 0.1)
    loans = {"amount": amount, "due_date": due_date, "interest": interest}
    update_user_data(user_id, {
        'balance': user_data['balance'] + amount,
        'loans': json.dumps(loans)
    })
    await ctx.send(f"💸 Loan granted: ${amount}! Repay ${amount + interest} by {due_date.split('T')[0]} with `!repay`.")

@bot.command()
async def repay(ctx):
    """Repay an active loan in full."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    loans = json.loads(user_data['loans'])
    
    if not loans:
        await ctx.send("❌ You have no active loan to repay!")
        return
    total_due = loans['amount'] + loans['interest']
    if user_data['balance'] < total_due:
        await ctx.send(f"❌ Need ${total_due} to repay, but you only have ${user_data['balance']}!")
        return
    
    update_user_data(user_id, {
        'balance': user_data['balance'] - total_due,
        'loans': '{}'
    })
    await ctx.send(f"💸 Loan of ${total_due} fully repaid!")
    
    if "debt_free" not in json.loads(user_data['achievements']):
        achievements = json.loads(user_data['achievements'])
        achievements.append("debt_free")
        update_user_data(user_id, {'achievements': json.dumps(achievements)})
        await ctx.send(f"🏆 {ctx.author.mention} earned **Debt Free**!")

@bot.command()
async def lottery(ctx, tickets: int = 1):
    """Purchase lottery tickets for the daily draw."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    cost = tickets * LOTTERY_TICKET_PRICE
    
    if tickets < 1 or cost > user_data['balance']:
        await ctx.send(f"❌ Tickets cost ${LOTTERY_TICKET_PRICE} each. You can afford {user_data['balance'] // LOTTERY_TICKET_PRICE} with ${user_data['balance']}!")
        return
    
    update_user_data(user_id, {
        'balance': user_data['balance'] - cost,
        'lottery_tickets': user_data['lottery_tickets'] + tickets
    })
    update_lottery_jackpot(cost // 2)
    await ctx.send(f"🎟️ Bought {tickets} lottery ticket(s) for ${cost}! Current jackpot: ${get_lottery_jackpot()}")

@bot.command()
async def craft(ctx, recipe_id: str):
    """Craft an item using collected resources."""
    user_id = ctx.author.id
    if recipe_id not in CRAFTING_RECIPES:
        await ctx.send("❌ Invalid recipe! Available: " + ", ".join(CRAFTING_RECIPES.keys()))
        return
    
    result = craft_item(user_id, recipe_id)
    await ctx.send(result)

# --- Multiplayer Commands ---
pending_challenges = {}

@bot.command()
async def challenge(ctx, opponent: discord.Member, game: str, amount: int):
    """Challenge another player to a multiplayer game."""
    if opponent == ctx.author:
        await ctx.send("❌ You can’t challenge yourself!")
        return
    game = game.lower()
    if game not in ["rps", "coinflip", "slots"]:
        await ctx.send("❌ Supported games: 'rps', 'coinflip', 'slots'!")
        return
    
    user_data = get_user_data(ctx.author.id)
    opponent_data = get_user_data(opponent.id)
    if amount < MIN_BET or amount > user_data['balance'] or amount > opponent_data['balance']:
        await ctx.send(f"❌ Amount must be at least ${MIN_BET} and within both players’ balances!")
        return
    
    pending_challenges[opponent.id] = {"challenger": ctx.author.id, "game": game, "amount": amount}
    await ctx.send(f"{opponent.mention}, {ctx.author.mention} challenges you to {game} for ${amount}! Type `!accept` to join.")

@bot.command()
async def accept(ctx):
    """Accept a pending multiplayer challenge."""
    if ctx.author.id not in pending_challenges:
        await ctx.send("❌ No pending challenge for you!")
        return
    
    challenge = pending_challenges.pop(ctx.author.id)
    challenger_id = challenge["challenger"]
    game = challenge["game"]
    amount = challenge["amount"]
    challenger = bot.get_user(challenger_id)
    
    await ctx.send(f"{ctx.author.mention} accepted {challenger.mention}'s challenge! DM your choice for {game}.")
    await challenger.send(f"Choose for {game}: {'rock/paper/scissors' if game == 'rps' else 'heads/tails' if game == 'coinflip' else 'ready'}")
    await ctx.author.send(f"Choose for {game}: {'rock/paper/scissors' if game == 'rps' else 'heads/tails' if game == 'coinflip' else 'ready'}")
    
    choices = {}
    def check(m):
        valid = ["rock", "paper", "scissors"] if game == "rps" else ["heads", "tails"] if game == "coinflip" else ["ready"]
        return m.author.id in [challenger_id, ctx.author.id] and m.channel.type == discord.ChannelType.private and m.content.lower() in valid
    
    try:
        while len(choices) < 2:
            msg = await bot.wait_for('message', check=check, timeout=60.0)
            choices[msg.author.id] = msg.content.lower()
        
        player1_choice = choices[challenger_id]
        player2_choice = choices[ctx.author.id]
        
        if game == "rps":
            outcomes = {"rock": {"rock": "tie", "paper": "lose", "scissors": "win"},
                        "paper": {"rock": "win", "paper": "tie", "scissors": "lose"},
                        "scissors": {"rock": "lose", "paper": "win", "scissors": "tie"}}
            result = outcomes[player1_choice][player2_choice]
            if result == "win":
                winner, loser = challenger_id, ctx.author.id
            elif result == "lose":
                winner, loser = ctx.author.id, challenger_id
            else:
                await ctx.send(f"Both chose {player1_choice}. It’s a tie!")
                return
        elif game == "coinflip":
            result = random.choice(["heads", "tails"])
            if player1_choice == result and player2_choice != result:
                winner, loser = challenger_id, ctx.author.id
            elif player2_choice == result and player1_choice != result:
                winner, loser = ctx.author.id, challenger_id
            else:
                await ctx.send(f"Both chose {player1_choice}. It’s a tie!")
                return
        else:  # slots
            p1_slots = spin_slots(1)
            p2_slots = spin_slots(1)
            p1_winnings, _, _ = check_win(p1_slots)
            p2_winnings, _, _ = check_win(p2_slots)
            if p1_winnings > p2_winnings:
                winner, loser = challenger_id, ctx.author.id
            elif p2_winnings > p1_winnings:
                winner, loser = ctx.author.id, challenger_id
            else:
                await ctx.send(f"Both tied with {p1_winnings}! No winner.")
                return
        
        winner_data = get_user_data(winner)
        loser_data = get_user_data(loser)
        update_user_data(winner, {'balance': winner_data['balance'] + amount})
        update_user_data(loser, {'balance': loser_data['balance'] - amount})
        await ctx.send(f"🏆 <@{winner}> wins ${amount}!\n{player1_choice} vs {player2_choice}" if game != "slots" else f"<@{winner}> wins with {p1_winnings if winner == challenger_id else p2_winnings}!")
    except asyncio.TimeoutError:
        await ctx.send("❌ Challenge timed out!")

# --- Tournament Commands ---
@bot.command()
async def tournament(ctx, game: str):
    """Start a tournament for a specified game, requiring a ticket."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    game = game.lower()
    
    if inventory.get("tournament_tickets", 0) < 1:
        await ctx.send("❌ You need a Tournament Ticket (`!buy tournament_ticket`)!")
        return
    if game not in ["rps", "coinflip", "slots"]:
        await ctx.send("❌ Supported games: 'rps', 'coinflip', 'slots'!")
        return
    channel_id = ctx.channel.id
    if get_tournament_data(channel_id) and get_tournament_data(channel_id)['active']:
        await ctx.send("❌ A tournament is already active here!")
        return
    
    update_tournament_data(channel_id, {
        'game_type': game,
        'players': json.dumps({user_id: 0}),
        'scores': json.dumps({user_id: 0}),
        'rounds': 3,
        'current_round': 0,
        'active': 1,
        'prize_pool': TOURNAMENT_ENTRY_FEE
    })
    inventory["tournament_tickets"] -= 1
    update_user_data(user_id, {
        'inventory': json.dumps(inventory),
        'balance': user_data['balance'] - TOURNAMENT_ENTRY_FEE
    })
    await ctx.send(f"🏆 {game.capitalize()} Tournament started by {ctx.author.mention}! Join with `!join`. Starts in 60s.")
    await asyncio.sleep(60)
    await run_tournament(channel_id)

@bot.command()
async def join(ctx):
    """Join an active tournament in the current channel."""
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    tournament = get_tournament_data(channel_id)
    
    if not tournament or not tournament['active']:
        await ctx.send("❌ No active tournament in this channel!")
        return
    if user_data['balance'] < TOURNAMENT_ENTRY_FEE:
        await ctx.send(f"❌ Entry fee is ${TOURNAMENT_ENTRY_FEE}, you have ${user_data['balance']}!")
        return
    
    players = json.loads(tournament['players'])
    scores = json.loads(tournament['scores'])
    if user_id not in players:
        players[user_id] = 0
        scores[user_id] = 0
        update_user_data(user_id, {'balance': user_data['balance'] - TOURNAMENT_ENTRY_FEE})
        update_tournament_data(channel_id, {
            'players': json.dumps(players),
            'scores': json.dumps(scores),
            'prize_pool': tournament['prize_pool'] + TOURNAMENT_ENTRY_FEE
        })
        await ctx.send(f"{ctx.author.mention} joined the {tournament['game_type']} tournament! Prize pool: ${tournament['prize_pool']}")

async def run_tournament(channel_id):
    """Run a multi-round tournament and award the winner."""
    tournament = get_tournament_data(channel_id)
    channel = bot.get_channel(channel_id)
    players = json.loads(tournament['players'])
    scores = json.loads(tournament['scores'])
    
    if len(players) < 2:
        await channel.send("❌ Tournament canceled: Not enough players!")
        update_tournament_data(channel_id, {'active': 0})
        return
    
    for round_num in range(1, tournament['rounds'] + 1):
        await channel.send(f"🏆 Round {round_num} of {tournament['game_type']} Tournament begins!")
        for player_id in players:
            if tournament['game_type'] == "rps":
                player_choice = random.choice(["rock", "paper", "scissors"])
                bot_choice = random.choice(["rock", "paper", "scissors"])
                outcomes = {"rock": {"scissors": 1}, "paper": {"rock": 1}, "scissors": {"paper": 1}}
                if player_choice in outcomes and bot_choice in outcomes[player_choice]:
                    scores[player_id] += 1
            elif tournament['game_type'] == "coinflip":
                if random.choice(["heads", "tails"]) == "heads":
                    scores[player_id] += 1
            elif tournament['game_type'] == "slots":
                slots = spin_slots(1)
                winnings, _, _ = check_win(slots)
                scores[player_id] += winnings
        update_tournament_data(channel_id, {
            'scores': json.dumps(scores),
            'current_round': round_num
        })
        await asyncio.sleep(3)
    
    winner_id = max(scores, key=scores.get)
    prize = tournament['prize_pool']
    update_user_data(winner_id, {
        'balance': get_user_data(winner_id)['balance'] + prize,
        'achievements': json.dumps(json.loads(get_user_data(winner_id)['achievements']) + ["tournament_champ"])
    })
    await channel.send(f"🏆 Tournament ends! <@{winner_id}> wins ${prize} with {scores[winner_id]} points!")
    update_tournament_data(channel_id, {'active': 0})

# --- Trading Commands ---
@bot.command()
async def trade(ctx, target: discord.Member, *, items: str):
    """Initiate a trade offer with another player."""
    user_id = ctx.author.id
    target_id = target.id
    if user_id == target_id:
        await ctx.send("❌ You can’t trade with yourself!")
        return
    
    # Parse items (e.g., "gold_coin:2 diamond:1, gold_bar:1")
    offered, requested = items.split(',', 1) if ',' in items else (items, "")
    offered_items = {}
    requested_items = {}
    
    for part in offered.split():
        item, qty = part.split(':') if ':' in part else (part, 1)
        offered_items[item] = int(qty)
    for part in requested.split():
        item, qty = part.split(':') if ':' in part else (part, 1)
        requested_items[item] = int(qty)
    
    user_data = get_user_data(user_id)
    crafting_items = json.loads(user_data['crafting_items'])
    for item, qty in offered_items.items():
        if crafting_items.get(item, 0) < qty:
            await ctx.send(f"❌ You don’t have enough {item}!")
            return
    
    offer_id = create_trade_offer(user_id, target_id, offered_items, requested_items)
    await ctx.send(f"{target.mention}, {ctx.author.mention} offers trade #{offer_id}! Check with `!tradeview {offer_id}` and accept with `!tradeaccept {offer_id}`.")

@bot.command()
async def tradeview(ctx, offer_id: int):
    """View details of a trade offer."""
    offer = get_trade_offer(offer_id)
    if not offer:
        await ctx.send("❌ Trade offer not found!")
        return
    
    embed = discord.Embed(title=f"Trade Offer #{offer_id}", color=0x3498db)
    embed.add_field(name="Offered by", value=f"<@{offer['sender_id']}>", inline=True)
    embed.add_field(name="To", value=f"<@{offer['receiver_id']}>", inline=True)
    embed.add_field(name="Offered Items", value="\n".join(f"{k}: {v}" for k, v in json.loads(offer['offered_items']).items()), inline=False)
    embed.add_field(name="Requested Items", value="\n".join(f"{k}: {v}" for k, v in json.loads(offer['requested_items']).items()) or "None", inline=False)
    embed.add_field(name="Status", value=offer['status'], inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def tradeaccept(ctx, offer_id: int):
    """Accept a trade offer and exchange items."""
    offer = get_trade_offer(offer_id)
    if not offer or offer['status'] != 'pending' or offer['receiver_id'] != ctx.author.id:
        await ctx.send("❌ Invalid or unavailable trade offer!")
        return
    
    sender_data = get_user_data(offer['sender_id'])
    receiver_data = get_user_data(offer['receiver_id'])
    sender_items = json.loads(sender_data['crafting_items'])
    receiver_items = json.loads(receiver_data['crafting_items'])
    offered = json.loads(offer['offered_items'])
    requested = json.loads(offer['requested_items'])
    
    for item, qty in requested.items():
        if receiver_items.get(item, 0) < qty:
            await ctx.send(f"❌ You don’t have enough {item}!")
            return
    
    # Execute trade
    for item, qty in offered.items():
        sender_items[item] -= qty
        receiver_items[item] = receiver_items.get(item, 0) + qty
    for item, qty in requested.items():
        receiver_items[item] -= qty
        sender_items[item] = sender_items.get(item, 0) + qty
    
    update_user_data(offer['sender_id'], {'crafting_items': json.dumps(sender_items)})
    update_user_data(offer['receiver_id'], {
        'crafting_items': json.dumps(receiver_items),
        'achievements': json.dumps(json.loads(receiver_data['achievements']) + ["trader"] if "trader" not in json.loads(receiver_data['achievements']) else [])
    })
    update_trade_offer(offer_id, {'status': 'completed'})
    await ctx.send(f"🤝 Trade #{offer_id} completed between <@{offer['sender_id']}> and <@{offer['receiver_id']}>!")

# --- Help Command ---
@bot.command(name="paradox")
async def paradox_help(ctx):
    """Display a detailed help menu with all commands."""
    embed = discord.Embed(title="🎰 Paradox Casino Machine", description="Welcome to your casino adventure!", color=0x3498db)
    embed.add_field(name="**Core Commands**", value="`!bet <amount> [lines]` - Spin the slots\n`!daily` - Claim daily reward\n`!profile [user]` - View profile\n`!missions` - View missions\n`!paradox` - This menu", inline=False)
    embed.add_field(name="**Games**", value="`!roulette <type> <value> <amount>` - Play Roulette\n`!poker <amount>` - Play Poker\n`!blackjack <amount>` - Play Blackjack\n`!craps <type> <amount>` - Play Craps\n`!baccarat <type> <amount>` - Play Baccarat", inline=False)
    embed.add_field(name="**Economy**", value="`!shop` - View shop\n`!buy <item_id>` - Purchase item\n`!setbg <bg_id>` - Set background\n`!settitle <title_id>` - Set title\n`!loan <amount>` - Take loan\n`!repay` - Repay loan\n`!lottery [tickets]` - Buy lottery tickets\n`!craft <recipe>` - Craft items", inline=False)
    embed.add_field(name="**Multiplayer**", value="`!challenge <user> <game> <amount>` - Challenge someone\n`!accept` - Accept challenge\n`!tournament <game>` - Start tournament\n`!join` - Join tournament", inline=False)
    embed.add_field(name="**Trading**", value="`!trade <user> <offered,requested>` - Offer trade\n`!tradeview <id>` - View trade\n`!tradeaccept <id>` - Accept trade", inline=False)
    embed.add_field(name="**Admin**", value="`!setdailyannouncement <channel> <message>` - Set daily announcement\n`!unsetdailyannouncement` - Unset announcement", inline=False)
    embed.set_footer(text="Prefix: ! | Enjoy responsibly!")
    await ctx.send(embed=embed)

# --- Error Handling ---
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully."""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Command on cooldown! Try again in {error.retry_after:.1f}s.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument! Check `!paradox` for usage.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don’t have permission to use this command!")
    else:
        logger.error(f"Error in command {ctx.command}: {error}")
        await ctx.send("❌ An error occurred! Please try again.")

# --- Startup Logic ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable not set!")
        exit(1)
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

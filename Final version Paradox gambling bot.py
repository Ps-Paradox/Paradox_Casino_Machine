# Import required libraries for bot functionality, database, and threading
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
    """Root endpoint to confirm bot operation."""
    return "Paradox Casino Bot is running smoothly!"

@app.route('/health')
def health_check():
    """Health check endpoint for bot status."""
    return json.dumps({"status": "healthy", "uptime": time.time() - start_time}), 200

@app.route('/<path:path>')
def catch_all(path):
    """Catch-all endpoint for invalid paths."""
    print(f"Received request for path: {path}")
    return f"Path {path} not found, but server is running!", 404

def run_flask():
    """Run Flask server in a thread for uptime monitoring."""
    port = int(os.environ.get('PORT', 8080))
    try:
        print(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask server failed: {e}")

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
    "You're on fire! 🔥", "Lucky spin! 🍀", "Cha-ching! 💰", "Winner winner! 🍗",
    "Defying odds! ✨", "Jackpot vibes! ⚡", "Fortune smiles! 🌟"
]
LOSS_MESSAGES = [
    "Better luck next time! 🎲", "So close! 📏", "House wins... for now! 🤔",
    "Paradox strikes! 😤", "Keep going! ✨", "Break the odds! 🔄"
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
BACCARAT_BETS = {"player": 1, "banker": 0.95, "tie": 8}

# --- Economy Constants ---
SHOP_ITEMS = {
    "profile_bg1": {"name": "Cosmic Sky", "description": "Starry backdrop", "price": 1000},
    "profile_bg2": {"name": "Golden Vault", "description": "Gold shine", "price": 1000},
    "title_gambler": {"name": "Gambler", "description": "Risk-taker", "price": 500},
    "title_highroller": {"name": "High Roller", "description": "Big spender", "price": 750},
    "daily_boost": {"name": "Daily Boost", "description": "2x daily reward (24h)", "price": 200},
    "xp_boost": {"name": "XP Boost", "description": "2x XP (24h)", "price": 300},
    "loan_pass": {"name": "Loan Pass", "description": "Take a loan", "price": 100},
    "tournament_ticket": {"name": "Tournament Ticket", "description": "Tournament entry", "price": 500},
    "crafting_kit": {"name": "Crafting Kit", "description": "Unlock crafting", "price": 800}
}

CRAFTING_RECIPES = {
    "lucky_charm": {"ingredients": {"gold_coin": 5, "four_leaf_clover": 1}, "description": "5% win boost (1h)", "duration": "1h"},
    "mega_jackpot": {"ingredients": {"gold_bar": 3, "diamond": 2}, "description": "3x jackpot once", "uses": 1}
}

ITEM_DROP_TABLE = {
    "gold_coin": {"chance": 0.5, "source": "slots"},
    "four_leaf_clover": {"chance": 0.1, "source": "roulette"},
    "gold_bar": {"chance": 0.05, "source": "poker"},
    "diamond": {"chance": 0.02, "source": "blackjack"}
}

# --- Achievements Dictionary ---
ACHIEVEMENTS = {
    "first_win": {"name": "Paradox Novice", "description": "Win first slot game", "emoji": "🏆"},
    "big_winner": {"name": "Paradox Master", "description": "Win over 1000 coins", "emoji": "💎"},
    "jackpot": {"name": "Paradox Breaker", "description": "Hit the jackpot", "emoji": "🎯"},
    "broke": {"name": "Rock Bottom", "description": "Lose all money", "emoji": "📉"},
    "comeback": {"name": "Phoenix Rising", "description": "Win with <100 coins", "emoji": "🔄"},
    "high_roller": {"name": "Paradox Whale", "description": "Bet max amount", "emoji": "💵"},
    "daily_streak": {"name": "Time Traveler", "description": "Claim 7 days", "emoji": "⏰"},
    "legendary": {"name": "Legendary Gambler", "description": "Win 5 in a row", "emoji": "👑"},
    "rps_master": {"name": "RPS Master", "description": "Win 5 RPS in a row", "emoji": "🪨"},
    "blackjack_pro": {"name": "Blackjack Pro", "description": "Win 3 Blackjack in a row", "emoji": "♠"},
    "roulette_master": {"name": "Roulette Master", "description": "Win number bet", "emoji": "🎡"},
    "poker_pro": {"name": "Poker Pro", "description": "Win Poker game", "emoji": "🃏"},
    "craps_winner": {"name": "Craps Winner", "description": "Win Craps game", "emoji": "🎲"},
    "baccarat_champ": {"name": "Baccarat Champ", "description": "Win Baccarat game", "emoji": "🎴"},
    "shopaholic": {"name": "Shopaholic", "description": "Buy 10 items", "emoji": "🛍️"},
    "vip_member": {"name": "VIP Member", "description": "Reach Level 5", "emoji": "👑"},
    "debt_free": {"name": "Debt Free", "description": "Pay off loan", "emoji": "💸"},
    "tournament_champ": {"name": "Tournament Champ", "description": "Win tournament", "emoji": "🏅"},
    "craftsman": {"name": "Craftsman", "description": "Craft first item", "emoji": "🔨"},
    "trader": {"name": "Trader", "description": "Complete a trade", "emoji": "🤝"},
    "trivia_genius": {"name": "Trivia Genius", "description": "Answer 10 trivia", "emoji": "❓"},
    "hangman_hero": {"name": "Hangman Hero", "description": "Win 5 Hangman", "emoji": "🔤"},
    "number_wizard": {"name": "Number Wizard", "description": "Guess number <10 tries", "emoji": "🔢"},
    "coinflip_streak": {"name": "Coinflip Champ", "description": "Win 3 coinflips", "emoji": "🪙"},
    "dice_master": {"name": "Dice Master", "description": "Win 5 dice rolls", "emoji": "🎲"},
    "lottery_winner": {"name": "Lottery Lord", "description": "Win lottery", "emoji": "🎟️"}
}

# --- Mission Constants ---
MISSIONS = {
    "daily": [
        {"id": "play_slots", "name": "Slot Enthusiast", "description": "Play 5 slots", "requirements": {"slot_plays": 5}, "rewards": {"coins": 100}},
        {"id": "win_games", "name": "Winner", "description": "Win 3 games", "requirements": {"wins": 3}, "rewards": {"coins": 150}}
    ],
    "weekly": [
        {"id": "slot_master", "name": "Slot Master", "description": "Win 10 slots", "requirements": {"slot_wins": 10}, "rewards": {"coins": 500}}
    ],
    "one-time": [
        {"id": "level_5", "name": "Level Up", "description": "Reach level 5", "requirements": {"level": 5}, "rewards": {"coins": 1000}},
        {"id": "jackpot", "name": "Jackpot Hunter", "description": "Win jackpot", "requirements": {"jackpot_wins": 1}, "rewards": {"coins": 2000}}
    ]
}

# --- SQLite Database Initialization ---
def init_db():
    """Initialize SQLite database with tables for users, lottery, tournaments, items, trades, and announcements."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
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
                    profile_custom TEXT DEFAULT '{}',
                    daily_claim TEXT,
                    streaks TEXT DEFAULT '{}',
                    trivia_correct INTEGER DEFAULT 0,
                    hangman_wins INTEGER DEFAULT 0,
                    number_guesses INTEGER DEFAULT 0,
                    coinflip_wins INTEGER DEFAULT 0,
                    dice_wins INTEGER DEFAULT 0,
                    rps_wins INTEGER DEFAULT 0,
                    blackjack_wins INTEGER DEFAULT 0,
                    craps_wins INTEGER DEFAULT 0,
                    crafting_items TEXT DEFAULT '{}',
                    active_effects TEXT DEFAULT '{}',
                    missions TEXT DEFAULT '{}'
                )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_users_id ON users (id)')
    c.execute('''CREATE TABLE IF NOT EXISTS lottery (
                    jackpot INTEGER DEFAULT 1000
                )''')
    c.execute('INSERT OR IGNORE INTO lottery (rowid, jackpot) VALUES (1, 1000)')
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
    c.execute('''CREATE TABLE IF NOT EXISTS items (
                    item_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    price INTEGER
                )''')
    for item_id, item in SHOP_ITEMS.items():
        c.execute('INSERT OR IGNORE INTO items (item_id, name, description, price) VALUES (?, ?, ?, ?)',
                  (item_id, item['name'], item['description'], item['price']))
    c.execute('''CREATE TABLE IF NOT EXISTS trade_offers (
                    offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    receiver_id INTEGER,
                    offered_items TEXT,
                    requested_items TEXT,
                    status TEXT DEFAULT 'pending'
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS announcement_settings (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    message TEXT
                )''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

init_db()

# --- Database Helper Functions ---
def get_user_data(user_id):
    """Retrieve user data, initializing if absent."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (id, balance) VALUES (?, ?)', (user_id, STARTING_BALANCE))
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    data = c.fetchone()
    conn.commit()
    conn.close()
    keys = ['id', 'balance', 'winnings', 'xp', 'level', 'achievements', 'inventory', 'loans',
            'lottery_tickets', 'profile_custom', 'daily_claim', 'streaks', 'trivia_correct',
            'hangman_wins', 'number_guesses', 'coinflip_wins', 'dice_wins', 'rps_wins',
            'blackjack_wins', 'craps_wins', 'crafting_items', 'active_effects', 'missions']
    return dict(zip(keys, data))

def update_user_data(user_id, updates):
    """Update user data with provided key-value pairs."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    query = 'UPDATE users SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE id = ?'
    values = list(updates.values()) + [user_id]
    c.execute(query, values)
    conn.commit()
    conn.close()
    logger.debug(f"Updated user {user_id}: {updates}")

def get_lottery_jackpot():
    """Retrieve current lottery jackpot."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT jackpot FROM lottery WHERE rowid = 1')
    jackpot = c.fetchone()[0]
    conn.close()
    return jackpot

def update_lottery_jackpot(amount):
    """Adjust lottery jackpot by amount."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('UPDATE lottery SET jackpot = jackpot + ? WHERE rowid = 1', (amount,))
    conn.commit()
    conn.close()
    logger.debug(f"Jackpot updated by {amount}")

def get_tournament_data(channel_id):
    """Retrieve tournament data for a channel."""
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
    """Update or insert tournament data."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO tournaments (channel_id) VALUES (?)', (channel_id,))
    query = 'UPDATE tournaments SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE channel_id = ?'
    values = list(updates.values()) + [channel_id]
    c.execute(query, values)
    conn.commit()
    conn.close()
    logger.debug(f"Tournament updated for {channel_id}: {updates}")

def get_item_data(item_id):
    """Retrieve item data from shop."""
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
    """Create a trade offer."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('''INSERT INTO trade_offers (sender_id, receiver_id, offered_items, requested_items)
                 VALUES (?, ?, ?, ?)''', (sender_id, receiver_id, json.dumps(offered_items), json.dumps(requested_items)))
    offer_id = c.lastrowid
    conn.commit()
    conn.close()
    return offer_id

def get_trade_offer(offer_id):
    """Retrieve trade offer details."""
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
    """Update trade offer status or details."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    query = 'UPDATE trade_offers SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE offer_id = ?'
    values = list(updates.values()) + [offer_id]
    c.execute(query, values)
    conn.commit()
    conn.close()

# --- Mission Helper Functions ---
def get_user_missions(user_id):
    """Retrieve user's mission progress."""
    user_data = get_user_data(user_id)
    return json.loads(user_data['missions'])

def update_user_missions(user_id, missions):
    """Update user's mission progress."""
    update_user_data(user_id, {'missions': json.dumps(missions)})

def initialize_missions(user_id):
    """Initialize missions for a user."""
    missions = {
        "daily": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["daily"]},
        "weekly": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["weekly"]},
        "one-time": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["one-time"]}
    }
    update_user_missions(user_id, missions)

def reset_missions(user_id, mission_type):
    """Reset missions of a specific type."""
    missions = get_user_missions(user_id)
    if mission_type in missions:
        missions[mission_type] = {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS[mission_type]}
        update_user_missions(user_id, missions)

# --- Slot Machine Functions ---
def spin_slots(lines):
    """Generate slot spin result."""
    return [[random.choice(SLOTS) for _ in range(3)] for _ in range(lines)]

def check_win(slots):
    """Check for wins and calculate winnings."""
    winnings = 0
    jackpot_win = False
    winning_lines = []
    for i, line in enumerate(slots):
        if line.count(line[0]) == 3:
            multiplier = JACKPOT_MULTIPLIER if line[0] == JACKPOT_SYMBOL else 1
            line_win = 100 * multiplier
            winnings += line_win
            winning_lines.append((i, line_win))
            if line[0] == JACKPOT_SYMBOL:
                jackpot_win = True
    return winnings, jackpot_win, winning_lines

def format_animated_slots(slots, revealed_columns):
    """Format slots for animation."""
    display_lines = []
    for line in slots:
        line_display = [line[i] if i in revealed_columns else '🎰' for i in range(3)]
        display_lines.append(' '.join(line_display))
    return '\n'.join(display_lines)

def format_slot_display(slots, winning_lines=None):
    """Format slot display with winning lines."""
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
    """Determine roulette number color."""
    if number in RED_NUMBERS:
        return "red"
    elif number in BLACK_NUMBERS:
        return "black"
    return "green"

def validate_roulette_bet(bet_type, bet_value):
    """Validate roulette bet."""
    if bet_type not in ROULETTE_BETS:
        return False
    return ROULETTE_BETS[bet_type]["validator"](bet_value)

def calculate_roulette_payout(bet_type, bet_value, spun_number):
    """Calculate roulette payout."""
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
    """Deal a 5-card poker hand."""
    deck = POKER_CARDS.copy()
    random.shuffle(deck)
    return deck[:5]

def evaluate_poker_hand(hand):
    """Evaluate poker hand rank and payout."""
    ranks = sorted([card[:-1].replace('T', '10').replace('J', '11').replace('Q', '12').replace('K', '13').replace('A', '14') for card in hand], key=int, reverse=True)
    suits = [card[-1] for card in hand]
    rank_values = [int(r) for r in ranks]
    is_flush = len(set(suits)) == 1
    is_straight = all(rank_values[i] - 1 == rank_values[i + 1] for i in range(4)) or (ranks == ['14', '5', '4', '3', '2'])
    counts = {r: ranks.count(r) for r in ranks}
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
    return "High Card", POKER_HANDS["High Card"]

# --- Blackjack Functions ---
def deal_blackjack_hand():
    """Deal a 2-card blackjack hand."""
    deck = BLACKJACK_CARDS.copy()
    random.shuffle(deck)
    return deck[:2]

def calculate_blackjack_score(hand):
    """Calculate blackjack hand score."""
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
    """Roll two dice."""
    return random.randint(1, 6), random.randint(1, 6)

def play_craps(bet_type, amount, user_id):
    """Play a Craps round."""
    user_data = get_user_data(user_id)
    if amount <= 0 or amount > user_data['balance']:
        return "Invalid bet!", None, user_data['balance']
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
    """Deal Baccarat hands."""
    deck = BLACKJACK_CARDS.copy()
    random.shuffle(deck)
    return deck[:2], deck[2:4]

def calculate_baccarat_score(hand):
    """Calculate Baccarat score."""
    return sum(CARD_VALUES[card[:-1]] for card in hand) % 10

def determine_baccarat_winner(player_score, banker_score):
    """Determine Baccarat winner."""
    if player_score > banker_score:
        return "player"
    elif banker_score > player_score:
        return "banker"
    return "tie"

# --- Additional Game Classes ---
class TicTacToe:
    def __init__(self):
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_active = False
        self.players = {}

    def display_board(self):
        return f"```\n  0 1 2\n0 {self.board[0][0]}|{self.board[0][1]}|{self.board[0][2]}\n  -+-+-\n1 {self.board[1][0]}|{self.board[1][1]}|{self.board[1][2]}\n  -+-+-\n2 {self.board[2][0]}|{self.board[2][1]}|{self.board[2][2]}\n```"

    def make_move(self, row, col, player):
        if 0 <= row <= 2 and 0 <= col <= 2 and self.board[row][col] == " ":
            self.board[row][col] = player
            return True
        return False

    def check_win(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != " ":
                return row[0]
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != " ":
                return self.board[0][col]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != " ":
            return self.board[0][2]
        return None

    def is_full(self):
        return all(cell != " " for row in self.board for cell in row)

game = TicTacToe()

HANGMAN_WORDS = ["luck", "casino", "jackpot", "paradox", "gamble", "slots", "dice"]
HANGMAN_STAGES = [
    "```\n  _____\n  |   |\n      |\n      |\n      |\n      |\n=========\n```",
    "```\n  _____\n  |   |\n  O   |\n      |\n      |\n      |\n=========\n```",
    "```\n  _____\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========\n```",
    "```\n  _____\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========\n```",
    "```\n  _____\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========\n```",
    "```\n  _____\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========\n```",
    "```\n  _____\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========\n```"
]

class HangmanGame:
    def __init__(self):
        self.word = random.choice(HANGMAN_WORDS).upper()
        self.guessed = set()
        self.wrong_guesses = 0
        self.active = False

    def display_word(self):
        return " ".join(c if c in self.guessed else "_" for c in self.word)

    def guess(self, letter):
        letter = letter.upper()
        if letter in self.guessed:
            return "already guessed"
        self.guessed.add(letter)
        if letter not in self.word:
            self.wrong_guesses += 1
            return "wrong"
        return "correct" if all(c in self.guessed for c in self.word) else "partial"

hangman_game = HangmanGame()

class NumberGuessGame:
    def __init__(self):
        self.number = random.randint(1, 100)
        self.guesses_left = 20
        self.guesses_made = 0
        self.active = False

    def guess(self, number):
        self.guesses_made += 1
        self.guesses_left -= 1
        if number == self.number:
            return "correct"
        return "higher" if number < self.number else "lower"

number_guess_game = NumberGuessGame()

TRIVIA_QUESTIONS = [
    {"question": "Highest Blackjack score?", "options": ["20", "21", "22", "23"], "correct": 1},
    {"question": "Jackpot symbol in slots?", "options": ["🍒", "💎", "7️⃣", "🔔"], "correct": 2},
    {"question": "First game added?", "options": ["Tic-Tac-Toe", "Slots", "Wheel", "Blackjack"], "correct": 1}
]

RPS_CHOICES = ["rock", "paper", "scissors"]
def rps_outcome(player, bot_choice):
    if player == bot_choice:
        return "tie"
    if (player == "rock" and bot_choice == "scissors") or \
       (player == "paper" and bot_choice == "rock") or \
       (player == "scissors" and bot_choice == "paper"):
        return "win"
    return "lose"

WHEEL_PRIZES = [0, 50, 100, 200, 500, 1000, "Jackpot"]

# --- XP and Leveling System ---
def add_xp(user_id, amount):
    """Add XP and handle level-ups."""
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    boosts = inventory.get('boosts', {})
    xp_multiplier = 2 if 'xp_boost' in boosts and datetime.fromisoformat(boosts['xp_boost']) > datetime.utcnow() else 1
    xp = user_data['xp'] + amount * xp_multiplier
    level = user_data['level']
    levels_gained = 0
    while xp >= 100 * level:
        xp -= 100 * level
        level += 1
        levels_gained += 1
    update_user_data(user_id, {
        'xp': xp,
        'level': level,
        'balance': user_data['balance'] + 500 * levels_gained
    })
    return levels_gained

# --- Achievements System ---
def check_achievements(user_id, bet_amount, win_amount, jackpot_win, balance, streaks, game_type=None):
    """Check and award achievements."""
    user_data = get_user_data(user_id)
    achievements = json.loads(user_data['achievements'])
    earned = []
    streaks = json.loads(streaks) if isinstance(streaks, str) else streaks
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
    if user_data['trivia_correct'] >= 10 and "trivia_genius" not in achievements:
        earned.append("trivia_genius")
    if user_data['hangman_wins'] >= 5 and "hangman_hero" not in achievements:
        earned.append("hangman_hero")
    if user_data['number_guesses'] > 0 and user_data['number_guesses'] <= 10 and "number_wizard" not in achievements:
        earned.append("number_wizard")
    if streaks.get('coinflip_wins', 0) >= 3 and "coinflip_streak" not in achievements:
        earned.append("coinflip_streak")
    if streaks.get('dice_wins', 0) >= 5 and "dice_master" not in achievements:
        earned.append("dice_master")
    update_user_data(user_id, {'achievements': json.dumps(achievements + earned)})
    return earned

# --- Crafting and Trading ---
def check_crafting_eligibility(user_id, recipe_id):
    """Check crafting eligibility."""
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data['inventory'])
    crafting_items = json.loads(user_data['crafting_items'])
    recipe = CRAFTING_RECIPES.get(recipe_id)
    if not recipe or 'crafting_kit' not in inventory:
        return False, "Need a crafting kit!"
    for item, qty in recipe['ingredients'].items():
        if crafting_items.get(item, 0) < qty:
            return False, f"Not enough {item}!"
    return True, "Eligible"

def craft_item(user_id, recipe_id):
    """Craft an item."""
    eligible, message = check_crafting_eligibility(user_id, recipe_id)
    if not eligible:
        return message
    user_data = get_user_data(user_id)
    crafting_items = json.loads(user_data['crafting_items'])
    recipe = CRAFTING_RECIPES[recipe_id]
    for item, qty in recipe['ingredients'].items():
        crafting_items[item] -= qty
    active_effects = json.loads(user_data['active_effects'])
    if recipe_id == "lucky_charm":
        active_effects[recipe_id] = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    elif recipe_id == "mega_jackpot":
        active_effects[recipe_id] = 1
    update_user_data(user_id, {
        'crafting_items': json.dumps(crafting_items),
        'active_effects': json.dumps(active_effects)
    })
    return f"Crafted {recipe_id}! {recipe['description']}"

def award_drop(user_id, game_type):
    """Award random crafting drop."""
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
    """Handle bot startup."""
    logger.info(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!paradox for commands"))
    bot.loop.create_task(casino_announcements())
    bot.loop.create_task(lottery_draw_task())
    bot.loop.create_task(save_data_periodically())
    bot.loop.create_task(daily_announcement_task())

async def casino_announcements():
    """Send periodic announcements."""
    await bot.wait_until_ready()
    announcements = [
        {"title": "🎰 Slot Frenzy!", "description": f"Spin `!bet` for {JACKPOT_SYMBOL}!"},
        {"title": "💰 Daily Rewards", "description": "Claim `!daily`!"},
        {"title": "🎡 Roulette", "description": "Bet with `!roulette`!"},
        {"title": "🃏 Poker", "description": "Play `!poker`!"},
        {"title": "♠ Blackjack", "description": "Beat dealer with `!blackjack`!"},
        {"title": "🎲 Craps", "description": "Roll `!craps`!"},
        {"title": "🎴 Baccarat", "description": "Play `!baccarat`!"}
    ]
    index = 0
    while not bot.is_closed():
        for guild in bot.guilds:
            channel = guild.system_channel or discord.utils.get(guild.text_channels, name='general')
            if channel:
                embed = discord.Embed(**announcements[index], color=0xf1c40f)
                embed.set_footer(text="Paradox Casino")
                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Announcement failed in {guild.name}: {e}")
        index = (index + 1) % len(announcements)
        await asyncio.sleep(3600 * 12)

async def lottery_draw_task():
    """Handle daily lottery draws."""
    while True:
        await asyncio.sleep(86400)
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
                'achievements': json.dumps(json.loads(user_data['achievements']) + ["lottery_winner"])
            })
            c.execute('UPDATE users SET lottery_tickets = 0')
            c.execute('UPDATE lottery SET jackpot = 1000 WHERE rowid = 1')
            conn.commit()
            for guild in bot.guilds:
                if guild.system_channel:
                    await guild.system_channel.send(f"<@{winner_id}> won ${jackpot} in the lottery!")
        conn.close()

async def save_data_periodically():
    """Periodic data save checkpoint."""
    while True:
        await asyncio.sleep(300)
        logger.info("Data saved.")

async def daily_announcement_task():
    """Send daily announcements to configured channels."""
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
                        logger.error(f"Daily announcement failed in {guild.name}: {e}")
        conn.close()

# --- Core Commands ---
@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet(ctx, amount: int, lines: int = 1):
    """Spin the slot machine."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    total_bet = amount * lines
    if amount < MIN_BET or amount > MAX_BET or lines < 1 or lines > MAX_LINES or total_bet > user_data['balance']:
        await ctx.send(f"❌ Bet ${MIN_BET}-${MAX_BET}, lines 1-{MAX_LINES}, funds: ${user_data['balance']}")
        return
    update_lottery_jackpot(int(total_bet * 0.05))
    slots = spin_slots(lines)
    winnings, jackpot_win, winning_lines = check_win(slots)
    if jackpot_win:
        jackpot_amount = get_lottery_jackpot()
        winnings += jackpot_amount
        update_lottery_jackpot(-jackpot_amount + 1000)
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
        'streaks': json.dumps(streaks)
    })
    embed = discord.Embed(
        title="🎰 Winner!" if winnings > 0 else "🎰 No Luck!",
        description=f"{random.choice(WIN_MESSAGES if winnings > 0 else LOSS_MESSAGES)}\nBet ${total_bet}, {'won' if winnings > 0 else 'lost'} ${winnings if winnings > 0 else total_bet}",
        color=0xf1c40f if winnings > 0 else 0x95a5a6
    )
    embed.add_field(name="Your Spin", value=f"```\n{format_slot_display(slots, winning_lines)}\n```", inline=False)
    embed.add_field(name="Balance", value=f"${user_data['balance']}", inline=True)
    if earned_achievements:
        embed.add_field(name="🏆 Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements), inline=False)
    await ctx.send(embed=embed)
    levels_gained = add_xp(user_id, 10)
    if levels_gained:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to {get_user_data(user_id)['level']}! +${500 * levels_gained}")

@bot.command()
async def daily(ctx):
    """Claim daily reward."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    now = datetime.utcnow().isoformat()
    last_claim = user_data['daily_claim']
    if not last_claim or (datetime.fromisoformat(last_claim) + timedelta(days=1)) <= datetime.fromisoformat(now):
        base_reward = DAILY_REWARD * (1.5 if user_data['level'] >= 5 else 1)
        streaks = json.loads(user_data['streaks'])
        daily_streak = streaks.get('daily', 0)
        if last_claim and (datetime.fromisoformat(last_claim) + timedelta(days=2)) > datetime.fromisoformat(now):
            daily_streak += 1
        else:
            daily_streak = 1
        streak_bonus = min(daily_streak * 50, DAILY_REWARD) if daily_streak < 7 else DAILY_REWARD
        total_reward = int(base_reward + streak_bonus)
        user_data['balance'] += total_reward
        streaks['daily'] = daily_streak
        earned_achievements = check_achievements(user_id, 0, total_reward, False, user_data['balance'], streaks)
        update_user_data(user_id, {
            'balance': user_data['balance'],
            'daily_claim': now,
            'streaks': json.dumps(streaks)
        })
        embed = discord.Embed(title="💸 Daily Reward!", description=f"${total_reward} claimed!", color=0x2ecc71)
        if streak_bonus:
            embed.add_field(name=f"🔥 {daily_streak}-Day Streak", value=f"+${streak_bonus}", inline=False)
        embed.add_field(name="Balance", value=f"${user_data['balance']}", inline=True)
        if earned_achievements:
            embed.add_field(name="🏆 Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements), inline=False)
        await ctx.send(embed=embed)
    else:
        time_left = (datetime.fromisoformat(last_claim) + timedelta(days=1)) - datetime.fromisoformat(now)
        await ctx.send(f"⏳ Wait {time_left.seconds // 3600}h {(time_left.seconds % 3600) // 60}m")

@bot.command()
async def profile(ctx, member: discord.Member = None):
    """Display user profile."""
    user = member or ctx.author
    user_data = get_user_data(user.id)
    embed = discord.Embed(
        title=f"👤 {user.name}'s Profile",
        description=f"Level: {user_data['level']}\nXP: {user_data['xp']}/{100 * user_data['level']}\nBalance: ${user_data['balance']}",
        color=0x3498db
    )
    achievements = json.loads(user_data['achievements'])
    if achievements:
        embed.add_field(name="Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} {ACHIEVEMENTS[a]['name']}" for a in achievements), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def jackpot(ctx):
    """Display current jackpot."""
    jackpot_amount = get_lottery_jackpot()
    embed = discord.Embed(title="🎰 Jackpot", description=f"${jackpot_amount}", color=0xf1c40f)
    await ctx.send(embed=embed)

# --- Game Commands ---
@bot.command()
async def tictactoe(ctx, opponent: discord.Member = None):
    """Start Tic-Tac-Toe."""
    if game.game_active:
        await ctx.send("❌ Game in progress!")
        return
    game.game_active = True
    game.players = {ctx.author.id: "X"}
    if opponent:
        if opponent == ctx.author:
            await ctx.send("❌ Can't play yourself!")
            return
        game.players[opponent.id] = "O"
        await ctx.send(f"🎮 Tic-Tac-Toe: {ctx.author.mention} (X) vs {opponent.mention} (O)! Use !move [row] [col].")
    else:
        game.players[bot.user.id] = "O"
        await ctx.send(f"🎮 Tic-Tac-Toe: {ctx.author.mention} (X) vs Bot (O). Use !move [row] [col].")
    await ctx.send(game.display_board())

@bot.command()
async def move(ctx, row: int, col: int):
    """Make a Tic-Tac-Toe move."""
    if not game.game_active:
        await ctx.send("❌ No game! Start with !tictactoe.")
        return
    if ctx.author.id not in game.players:
        await ctx.send("❌ Not in this game!")
        return
    if game.current_player != game.players.get(ctx.author.id):
        await ctx.send("❌ Not your turn!")
        return
    if row not in [0, 1, 2] or col not in [0, 1, 2]:
        await ctx.send("❌ Invalid move! 0-2 only.")
        return
    if game.make_move(row, col, game.current_player):
        winner = game.check_win()
        if winner:
            update_user_data(ctx.author.id, {'balance': get_user_data(ctx.author.id)['balance'] + 100})
            await ctx.send(f"{game.display_board()}\n{ctx.author.mention} wins! +$100")
            game.game_active = False
        elif game.is_full():
            await ctx.send(f"{game.display_board()}\nTie!")
            game.game_active = False
        else:
            game.current_player = "O" if game.current_player == "X" else "X"
            next_player = next(k for k, v in game.players.items() if v == game.current_player)
            await ctx.send(f"{game.display_board()}\n<@{next_player}>'s turn!")
            if next_player == bot.user.id:
                await asyncio.sleep(1)
                while True:
                    bot_row, bot_col = random.randint(0, 2), random.randint(0, 2)
                    if game.make_move(bot_row, bot_col, "O"):
                        winner = game.check_win()
                        await ctx.send(f"{game.display_board()}\nBot moved to ({bot_row}, {bot_col})!")
                        if winner:
                            await ctx.send("🤖 Bot wins!")
                            game.game_active = False
                        elif game.is_full():
                            await ctx.send("🤝 Tie!")
                            game.game_active = False
                        break

@bot.command()
async def hangman(ctx):
    """Start Hangman."""
    if hangman_game.active:
        await ctx.send("❌ Hangman in progress!")
        return
    hangman_game.active = True
    hangman_game.__init__()
    await ctx.send(f"{HANGMAN_STAGES[0]}\nWord: {hangman_game.display_word()}\nGuess with `!guess letter`")

@bot.command()
async def guess(ctx, letter: str):
    """Guess in Hangman."""
    if not hangman_game.active:
        await ctx.send("❌ No Hangman game!")
        return
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    result = hangman_game.guess(letter)
    if result == "already guessed":
        await ctx.send("❌ Already guessed!")
    elif result == "wrong":
        await ctx.send(f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\nWord: {hangman_game.display_word()}")
        if hangman_game.wrong_guesses == 6:
            await ctx.send(f"Game Over! Word was {hangman_game.word}")
            hangman_game.active = False
    elif result == "correct":
        update_user_data(user_id, {
            'balance': user_data['balance'] + 50,
            'hangman_wins': user_data['hangman_wins'] + 1
        })
        await ctx.send(f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\nWord: {hangman_game.display_word()}\nWin! +$50")
        hangman_game.active = False
    else:
        await ctx.send(f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\nWord: {hangman_game.display_word()}")

@bot.command()
async def guessnumber(ctx):
    """Start number guessing."""
    if number_guess_game.active:
        await ctx.send("❌ Game in progress!")
        return
    number_guess_game.active = True
    number_guess_game.__init__()
    await ctx.send(f"Guess 1-100! {number_guess_game.guesses_left} guesses left. Use `!number guess`")

@bot.command()
async def number(ctx, guess: int):
    """Guess in number game."""
    if not number_guess_game.active:
        await ctx.send("❌ No game!")
        return
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    result = number_guess_game.guess(guess)
    if result == "correct":
        update_user_data(user_id, {
            'balance': user_data['balance'] + 50,
            'number_guesses': number_guess_game.guesses_made
        })
        await ctx.send(f"Correct! {number_guess_game.number} in {number_guess_game.guesses_made} guesses! +$50")
        number_guess_game.active = False
    elif number_guess_game.guesses_left == 0:
        await ctx.send(f"Out of guesses! Was {number_guess_game.number}.")
        number_guess_game.active = False
    else:
        await ctx.send(f"Too {'high' if result == 'lower' else 'low'}! {number_guess_game.guesses_left} left.")

@bot.command()
async def trivia(ctx):
    """Answer trivia."""
    question = random.choice(TRIVIA_QUESTIONS)
    embed = discord.Embed(title="❓ Trivia", description=question["question"], color=0x3498db)
    for i, opt in enumerate(question["options"], 1):
        embed.add_field(name=f"{i}. {opt}", value="\u200b", inline=False)
    await ctx.send(embed=embed)
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() and 1 <= int(m.content) <= 4
    try:
        response = await bot.wait_for('message', check=check, timeout=30.0)
        user_id = ctx.author.id
        user_data = get_user_data(user_id)
        if int(response.content) - 1 == question["correct"]:
            update_user_data(user_id, {
                'balance': user_data['balance'] + 100,
                'trivia_correct': user_data['trivia_correct'] + 1
            })
            await ctx.send("Correct! +$100")
        else:
            await ctx.send(f"Wrong! Answer was {question['options'][question['correct']]}.")
    except asyncio.TimeoutError:
        await ctx.send("Time’s up!")

@bot.command()
async def rps(ctx, amount: int):
    """Play RPS."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet ${MIN_BET}-${MAX_BET}, funds: ${user_data['balance']}")
        return
    await ctx.send("Choose: rock, paper, or scissors")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in RPS_CHOICES
    try:
        response = await bot.wait_for('message', check=check, timeout=30.0)
        player_choice = response.content.lower()
        bot_choice = random.choice(RPS_CHOICES)
        outcome = rps_outcome(player_choice, bot_choice)
        streaks = json.loads(user_data['streaks'])
        if outcome == "win":
            streaks['rps_wins'] = streaks.get('rps_wins', 0) + 1
            update_user_data(user_id, {
                'balance': user_data['balance'] + amount,
                'rps_wins': user_data['rps_wins'] + 1,
                'streaks': json.dumps(streaks)
            })
            await ctx.send(f"You chose {player_choice}, bot chose {bot_choice}. Win! +${amount}")
        elif outcome == "lose":
            streaks['rps_wins'] = 0
            update_user_data(user_id, {
                'balance': user_data['balance'] - amount,
                'streaks': json.dumps(streaks)
            })
            await ctx.send(f"You chose {player_choice}, bot chose {bot_choice}. Lose! -${amount}")
        else:
            await ctx.send(f"You chose {player_choice}, bot chose {bot_choice}. Tie!")
    except asyncio.TimeoutError:
        await ctx.send("Time’s up!")

@bot.command()
async def blackjack(ctx, amount: int):
    """Play Blackjack."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet ${MIN_BET}-${MAX_BET}, funds: ${user_data['balance']}")
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
        title="♠ Blackjack",
        description=f"Your Hand: {' '.join(player_hand)} ({player_score})\nDealer: {' '.join(dealer_hand)} ({dealer_score})",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Result", value=f"{'Win' if win else 'Lose'}! Payout: ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    update_user_data(user_id, {'balance': new_balance})
    if win:
        check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "blackjack")

@bot.command()
async def wheel(ctx, amount: int):
    """Spin Wheel of Fortune."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet ${MIN_BET}-${MAX_BET}, funds: ${user_data['balance']}")
        return
    prize = random.choice(WHEEL_PRIZES)
    winnings = get_lottery_jackpot() if prize == "Jackpot" else prize
    if prize == "Jackpot":
        update_lottery_jackpot(-winnings + 1000)
    update_user_data(user_id, {'balance': user_data['balance'] - amount + winnings})
    await ctx.send(f"Spun wheel and won {prize if prize != 'Jackpot' else f'${winnings} Jackpot'}! Balance: ${user_data['balance'] - amount + winnings}")

@bot.command()
async def coinflip(ctx, amount: int, choice: str):
    """Flip a coin."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount <= 0 or amount > user_data['balance'] or choice.lower() not in ["heads", "tails"]:
        await ctx.send("❌ Invalid amount or choice!")
        return
    result = random.choice(["heads", "tails"])
    win = choice.lower() == result
    payout = amount if win else -amount
    streaks = json.loads(user_data['streaks'])
    streaks['coinflip_wins'] = streaks.get('coinflip_wins', 0) + 1 if win else 0
    update_user_data(user_id, {
        'balance': user_data['balance'] + payout,
        'coinflip_wins': user_data['coinflip_wins'] + 1 if win else user_data['coinflip_wins'],
        'streaks': json.dumps(streaks)
    })
    embed = discord.Embed(
        title="🪙 Coin Flip",
        description=f"Flipped {result}. {'Won' if win else 'Lost'} ${abs(payout)}!",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Balance", value=f"${user_data['balance'] + payout}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def dice(ctx, amount: int, prediction: str):
    """Roll dice."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount <= 0 or amount > user_data['balance'] or prediction.lower() not in ["over 7", "under 7", "exactly 7"]:
        await ctx.send("❌ Invalid amount or prediction!")
        return
    dice1, dice2 = random.randint(1, 6), random.randint(1, 6)
    total = dice1 + dice2
    win = (prediction.lower() == "over 7" and total > 7) or \
          (prediction.lower() == "under 7" and total < 7) or \
          (prediction.lower() == "exactly 7" and total == 7)
    payout = amount * 5 if prediction.lower() == "exactly 7" and win else amount if win else -amount
    streaks = json.loads(user_data['streaks'])
    streaks['dice_wins'] = streaks.get('dice_wins', 0) + 1 if win else 0
    update_user_data(user_id, {
        'balance': user_data['balance'] + payout,
        'dice_wins': user_data['dice_wins'] + 1 if win else user_data['dice_wins'],
        'streaks': json.dumps(streaks)
    })
    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=f"Rolled {dice1} + {dice2} = {total}. {'Won' if win else 'Lost'} ${abs(payout)}!",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Balance", value=f"${user_data['balance'] + payout}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def roulette(ctx, bet_type: str, bet_value: str, amount: int):
    """Play Roulette."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    bet_type = bet_type.lower()
    if not validate_roulette_bet(bet_type, bet_value):
        await ctx.send("❌ Invalid bet! Use: number (0-36), color (red/black), etc.")
        return
    if amount < MIN_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet ${MIN_BET}+, funds: ${user_data['balance']}")
        return
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    spun_number = random.randint(0, 36)
    payout_multiplier = calculate_roulette_payout(bet_type, bet_value, spun_number)
    payout = amount * payout_multiplier
    new_balance = user_data['balance'] - amount + payout
    embed = discord.Embed(
        title="🎡 Roulette",
        description=f"Landed on {spun_number} ({get_roulette_color(spun_number)})",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="Bet", value=f"{bet_type.capitalize()} {bet_value}: ${amount}", inline=False)
    embed.add_field(name="Result", value=f"{'Win' if payout > 0 else 'Lose'}! ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    update_user_data(user_id, {'balance': new_balance})
    if payout > 0:
        check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "roulette")

@bot.command()
async def poker(ctx, amount: int):
    """Play Poker."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet ${MIN_BET}-${MAX_BET}, funds: ${user_data['balance']}")
        return
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    player_hand = deal_poker_hand()
    bot_hand = deal_poker_hand()
    player_rank, player_multiplier = evaluate_poker_hand(player_hand)
    bot_rank, bot_multiplier = evaluate_poker_hand(bot_hand)
    win = list(POKER_HANDS.keys()).index(player_rank) < list(POKER_HANDS.keys()).index(bot_rank)
    payout = amount * player_multiplier if win else 0
    new_balance = user_data['balance'] - amount + payout
    embed = discord.Embed(
        title="🃏 Poker",
        description=f"Your Hand: {' '.join(player_hand)} ({player_rank})\nBot: {' '.join(bot_hand)} ({bot_rank})",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Result", value=f"{'Win' if win else 'Lose'}! ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    update_user_data(user_id, {'balance': new_balance})
    if win:
        check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "poker")

@bot.command()
async def craps(ctx, bet_type: str, amount: int):
    """Play Craps."""
    user_id = ctx.author.id
    bet_type = bet_type.lower()
    if bet_type not in ["pass", "dont_pass"]:
        await ctx.send("❌ Use 'pass' or 'dont_pass'!")
        return
    result, payout, new_balance = play_craps(bet_type, amount, user_id)
    await ctx.send(embed=discord.Embed(
        title="🎲 Craps",
        description=result,
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    ).add_field(name="Balance", value=f"${new_balance}", inline=True))
    if payout > 0:
        check_achievements(user_id, amount, payout, False, new_balance, get_user_data(user_id)['streaks'], "craps")

@bot.command()
async def baccarat(ctx, bet_type: str, amount: int):
    """Play Baccarat."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    bet_type = bet_type.lower()
    if bet_type not in BACCARAT_BETS:
        await ctx.send("❌ Use 'player', 'banker', or 'tie'!")
        return
    if amount < MIN_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Bet ${MIN_BET}+, funds: ${user_data['balance']}")
        return
    update_user_data(user_id, {'balance': user_data['balance'] - amount})
    player_hand, banker_hand = deal_baccarat_hands()
    player_score = calculate_baccarat_score(player_hand)
    banker_score = calculate_baccarat_score(banker_hand)
    result = determine_baccarat_winner(player_score, banker_score)
    payout = int(amount * BACCARAT_BETS[bet_type]) if result == bet_type else 0
    new_balance = user_data['balance'] - amount + payout
    embed = discord.Embed(
        title="🎴 Baccarat",
        description=f"Player: {' '.join(player_hand)} ({player_score})\nBanker: {' '.join(banker_hand)} ({banker_score})",
        color=0x2ecc71 if payout > 0 else 0xe74c3c
    )
    embed.add_field(name="Bet", value=f"{bet_type.capitalize()}: ${amount}", inline=False)
    embed.add_field(name="Result", value=f"{'Win' if payout > 0 else 'Lose'}! ${payout}", inline=False)
    embed.add_field(name="Balance", value=f"${new_balance}", inline=True)
    await ctx.send(embed=embed)
    update_user_data(user_id, {'balance': new_balance})
    if payout > 0:
        check_achievements(user_id, amount, payout, False, new_balance, user_data['streaks'], "baccarat")

# --- Economy Commands ---
@bot.command()
async def shop(ctx):
    """Display shop."""
    embed = discord.Embed(title="🛒 Shop", description="Use `!buy [item_id]`", color=0x3498db)
    for item_id, item in SHOP_ITEMS.items():
        embed.add_field(name=f"{item['name']} - ${item['price']} ({item_id})", value=item['description'], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def buy(ctx, item_id: str):
    """Buy from shop."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    item = SHOP_ITEMS.get(item_id)
    if not item:
        await ctx.send("❌ Item not found!")
        return
    if user_data['balance'] < item['price']:
        await ctx.send(f"❌ Need ${item['price']}, have ${user_data['balance']}")
        return
    inventory = json.loads(user_data['inventory'])
    if item_id.startswith("profile_bg") and item_id not in inventory.get("owned_bgs", []):
        inventory["owned_bgs"] = inventory.get("owned_bgs", []) + [item_id]
    elif item_id.startswith("title") and item_id not in inventory.get("owned_titles", []):
        inventory["owned_titles"] = inventory.get("owned_titles", []) + [item_id]
    elif item_id in ["daily_boost", "xp_boost"]:
        inventory["boosts"] = inventory.get("boosts", {})
        inventory["boosts"][item_id] = (datetime.utcnow() + timedelta(days=1)).isoformat()
    elif item_id == "loan_pass":
        inventory["loan_pass"] = True
    elif item_id == "tournament_ticket":
        inventory["tournament_tickets"] = inventory.get("tournament_tickets", 0) + 1
    elif item_id == "crafting_kit":
        inventory["crafting_kit"] = True
    update_user_data(user_id, {
        'balance': user_data['balance'] - item['price'],
        'inventory': json.dumps(inventory)
    })
    await ctx.send(f"🛍️ Bought {item['name']} for ${item['price']}!")

@bot.command()
async def lottery(ctx, tickets: int = 1):
    """Buy lottery tickets."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    cost = tickets * LOTTERY_TICKET_PRICE
    if tickets < 1 or cost > user_data['balance']:
        await ctx.send(f"❌ ${LOTTERY_TICKET_PRICE}/ticket, can afford {user_data['balance'] // LOTTERY_TICKET_PRICE}")
        return
    update_user_data(user_id, {
        'balance': user_data['balance'] - cost,
        'lottery_tickets': user_data['lottery_tickets'] + tickets
    })
    update_lottery_jackpot(cost // 2)
    await ctx.send(f"🎟️ Bought {tickets} tickets for ${cost}! Jackpot: ${get_lottery_jackpot()}")

@bot.command()
async def craft(ctx, recipe_id: str):
    """Craft an item."""
    if recipe_id not in CRAFTING_RECIPES:
        await ctx.send("❌ Invalid recipe! Options: " + ", ".join(CRAFTING_RECIPES.keys()))
        return
    result = craft_item(ctx.author.id, recipe_id)
    await ctx.send(result)

# --- Tournament Commands ---
@bot.command()
async def tournament(ctx, game: str):
    """Start a tournament."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    game = game.lower()
    if game not in ["coinflip", "dice", "slots"]:
        await ctx.send("❌ Use 'coinflip', 'dice', or 'slots'!")
        return
    channel_id = ctx.channel.id
    if get_tournament_data(channel_id) and get_tournament_data(channel_id)['active']:
        await ctx.send("❌ Tournament already active!")
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
    update_user_data(user_id, {'balance': user_data['balance'] - TOURNAMENT_ENTRY_FEE})
    await ctx.send(f"🏆 {game.capitalize()} Tournament started! Join with `!join`. Starts in 60s.")
    await asyncio.sleep(60)
    await run_tournament(channel_id)

@bot.command()
async def join(ctx):
    """Join a tournament."""
    channel_id = ctx.channel.id
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    tournament = get_tournament_data(channel_id)
    if not tournament or not tournament['active']:
        await ctx.send("❌ No active tournament!")
        return
    if user_data['balance'] < TOURNAMENT_ENTRY_FEE:
        await ctx.send(f"❌ Need ${TOURNAMENT_ENTRY_FEE}, have ${user_data['balance']}")
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
        await ctx.send(f"{ctx.author.mention} joined {tournament['game_type']} tournament! Prize: ${tournament['prize_pool']}")

async def run_tournament(channel_id):
    """Run tournament rounds."""
    tournament = get_tournament_data(channel_id)
    channel = bot.get_channel(channel_id)
    players = json.loads(tournament['players'])
    scores = json.loads(tournament['scores'])
    if len(players) < 2:
        await channel.send("❌ Not enough players!")
        update_tournament_data(channel_id, {'active': 0})
        return
    for round_num in range(1, tournament['rounds'] + 1):
        await channel.send(f"Round {round_num} begins!")
        for player_id in players:
            if tournament['game_type'] == "coinflip":
                win = random.choice([True, False])
                scores[player_id] += 100 if win else -100
            elif tournament['game_type'] == "dice":
                total = sum(random.randint(1, 6) for _ in range(2))
                scores[player_id] += 100 if total > 7 else -100
            else:  # slots
                slots = spin_slots(1)
                winnings, _, _ = check_win(slots)
                scores[player_id] += winnings
        update_tournament_data(channel_id, {'scores': json.dumps(scores), 'current_round': round_num})
        await asyncio.sleep(5)
    winner_id = max(scores, key=scores.get)
    update_user_data(winner_id, {
        'balance': get_user_data(winner_id)['balance'] + tournament['prize_pool'],
        'achievements': json.dumps(json.loads(get_user_data(winner_id)['achievements']) + ["tournament_champ"])
    })
    await channel.send(f"🏆 <@{winner_id}> wins ${tournament['prize_pool']} with {scores[winner_id]} points!")
    update_tournament_data(channel_id, {'active': 0})

# --- Announcement Commands ---
@bot.command()
@commands.has_permissions(manage_guild=True)
async def setdailyannouncement(ctx, channel: discord.TextChannel, *, message: str):
    """Set daily announcement channel."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO announcement_settings (guild_id, channel_id, message) VALUES (?, ?, ?)',
              (ctx.guild.id, channel.id, message))
    conn.commit()
    conn.close()
    await ctx.send(f"📢 Daily announcement set for {channel.mention}: '{message}'")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def unsetdailyannouncement(ctx):
    """Unset daily announcement."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('DELETE FROM announcement_settings WHERE guild_id = ?', (ctx.guild.id,))
    conn.commit()
    conn.close()
    await ctx.send("📢 Daily announcement unset.")

# --- Help Command ---
@bot.command(name="paradox")
async def paradox_help(ctx):
    """Display help menu."""
    embed = discord.Embed(title="🎰 Paradox Casino Help", description="All commands:", color=0x3498db)
    embed.add_field(name="Core", value="`!bet [amt] [lines]`, `!daily`, `!profile [user]`, `!jackpot`", inline=False)
    embed.add_field(name="Games", value="`!tictactoe [@user]`, `!move [row] [col]`, `!hangman`, `!guess [letter]`, `!guessnumber`, `!number [guess]`, `!trivia`, `!rps [amt]`, `!blackjack [amt]`, `!wheel [amt]`, `!coinflip [amt] [choice]`, `!dice [amt] [pred]`, `!roulette [type] [val] [amt]`, `!poker [amt]`, `!craps [type] [amt]`, `!baccarat [type] [amt]`", inline=False)
    embed.add_field(name="Economy", value="`!shop`, `!buy [item]`, `!lottery [tickets]`, `!craft [recipe]`", inline=False)
    embed.add_field(name="Multiplayer", value="`!tournament [game]`, `!join`", inline=False)
    embed.add_field(name="Admin", value="`!setdailyannouncement [channel] [msg]`, `!unsetdailyannouncement`", inline=False)
    embed.set_footer(text="Prefix: !")
    await ctx.send(embed=embed)

# --- Error Handling ---
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Wait {error.retry_after:.1f}s")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing argument! See `!paradox`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No permission!")
    else:
        logger.error(f"Error in {ctx.command}: {error}")
        await ctx.send("❌ Error occurred!")

# --- Startup Logic ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("No DISCORD_BOT_TOKEN!")
        exit(1)
    bot.run(token)

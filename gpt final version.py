# -------------------- Segment 1: Imports, Global Constants, Logger & Shop Items --------------------
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
# Removed unused: import math

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('ParadoxCasinoBot')

# Global Constants
STARTING_BALANCE = 7000
DAILY_REWARD = 500
JACKPOT_SYMBOL = '7️⃣'
JACKPOT_MULTIPLIER = 5

# Global variable for events
HIGHROLLER_EVENT_ACTIVE = False

# -------------------- Economy Constants & Shop Items --------------------
SHOP_ITEMS = {
    "profile_bg1": {"name": "Cosmic Sky", "description": "Starry backdrop", "price": 1000},
    "profile_bg2": {"name": "Golden Vault", "description": "Gold shine", "price": 1000},
    "title_gambler": {"name": "Gambler", "description": "For risk-takers", "price": 500},
    "title_highroller": {"name": "High Roller", "description": "Big spender", "price": 750},
    "daily_boost": {"name": "Daily Boost", "description": "2x daily reward (24h)", "price": 200},
    "xp_boost": {"name": "XP Boost", "description": "2x XP gain (24h)", "price": 300},
    "loan_pass": {"name": "Loan Pass", "description": "Allows taking a loan", "price": 100},
    "tournament_ticket": {"name": "Tournament Ticket", "description": "Entry to tournaments", "price": 500},
    "crafting_kit": {"name": "Crafting Kit", "description": "Unlock crafting recipes", "price": 800}
}

# (Optional: Define additional constants like CRAFTING_RECIPES here if needed)
# -------------------- Segment 2: Database Integration --------------------
def init_db():
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT {},
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        achievements TEXT DEFAULT '[]',
        inventory TEXT DEFAULT '{}',
        missions TEXT DEFAULT '{}'
    )
    '''.format(STARTING_BALANCE))
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS lottery (
        jackpot INTEGER DEFAULT 1000
    )
    ''')
    c.execute('INSERT OR IGNORE INTO lottery (rowid, jackpot) VALUES (1, 1000)')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS tournaments (
        channel_id INTEGER PRIMARY KEY,
        game_type TEXT,
        players TEXT DEFAULT '{}',
        scores TEXT DEFAULT '{}',
        rounds INTEGER DEFAULT 3,
        current_round INTEGER DEFAULT 0,
        active INTEGER DEFAULT 0,
        prize_pool INTEGER DEFAULT 0
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        item_id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        price INTEGER
    )
    ''')
    # Insert shop items from SHOP_ITEMS
    for item_id, item in SHOP_ITEMS.items():
        c.execute('INSERT OR IGNORE INTO items (item_id, name, description, price) VALUES (?, ?, ?, ?)',
                  (item_id, item['name'], item['description'], item['price']))
    
    # Create Trade Offers Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS trade_offers (
        offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        offered_items TEXT,
        requested_items TEXT,
        status TEXT DEFAULT 'pending'
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

init_db()

# -------------------- Database Helper Functions --------------------
def get_user_data(user_id):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (id, balance) VALUES (?, ?)', (user_id, STARTING_BALANCE))
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    data = c.fetchone()
    conn.commit()
    conn.close()
    keys = ['id', 'balance', 'xp', 'level', 'achievements', 'inventory', 'missions']
    return dict(zip(keys, data))

def update_user_data(user_id, updates):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    query = 'UPDATE users SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE id = ?'
    values = list(updates.values()) + [user_id]
    c.execute(query, values)
    conn.commit()
    conn.close()

def get_lottery_jackpot():
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('SELECT jackpot FROM lottery WHERE rowid = 1')
    jackpot = c.fetchone()[0]
    conn.close()
    return jackpot

def update_lottery_jackpot(amount):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('UPDATE lottery SET jackpot = jackpot + ? WHERE rowid = 1', (amount,))
    conn.commit()
    conn.close()

def get_tournament_data(channel_id):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tournaments WHERE channel_id = ?', (channel_id,))
    data = c.fetchone()
    conn.close()
    if data:
        keys = ['channel_id', 'game_type', 'players', 'scores', 'rounds', 'current_round', 'active', 'prize_pool']
        return dict(zip(keys, data))
    return None

def update_tournament_data(channel_id, updates):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO tournaments (channel_id) VALUES (?)', (channel_id,))
    query = 'UPDATE tournaments SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE channel_id = ?'
    values = list(updates.values()) + [channel_id]
    c.execute(query, values)
    conn.commit()
    conn.close()

def check_achievements(user_id, bet_amount, win_amount, jackpot_win, balance, streaks):
    # Stub: For now, return an empty list.
    # You can implement logic to check and award achievements.
    return []



# ==================== End of Segment 2 ====================
# ==================== Segment 3 (Lines 201-300) ====================
# -------------------- Economy, Crafting, and Trade Systems --------------------
SHOP_ITEMS = {
    "profile_bg1": {"name": "Cosmic Sky", "description": "Starry backdrop", "price": 1000},
    "profile_bg2": {"name": "Golden Vault", "description": "Gold shine", "price": 1000},
    "title_gambler": {"name": "Gambler", "description": "For risk-takers", "price": 500},
    "title_highroller": {"name": "High Roller", "description": "Big spender", "price": 750},
    "daily_boost": {"name": "Daily Boost", "description": "2x daily reward (24h)", "price": 200},
    "xp_boost": {"name": "XP Boost", "description": "2x XP gain (24h)", "price": 300},
    "loan_pass": {"name": "Loan Pass", "description": "Allows taking a loan", "price": 100},
    "tournament_ticket": {"name": "Tournament Ticket", "description": "Entry to tournaments", "price": 500},
    "crafting_kit": {"name": "Crafting Kit", "description": "Unlock crafting recipes", "price": 800}
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

# -------------------- Expanded Crafting System --------------------
CRAFTING_RECIPES.update({
    "fortune_charm": {
        "ingredients": {"gold_coin": 10, "four_leaf_clover": 2},
        "description": "Increases slot machine winnings by 10% for 1 hour",
        "duration": "1h"
    },
    "diamond_ticket": {
        "ingredients": {"gold_bar": 5, "diamond": 3},
        "description": "Grants free entry to a high-roller tournament",
        "uses": 1
    }
})


ITEM_DROP_TABLE = {
    "gold_coin": {"chance": 0.5, "source": "slots"},
    "four_leaf_clover": {"chance": 0.1, "source": "roulette"},
    "gold_bar": {"chance": 0.05, "source": "poker"},
    "diamond": {"chance": 0.02, "source": "blackjack"}
}

def create_trade_offer(sender_id, receiver_id, offered_items, requested_items):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('''INSERT INTO trade_offers (sender_id, receiver_id, offered_items, requested_items)
                 VALUES (?, ?, ?, ?)''', (sender_id, receiver_id, json.dumps(offered_items), json.dumps(requested_items)))
    offer_id = c.lastrowid
    conn.commit()
    conn.close()
    return offer_id

def get_trade_offer(offer_id):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM trade_offers WHERE offer_id = ?', (offer_id,))
    data = c.fetchone()
    conn.close()
    if data:
        keys = ['offer_id', 'sender_id', 'receiver_id', 'offered_items', 'requested_items', 'status']
        return dict(zip(keys, data))
    return None

def update_trade_offer(offer_id, updates):
    conn = sqlite3.connect('unified_casino.db')
    c = conn.cursor()
    query = 'UPDATE trade_offers SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE offer_id = ?'
    values = list(updates.values()) + [offer_id]
    c.execute(query, values)
    conn.commit()
    conn.close()
# ==================== End of Segment 3 ====================
# ==================== Segment 4 (Lines 301-400) ====================
# -------------------- Achievements & Missions Systems --------------------
ACHIEVEMENTS = {
    "first_win": {"name": "Paradox Novice", "description": "Win your first slot game", "emoji": "🏆"},
    "big_winner": {"name": "Paradox Master", "description": "Win over 1000 coins", "emoji": "💎"},
    "jackpot": {"name": "Paradox Breaker", "description": "Hit the jackpot", "emoji": "🎯"},
    "broke": {"name": "Rock Bottom", "description": "Lose all your money", "emoji": "📉"},
    "comeback": {"name": "Phoenix Rising", "description": "Win with less than 100 coins", "emoji": "🔄"},
    "high_roller": {"name": "Paradox Whale", "description": "Bet the maximum amount", "emoji": "💵"},
    "daily_streak": {"name": "Time Traveler", "description": "Claim rewards for 7 days", "emoji": "⏰"},
    "legendary": {"name": "Legendary Gambler", "description": "Win 5 times in a row", "emoji": "👑"}
}

MISSIONS = {
    "daily": [
        {"id": "play_slots", "name": "Slot Enthusiast", "description": "Play 5 slot games", "requirements": {"slot_plays": 5}, "rewards": {"coins": 100}},
        {"id": "win_games", "name": "Winner", "description": "Win 3 games", "requirements": {"wins": 3}, "rewards": {"coins": 150}}
    ],
    "weekly": [
        {"id": "slot_master", "name": "Slot Master", "description": "Win 10 slot games", "requirements": {"slot_wins": 10}, "rewards": {"coins": 500}}
    ],
    "one-time": [
        {"id": "level_5", "name": "Level Up", "description": "Reach level 5", "requirements": {"level": 5}, "rewards": {"coins": 1000}},
        {"id": "jackpot", "name": "Jackpot Hunter", "description": "Win the jackpot", "requirements": {"jackpot_wins": 1}, "rewards": {"coins": 2000}}
    ]
}

def get_user_missions(user_id):
    data = get_user_data(user_id)
    return json.loads(data.get('missions', '{}'))

def update_user_missions(user_id, missions):
    update_user_data(user_id, {'missions': json.dumps(missions)})

def initialize_missions(user_id):
    missions = {
        "daily": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["daily"]},
        "weekly": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["weekly"]},
        "one-time": {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS["one-time"]}
    }
    update_user_missions(user_id, missions)

def reset_missions(user_id, mission_type):
    missions = get_user_missions(user_id)
    if mission_type in missions:
        missions[mission_type] = {m["id"]: {"progress": 0, "completed": False} for m in MISSIONS[mission_type]}
        update_user_missions(user_id, missions)
# ==================== End of Segment 4 ====================
# ==================== Segment 5 (Lines 401-500) ====================
# -------------------- Casino Game: Slot Machine --------------------
def spin_slots(lines):
    """Generate a slot machine spin result for the specified number of lines."""
    return [[random.choice(SLOTS) for _ in range(3)] for _ in range(lines)]

def check_win(slots):
    """Check slot spin for wins and calculate total winnings."""
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
    """Format slot display for animation with specified columns revealed."""
    display_lines = []
    for line in slots:
        line_display = [line[i] if i in revealed_columns else '🎰' for i in range(3)]
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
# ==================== End of Segment 5 ====================
# ==================== Segment 6 (Lines 501-600) ====================
# -------------------- Casino Game: Roulette --------------------
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

def get_roulette_color(number):
    if number in RED_NUMBERS:
        return "red"
    elif number in BLACK_NUMBERS:
        return "black"
    return "green"

def validate_roulette_bet(bet_type, bet_value):
    if bet_type not in ROULETTE_BETS:
        return False
    return ROULETTE_BETS[bet_type]["validator"](bet_value)

def calculate_roulette_payout(bet_type, bet_value, spun_number):
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
            1: [1,4,7,10,13,16,19,22,25,28,31,34],
            2: [2,5,8,11,14,17,20,23,26,29,32,35],
            3: [3,6,9,12,15,18,21,24,27,30,33,36]
        }
        if spun_number == 0:
            return 0
        return ROULETTE_BETS[bet_type]["payout"] if spun_number in columns[int(bet_value)] else 0
    return 0
# ==================== End of Segment 6 ====================
# ==================== Segment 7 (Lines 601-700) ====================
# -------------------- Casino Game: Poker --------------------
POKER_CARDS = [f"{rank}{suit}" for suit in "♠♥♦♣" for rank in "23456789TJQKA"]
POKER_HANDS = {
    "Royal Flush": 250,
    "Straight Flush": 50,
    "Four of a Kind": 25,
    "Full House": 9,
    "Flush": 6,
    "Straight": 4,
    "Three of a Kind": 3,
    "Two Pair": 2,
    "One Pair": 1,
    "High Card": 0
}

def deal_poker_hand():
    deck = POKER_CARDS.copy()
    random.shuffle(deck)
    return deck[:5]

def evaluate_poker_hand(hand):
    # Placeholder for hand evaluation logic (detailed evaluation code goes here)
    # For now, we return a dummy hand type and multiplier.
    return "High Card", 0

# -------------------- Casino Game: Blackjack --------------------
CARD_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10,
    'J': 10, 'Q': 10, 'K': 10, 'A': 11
}
BLACKJACK_CARDS = [f"{rank}{suit}" for suit in "♠♥♦♣" for rank in "23456789TJQKA"]

class BlackjackGame:
    def __init__(self):
        self.deck = BLACKJACK_CARDS.copy() * 4
        random.shuffle(self.deck)
        self.player_hand = []
        self.dealer_hand = []
    
    def deal_card(self, hand):
        card = self.deck.pop()
        hand.append(card)
        return card
    
    def start_game(self):
        self.player_hand = []
        self.dealer_hand = []
        self.deal_card(self.player_hand)
        self.deal_card(self.dealer_hand)
        self.deal_card(self.player_hand)
        self.deal_card(self.dealer_hand)
    
    def get_hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            rank = card[:-1]
            value += CARD_VALUES[rank]
            if rank == 'A':
                aces += 1
        # Adjust for aces if value > 21
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value
# ==================== End of Segment 7 ====================
# ==================== Segment 8 (Lines 701-800) ====================
# -------------------- Mini-Game: Tic-Tac-Toe --------------------
class TicTacToe:
    def __init__(self):
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_active = False
        self.players = {}

    def display_board(self):
        board_str = "```\n  0 1 2\n"
        for idx, row in enumerate(self.board):
            board_str += f"{idx} " + "|".join(row) + "\n"
            if idx < 2:
                board_str += "  -+-+-\n"
        board_str += "```"
        return board_str

    def make_move(self, row, col, player):
        if 0 <= row < 3 and 0 <= col < 3 and self.board[row][col] == " ":
            self.board[row][col] = player
            return True
        return False

    def check_win(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != " ":
                return row[0]
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != " ":
                return self.board[0][col]
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != " ":
            return self.board[0][2]
        return None

    def is_full(self):
        return all(cell != " " for row in self.board for cell in row)
# ==================== End of Segment 8 ====================
# ==================== Segment 9 (Lines 801-900) ====================
# -------------------- Mini-Game: Hangman --------------------
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
            return "already"
        self.guessed.add(letter)
        if letter not in self.word:
            self.wrong_guesses += 1
            return "wrong"
        if all(c in self.guessed for c in self.word):
            return "correct"
        return "partial"
# ==================== End of Segment 9 ====================
# ==================== Segment 10 (Lines 901-1000) ====================
# -------------------- Mini-Game: Number Guessing --------------------
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
        elif number < self.number:
            return "higher"
        else:
            return "lower"

# -------------------- Mini-Game: Trivia --------------------
TRIVIA_QUESTIONS = [
    {"question": "What is the highest possible score in a single Blackjack hand?", "options": ["20", "21", "22", "23"], "correct": 1},
    {"question": "Which symbol gives the jackpot in Paradox Slots?", "options": ["🍒", "💎", "7️⃣", "🔔"], "correct": 2},
    {"question": "What game was added first to Paradox Casino?", "options": ["Tic-Tac-Toe", "Slots", "Wheel", "Blackjack"], "correct": 1}
]
# -------------------- Trivia Expansion --------------------
TRIVIA_QUESTIONS.extend([
    {"question": "What is the probability of drawing an Ace in a shuffled deck?", "options": ["1/13", "1/10", "1/8", "1/5"], "correct": 0},
    {"question": "Which of the following is NOT a valid hand in Poker?", "options": ["Straight Flush", "Full House", "Double Flush", "Four of a Kind"], "correct": 2},
    {"question": "What is the maximum number of players in a standard Blackjack table?", "options": ["5", "6", "7", "8"], "correct": 2}
])

def get_trivia_question():
    return random.choice(TRIVIA_QUESTIONS)


import aiohttp  # For making async web requests

# -------------------- Dynamic Web Trivia --------------------
import aiohttp  # For making async web requests
from web import search  # Assuming web search functionality is enabled

# -------------------- Dynamic Web Trivia --------------------
TRIVIA_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"

bot.trivia_answers = {}  # Dictionary to store correct answers per user

@bot.command(name='trivia')
async def trivia_command(ctx):
    """Fetch a random trivia question from the web (Trivia API)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(TRIVIA_API_URL) as response:
            data = await response.json()
            if not data["results"]:
                await ctx.send("⚠️ Failed to fetch a trivia question. Try again!")
                return
            
            question_data = data["results"][0]
            question = question_data["question"]
            options = question_data["incorrect_answers"] + [question_data["correct_answer"]]
            random.shuffle(options)

            options_text = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
            correct_answer = options.index(question_data["correct_answer"]) + 1

            # Save correct answer for validation
            bot.trivia_answers[ctx.author.id] = correct_answer

            await ctx.send(f"🧠 **Trivia Time!**\n{question}\n{options_text}\nReply with the number of your answer.")

@bot.command(name='triviaweb')
async def trivia_web_command(ctx):
    """Fetch a trivia question by searching the web."""
    results = search("random trivia question site:trivia.fyi OR site:usefultrivia.com")
    
    if not results:
        await ctx.send("⚠️ Could not find a trivia question online. Try again!")
        return
    
    trivia_question = results[0]  # Extract the first relevant question
    await ctx.send(f"🧠 **Web Trivia:** {trivia_question}")

# -------------------- Mini-Game: Tic-Tac-Toe --------------------
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

game = TicTacToe()

@bot.command(name="tictactoe")
async def tictactoe(ctx, opponent: discord.Member = None):
    """Start a Tic-Tac-Toe game."""
    if game.game_active:
        await ctx.send("❌ A game is already in progress!")
        return
    game.game_active = True
    game.players = {ctx.author.id: "X"}
    if opponent:
        game.players[opponent.id] = "O"
        await ctx.send(f"🎮 {ctx.author.mention} (X) vs {opponent.mention} (O)! Use `!move row col`.")
    else:
        game.players[bot.user.id] = "O"
        await ctx.send(f"🎮 {ctx.author.mention} (X) vs Bot (O). Use `!move row col`.")
    await ctx.send(game.display_board())

@bot.command(name="move")
async def move(ctx, row: int, col: int):
    """Make a Tic-Tac-Toe move."""
    if not game.game_active:
        await ctx.send("❌ No game in progress! Start with `!tictactoe`.")
        return
    if ctx.author.id not in game.players:
        await ctx.send("❌ You are not part of this game!")
        return
    player = game.players[ctx.author.id]
    if game.make_move(row, col, player):
        await ctx.send(game.display_board())
    else:
        await ctx.send("❌ Invalid move! Try again.")





# -------------------- Mini-Game: Rock-Paper-Scissors --------------------
RPS_CHOICES = ["rock", "paper", "scissors"]
def rps_outcome(player_choice, bot_choice):
    if player_choice == bot_choice:
        return "tie"
    if (player_choice == "rock" and bot_choice == "scissors") or \
       (player_choice == "paper" and bot_choice == "rock") or \
       (player_choice == "scissors" and bot_choice == "paper"):
        return "win"
    return "lose"
# ==================== End of Segment 10 ====================
# ==================== Segment 11 (Lines 1001-1100) ====================
# -------------------- Casino Game: Craps --------------------
CRAPS_PASS_LINE = {"win": [7, 11], "lose": [2, 3, 12], "point": [4, 5, 6, 8, 9, 10]}
CRAPS_DONT_PASS = {"win": [2, 3], "lose": [7, 11], "push": [12], "point": [4, 5, 6, 8, 9, 10]}

def roll_dice():
    return random.randint(1, 6), random.randint(1, 6)

def play_craps_pass_line():
    first_roll = sum(roll_dice())
    if first_roll in CRAPS_PASS_LINE["win"]:
        return "win", first_roll
    elif first_roll in CRAPS_PASS_LINE["lose"]:
        return "lose", first_roll
    else:
        point = first_roll
        while True:
            roll = sum(roll_dice())
            if roll == point:
                return "win", roll
            elif roll == 7:
                return "lose", roll

def play_craps_dont_pass():
    first_roll = sum(roll_dice())
    if first_roll in CRAPS_DONT_PASS["win"]:
        return "win", first_roll
    elif first_roll in CRAPS_DONT_PASS["lose"]:
        return "lose", first_roll
    elif first_roll in CRAPS_DONT_PASS["push"]:
        return "push", first_roll
    else:
        point = first_roll
        while True:
            roll = sum(roll_dice())
            if roll == 7:
                return "win", roll
            elif roll == point:
                return "lose", roll

# Placeholder function for handling craps bets
def handle_craps_bet(bet_type, amount, pass_line=True):
    if pass_line:
        outcome, roll = play_craps_pass_line()
    else:
        outcome, roll = play_craps_dont_pass()
    multiplier = 1
    if outcome == "win":
        winnings = amount * multiplier
    elif outcome == "lose":
        winnings = -amount
    else:
        winnings = 0
    return outcome, roll, winnings
# ==================== End of Segment 11 ====================
# ==================== Segment 12 (Lines 1101-1200) ====================
# -------------------- Casino Game: Baccarat --------------------
BACCARAT_BETS = {"player": 1, "banker": 0.95, "tie": 8}

def deal_baccarat_hand():
    # Use a simplified deck for Baccarat
    deck = BLACKJACK_CARDS.copy() * 4
    random.shuffle(deck)
    return [deck.pop(), deck.pop()]

def baccarat_total(hand):
    # Calculate Baccarat hand total (only last digit matters)
    total = 0
    for card in hand:
        rank = card[:-1]
        value = int(rank) if rank.isdigit() else (10 if rank in ['J','Q','K'] else 1)
        total += value
    return total % 10

def play_baccarat(bet_on):
    player_hand = deal_baccarat_hand()
    banker_hand = deal_baccarat_hand()
    player_total = baccarat_total(player_hand)
    banker_total = baccarat_total(banker_hand)
    # Simple drawing rule: if total < 6, draw one more card (detailed rules omitted)
    if player_total < 6:
        player_hand.append(random.choice(BLACKJACK_CARDS))
        player_total = baccarat_total(player_hand)
    if banker_total < 6:
        banker_hand.append(random.choice(BLACKJACK_CARDS))
        banker_total = baccarat_total(banker_hand)
    if player_total > banker_total:
        winner = "player"
    elif banker_total > player_total:
        winner = "banker"
    else:
        winner = "tie"
    payout = BACCARAT_BETS.get(bet_on, 0) if winner == bet_on else 0
    return winner, player_total, banker_total, payout
# ==================== End of Segment 12 ====================
# ==================== Segment 13 (Lines 1201-1300) ====================
# -------------------- XP and Leveling System --------------------
def add_xp(user_id, amount):
    """Add XP to a user and handle level-ups."""
    user_data = get_user_data(user_id)
    xp = user_data['xp'] + amount
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

def add_balance(user_id, amount):
    user_data = get_user_data(user_id)
    new_balance = user_data['balance'] + amount
    update_user_data(user_id, {'balance': new_balance})
    return new_balance

def deduct_balance(user_id, amount):
    user_data = get_user_data(user_id)
    new_balance = max(0, user_data['balance'] - amount)
    update_user_data(user_id, {'balance': new_balance})
    return new_balance
# ==================== End of Segment 13 ====================
# ==================== Segment 14 (Lines 1301-1400) ====================
# -------------------- Bot Commands: Slots --------------------
@bot.command(name='slots')
async def slots_command(ctx, lines: int = 1, bet: int = 10):
    user_id = ctx.author.id
    if lines < 1 or lines > MAX_LINES:
        await ctx.send("Invalid number of lines.")
        return
    if bet < MIN_BET or bet > MAX_BET:
        await ctx.send("Invalid bet amount.")
        return
    # Deduct bet amount from user balance
    user_data = get_user_data(user_id)
    if user_data['balance'] < bet:
        await ctx.send("Insufficient balance.")
        return
    deduct_balance(user_id, bet)
    slots = spin_slots(lines)
    winnings, jackpot_win, winning_lines = check_win(slots)
    result_display = format_slot_display(slots, winning_lines)
    add_balance(user_id, winnings)
    response = f"**Slots Result:**\n{result_display}\nYou won: ${winnings}"
    if jackpot_win:
        response += "\n**Jackpot Hit!**"
    await ctx.send(response)
# ==================== End of Segment 14 ====================
# ==================== Segment 15 (Lines 1401-1500) ====================
# -------------------- Bot Commands: Roulette --------------------
@bot.command(name='roulette')
async def roulette_command(ctx, bet_type: str, bet_value: str, bet_amount: int):
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if user_data['balance'] < bet_amount:
        await ctx.send("Insufficient balance for roulette bet.")
        return
    if not validate_roulette_bet(bet_type, bet_value):
        await ctx.send("Invalid bet type or value for roulette.")
        return
    deduct_balance(user_id, bet_amount)
    spun_number = random.randint(0, 36)
    payout_multiplier = calculate_roulette_payout(bet_type, bet_value, spun_number)
    winnings = bet_amount * payout_multiplier
    add_balance(user_id, winnings)
    outcome = "won" if winnings > 0 else "lost"
    await ctx.send(f"Roulette spun: {spun_number}\nYou {outcome} ${winnings}!")

# -------------------- Bot Commands: Tournaments --------------------
@bot.command(name='tournament')
async def tournament_command(ctx, game_type: str, buy_in: int):
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    
    if user_data['balance'] < buy_in:
        await ctx.send("Insufficient balance to enter the tournament.")
        return

    deduct_balance(user_id, buy_in)

    tournament_data = get_tournament_data(ctx.channel.id)
    if tournament_data and tournament_data['active']:
        await ctx.send("A tournament is already running in this channel!")
        return

    new_tournament = {
        'channel_id': ctx.channel.id,
        'game_type': game_type,
        'players': json.dumps({user_id: 0}),
        'scores': json.dumps({}),
        'rounds': 3,
        'current_round': 0,
        'active': 1,
        'prize_pool': buy_in
    }
    update_tournament_data(ctx.channel.id, new_tournament)
    
    await ctx.send(f"A **{game_type}** tournament has started with a buy-in of ${buy_in}. Type `!join` to participate!")

@bot.command(name='join')
async def join_tournament(ctx):
    user_id = ctx.author.id
    tournament_data = get_tournament_data(ctx.channel.id)

    if not tournament_data or not tournament_data['active']:
        await ctx.send("There is no active tournament in this channel.")
        return

    players = json.loads(tournament_data['players'])
    if user_id in players:
        await ctx.send("You're already in this tournament!")
        return

    players[user_id] = 0
    tournament_data['players'] = json.dumps(players)
    update_tournament_data(ctx.channel.id, tournament_data)

    await ctx.send(f"{ctx.author.mention} has joined the tournament!")
# ==================== End of Segment 15 ====================
# ==================== Segment 16 (Lines 1501-1600) ====================
# -------------------- Bot Commands: Poker --------------------

# -------------------- Bot Commands: Coin Flip --------------------
@bot.command(name='coinflip')
async def coinflip_command(ctx, bet: int, choice: str):
    """Flip a coin with a bet."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    
    if choice.lower() not in ["heads", "tails"]:
        await ctx.send("❌ Choose either 'heads' or 'tails'!")
        return

    if user_data['balance'] < bet:
        await ctx.send("❌ Insufficient balance!")
        return

    deduct_balance(user_id, bet)
    result = random.choice(["heads", "tails"])
    if result == choice.lower():
        winnings = bet * 2
        add_balance(user_id, winnings)
        await ctx.send(f"🪙 The coin landed on **{result}**! You win **${winnings}**!")
    else:
        await ctx.send(f"🪙 The coin landed on **{result}**! You lose **${bet}**.")


# -------------------- Bot Commands: Wheel of Fortune --------------------
@bot.command(name='wheel')
async def wheel_command(ctx, bet: int):
    """Spin the Wheel of Fortune for rewards."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    
    if user_data['balance'] < bet:
        await ctx.send("❌ Insufficient balance!")
        return

    deduct_balance(user_id, bet)
    prize = random.choice(WHEEL_PRIZES)
    winnings = bet * 2 if prize == "Jackpot" else bet * (prize / 100)
    add_balance(user_id, winnings)
    
    await ctx.send(f"🎡 You spun the wheel and won **${winnings}**!")


# -------------------- Bot Commands: Dice Roll --------------------
@bot.command(name='dice')
async def dice_command(ctx, bet: int, prediction: int):
    """Roll a dice with a bet."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if prediction not in range(1, 7):
        await ctx.send("❌ Choose a number between 1 and 6!")
        return

    if user_data['balance'] < bet:
        await ctx.send("❌ Insufficient balance!")
        return

    deduct_balance(user_id, bet)
    roll = random.randint(1, 6)
    if roll == prediction:
        winnings = bet * 5
        add_balance(user_id, winnings)
        await ctx.send(f"🎲 You rolled a **{roll}**! You win **${winnings}**!")
    else:
        await ctx.send(f"🎲 You rolled a **{roll}**! You lose **${bet}**.")



@bot.command(name='poker')
async def poker_command(ctx, bet_amount: int):
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if user_data['balance'] < bet_amount:
        await ctx.send("Insufficient balance for poker.")
        return
    deduct_balance(user_id, bet_amount)
    hand = deal_poker_hand()
    hand_type, multiplier = evaluate_poker_hand(hand)
    winnings = bet_amount * multiplier
    add_balance(user_id, winnings)
    hand_display = " ".join(hand)
    await ctx.send(f"Your hand: {hand_display}\nHand Type: {hand_type}\nYou won: ${winnings}!")
# ==================== End of Segment 16 ====================
# ==================== Segment 17 (Lines 1601-1700) ====================
# -------------------- Bot Commands: Blackjack --------------------
@bot.command(name='blackjack')
async def blackjack_command(ctx, bet_amount: int):
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if user_data['balance'] < bet_amount:
        await ctx.send("Insufficient balance for blackjack.")
        return
    deduct_balance(user_id, bet_amount)
    game = BlackjackGame()
    game.start_game()
    player_value = game.get_hand_value(game.player_hand)
    dealer_value = game.get_hand_value(game.dealer_hand)
    response = f"Your hand: {', '.join(game.player_hand)} (Value: {player_value})\n"
    response += f"Dealer's hand: {', '.join(game.dealer_hand)} (Value: {dealer_value})\n"
    if player_value > 21:
        outcome = "lose"
    elif dealer_value > 21 or player_value > dealer_value:
        outcome = "win"
    elif player_value == dealer_value:
        outcome = "push"
    else:
        outcome = "lose"
    if outcome == "win":
        winnings = bet_amount
        add_balance(user_id, winnings * 2)
        response += f"You win ${winnings}!"
    elif outcome == "push":
        add_balance(user_id, bet_amount)
        response += "It's a push! Your bet is returned."
    else:
        response += "You lose your bet."
    await ctx.send(response)

# -------------------- Expanded Achievements --------------------
ACHIEVEMENTS.update({
    "roulette_master": {"name": "Roulette Master", "description": "Win a number bet", "emoji": "🎡"},
    "poker_pro": {"name": "Poker Pro", "description": "Win a Poker game", "emoji": "🃏"},
    "craps_winner": {"name": "Craps Winner", "description": "Win a Craps game", "emoji": "🎲"},
    "baccarat_champ": {"name": "Baccarat Champ", "description": "Win a Baccarat game", "emoji": "🎴"},
    "shopaholic": {"name": "Shopaholic", "description": "Buy 10 items", "emoji": "🛍️"},
    "vip_member": {"name": "VIP Member", "description": "Reach Level 5", "emoji": "👑"},
    "debt_free": {"name": "Debt Free", "description": "Pay off a loan", "emoji": "💸"},
    "craftsman": {"name": "Craftsman", "description": "Craft your first item", "emoji": "🔨"},
    "trader": {"name": "Trader", "description": "Complete a trade", "emoji": "🤝"}
})


# -------------------- Expanded Missions --------------------
MISSIONS["weekly"].extend([
    {"id": "slot_master", "name": "Slot Master", "description": "Win 10 slots", "requirements": {"slot_wins": 10}, "rewards": {"coins": 500}},
    {"id": "roulette_wins", "name": "Roulette Expert", "description": "Win 5 roulette bets", "requirements": {"roulette_wins": 5}, "rewards": {"coins": 750}}
])

MISSIONS["one-time"].extend([
    {"id": "level_10", "name": "True Gambler", "description": "Reach level 10", "requirements": {"level": 10}, "rewards": {"coins": 2000}},
    {"id": "jackpot_winner", "name": "Jackpot Hunter", "description": "Win the jackpot", "requirements": {"jackpot_wins": 1}, "rewards": {"coins": 5000}}
])

# -------------------- XP and Leveling System --------------------
def add_xp(user_id, amount):
    """Add XP and handle level-ups with bonuses."""
    user_data = get_user_data(user_id)
    xp = user_data['xp'] + amount
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

# -------------------- Expanded Achievements System --------------------
ACHIEVEMENTS.update({
    "tournament_champ": {"name": "Tournament Champ", "description": "Win a tournament", "emoji": "🏅"},
    "crafting_expert": {"name": "Crafting Expert", "description": "Craft 5 unique items", "emoji": "🔨"},
    "coinflip_streak": {"name": "Coinflip Streak", "description": "Win 3 consecutive coin flips", "emoji": "🪙"},
    "dice_master": {"name": "Dice Master", "description": "Win 5 dice games", "emoji": "🎲"},
    "highroller_vip": {"name": "High Roller", "description": "Win a bet of $5000 or more", "emoji": "💰"}
})



# ==================== End of Segment 17 ====================
# ==================== Segment 18 (Lines 1701-1800) ====================
# -------------------- Bot Commands: Mini-Games --------------------
@bot.command(name='tictactoe')
async def tictactoe_command(ctx):
    game = TicTacToe()
    game.game_active = True
    await ctx.send("Starting Tic-Tac-Toe!\n" + game.display_board())

@bot.command(name='hangman')
async def hangman_command(ctx):
    game = HangmanGame()
    game.active = True
    await ctx.send(f"Starting Hangman!\n{game.display_word()}\n{HANGMAN_STAGES[0]}")

@bot.command(name='numberguess')
async def numberguess_command(ctx):
    game = NumberGuessGame()
    game.active = True
    await ctx.send("I have chosen a number between 1 and 100. Start guessing!")

@bot.command(name='trivia')
async def trivia_command(ctx):
    question = get_trivia_question()
    options = "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(question['options']))
    await ctx.send(f"Trivia Time!\n{question['question']}\n{options}\nReply with the option number.")
    
@bot.command(name='rps')
async def rps_command(ctx, player_choice: str):
    player_choice = player_choice.lower()
    if player_choice not in RPS_CHOICES:
        await ctx.send("Invalid choice. Choose rock, paper, or scissors.")
        return
    bot_choice = random.choice(RPS_CHOICES)
    result = rps_outcome(player_choice, bot_choice)
    await ctx.send(f"You chose {player_choice}. I chose {bot_choice}. Result: {result}!")

# -------------------- Leaderboard --------------------
@bot.command(name='top')
async def top_command(ctx):
    """Display the top 5 players by balance."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT id, balance FROM users ORDER BY balance DESC LIMIT 5')
    leaderboard = c.fetchall()
    conn.close()

    embed = discord.Embed(title="🏆 Top Players", color=0xf1c40f)
    for i, (uid, bal) in enumerate(leaderboard, 1):
        embed.add_field(name=f"{i}. <@{uid}>", value=f"${bal}", inline=False)
    await ctx.send(embed=embed)

# -------------------- Missions Command --------------------
@bot.command(name='missions')
async def missions_command(ctx):
    """Display the user's active missions and progress."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    missions = json.loads(user_data.get('missions', '{}'))

    embed = discord.Embed(title="📜 Active Missions", color=0x3498db)
    for category, mission_list in MISSIONS.items():
        for mission in mission_list:
            progress = missions.get(category, {}).get(mission['id'], 0)
            completed = "✅" if progress >= mission["requirements"].get("wins", 9999) else "❌"
            embed.add_field(name=f"{mission['name']} ({category})", value=f"{mission['description']}\nProgress: {progress}/{mission['requirements'].get('wins', 'N/A')} {completed}", inline=False)

    await ctx.send(embed=embed)

# -------------------- Casino Events --------------------
@bot.command(name='highroller')
async def highroller_command(ctx):
    """Start a high-roller event where only big bets count."""
    global HIGHROLLER_EVENT_ACTIVE
    if HIGHROLLER_EVENT_ACTIVE:
        await ctx.send("⚠️ A high-roller event is already active!")
        return
    
    HIGHROLLER_EVENT_ACTIVE = True
    await ctx.send("💰 **High Roller Event Started!** Minimum bet: **$5000**")
    await asyncio.sleep(300)  # 5 minutes duration
    HIGHROLLER_EVENT_ACTIVE = False
    await ctx.send("🏁 **High Roller Event has ended!**")

@bot.command(name='event')
async def event_command(ctx):
    """Display current or upcoming events."""
    if HIGHROLLER_EVENT_ACTIVE:
        await ctx.send("💰 **Ongoing Event:** High Roller - Only bets above $5000 count!")
    else:
        await ctx.send("📢 No active events. Check back later!")



# ==================== End of Segment 18 ====================
# ==================== Segment 19 (Lines 1801-1900) ====================
# -------------------- Bot Commands: Trade and Economy --------------------
@bot.command(name='shop')
async def shop_command(ctx):
    items_display = "\n".join([f"{item_id}: {item['name']} - ${item['price']}" for item_id, item in SHOP_ITEMS.items()])
    await ctx.send(f"**Shop Items:**\n{items_display}")

@bot.command(name='buy')
async def buy_command(ctx, item_id: str):
    user_id = ctx.author.id
    item = SHOP_ITEMS.get(item_id)
    if not item:
        await ctx.send("Invalid item ID.")
        return
    user_data = get_user_data(user_id)
    if user_data['balance'] < item['price']:
        await ctx.send("Insufficient balance to buy this item.")
        return
    deduct_balance(user_id, item['price'])
    inventory = json.loads(user_data['inventory'])
    inventory[item_id] = inventory.get(item_id, 0) + 1
    update_user_data(user_id, {'inventory': json.dumps(inventory)})
    await ctx.send(f"You bought {item['name']} for ${item['price']}.")

@bot.command(name='trade')
async def trade_command(ctx, receiver: discord.Member, offered_item: str, requested_item: str):
    sender_id = ctx.author.id
    receiver_id = receiver.id
    offer_id = create_trade_offer(sender_id, receiver_id, {offered_item: 1}, {requested_item: 1})
    await ctx.send(f"Trade offer created with ID {offer_id}.")

    # -------------------- Bot Commands: Profile Customization --------------------
@bot.command(name='setbg')
async def set_background(ctx, bg_id: str):
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data.get('inventory', '{}'))
    
    if bg_id not in inventory or inventory[bg_id] <= 0:
        await ctx.send("You don't own this background.")
        return

    profile_custom = json.loads(user_data.get('profile_custom', '{}'))
    profile_custom['background'] = bg_id
    update_user_data(user_id, {'profile_custom': json.dumps(profile_custom)})

    await ctx.send(f"Your profile background has been set to **{SHOP_ITEMS[bg_id]['name']}**!")

@bot.command(name='settitle')
async def set_title(ctx, title_id: str):
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data.get('inventory', '{}'))

    if title_id not in inventory or inventory[title_id] <= 0:
        await ctx.send("You don't own this title.")
        return

    profile_custom = json.loads(user_data.get('profile_custom', '{}'))
    profile_custom['title'] = title_id
    update_user_data(user_id, {'profile_custom': json.dumps(profile_custom)})

    await ctx.send(f"Your profile title has been set to **{SHOP_ITEMS[title_id]['name']}**!")

# -------------------- Lottery System --------------------
LOTTERY_TICKET_PRICE = 100

@bot.command(name='lottery')
async def lottery_command(ctx, tickets: int = 1):
    """Buy lottery tickets for a chance to win the jackpot."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    cost = tickets * LOTTERY_TICKET_PRICE

    if tickets < 1 or cost > user_data['balance']:
        await ctx.send(f"❌ Tickets cost ${LOTTERY_TICKET_PRICE} each. You can afford {user_data['balance'] // LOTTERY_TICKET_PRICE}.")
        return

    update_user_data(user_id, {
        'balance': user_data['balance'] - cost,
        'lottery_tickets': user_data.get('lottery_tickets', 0) + tickets
    })
    
    update_lottery_jackpot(cost // 2)
    await ctx.send(f"🎟️ Bought {tickets} tickets for ${cost}! Current jackpot: ${get_lottery_jackpot()}.")


# -------------------- Jackpot Display --------------------
@bot.command(name='jackpot')
async def jackpot_command(ctx):
    """Display the current progressive jackpot."""
    jackpot_amount = get_lottery_jackpot()
    embed = discord.Embed(title="🎰 Jackpot", description=f"💰 Current Jackpot: **${jackpot_amount}**", color=0xf1c40f)
    embed.set_footer(text="Try your luck with !lottery!")
    await ctx.send(embed=embed)


# -------------------- Loan System --------------------
LOAN_LIMIT = 1000
LOAN_INTEREST = 1.2  # 20% Interest

@bot.command(name='loan')
async def loan_command(ctx, amount: int):
    """Borrow money with interest."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)

    if amount > LOAN_LIMIT:
        await ctx.send(f"❌ You can borrow up to ${LOAN_LIMIT}.")
        return

    update_user_data(user_id, {'balance': user_data['balance'] + amount, 'loan': amount * LOAN_INTEREST})
    await ctx.send(f"💰 Loan approved! Borrowed **${amount}**. You owe **${amount * LOAN_INTEREST}**.")

@bot.command(name='repay')
async def repay_command(ctx):
    """Repay the loan if the user has enough balance."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    loan_amount = user_data.get('loan', 0)

    if loan_amount == 0:
        await ctx.send("✅ No outstanding loans!")
        return

    if user_data['balance'] < loan_amount:
        await ctx.send(f"❌ Insufficient balance to repay ${loan_amount}.")
        return

    update_user_data(user_id, {'balance': user_data['balance'] - loan_amount, 'loan': 0})
    await ctx.send("✅ Loan fully repaid! You are debt-free. 💸")


# -------------------- User Profiles --------------------
@bot.command(name='profile')
async def profile_command(ctx, member: discord.Member = None):
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
        embed.add_field(name="🏆 Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} {ACHIEVEMENTS[a]['name']}" for a in achievements), inline=False)
    await ctx.send(embed=embed)


# -------------------- Trading System --------------------
@bot.command(name='trade')
async def trade_command(ctx, member: discord.Member, offered_items: str, requested_items: str):
    """Offer a trade to another player."""
    user_id = ctx.author.id
    receiver_id = member.id
    if user_id == receiver_id:
        await ctx.send("❌ You cannot trade with yourself!")
        return
    
    trade_id = create_trade_offer(user_id, receiver_id, offered_items, requested_items)
    await ctx.send(f"🤝 Trade #{trade_id} created between {ctx.author.mention} and {member.mention}! Use `!tradeview {trade_id}` to check the trade.")

@bot.command(name='tradeview')
async def tradeview_command(ctx, trade_id: int):
    """View an existing trade offer."""
    offer = get_trade_offer(trade_id)
    if not offer:
        await ctx.send("❌ Trade offer not found!")
        return

    embed = discord.Embed(title=f"Trade Offer #{trade_id}", color=0x3498db)
    embed.add_field(name="Offered By", value=f"<@{offer['sender_id']}>", inline=True)
    embed.add_field(name="To", value=f"<@{offer['receiver_id']}>", inline=True)
    embed.add_field(name="Offered Items", value=offer['offered_items'], inline=False)
    embed.add_field(name="Requested Items", value=offer['requested_items'], inline=False)
    embed.add_field(name="Status", value=offer['status'], inline=True)
    await ctx.send(embed=embed)

@bot.command(name='tradeaccept')
async def tradeaccept_command(ctx, trade_id: int):
    """Accept a trade offer."""
    offer = get_trade_offer(trade_id)
    if not offer or offer['status'] != 'pending' or offer['receiver_id'] != ctx.author.id:
        await ctx.send("❌ Invalid or unavailable trade offer!")
        return
    
    complete_trade(trade_id)
    await ctx.send(f"✅ Trade #{trade_id} completed successfully!")



# -------------------- Expanded Daily Reward --------------------
@bot.command(name='daily')
async def daily_command(ctx):
    """Claim daily reward with streak bonuses."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    now = datetime.utcnow().isoformat()
    
    last_claim = user_data.get('daily_claim', None)
    if not last_claim or (datetime.fromisoformat(last_claim) + timedelta(days=1)) <= datetime.utcnow():
        base_reward = DAILY_REWARD * (2 if user_data['level'] >= 5 else 1)
        streaks = json.loads(user_data['streaks'])
        daily_streak = streaks.get('daily', 0)
        if last_claim and (datetime.fromisoformat(last_claim) + timedelta(days=2)) > datetime.utcnow():
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

        embed = discord.Embed(title="💸 Daily Reward!", description=f"You received **${total_reward}**!", color=0x2ecc71)
        embed.add_field(name="🔥 Streak", value=f"{daily_streak} days (+${streak_bonus})", inline=False)
        embed.add_field(name="💰 New Balance", value=f"${user_data['balance']}", inline=True)
        if earned_achievements:
            embed.add_field(name="🏆 Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}**" for a in earned_achievements), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("⏳ You have already claimed today's reward. Try again tomorrow!")


# -------------------- Shop and Purchases --------------------
@bot.command(name='shop')
async def shop_command(ctx):
    """Display available shop items."""
    embed = discord.Embed(title="🛒 Shop", description="Use `!buy [item_id]` to purchase.", color=0x3498db)
    for item_id, item in SHOP_ITEMS.items():
        embed.add_field(name=f"{item['name']} - ${item['price']} ({item_id})", value=item['description'], inline=False)
    await ctx.send(embed=embed)

@bot.command(name='buy')
async def buy_command(ctx, item_id: str):
    """Buy an item from the shop."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    item = SHOP_ITEMS.get(item_id)
    
    if not item:
        await ctx.send("❌ Item not found!")
        return
    if user_data['balance'] < item['price']:
        await ctx.send(f"❌ You need ${item['price']}, but you only have ${user_data['balance']}!")
        return

    update_user_data(user_id, {
        'balance': user_data['balance'] - item['price'],
        'inventory': json.dumps(user_data.get('inventory', {}) | {item_id: user_data.get('inventory', {}).get(item_id, 0) + 1})
    })
    
    await ctx.send(f"🛍️ Purchased **{item['name']}** for **${item['price']}**!")


# -------------------- Custom Item Drops --------------------
ITEM_DROP_TABLE = {
    "gold_coin": {"chance": 0.5, "source": "slots"},
    "four_leaf_clover": {"chance": 0.1, "source": "roulette"},
    "gold_bar": {"chance": 0.05, "source": "poker"},
    "diamond": {"chance": 0.02, "source": "blackjack"}
}

def award_drop(user_id, game):
    """Award an item drop based on game played."""
    drops = [item for item, data in ITEM_DROP_TABLE.items() if data["source"] == game]
    drop = random.choices(drops, weights=[ITEM_DROP_TABLE[d]["chance"] for d in drops], k=1)[0] if drops else None

    if drop:
        user_data = get_user_data(user_id)
        inventory = json.loads(user_data.get("inventory", "{}"))
        inventory[drop] = inventory.get(drop, 0) + 1
        update_user_data(user_id, {"inventory": json.dumps(inventory)})
        return f"🎁 You received a **{drop.replace('_', ' ').title()}**!"
    return None


# -------------------- Crafting System --------------------
CRAFTING_RECIPES.update({
    "mystery_box": {
        "ingredients": {"gold_coin": 15, "four_leaf_clover": 3, "gold_bar": 2},
        "description": "Contains a random rare item",
        "uses": 1
    },
    "fortune_potion": {
        "ingredients": {"gold_coin": 10, "diamond": 1},
        "description": "Doubles XP gain for 24 hours",
        "duration": "24h"
    }
})

@bot.command(name='craft')
async def craft_command(ctx, recipe: str):
    """Craft an item using required materials."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    inventory = json.loads(user_data.get("inventory", "{}"))

    if recipe not in CRAFTING_RECIPES:
        await ctx.send("❌ Invalid recipe! Use `!recipes` to see available crafting options.")
        return

    required = CRAFTING_RECIPES[recipe]["ingredients"]
    if all(inventory.get(item, 0) >= qty for item, qty in required.items()):
        for item, qty in required.items():
            inventory[item] -= qty
        inventory[recipe] = inventory.get(recipe, 0) + 1
        update_user_data(user_id, {"inventory": json.dumps(inventory)})
        await ctx.send(f"🔨 Successfully crafted **{recipe.replace('_', ' ').title()}**!")
    else:
        await ctx.send("❌ You don't have the necessary materials to craft this item.")




# ==================== End of Segment 19 ====================
# ==================== Segment 20 (Lines 1901-2000) ====================
# -------------------- Miscellaneous Bot Commands and Run --------------------
@bot.command(name='balance')
async def balance_command(ctx):
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    await ctx.send(f"Your current balance is: ${user_data['balance']}")

@bot.command(name='xp')
async def xp_command(ctx, amount: int):
    user_id = ctx.author.id
    levels = add_xp(user_id, amount)
    await ctx.send(f"Added {amount} XP. Levels gained: {levels}")

@bot.command(name='missions')
async def missions_command(ctx):
    user_id = ctx.author.id
    missions = get_user_missions(user_id)
    await ctx.send(f"Your missions: {json.dumps(missions)}")

@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Error: {error}")
    await ctx.send("An error occurred. Please try again later.")

    # -------------------- Custom Announcements --------------------
ANNOUNCEMENT_CHANNEL = None
ANNOUNCEMENT_MESSAGE = ""

@bot.command(name="setdailyannouncement")
async def set_announcement(ctx, channel: discord.TextChannel, *, message: str):
    """Set a daily announcement in a specific channel."""
    global ANNOUNCEMENT_CHANNEL, ANNOUNCEMENT_MESSAGE
    ANNOUNCEMENT_CHANNEL = channel.id
    ANNOUNCEMENT_MESSAGE = message
    await ctx.send(f"📢 Daily announcement set in {channel.mention}: {message}")

@bot.command(name="unsetdailyannouncement")
async def unset_announcement(ctx):
    """Remove the daily announcement."""
    global ANNOUNCEMENT_CHANNEL, ANNOUNCEMENT_MESSAGE
    ANNOUNCEMENT_CHANNEL = None
    ANNOUNCEMENT_MESSAGE = ""
    await ctx.send("❌ Daily announcement removed.")

 
    # -------------------- Help Command --------------------
@bot.command(name='paradox')
async def paradox(ctx):
    """Displays your Paradox Casino status and system info."""
    try:
        user_id = ctx.author.id
        # Retrieve user data from the database
        user_data = get_user_data(user_id)
        # Retrieve the current lottery jackpot value
        jackpot = get_lottery_jackpot()
        
        # Construct the status message
        status_message = (
            f"**Paradox Casino Status for {ctx.author.display_name}**\n"
            f"Balance: **{user_data['balance']}** coins\n"
            f"XP: **{user_data['xp']}** | Level: **{user_data['level']}**\n"
            f"Lottery Jackpot: **{jackpot}** coins\n"
            f"Daily Reward: **{DAILY_REWARD}** coins\n"
            f"Starting Balance: **{STARTING_BALANCE}** coins\n\n"
            f"**Features Available:**\n"
            f"- Slots\n"
            f"- Lottery\n"
            f"- Tournaments\n"
            f"- Crafting & Trading\n"
            f"- Missions & Achievements\n\n"
            f"Type `!help` to see all commands."
        )
        await ctx.send(status_message)
    except Exception as e:
        logger.error(f"Error in !paradox command: {e}")
        await ctx.send("Oops! Something went wrong while retrieving your casino status.")



# -------------------- Bot Run --------------------
if __name__ == '__main__':
    bot.run(os.environ.get('DISCORD_TOKEN', 'YOUR_DISCORD_TOKEN_HERE'))
# ==================== End of Segment 20 ====================
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

# --- Flask Setup for Uptime Monitoring ---
app = Flask(__name__)

@app.route('/')
def home():
    """Root endpoint for uptime monitoring."""
    return "Paradox Casino Bot is running smoothly!"

@app.route('/<path:path>')
def catch_all(path):
    """Catch-all endpoint for invalid paths."""
    print(f"Received request for path: {path}")
    return f"Path {path} not found, but server is running!", 404

def run_flask():
    """Run Flask server in a separate thread for uptime monitoring."""
    port = int(os.environ.get('PORT', 8080))
    try:
        print(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask server failed: {e}")

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('ParadoxCasinoBot')

# --- Bot Configuration ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
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

SLOTS = ['🍒', '🍋', '🍇', '🔔', '💎', '7️⃣']
WIN_MESSAGES = [
    "You're on fire! 🔥", "Lucky spin! 🍀", "Cha-ching! 💰", "Winner winner chicken dinner! 🍗",
    "The odds defy reality! ✨", "Jackpot vibes! ⚡", "Fortune smiles upon you! 🌟"
]
LOSS_MESSAGES = [
    "Better luck next time! 🎲", "So close! 📏", "House wins... for now! 🤔", "The paradox strikes! 😤",
    "Don't give up! ✨", "Try breaking the odds! 🔄"
]

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
    "trivia_genius": {"name": "Trivia Genius", "description": "Answer 10 trivia questions correctly", "emoji": "❓"},
    "hangman_hero": {"name": "Hangman Hero", "description": "Win 5 Hangman games", "emoji": "🔤"},
    "number_wizard": {"name": "Number Wizard", "description": "Guess the number in under 10 tries", "emoji": "🔢"},
    "coinflip_streak": {"name": "Coinflip Champ", "description": "Win 3 coinflips in a row", "emoji": "🪙"},
    "dice_master": {"name": "Dice Master", "description": "Win 5 dice rolls in a row", "emoji": "🎲"},
    "lottery_winner": {"name": "Lottery Lord", "description": "Win the lottery jackpot", "emoji": "🎟️"},
    "tournament_champ": {"name": "Tournament Titan", "description": "Win a tournament", "emoji": "🏅"}
}

# --- SQLite Database Initialization ---
def init_db():
    """Initialize SQLite database with tables for users, lottery, and tournaments."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 7000,
                    winnings INTEGER DEFAULT 0,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    achievements TEXT DEFAULT '[]',
                    vip_level INTEGER DEFAULT 0,
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
                    blackjack_wins INTEGER DEFAULT 0
                )''')
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
                    active INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

init_db()

# --- Database Helper Functions ---
def get_user_data(user_id):
    """Retrieve user data from SQLite, initializing if not present."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (id, balance) VALUES (?, ?)', (user_id, STARTING_BALANCE))
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    data = c.fetchone()
    conn.commit()
    conn.close()
    keys = ['id', 'balance', 'winnings', 'xp', 'level', 'achievements', 'vip_level', 'lottery_tickets',
            'profile_custom', 'daily_claim', 'streaks', 'trivia_correct', 'hangman_wins', 'number_guesses',
            'coinflip_wins', 'dice_wins', 'rps_wins', 'blackjack_wins']
    return dict(zip(keys, data))

def update_user_data(user_id, updates):
    """Update user data in SQLite with provided key-value pairs."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    query = 'UPDATE users SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE id = ?'
    values = list(updates.values()) + [user_id]
    c.execute(query, values)
    conn.commit()
    conn.close()
    logger.debug(f"Updated user data for ID {user_id}: {updates}")

def get_lottery_jackpot():
    """Retrieve the current lottery jackpot."""
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
    logger.debug(f"Lottery jackpot updated by {amount}")

def get_tournament_data(channel_id):
    """Retrieve tournament data for a channel."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tournaments WHERE channel_id = ?', (channel_id,))
    data = c.fetchone()
    conn.close()
    if data:
        keys = ['channel_id', 'game_type', 'players', 'scores', 'rounds', 'current_round', 'active']
        return dict(zip(keys, data))
    return None

def update_tournament_data(channel_id, updates):
    """Update or insert tournament data in SQLite."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO tournaments (channel_id) VALUES (?)', (channel_id,))
    query = 'UPDATE tournaments SET ' + ', '.join(f'{k} = ?' for k in updates) + ' WHERE channel_id = ?'
    values = list(updates.values()) + [channel_id]
    c.execute(query, values)
    conn.commit()
    conn.close()
    logger.debug(f"Updated tournament data for channel {channel_id}: {updates}")

# --- Slot Machine Functions ---
def spin_slots(lines):
    """Generate a slot machine spin result for the given number of lines."""
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

def format_slot_display(slots, winning_lines=None):
    """Format slot machine display with highlighted winning lines."""
    if winning_lines is None:
        winning_lines = []
    winning_line_indices = [line[0] for line in winning_lines]
    display_lines = []
    for i, line in enumerate(slots):
        if i in winning_line_indices:
            display_lines.append(f"▶️ {' '.join(line)} ◀️ +${dict(winning_lines)[i]}")
        else:
            display_lines.append(f"   {' '.join(line)}")
    return '\n'.join(display_lines)

# --- XP and Leveling System ---
def add_xp(user_id, amount):
    """Add XP to a user and handle level-ups with coin bonuses."""
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

# --- Achievements System ---
def check_achievements(user_id, bet_amount, win_amount, jackpot_win, balance, streaks):
    """Check and award achievements based on user activity."""
    user_data = get_user_data(user_id)
    achievements = json.loads(user_data['achievements'])
    earned = []
    streaks = json.loads(streaks) if isinstance(streaks, str) else streaks

    if win_amount > 0 and "first_win" not in achievements:
        achievements.append("first_win")
        earned.append("first_win")
    if win_amount >= 1000 and "big_winner" not in achievements:
        achievements.append("big_winner")
        earned.append("big_winner")
    if jackpot_win and "jackpot" not in achievements:
        achievements.append("jackpot")
        earned.append("jackpot")
    if balance == 0 and "broke" not in achievements:
        achievements.append("broke")
        earned.append("broke")
    if balance <= 100 and win_amount > 0 and "comeback" not in achievements:
        achievements.append("comeback")
        earned.append("comeback")
    if bet_amount == MAX_BET and "high_roller" not in achievements:
        achievements.append("high_roller")
        earned.append("high_roller")
    if streaks.get('daily', 0) >= 7 and "daily_streak" not in achievements:
        achievements.append("daily_streak")
        earned.append("daily_streak")
    if streaks.get('wins', 0) >= 5 and "legendary" not in achievements:
        achievements.append("legendary")
        earned.append("legendary")
    if streaks.get('rps_wins', 0) >= 5 and "rps_master" not in achievements:
        achievements.append("rps_master")
        earned.append("rps_master")
    if streaks.get('blackjack_wins', 0) >= 3 and "blackjack_pro" not in achievements:
        achievements.append("blackjack_pro")
        earned.append("blackjack_pro")
    if user_data['trivia_correct'] >= 10 and "trivia_genius" not in achievements:
        achievements.append("trivia_genius")
        earned.append("trivia_genius")
    if user_data['hangman_wins'] >= 5 and "hangman_hero" not in achievements:
        achievements.append("hangman_hero")
        earned.append("hangman_hero")
    if user_data['number_guesses'] > 0 and user_data['number_guesses'] <= 10 and "number_wizard" not in achievements:
        achievements.append("number_wizard")
        earned.append("number_wizard")
    if streaks.get('coinflip_wins', 0) >= 3 and "coinflip_streak" not in achievements:
        achievements.append("coinflip_streak")
        earned.append("coinflip_streak")
    if streaks.get('dice_wins', 0) >= 5 and "dice_master" not in achievements:
        achievements.append("dice_master")
        earned.append("dice_master")

    update_user_data(user_id, {'achievements': json.dumps(achievements)})
    return earned

# --- Tic-Tac-Toe Game Class ---
class TicTacToe:
    def __init__(self):
        """Initialize a new Tic-Tac-Toe game."""
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_active = False
        self.players = {}

    def display_board(self):
        """Display the current state of the Tic-Tac-Toe board."""
        return f"```\n  0 1 2\n0 {self.board[0][0]}|{self.board[0][1]}|{self.board[0][2]}\n  -+-+-\n1 {self.board[1][0]}|{self.board[1][1]}|{self.board[1][2]}\n  -+-+-\n2 {self.board[2][0]}|{self.board[2][1]}|{self.board[2][2]}\n```"

    def make_move(self, row, col, player):
        """Attempt to place a player's mark on the board."""
        if 0 <= row <= 2 and 0 <= col <= 2 and self.board[row][col] == " ":
            self.board[row][col] = player
            return True
        return False

    def check_win(self):
        """Check if there is a winner on the board."""
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
        """Check if the board is full, indicating a draw."""
        return all(cell != " " for row in self.board for cell in row)

game = TicTacToe()

# --- Hangman Game Setup ---
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
        """Initialize a new Hangman game."""
        self.word = random.choice(HANGMAN_WORDS).upper()
        self.guessed = set()
        self.wrong_guesses = 0
        self.active = False

    def display_word(self):
        """Display the current state of the word with guessed letters."""
        return " ".join(c if c in self.guessed else "_" for c in self.word)

    def guess(self, letter):
        """Process a letter guess in Hangman."""
        letter = letter.upper()
        if letter in self.guessed:
            return "already guessed"
        self.guessed.add(letter)
        if letter not in self.word:
            self.wrong_guesses += 1
            return "wrong"
        return "correct" if all(c in self.guessed for c in self.word) else "partial"

hangman_game = HangmanGame()

# --- Number Guessing Game Setup ---
class NumberGuessGame:
    def __init__(self):
        """Initialize a new number guessing game."""
        self.number = random.randint(1, 100)
        self.guesses_left = 20
        self.guesses_made = 0
        self.active = False

    def guess(self, number):
        """Process a guess in the number guessing game."""
        self.guesses_made += 1
        self.guesses_left -= 1
        if number == self.number:
            return "correct"
        return "higher" if number < self.number else "lower"

number_guess_game = NumberGuessGame()

# --- Trivia Questions ---
TRIVIA_QUESTIONS = [
    {"question": "What is the highest possible score in a single Blackjack hand?", "options": ["20", "21", "22", "23"], "correct": 1},
    {"question": "Which symbol gives the jackpot in Paradox Slots?", "options": ["🍒", "💎", "7️⃣", "🔔"], "correct": 2},
    {"question": "What game was added first to Paradox Casino?", "options": ["Tic-Tac-Toe", "Slots", "Wheel", "Blackjack"], "correct": 1}
]

# --- Rock-Paper-Scissors Logic ---
RPS_CHOICES = ["rock", "paper", "scissors"]
def rps_outcome(player, bot_choice):
    """Determine the outcome of a Rock-Paper-Scissors game."""
    if player == bot_choice:
        return "tie"
    if (player == "rock" and bot_choice == "scissors") or \
       (player == "paper" and bot_choice == "rock") or \
       (player == "scissors" and bot_choice == "paper"):
        return "win"
    return "lose"

# --- Blackjack Game Logic ---
class BlackjackGame:
    def __init__(self):
        """Initialize a new Blackjack game."""
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        random.shuffle(self.deck)
        self.player_hand = []
        self.dealer_hand = []
        self.active = False

    def deal_initial(self):
        """Deal initial cards for Blackjack."""
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]

    def hand_value(self, hand):
        """Calculate the value of a Blackjack hand, adjusting for aces."""
        value = sum(hand)
        aces = hand.count(11)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

blackjack_game = BlackjackGame()

# --- Wheel of Fortune Logic ---
WHEEL_PRIZES = [0, 50, 100, 200, 500, 1000, "Jackpot"]

# --- Bot Events ---
@bot.event
async def on_ready():
    """Handle bot startup and set presence."""
    logger.info(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!paradox for commands"))
    bot.loop.create_task(casino_announcements())
    bot.loop.create_task(lottery_draw_task())
    bot.loop.create_task(save_data_periodically())

async def casino_announcements():
    """Send periodic announcements to guild system channels."""
    await bot.wait_until_ready()
    announcements = [
        {"title": "🎰 Feeling Lucky?", "description": f"Try `!bet` for the {JACKPOT_SYMBOL} jackpot!"},
        {"title": "💰 Daily Rewards", "description": "Claim `!daily` with streak bonuses!"},
        {"title": "🎡 Wheel of Fortune", "description": "Spin `!wheel` to multiply coins!"},
        {"title": "🪨📜✂️ Rock, Paper, Scissors", "description": "Challenge with `!rps`!"},
        {"title": "♠♥♦♣ Blackjack", "description": "Play `!blackjack` to beat the dealer!"},
        {"title": "❓ Trivia", "description": "Answer `!trivia` for coins!"},
        {"title": "🔤 Hangman", "description": "Guess the word with `!hangman`!"},
        {"title": "🔢 Number Guessing", "description": "Play `!guessnumber` for $50!"},
        {"title": "🪙 Coin Flip", "description": "Flip a coin with `!coinflip`!"},
        {"title": "🎲 Dice Roll", "description": "Roll dice with `!dice`!"},
        {"title": "🎟️ Lottery", "description": "Buy tickets with `!lottery buy`!"},
        {"title": "🏆 Tournaments", "description": "Join with `!tournament`!"}
    ]
    index = 0
    while not bot.is_closed():
        for guild in bot.guilds:
            if guild.system_channel:
                embed = discord.Embed(**announcements[index], color=0xf1c40f)
                embed.set_footer(text="Paradox Casino Machine")
                try:
                    await guild.system_channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to send announcement to {guild.name}: {e}")
        index = (index + 1) % len(announcements)
        await asyncio.sleep(3600 * 12)  # Every 12 hours
        logger.info(f"Sent announcement #{index}")

async def lottery_draw_task():
    """Handle daily lottery draws and reset jackpot."""
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
                'lottery_tickets': 0,
                'achievements': json.dumps(json.loads(user_data['achievements']) + ["lottery_winner"])
            })
            c.execute('UPDATE users SET lottery_tickets = 0')
            c.execute('UPDATE lottery SET jackpot = 1000 WHERE rowid = 1')
            conn.commit()
            channel = bot.get_channel(YOUR_CHANNEL_ID)  # Replace with your channel ID
            if channel:
                await channel.send(f"<@{winner_id}> won the lottery jackpot of ${jackpot}!")
                logger.info(f"Lottery won by {winner_id}: ${jackpot}")
        conn.close()

async def save_data_periodically():
    """Periodically log data save for debugging."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        logger.info("User data persists in SQLite.")

# --- Core Commands ---
@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet(ctx, amount: int, lines: int = 1):
    """Place a bet and spin the slot machine."""
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
    earned_achievements = check_achievements(user_id, amount, winnings, jackpot_win, user_data['balance'], streaks)
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
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to {get_user_data(user_id)['level']}! +{500 * levels_gained} coins")

@bot.command()
async def daily(ctx):
    """Claim daily reward with streak bonuses."""
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
async def profile(ctx):
    """Display user profile with detailed stats."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    level = user_data['level']
    xp = user_data['xp']
    xp_needed = 100 * level
    vip = "Yes" if level >= 5 else "No"
    embed = discord.Embed(
        title=f"👤 {ctx.author.name}'s Profile",
        description=f"Level: {level}\nXP: {xp}/{xp_needed}\nVIP: {vip}\nBalance: ${user_data['balance']}",
        color=0x3498db
    )
    achievements = json.loads(user_data['achievements'])
    if achievements:
        embed.add_field(name="Achievements", value="\n".join(f"{ACHIEVEMENTS[a]['emoji']} {ACHIEVEMENTS[a]['name']}" for a in achievements), inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def jackpot(ctx):
    """Display the current progressive jackpot."""
    jackpot_amount = get_lottery_jackpot()
    embed = discord.Embed(
        title="🎰 Current Jackpot",
        description=f"The progressive jackpot is ${jackpot_amount}.",
        color=0xf1c40f
    )
    embed.set_footer(text="Paradox Casino | Win it all!")
    await ctx.send(embed=embed)

# --- Original Game Commands ---
@bot.command()
async def tictactoe(ctx, opponent: discord.Member = None):
    """Start a Tic-Tac-Toe game with an opponent or the bot."""
    if game.game_active:
        await ctx.send("❌ A game is already in progress!")
        return
    game.game_active = True
    game.players = {ctx.author.id: "X"}
    if opponent:
        if opponent == ctx.author:
            await ctx.send("❌ You can't play against yourself!")
            return
        game.players[opponent.id] = "O"
        await ctx.send(f"🎮 Tic-Tac-Toe started between {ctx.author.mention} (X) and {opponent.mention} (O)!\nUse !move [row] [col] (0-2).")
    else:
        game.players[bot.user.id] = "O"
        await ctx.send(f"🎮 Tic-Tac-Toe started! {ctx.author.mention} (X) vs Bot (O).\nUse !move [row] [col] (0-2).")
    await ctx.send(game.display_board())

@bot.command()
async def move(ctx, row: int, col: int):
    """Make a move in the Tic-Tac-Toe game."""
    if not game.game_active:
        await ctx.send("❌ No game in progress! Start one with !tictactoe.")
        return
    if ctx.author.id not in game.players and bot.user.id != ctx.author.id:
        await ctx.send("❌ You're not part of this game!")
        return
    if game.current_player != game.players.get(ctx.author.id):
        await ctx.send("❌ It's not your turn!")
        return
    if row not in [0, 1, 2] or col not in [0, 1, 2]:
        await ctx.send("❌ Invalid move! Use row and col between 0 and 2.")
        return
    if game.board[row][col] != " ":
        await ctx.send("❌ That spot is already taken!")
        return
    player = game.players[ctx.author.id]
    if game.make_move(row, col, player):
        winner = game.check_win()
        if winner:
            update_user_data(ctx.author.id, {'balance': get_user_data(ctx.author.id)['balance'] + 100})
            await ctx.send(f"{game.display_board()}\n{ctx.author.mention} wins! +$100")
            game.game_active = False
        elif game.is_full():
            await ctx.send(f"{game.display_board()}\nIt's a tie!")
            game.game_active = False
        else:
            game.current_player = "O" if player == "X" else "X"
            next_player = next(k for k, v in game.players.items() if v == game.current_player)
            await ctx.send(f"{game.display_board()}\n<@{next_player}>'s turn!")
            if next_player == bot.user.id:
                await asyncio.sleep(1)
                while True:
                    bot_row = random.randint(0, 2)
                    bot_col = random.randint(0, 2)
                    if game.make_move(bot_row, bot_col, "O"):
                        winner = game.check_win()
                        await ctx.send(f"{game.display_board()}\nBot moved to ({bot_row}, {bot_col})!")
                        if winner:
                            await ctx.send("🤖 Bot wins!")
                            game.game_active = False
                        elif game.is_full():
                            await ctx.send("🤝 It's a tie!")
                            game.game_active = False
                        break

@bot.command()
async def hangman(ctx):
    """Start a Hangman game."""
    if hangman_game.active:
        await ctx.send("❌ Hangman is already in progress!")
        return
    hangman_game.active = True
    hangman_game.__init__()
    await ctx.send(f"{HANGMAN_STAGES[0]}\nWord: {hangman_game.display_word()}\nGuess a letter with `!guess letter`")

@bot.command()
async def guess(ctx, letter: str):
    """Guess a letter in the Hangman game."""
    if not hangman_game.active:
        await ctx.send("❌ No Hangman game in progress!")
        return
    result = hangman_game.guess(letter)
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if result == "already guessed":
        await ctx.send("❌ You already guessed that!")
    elif result == "wrong":
        await ctx.send(f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\nWord: {hangman_game.display_word()}")
        if hangman_game.wrong_guesses == 6:
            await ctx.send(f"Game Over! The word was {hangman_game.word}")
            hangman_game.active = False
    elif result == "correct":
        update_user_data(user_id, {
            'balance': user_data['balance'] + 50,
            'hangman_wins': user_data['hangman_wins'] + 1
        })
        await ctx.send(f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\nWord: {hangman_game.display_word()}\nYou win! +$50")
        check_achievements(user_id, 0, 50, False, user_data['balance'] + 50, user_data['streaks'])
        hangman_game.active = False
    else:
        await ctx.send(f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\nWord: {hangman_game.display_word()}")

@bot.command()
async def guessnumber(ctx):
    """Start a number guessing game."""
    if number_guess_game.active:
        await ctx.send("❌ A number guessing game is already in progress!")
        return
    number_guess_game.active = True
    number_guess_game.__init__()
    await ctx.send(f"Guess a number between 1 and 100! You have {number_guess_game.guesses_left} guesses. Use `!number guess`")

@bot.command()
async def number(ctx, guess: int):
    """Make a guess in the number guessing game."""
    if not number_guess_game.active:
        await ctx.send("❌ No number guessing game in progress!")
        return
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    result = number_guess_game.guess(guess)
    if result == "correct":
        update_user_data(user_id, {
            'balance': user_data['balance'] + 50,
            'number_guesses': number_guess_game.guesses_made
        })
        await ctx.send(f"Correct! The number was {number_guess_game.number}. You win $50 in {number_guess_game.guesses_made} guesses!")
        check_achievements(user_id, 0, 50, False, user_data['balance'] + 50, user_data['streaks'])
        number_guess_game.active = False
    elif number_guess_game.guesses_left == 0:
        await ctx.send(f"Out of guesses! The number was {number_guess_game.number}.")
        number_guess_game.active = False
    else:
        await ctx.send(f"Too {'high' if result == 'lower' else 'low'}! {number_guess_game.guesses_left} guesses left.")

@bot.command()
async def trivia(ctx):
    """Answer a trivia question to win coins."""
    question = random.choice(TRIVIA_QUESTIONS)
    embed = discord.Embed(title="❓ Trivia Time!", description=question["question"], color=0x3498db)
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
            check_achievements(user_id, 0, 100, False, user_data['balance'] + 100, user_data['streaks'])
        else:
            await ctx.send(f"Wrong! The answer was {question['options'][question['correct']]}.")
    except asyncio.TimeoutError:
        await ctx.send("Time's up!")

@bot.command()
async def rps(ctx, amount: int):
    """Play Rock-Paper-Scissors with a bet."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Invalid bet or insufficient funds!")
        return
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    await ctx.send("Choose your move: rock, paper, or scissors")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in choices
    try:
        response = await bot.wait_for('message', check=check, timeout=30.0)
        player_choice = response.content.lower()
        outcome = rps_outcome(player_choice, bot_choice)
        streaks = json.loads(user_data['streaks'])
        if outcome == "win":
            streaks['rps_wins'] = streaks.get('rps_wins', 0) + 1
            update_user_data(user_id, {
                'balance': user_data['balance'] + amount,
                'rps_wins': user_data['rps_wins'] + 1,
                'streaks': json.dumps(streaks)
            })
            await ctx.send(f"You chose {player_choice}, bot chose {bot_choice}. You win! +${amount}")
            check_achievements(user_id, amount, amount, False, user_data['balance'] + amount, streaks)
        elif outcome == "lose":
            streaks['rps_wins'] = 0
            update_user_data(user_id, {
                'balance': user_data['balance'] - amount,
                'streaks': json.dumps(streaks)
            })
            await ctx.send(f"You chose {player_choice}, bot chose {bot_choice}. You lose! -${amount}")
        else:
            await ctx.send(f"You chose {player_choice}, bot chose {bot_choice}. It's a tie!")
    except asyncio.TimeoutError:
        await ctx.send("Time's up! You didn't make a choice.")

@bot.command()
async def blackjack(ctx, amount: int):
    """Start a Blackjack game with a bet."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Invalid bet or insufficient funds!")
        return
    blackjack_game.active = True
    blackjack_game.deal_initial()
    await ctx.send(f"Your hand: {blackjack_game.player_hand} ({blackjack_game.hand_value(blackjack_game.player_hand)})\nDealer's hand: [{blackjack_game.dealer_hand[0]}, ?]\n`!hit` or `!stand`")

@bot.command()
async def hit(ctx):
    """Hit to draw another card in Blackjack."""
    if not blackjack_game.active:
        await ctx.send("❌ No Blackjack game in progress!")
        return
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    blackjack_game.player_hand.append(blackjack_game.deck.pop())
    value = blackjack_game.hand_value(blackjack_game.player_hand)
    if value > 21:
        update_user_data(user_id, {'balance': user_data['balance'] - amount})
        await ctx.send(f"Your hand: {blackjack_game.player_hand} ({value})\nBust! You lose.")
        blackjack_game.active = False
    else:
        await ctx.send(f"Your hand: {blackjack_game.player_hand} ({value})\n`!hit` or `!stand`")

@bot.command()
async def stand(ctx):
    """Stand to end your turn in Blackjack."""
    if not blackjack_game.active:
        await ctx.send("❌ No Blackjack game in progress!")
        return
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    while blackjack_game.hand_value(blackjack_game.dealer_hand) < 17:
        blackjack_game.dealer_hand.append(blackjack_game.deck.pop())
    player_value = blackjack_game.hand_value(blackjack_game.player_hand)
    dealer_value = blackjack_game.hand_value(blackjack_game.dealer_hand)
    streaks = json.loads(user_data['streaks'])
    if dealer_value > 21 or player_value > dealer_value:
        streaks['blackjack_wins'] = streaks.get('blackjack_wins', 0) + 1
        update_user_data(user_id, {
            'balance': user_data['balance'] + amount,
            'blackjack_wins': user_data['blackjack_wins'] + 1,
            'streaks': json.dumps(streaks)
        })
        await ctx.send(f"Your hand: {blackjack_game.player_hand} ({player_value})\nDealer's hand: {blackjack_game.dealer_hand} ({dealer_value})\nYou win! +${amount}")
        check_achievements(user_id, amount, amount, False, user_data['balance'] + amount, streaks)
    elif player_value < dealer_value:
        streaks['blackjack_wins'] = 0
        update_user_data(user_id, {
            'balance': user_data['balance'] - amount,
            'streaks': json.dumps(streaks)
        })
        await ctx.send(f"Your hand: {blackjack_game.player_hand} ({player_value})\nDealer's hand: {blackjack_game.dealer_hand} ({dealer_value})\nYou lose! -${amount}")
    else:
        await ctx.send(f"Your hand: {blackjack_game.player_hand} ({player_value})\nDealer's hand: {blackjack_game.dealer_hand} ({dealer_value})\nTie!")
    blackjack_game.active = False

@bot.command()
async def wheel(ctx, amount: int):
    """Spin the Wheel of Fortune with a bet."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount < MIN_BET or amount > MAX_BET or amount > user_data['balance']:
        await ctx.send(f"❌ Invalid bet or insufficient funds!")
        return
    prize = random.choice(WHEEL_PRIZES)
    if prize == "Jackpot":
        winnings = get_lottery_jackpot()
        update_lottery_jackpot(-winnings + 1000)
    else:
        winnings = prize
    update_user_data(user_id, {'balance': user_data['balance'] - amount + winnings})
    await ctx.send(f"You spun the wheel and won {prize if prize != 'Jackpot' else f'${winnings} Jackpot'}! New balance: ${user_data['balance'] - amount + winnings}")

# --- New Game Commands ---
@bot.command()
async def coinflip(ctx, amount: int, choice: str):
    """Flip a coin with a bet."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount <= 0 or amount > user_data['balance'] or choice.lower() not in ["heads", "tails"]:
        await ctx.send("❌ Invalid amount or choice ('heads' or 'tails')!")
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
        description=f"Flipped {result}. You {'won' if win else 'lost'} ${abs(payout)}!",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Balance", value=f"${user_data['balance'] + payout}", inline=True)
    check_achievements(user_id, amount, payout if win else 0, False, user_data['balance'] + payout, streaks)
    await ctx.send(embed=embed)

@bot.command()
async def dice(ctx, amount: int, prediction: str):
    """Roll two dice with a prediction."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    if amount <= 0 or amount > user_data['balance'] or prediction.lower() not in ["over 7", "under 7", "exactly 7"]:
        await ctx.send("❌ Invalid amount or prediction ('over 7', 'under 7', 'exactly 7')!")
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
        description=f"Rolled {dice1} + {dice2} = {total}. You {'won' if win else 'lost'} ${abs(payout)}!",
        color=0x2ecc71 if win else 0xe74c3c
    )
    embed.add_field(name="Balance", value=f"${user_data['balance'] + payout}", inline=True)
    check_achievements(user_id, amount, payout if win else 0, False, user_data['balance'] + payout, streaks)
    await ctx.send(embed=embed)

@bot.command()
async def lottery(ctx, action: str, tickets: int = 1):
    """Manage lottery participation (buy or check tickets)."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    action = action.lower()
    if action == "buy":
        cost = tickets * 100
        if cost > user_data['balance']:
            await ctx.send("❌ Not enough coins!")
            return
        update_user_data(user_id, {
            'balance': user_data['balance'] - cost,
            'lottery_tickets': user_data['lottery_tickets'] + tickets
        })
        update_lottery_jackpot(tickets * 50)
        await ctx.send(f"🎟️ Bought {tickets} lottery tickets for ${cost}! Jackpot now: ${get_lottery_jackpot()}")
    elif action == "check":
        await ctx.send(f"🎟️ You have {user_data['lottery_tickets']} tickets. Jackpot: ${get_lottery_jackpot()}")
    else:
        await ctx.send("❌ Use `!lottery buy [tickets]` or `!lottery check`")

# --- Tournament System ---
@bot.command()
async def tournament(ctx, game: str):
    """Start a tournament for a specific game."""
    channel_id = ctx.channel.id
    game = game.lower()
    if game not in ["coinflip", "dice"]:
        await ctx.send("❌ Only 'coinflip' and 'dice' tournaments supported!")
        return
    if get_tournament_data(channel_id) and get_tournament_data(channel_id)['active']:
        await ctx.send("❌ A tournament is already active in this channel!")
        return
    update_tournament_data(channel_id, {
        'game_type': game,
        'players': json.dumps({}),
        'scores': json.dumps({}),
        'rounds': 3,
        'current_round': 0,
        'active': 1
    })
    await ctx.send(f"🏆 {game.capitalize()} tournament started! Join with `!join`. Starts in 60 seconds.")
    await asyncio.sleep(60)
    tournament = get_tournament_data(channel_id)
    players = json.loads(tournament['players'])
    if len(players) < 2:
        await ctx.send("❌ Not enough players joined!")
        update_tournament_data(channel_id, {'active': 0})
        return
    await run_tournament(channel_id)

@bot.command()
async def join(ctx):
    """Join an active tournament in the channel."""
    channel_id = ctx.channel.id
    tournament = get_tournament_data(channel_id)
    if not tournament or not tournament['active']:
        await ctx.send("❌ No active tournament in this channel!")
        return
    players = json.loads(tournament['players'])
    scores = json.loads(tournament['scores'])
    if ctx.author.id not in players:
        players[ctx.author.id] = 0
        scores[ctx.author.id] = 0
        update_tournament_data(channel_id, {
            'players': json.dumps(players),
            'scores': json.dumps(scores)
        })
        await ctx.send(f"{ctx.author.mention} joined the {tournament['game_type']} tournament!")

async def run_tournament(channel_id):
    """Execute the tournament rounds and determine the winner."""
    tournament = get_tournament_data(channel_id)
    channel = bot.get_channel(channel_id)
    players = json.loads(tournament['players'])
    scores = json.loads(tournament['scores'])
    for round_num in range(1, tournament['rounds'] + 1):
        update_tournament_data(channel_id, {'current_round': round_num})
        await channel.send(f"Round {round_num} of {tournament['game_type']} tournament begins!")
        for player_id in players:
            user_data = get_user_data(player_id)
            if tournament['game_type'] == "coinflip":
                result = random.choice(["heads", "tails"])
                win = random.choice([True, False])
                payout = 100 if win else -100
            else:  # dice
                dice1, dice2 = random.randint(1, 6), random.randint(1, 6)
                total = dice1 + dice2
                win = total > 7  # Simplified rule
                payout = 100 if win else -100
            scores[player_id] = scores.get(player_id, 0) + payout
            update_user_data(player_id, {'balance': user_data['balance'] + payout})
        update_tournament_data(channel_id, {'scores': json.dumps(scores)})
        await asyncio.sleep(5)
    winner_id = max(scores, key=scores.get)
    update_user_data(winner_id, {
        'balance': get_user_data(winner_id)['balance'] + 500,
        'achievements': json.dumps(json.loads(get_user_data(winner_id)['achievements']) + ["tournament_champ"])
    })
    await channel.send(f"🏆 Tournament over! <@{winner_id}> wins with {scores[winner_id]} points! +$500")
    update_tournament_data(channel_id, {'active': 0})

# --- Additional Commands ---
@bot.command()
async def balance(ctx):
    """Check the user's current balance."""
    user_id = ctx.author.id
    user_data = get_user_data(user_id)
    embed = discord.Embed(
        title="💰 Balance",
        description=f"{ctx.author.mention}, balance: ${user_data['balance']}",
        color=0x2ecc71
    )
    embed.add_field(name="Total Winnings", value=f"${user_data['winnings']}", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def top(ctx):
    """Display the top 5 players by balance."""
    conn = sqlite3.connect('casino.db')
    c = conn.cursor()
    c.execute('SELECT id, balance FROM users ORDER BY balance DESC LIMIT 5')
    leaderboard = c.fetchall()
    conn.close()
    embed = discord.Embed(title="🏆 Top Balances", color=0xf1c40f)
    for i, (uid, bal) in enumerate(leaderboard, 1):
        embed.add_field(name=f"{i}. <@{uid}>", value=f"${bal}", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def achievements(ctx, member: discord.Member = None):
    """Display achievements for a user."""
    target = member or ctx.author
    user_id = target.id
    user_data = get_user_data(user_id)
    achievements = json.loads(user_data['achievements'])
    if not achievements:
        await ctx.send(f"{target.mention} has no achievements yet!")
        return
    embed = discord.Embed(
        title=f"🏆 {target.name}'s Achievements",
        description="Earned in Paradox Casino",
        color=0x9b59b6
    )
    for a in achievements:
        embed.add_field(name=f"{ACHIEVEMENTS[a]['emoji']} {ACHIEVEMENTS[a]['name']}", value=ACHIEVEMENTS[a]['description'], inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def give(ctx, recipient: discord.Member, amount: int):
    """Transfer coins to another user."""
    sender_id = ctx.author.id
    recipient_id = recipient.id
    sender_data = get_user_data(sender_id)
    recipient_data = get_user_data(recipient_id)
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    if sender_id == recipient_id:
        await ctx.send("❓ Can't give to yourself!")
        return
    if amount > sender_data['balance']:
        await ctx.send(f"❌ Insufficient funds! Balance: ${sender_data['balance']}.")
        return
    update_user_data(sender_id, {'balance': sender_data['balance'] - amount})
    update_user_data(recipient_id, {'balance': recipient_data['balance'] + amount})
    embed = discord.Embed(
        title="💸 Money Transfer",
        description=f"{ctx.author.mention} gave ${amount} to {recipient.mention}!",
        color=0x2ecc71
    )
    embed.add_field(name=f"{ctx.author.name}'s Balance", value=f"${sender_data['balance'] - amount}", inline=True)
    embed.add_field(name=f"{recipient.name}'s Balance", value=f"${recipient_data['balance'] + amount}", inline=True)
    await ctx.send(embed=embed)

# --- Help Command ---
@bot.command(name="paradox")
async def paradox_help(ctx):
    """Display the comprehensive help menu."""
    embed = discord.Embed(
        title="🎰 Paradox Casino Machine - Commands",
        description="Explore the games of Paradox Casino!",
        color=0x3498db
    )
    embed.add_field(name="!bet [amount] [lines]", value="Spin the slots", inline=False)
    embed.add_field(name="!daily", value="Claim daily reward", inline=False)
    embed.add_field(name="!profile", value="View your profile", inline=False)
    embed.add_field(name="!jackpot", value="Check jackpot", inline=False)
    embed.add_field(name="!balance", value="Check your balance", inline=False)
    embed.add_field(name="!top", value="View leaderboard", inline=False)
    embed.add_field(name="!achievements [user]", value="View achievements", inline=False)
    embed.add_field(name="!give [user] [amount]", value="Give coins", inline=False)
    embed.add_field(name="!tictactoe [@user]", value="Play Tic-Tac-Toe", inline=False)
    embed.add_field(name="!move [row] [col]", value="Move in Tic-Tac-Toe", inline=False)
    embed.add_field(name="!hangman", value="Start Hangman", inline=False)
    embed.add_field(name="!guess [letter]", value="Guess in Hangman", inline=False)
    embed.add_field(name="!guessnumber", value="Start number guessing", inline=False)
    embed.add_field(name="!number [guess]", value="Guess a number", inline=False)
    embed.add_field(name="!trivia", value="Answer trivia", inline=False)
    embed.add_field(name="!rps [amount]", value="Play Rock-Paper-Scissors", inline=False)
    embed.add_field(name="!blackjack [amount]", value="Start Blackjack", inline=False)
    embed.add_field(name="!hit", value="Hit in Blackjack", inline=False)
    embed.add_field(name="!stand", value="Stand in Blackjack", inline=False)
    embed.add_field(name="!wheel [amount]", value="Spin Wheel of Fortune", inline=False)
    embed.add_field(name="!coinflip [amount] [choice]", value="Flip a coin", inline=False)
    embed.add_field(name="!dice [amount] [prediction]", value="Roll dice", inline=False)
    embed.add_field(name="!lottery [action] [tickets]", value="Manage lottery", inline=False)
    embed.add_field(name="!tournament [game]", value="Start a tournament", inline=False)
    embed.add_field(name="!join", value="Join a tournament", inline=False)
    embed.set_footer(text="Paradox Casino | Where probability defies reality")
    await ctx.send(embed=embed)

# --- Error Handling ---
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors with detailed feedback."""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Wait {error.retry_after:.1f} seconds.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument! Use `!paradox` for help.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument! Use `!paradox` for help.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found!")
    else:
        await ctx.send(f"❌ Error: {error}")
        logger.error(f"Command error from {ctx.author}: {error}")

# --- Startup Logic ---
if __name__ == "__main__":
    YOUR_CHANNEL_ID = 123456789012345678  # Replace with your channel ID
    try:
        logger.info("Starting bot...")
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN not set in environment variables!")
        loop = asyncio.get_event_loop()
        loop.create_task(bot.start(token))
        loop.run_forever()
    except discord.errors.HTTPException as e:
        logger.error(f"HTTPException during startup: {e}")
        if e.status == 429:
            retry_after = float(e.response.headers.get('Retry-After', 5))
            logger.info(f"Rate limited. Retrying after {retry_after} seconds...")
            asyncio.sleep(retry_after)
            loop.run_until_complete(bot.start(token))
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        loop.run_until_complete(bot.close())
    finally:
        logger.info("Bot shutdown initiated.")
        for task in asyncio.all_tasks(loop):
            if not task.done():
                task.cancel()
        loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True))
        loop.close()
import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
import os
import json
from flask import Flask, request
import threading

# Flask setup for UptimeRobot with debugging
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/<path:path>')
def catch_all(path):
    print(f"Received request for path: {path}")
    return f"Path {path} not found, but server is running!", 404

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    try:
        print(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask server failed: {e}")

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# Bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# Game constants
MAX_LINES = 3
MAX_BET = 1000
MIN_BET = 10
DAILY_REWARD = 500
JACKPOT_SYMBOL = '7️⃣'
JACKPOT_MULTIPLIER = 5
STARTING_BALANCE = 7000  # Updated starting balance to 7000

SLOTS = ['🍒', '🍋', '🍇', '🔔', '💎', '7️⃣']

# Global dictionaries to store user data
user_balances = {}
user_winnings = {}
user_daily_claims = {}
user_streaks = {}
betting_cooldowns = {}
user_xp = {}  # XP system
user_levels = {}  # Level system
jackpot = 1000  # Progressive jackpot starting value

WIN_MESSAGES = [
    "You're on fire! 🔥", "Lucky spin! 🍀", "The Paradox Casino is feeling generous today! 💸",
    "Winner winner chicken dinner! 🍗", "Cha-ching! 💰", "The odds are in your favor! ✨",
    "Jackpot energy! ⚡", "Your luck is through the roof! 🚀"
]

LOSS_MESSAGES = [
    "Better luck next time! 🎲", "So close, yet so far! 📏", "The Paradox machines are stubborn! 😤",
    "Don't give up! Your win is coming! ✨", "That's how they get you! 🎯", "House wins... or does it? 🤔",
    "Break the losing paradox! 🔄", "Fortune favors the persistent! 🌟"
]

user_achievements = {}

ACHIEVEMENTS = {
    "first_win": {"name": "Paradox Novice", "description": "Win your first slot game", "emoji": "🏆"},
    "big_winner": {"name": "Paradox Master", "description": "Win over 1000 coins in a spin", "emoji": "💎"},
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
    "number_wizard": {"name": "Number Wizard", "description": "Guess the number in under 10 tries", "emoji": "🔢"}
}

def spin_slots(lines):
    """Generate slot machine results for the specified number of lines."""
    return [[random.choice(SLOTS) for _ in range(3)] for _ in range(lines)]

def check_win(slots):
    """Check if the slot results are a win and calculate winnings."""
    winnings = 0
    jackpot_win = False
    winning_lines = []
    for i, line in enumerate(slots):
        if line.count(line[0]) == 3:  # All three symbols match
            multiplier = JACKPOT_MULTIPLIER if line[0] == JACKPOT_SYMBOL else 1
            line_win = 100 * multiplier
            winnings += line_win
            winning_lines.append((i, line_win))
            if line[0] == JACKPOT_SYMBOL:
                jackpot_win = True
    return winnings, jackpot_win, winning_lines

def format_slot_display(slots, winning_lines=None):
    """Format the slot machine display with winning lines highlighted."""
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

def add_xp(user, amount):
    """Add XP to a user and handle leveling up with a coin bonus."""
    if user not in user_xp:
        user_xp[user] = 0
        user_levels[user] = 1
    user_xp[user] += amount
    levels_gained = 0
    while user_xp[user] >= 100 * user_levels[user]:
        user_xp[user] -= 100 * user_levels[user]
        user_levels[user] += 1
        levels_gained += 1
        user_balances[user] += 500  # Bonus for leveling up
    return levels_gained

def check_achievements(user, bet_amount, win_amount, jackpot, balance, win_streak=0, trivia_count=0, hangman_wins=0, number_guesses=0):
    """Check and award achievements based on user actions."""
    if user not in user_achievements:
        user_achievements[user] = set()
    achievements_earned = []
    if win_amount > 0 and "first_win" not in user_achievements[user]:
        user_achievements[user].add("first_win")
        achievements_earned.append("first_win")
    if win_amount >= 1000 and "big_winner" not in user_achievements[user]:
        user_achievements[user].add("big_winner")
        achievements_earned.append("big_winner")
    if jackpot and "jackpot" not in user_achievements[user]:
        user_achievements[user].add("jackpot")
        achievements_earned.append("jackpot")
    if balance == 0 and "broke" not in user_achievements[user]:
        user_achievements[user].add("broke")
        achievements_earned.append("broke")
    if balance <= 100 and win_amount > 0 and "comeback" not in user_achievements[user]:
        user_achievements[user].add("comeback")
        achievements_earned.append("comeback")
    if bet_amount == MAX_BET and "high_roller" not in user_achievements[user]:
        user_achievements[user].add("high_roller")
        achievements_earned.append("high_roller")
    if win_streak >= 5 and "legendary" not in user_achievements[user]:
        user_achievements[user].add("legendary")
        achievements_earned.append("legendary")
    if user_streaks.get(user, {}).get("rps_wins", 0) >= 5 and "rps_master" not in user_achievements[user]:
        user_achievements[user].add("rps_master")
        achievements_earned.append("rps_master")
    if user_streaks.get(user, {}).get("blackjack_wins", 0) >= 3 and "blackjack_pro" not in user_achievements[user]:
        user_achievements[user].add("blackjack_pro")
        achievements_earned.append("blackjack_pro")
    if trivia_count >= 10 and "trivia_genius" not in user_achievements[user]:
        user_achievements[user].add("trivia_genius")
        achievements_earned.append("trivia_genius")
    if hangman_wins >= 5 and "hangman_hero" not in user_achievements[user]:
        user_achievements[user].add("hangman_hero")
        achievements_earned.append("hangman_hero")
    if number_guesses <= 10 and "number_wizard" not in user_achievements[user]:
        user_achievements[user].add("number_wizard")
        achievements_earned.append("number_wizard")
    return achievements_earned

# Tic-Tac-Toe game setup
class TicTacToe:
    def __init__(self):
        self.board = [[" " for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_active = False
        self.players = {}

    def display_board(self):
        return f"```\n  0 1 2\n0 {self.board[0][0]}|{self.board[0][1]}|{self.board[0][2]}\n  -+-+-\n1 {self.board[1][0]}|{self.board[1][1]}|{self.board[1][2]}\n  -+-+-\n2 {self.board[2][0]}|{self.board[2][1]}|{self.board[2][2]}\n```"

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

# Hangman game setup
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
        self.hangman_wins = 0

hangman_game = HangmanGame()

# Number Guessing game setup
class NumberGuessGame:
    def __init__(self):
        self.number = random.randint(1, 100)
        self.guesses_left = 20
        self.active = False

number_guess_game = NumberGuessGame()

# Trivia questions
TRIVIA_QUESTIONS = [
    {"question": "What is the highest possible score in a single Blackjack hand?", "options": ["20", "21", "22", "23"], "correct": 1},
    {"question": "Which symbol gives the jackpot in Paradox Slots?", "options": ["🍒", "💎", "7️⃣", "🔔"], "correct": 2},
    {"question": "What game was added first to Paradox Casino?", "options": ["Tic-Tac-Toe", "Slots", "Wheel of Fortune", "Blackjack"], "correct": 1}
]

@bot.event
async def on_ready():
    """Event triggered when the bot is ready."""
    print(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!paradox for commands"))
    bot.loop.create_task(casino_announcements())

async def casino_announcements():
    """Periodically send casino announcements to guild system channels."""
    await bot.wait_until_ready()
    announcements = [
        {"title": "🎰 Feeling Lucky?", "description": f"Try your luck with `!bet` and aim for the {JACKPOT_SYMBOL} jackpot!"},
        {"title": "💰 Daily Rewards", "description": "Claim your `!daily` reward with streak bonuses!"},
        {"title": "🎡 Wheel of Fortune", "description": "Spin the `!wheel` to multiply your coins!"},
        {"title": "🪨📜✂️ Rock, Paper, Scissors", "description": "Challenge the bot with `!rps` and double your bet!"},
        {"title": "♠♥♦♣ Blackjack", "description": "Play `!blackjack` to beat the dealer!"},
        {"title": "❓ Test Your Knowledge", "description": "Answer `!trivia` questions to earn coins!"},
        {"title": "🔤 Hangman Challenge", "description": "Guess the word with `!hangman` to win coins!"},
        {"title": "🔢 Guess the Number", "description": "Play `!guessnumber` to win $50!"}
    ]
    announcement_index = 0
    while not bot.is_closed():
        for guild in bot.guilds:
            if guild.system_channel:
                current_announcement = announcements[announcement_index]
                embed = discord.Embed(title=current_announcement["title"], description=current_announcement["description"], color=0xf1c40f)
                embed.set_footer(text="Paradox Casino Machine | Type !paradox for help")
                try:
                    await guild.system_channel.send(embed=embed)
                except:
                    pass
        announcement_index = (announcement_index + 1) % len(announcements)
        print(f"Sent announcement at {datetime.now()}")
        await asyncio.sleep(3600 * 12)  # Announce every 12 hours

@bot.command()
async def tictactoe(ctx, opponent: discord.Member = None):
    global game
    if game.game_active:
        await ctx.send("❌ A game is already in progress! Finish it first.")
        return
    game = TicTacToe()
    game.game_active = True
    game.players[ctx.author.id] = "X"
    if opponent:
        if opponent == ctx.author:
            await ctx.send("❌ You can't play against yourself!")
            return
        game.players[opponent.id] = "O"
        await ctx.send(f"🎮 Tic-Tac-Toe started between {ctx.author.mention} (X) and {opponent.mention} (O)!\nUse !move [row] [col] (0-2).")
    else:
        game.players[bot.user.id] = "O"
        await ctx.send(f"🎮 Tic-Tac-Toe started! {ctx.author.mention} (X) vs Bot (O).\nUse !move [row] [col] (0-2).\n{game.display_board()}")
    await ctx.send(game.display_board())

@bot.command()
async def move(ctx, row: int, col: int):
    global game
    if not game.game_active:
        await ctx.send("❌ No game in progress! Start one with !tictactoe.")
        return
    if ctx.author.id not in game.players and bot.user.id != ctx.author.id:
        await ctx.send("❌ You're not part of this game!")
        return
    if row not in [0, 1, 2] or col not in [0, 1, 2]:
        await ctx.send("❌ Invalid move! Use row and col between 0 and 2.")
        return
    if game.board[row][col] != " ":
        await ctx.send("❌ That spot is already taken!")
        return
    player = game.players.get(ctx.author.id)
    if not player and ctx.author.id != bot.user.id:
        await ctx.send("❌ It's not your turn or you're not a player!")
        return
    game.board[row][col] = player
    await ctx.send(f"✅ {ctx.author.mention} placed {player} at ({row}, {col})\n{game.display_board()}")
    winner = game.check_win()
    if winner:
        game.game_active = False
        await ctx.send(f"🏆 {ctx.author.mention if player == winner else 'Bot'} wins! Game over.")
        return
    elif game.is_full():
        game.game_active = False
        await ctx.send("🤝 It's a draw! Game over.")
        return
    if bot.user.id in game.players and game.current_player == "O":
        await asyncio.sleep(1)
        while True:
            bot_row = random.randint(0, 2)
            bot_col = random.randint(0, 2)
            if game.board[bot_row][bot_col] == " ":
                game.board[bot_row][bot_col] = "O"
                await ctx.send(f"🤖 Bot placed O at ({bot_row}, {bot_col})\n{game.display_board()}")
                break
        winner = game.check_win()
        if winner:
            game.game_active = False
            await ctx.send("🤖 Bot wins! Game over.")
            return
        elif game.is_full():
            game.game_active = False
            await ctx.send("🤝 It's a draw! Game over.")
            return
    game.current_player = "O" if player == "X" else "X"

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet(ctx, amount: int, lines: int = 1):
    """Command to place a bet and spin the slots."""
    global jackpot
    user = ctx.author.id
    if user in betting_cooldowns and datetime.utcnow() - betting_cooldowns[user] < timedelta(seconds=3):
        remaining = 3 - (datetime.utcnow() - betting_cooldowns[user]).total_seconds()
        await ctx.send(f"⏳ {ctx.author.mention}, wait {remaining:.1f} seconds between bets!")
        return
    betting_cooldowns[user] = datetime.utcnow()
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    if user not in user_winnings:
        user_winnings[user] = 0
    if user not in user_streaks:
        user_streaks[user] = {"wins": 0, "losses": 0}

    if amount < MIN_BET or amount > MAX_BET:
        await ctx.send(f'❌ Bet between ${MIN_BET} and ${MAX_BET}.')
        return
    if lines < 1 or lines > MAX_LINES:
        await ctx.send(f'❌ Choose 1 to {MAX_LINES} lines.')
        return
    total_bet = amount * lines
    if total_bet > user_balances[user]:
        await ctx.send(f'❌ Insufficient funds! Balance: ${user_balances[user]}.')
        return

    jackpot += int(0.05 * total_bet)  # Add 5% of total bet to jackpot
    user_balances[user] -= total_bet
    if amount >= 100:
        message = await ctx.send("🎰 Spinning...")
        await asyncio.sleep(1.0)
        await message.edit(content="🎰 Spinning... 🍒")
        await asyncio.sleep(0.5)
        await message.edit(content="🎰 Spinning... 🍒 🍋")
        await asyncio.sleep(0.5)
        await message.edit(content="🎰 Spinning... 🍒 🍋 🍇")
        await asyncio.sleep(0.5)
    slots = spin_slots(lines)
    winnings, jackpot_win, winning_lines = check_win(slots)

    if jackpot_win:
        winnings += jackpot
        jackpot = 1000  # Reset jackpot
        await ctx.send(f"🎉 {ctx.author.mention} won the jackpot of ${winnings}!")

    user_balances[user] += winnings
    if winnings > 0:
        user_winnings[user] += winnings
        user_streaks[user]["wins"] += 1
        user_streaks[user]["losses"] = 0
    else:
        user_streaks[user]["losses"] += 1
        user_streaks[user]["wins"] = 0

    earned_achievements = check_achievements(user, amount, winnings, jackpot_win, user_balances[user], user_streaks[user]["wins"])
    if winnings > 0:
        color = 0xf1c40f
        result_title = "🎰 Winner!"
        result_message = f"{random.choice(WIN_MESSAGES)}\nBet ${total_bet}, won ${winnings}!"
    else:
        color = 0x95a5a6
        result_title = "🎰 No Luck!"
        result_message = f"{random.choice(LOSS_MESSAGES)}\nBet ${total_bet}, lost."

    embed = discord.Embed(title=result_title, description=result_message, color=color)
    slot_display = format_slot_display(slots, winning_lines)
    embed.add_field(name="Your Spin", value=f"```\n{slot_display}\n```", inline=False)
    if user_streaks[user]["wins"] >= 3:
        embed.add_field(name="🔥 Win Streak", value=f"{user_streaks[user]['wins']} wins!", inline=True)
    elif user_streaks[user]["losses"] >= 5:
        embed.add_field(name="📉 Losing Streak", value=f"{user_streaks[user]['losses']} losses...", inline=True)
    embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
    if jackpot_win:
        embed.add_field(name="🎯 JACKPOT!", value="You broke the paradox!", inline=False)
    if earned_achievements:
        achievement_text = "\n".join([f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}** - {ACHIEVEMENTS[a]['description']}" for a in earned_achievements])
        embed.add_field(name="🏆 Achievements!", value=achievement_text, inline=False)
    embed.set_footer(text="Paradox Casino | Try again!")
    await ctx.send(embed=embed)

    levels_gained = add_xp(user, 10)  # Award 10 XP for betting
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user]}! +500 coins.")
    if user_streaks[user]["wins"] == 5:
        await ctx.send(f"🔥 {ctx.author.mention} broke the Paradox with 5 wins!")
    elif user_streaks[user]["losses"] == 7:
        await ctx.send(f"😱 {ctx.author.mention} hit 7 losses... take a break!")

@bot.command()
async def profile(ctx):
    """Command to display a user's profile."""
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    if user not in user_xp:
        user_xp[user] = 0
        user_levels[user] = 1
    level = user_levels[user]
    xp = user_xp[user]
    xp_needed = 100 * level
    vip = "Yes" if level >= 5 else "No"
    embed = discord.Embed(
        title=f"👤 {ctx.author.name}'s Profile",
        description=f"Level: {level}\nXP: {xp}/{xp_needed}\nVIP: {vip}\nBalance: ${user_balances[user]}",
        color=0x3498db
    )
    await ctx.send(embed=embed)

@bot.command()
async def jackpot(ctx):
    """Command to check the current jackpot amount."""
    embed = discord.Embed(
        title="🎰 Current Jackpot",
        description=f"The progressive jackpot is currently ${jackpot}.",
        color=0xf1c40f
    )
    embed.set_footer(text="Paradox Casino | Win it all!")
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def wheel(ctx, amount: int):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = STARTING_BALANCE
    if amount < MIN_BET or amount > MAX_BET:
        await ctx.send(f'❌ Bet between ${MIN_BET} and ${MAX_BET}.')
        return
    if amount > user_balances[user_id]:
        await ctx.send(f'❌ Insufficient funds! Balance: ${user_balances[user_id]}.')
        return
    user_balances[user_id] -= amount
    wheel = [(0, 20), (0.5, 15), (1, 30), (1.5, 15), (2, 10), (3, 7), (5, 2), (10, 1)]
    weights = [segment[1] for segment in wheel]
    result = random.choices(wheel, weights=weights, k=1)[0]
    multiplier = result[0]
    winnings = int(amount * multiplier)
    user_balances[user_id] += winnings
    wheel_msg = await ctx.send("🎡 Spinning Wheel...")
    wheel_emojis = ['💰', '✨', '💎', '🔔', '⭐️', '🎯', '🎪', '🎨']
    for _ in range(3):
        await asyncio.sleep(0.7)
        await wheel_msg.edit(content=f"🎡 Spinning Wheel... {random.choice(wheel_emojis)}")
    if multiplier == 0:
        result_text = f"❌ Lost ${amount}!"
        color = 0xe74c3c
    elif multiplier < 1:
        result_text = f"⚠️ Got ${winnings} (lost ${amount - winnings})."
        color = 0xe67e22
    elif multiplier == 1:
        result_text = f"🔄 Returned ${winnings}."
        color = 0x3498db
    else:
        result_text = f"✨ Won ${winnings} ({multiplier}x bet)!"
        color = 0x2ecc71
    embed = discord.Embed(title="🎡 Wheel Result", description=result_text, color=color)
    embed.add_field(name="Balance", value=f"${user_balances[user_id]}", inline=True)
    embed.set_footer(text="Paradox Casino | Spin again!")
    await ctx.send(embed=embed)

    levels_gained = add_xp(user_id, 5)  # Award 5 XP for wheel spin
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user_id]}! +500 coins.")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def rps(ctx, amount: int):
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    if amount < MIN_BET or amount > MAX_BET:
        await ctx.send(f'❌ Bet between ${MIN_BET} and ${MAX_BET}.')
        return
    if amount > user_balances[user]:
        await ctx.send(f'❌ Insufficient funds! Balance: ${user_balances[user]}.')
        return
    embed = discord.Embed(
        title="🪨📜✂️ Rock, Paper, Scissors!",
        description=f"{ctx.author.mention}, bet ${amount}. Choose by reacting!\n🪨 Rock\n📜 Paper\n✂️ Scissors",
        color=0x3498db
    )
    embed.set_footer(text="30 seconds to choose!")
    message = await ctx.send(embed=embed)
    await message.add_reaction("🪨")
    await message.add_reaction("📜")
    await message.add_reaction("✂️")
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["🪨", "📜", "✂️"] and reaction.message.id == message.id
    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        user_choice = {"🪨": "Rock", "📜": "Paper", "✂️": "Scissors"}[str(reaction.emoji)]
    except asyncio.TimeoutError:
        user_balances[user] -= amount
        embed = discord.Embed(
            title="🪨📜✂️ Time's Up!",
            description=f"{ctx.author.mention}, too slow! Lost ${amount}.",
            color=0xe74c3c
        )
        embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
        await ctx.send(embed=embed)
        return
    bot_choice = random.choice(["Rock", "Paper", "Scissors"])
    if user_choice == bot_choice:
        result = "Tie! Bet returned."
        color = 0x95a5a6
        winnings = amount
    elif (user_choice == "Rock" and bot_choice == "Scissors") or \
         (user_choice == "Paper" and bot_choice == "Rock") or \
         (user_choice == "Scissors" and bot_choice == "Paper"):
        result = f"Win! Earned ${amount}!"
        color = 0x2ecc71
        winnings = amount * 2
        user_streaks[user] = user_streaks.get(user, {})
        user_streaks[user]["rps_wins"] = user_streaks[user].get("rps_wins", 0) + 1
    else:
        result = f"Lose! Lost ${amount}."
        color = 0xe74c3c
        winnings = 0
        user_streaks[user] = user_streaks.get(user, {})
        user_streaks[user]["rps_wins"] = 0
    user_balances[user] -= amount
    user_balances[user] += winnings
    earned_achievements = check_achievements(user, amount, winnings if winnings > amount else 0, False, user_balances[user], 0, 0, 0, 0)
    embed = discord.Embed(
        title="🪨📜✂️ Result",
        description=f"{ctx.author.mention} chose **{user_choice}**\nBot chose **{bot_choice}**\n\n{result}",
        color=color
    )
    embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
    if earned_achievements:
        achievement_text = "\n".join([f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}** - {ACHIEVEMENTS[a]['description']}" for a in earned_achievements])
        embed.add_field(name="🏆 Achievements!", value=achievement_text, inline=False)
    embed.set_footer(text="Paradox Casino | Try again!")
    await ctx.send(embed=embed)

    levels_gained = add_xp(user, 5)  # Award 5 XP for RPS
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user]}! +500 coins.")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def blackjack(ctx, amount: int):
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    if amount < MIN_BET or amount > MAX_BET:
        await ctx.send(f'❌ Bet between ${MIN_BET} and ${MAX_BET}.')
        return
    if amount > user_balances[user]:
        await ctx.send(f'❌ Insufficient funds! Balance: ${user_balances[user]}.')
        return
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [rank + suit for suit in suits for rank in ranks]
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    def calculate_hand(hand):
        value = 0
        aces = 0
        for card in hand:
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
    player_value = calculate_hand(player_hand)
    dealer_value = calculate_hand(dealer_hand)
    embed = discord.Embed(
        title="♠♥♦♣ Blackjack",
        description=f"{ctx.author.mention}, bet ${amount}.\n\nYour Hand ({player_value}): {', '.join(player_hand)}\n"
                    f"Dealer's Hand: {dealer_hand[0]}, [Hidden]",
        color=0x3498db
    )
    embed.add_field(name="Options", value="✅ Hit, ❌ Stand", inline=False)
    embed.set_footer(text="30 seconds to choose!")
    message = await ctx.send(embed=embed)
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    while player_value < 21:
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id
        try:
            reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            user_balances[user] -= amount
            embed = discord.Embed(
                title="♠♥♦♣ Time's Up!",
                description=f"{ctx.author.mention}, too slow! Lost ${amount}.",
                color=0xe74c3c
            )
            embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
            await ctx.send(embed=embed)
            return
        if str(reaction.emoji) == "❌":
            break
        player_hand.append(deck.pop())
        player_value = calculate_hand(player_hand)
        embed = discord.Embed(
            title="♠♥♦♣ Blackjack",
            description=f"{ctx.author.mention}, bet ${amount}.\n\nYour Hand ({player_value}): {', '.join(player_hand)}\n"
                        f"Dealer's Hand: {dealer_hand[0]}, [Hidden]",
            color=0x3498db
        )
        if player_value < 21:
            embed.add_field(name="Options", value="✅ Hit, ❌ Stand", inline=False)
            embed.set_footer(text="30 seconds to choose!")
            message = await ctx.send(embed=embed)
            await message.add_reaction("✅")
            await message.add_reaction("❌")
        else:
            break
    if player_value > 21:
        user_balances[user] -= amount
        embed = discord.Embed(
            title="♠♥♦♣ Bust!",
            description=f"{ctx.author.mention}, busted with {player_value}! Lost ${amount}.",
            color=0xe74c3c
        )
        embed.add_field(name="Your Hand", value=', '.join(player_hand), inline=False)
        embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
        await ctx.send(embed=embed)
        return
    while dealer_value < 17:
        dealer_hand.append(deck.pop())
        dealer_value = calculate_hand(dealer_hand)
    if dealer_value > 21:
        result = "Dealer busts! Win ${amount}!"
        color = 0x2ecc71
        winnings = amount * 2
    elif player_value > dealer_value:
        result = f"Win! {player_value} beats {dealer_value}. Earned ${amount}!"
        color = 0x2ecc71
        winnings = amount * 2
    elif player_value == dealer_value:
        result = "Tie! Bet returned."
        color = 0x95a5a6
        winnings = amount
    else:
        result = f"Lose! {dealer_value} beats {player_value}. Lost ${amount}."
        color = 0xe74c3c
        winnings = 0
    user_balances[user] -= amount
    user_balances[user] += winnings
    user_streaks[user] = user_streaks.get(user, {})
    user_streaks[user]["blackjack_wins"] = user_streaks[user].get("blackjack_wins", 0) + (1 if winnings > amount else 0)
    earned_achievements = check_achievements(user, amount, winnings if winnings > amount else 0, False, user_balances[user], 0, 0, 0, 0)
    embed = discord.Embed(
        title="♠♥♦♣ Result",
        description=f"{ctx.author.mention}\n\n{result}",
        color=color
    )
    embed.add_field(name="Your Hand", value=f"{', '.join(player_hand)} ({player_value})", inline=False)
    embed.add_field(name="Dealer's Hand", value=f"{', '.join(dealer_hand)} ({dealer_value})", inline=False)
    embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
    if earned_achievements:
        achievement_text = "\n".join([f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}** - {ACHIEVEMENTS[a]['description']}" for a in earned_achievements])
        embed.add_field(name="🏆 Achievements!", value=achievement_text, inline=False)
    embed.set_footer(text="Paradox Casino | Try again!")
    await ctx.send(embed=embed)

    levels_gained = add_xp(user, 5)  # Award 5 XP for blackjack
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user]}! +500 coins.")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def trivia(ctx):
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    question_data = random.choice(TRIVIA_QUESTIONS)
    question = question_data["question"]
    options = question_data["options"]
    correct_answer = question_data["correct"]
    embed = discord.Embed(
        title="❓ Trivia Challenge",
        description=f"{ctx.author.mention}, win $50!\n\n**Question:** {question}\n\n"
                    f"1️⃣ {options[0]}\n2️⃣ {options[1]}\n3️⃣ {options[2]}\n4️⃣ {options[3]}",
        color=0x9b59b6
    )
    embed.set_footer(text="30 seconds to answer!")
    message = await ctx.send(embed=embed)
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    for reaction in reactions:
        await message.add_reaction(reaction)
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == message.id
    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        user_answer = reactions.index(str(reaction.emoji))
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="❓ Time's Up!",
            description=f"{ctx.author.mention}, too slow!",
            color=0xe74c3c
        )
        embed.add_field(name="Correct Answer", value=options[correct_answer], inline=False)
        await ctx.send(embed=embed)
        return
    if user_answer == correct_answer:
        user_balances[user] += 50
        user_streaks[user] = user_streaks.get(user, {})
        user_streaks[user]["trivia_correct"] = user_streaks[user].get("trivia_correct", 0) + 1
        earned_achievements = check_achievements(user, 0, 50, False, user_balances[user], 0, user_streaks[user].get("trivia_correct", 0), 0, 0)
        embed = discord.Embed(
            title="❓ Correct!",
            description=f"{ctx.author.mention}, right! Earned $50!",
            color=0x2ecc71
        )
    else:
        embed = discord.Embed(
            title="❓ Incorrect!",
            description=f"{ctx.author.mention}, wrong!",
            color=0xe74c3c
        )
        embed.add_field(name="Correct Answer", value=options[correct_answer], inline=False)
    embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
    if earned_achievements:
        achievement_text = "\n".join([f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}** - {ACHIEVEMENTS[a]['description']}" for a in earned_achievements])
        embed.add_field(name="🏆 Achievements!", value=achievement_text, inline=False)
    embed.set_footer(text="Paradox Casino | Try again!")
    await ctx.send(embed=embed)

    levels_gained = add_xp(user, 5)  # Award 5 XP for trivia
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user]}! +500 coins.")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def hangman(ctx):
    global hangman_game
    if hangman_game.active:
        await ctx.send("❌ A game is in progress! Use !guess.")
        return
    hangman_game = HangmanGame()
    hangman_game.active = True
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    word_display = ' '.join(letter if letter in hangman_game.guessed else '_' for letter in hangman_game.word)
    embed = discord.Embed(
        title="🔤 Hangman",
        description=f"{ctx.author.mention}, guess the word!\n\n**Word**: {word_display}\n"
                    f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\n"
                    f"Guessed: {', '.join(sorted(hangman_game.guessed)) if hangman_game.guessed else 'None'}",
        color=0xffb6c1
    )
    embed.add_field(name="How to Play", value="Use !guess [letter].", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def guess(ctx, letter: str):
    global hangman_game
    if not hangman_game.active:
        await ctx.send("❌ No game! Start with !hangman.")
        return
    user = ctx.author.id
    letter = letter.upper()
    if len(letter) != 1 or not letter.isalpha():
        await ctx.send("❌ Guess a single letter (A-Z)!")
        return
    if letter in hangman_game.guessed:
        await ctx.send(f"❌ Already guessed '{letter}'!")
        return
    hangman_game.guessed.add(letter)
    if letter not in hangman_game.word:
        hangman_game.wrong_guesses += 1
    word_display = ' '.join(letter if letter in hangman_game.guessed else '_' for letter in hangman_game.word)
    embed = discord.Embed(
        title="🔤 Hangman",
        description=f"{ctx.author.mention}\n\n**Word**: {word_display}\n"
                    f"{HANGMAN_STAGES[hangman_game.wrong_guesses]}\n"
                    f"Guessed: {', '.join(sorted(hangman_game.guessed))}",
        color=0xffb6c1
    )
    if hangman_game.wrong_guesses >= 6:
        hangman_game.active = False
        embed.description += f"\n\n**Game Over!** Lost. Word was **{hangman_game.word}**."
        embed.color = 0xe74c3c
    elif all(letter in hangman_game.guessed for letter in hangman_game.word):
        hangman_game.active = False
        user_balances[user] += 25
        hangman_game.hangman_wins += 1
        earned_achievements = check_achievements(user, 0, 25, False, user_balances[user], 0, 0, hangman_game.hangman_wins, 0)
        embed.description += f"\n\n**Win!** Word was **{hangman_game.word}**. Earned $25!"
        embed.color = 0x2ecc71
        embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
    else:
        embed.add_field(name="Keep Guessing", value="Use !guess [letter].", inline=False)
    if earned_achievements:
        achievement_text = "\n".join([f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}** - {ACHIEVEMENTS[a]['description']}" for a in earned_achievements])
        embed.add_field(name="🏆 Achievements!", value=achievement_text, inline=False)
    embed.set_footer(text="Paradox Casino | Guess again!")
    await ctx.send(embed=embed)

    levels_gained = add_xp(user, 5)  # Award 5 XP for hangman
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user]}! +500 coins.")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def guessnumber(ctx):
    global number_guess_game
    if number_guess_game.active:
        await ctx.send("❌ A game is in progress! Use !guessnum.")
        return
    number_guess_game = NumberGuessGame()
    number_guess_game.active = True
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    embed = discord.Embed(
        title="🔢 Number Guessing",
        description=f"{ctx.author.mention}, guess 1-100. {number_guess_game.guesses_left} guesses to win $50!",
        color=0x00CED1
    )
    embed.add_field(name="How to Play", value="Use !guessnum [number].", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def guessnum(ctx, guess: int):
    global number_guess_game
    if not number_guess_game.active:
        await ctx.send("❌ No game! Start with !guessnumber.")
        return
    user = ctx.author.id
    if guess < 1 or guess > 100:
        await ctx.send("❌ Guess 1-100!")
        return
    number_guess_game.guesses_left -= 1
    embed = discord.Embed(
        title="🔢 Number Guessing",
        description=f"{ctx.author.mention}, guessed {guess}.",
        color=0x00CED1
    )
    if guess == number_guess_game.number:
        user_balances[user] += 50
        embed.description += f"\n\n**Correct!** Number was {number_guess_game.number}. Won $50!"
        embed.color = 0x2ecc71
        embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
        number_guess_game.active = False
    elif number_guess_game.guesses_left <= 0:
        embed.description += f"\n\n**Game Over!** Out of guesses. Number was {number_guess_game.number}."
        embed.color = 0xe74c3c
        number_guess_game.active = False
    else:
        hint = "Too high!" if guess > number_guess_game.number else "Too low!"
        embed.description += f"\n{hint} {number_guess_game.guesses_left} guesses left."
        embed.add_field(name="Keep Guessing", value="Use !guessnum [number].", inline=False)
    earned_achievements = check_achievements(user, 0, 50 if guess == number_guess_game.number else 0, False, user_balances[user], 0, 0, 0, 21 - number_guess_game.guesses_left)
    if earned_achievements:
        achievement_text = "\n".join([f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}** - {ACHIEVEMENTS[a]['description']}" for a in earned_achievements])
        embed.add_field(name="🏆 Achievements!", value=achievement_text, inline=False)
    embed.set_footer(text="Paradox Casino | Guess again!")
    await ctx.send(embed=embed)

    levels_gained = add_xp(user, 5)  # Award 5 XP for number guessing
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user]}! +500 coins.")

@bot.command()
async def balance(ctx):
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    embed = discord.Embed(
        title="💰 Balance",
        description=f"{ctx.author.mention}, balance: ${user_balances[user]}",
        color=0x2ecc71
    )
    if user in user_winnings:
        embed.add_field(name="Total Winnings", value=f"${user_winnings.get(user, 0)}", inline=True)
    embed.set_footer(text="Paradox Casino | Mysterious odds")
    await ctx.send(embed=embed)

@bot.command()
async def daily(ctx):
    """Command to claim a daily reward with VIP multiplier."""
    user = ctx.author.id
    now = datetime.utcnow()
    if user not in user_balances:
        user_balances[user] = STARTING_BALANCE
    if user not in user_daily_claims or now - user_daily_claims[user] >= timedelta(days=1):
        base_reward = DAILY_REWARD
        if user_levels.get(user, 1) >= 5:  # VIP check (level 5+ gets 1.5x)
            base_reward = int(base_reward * 1.5)
        streak_bonus = 0
        if user in user_daily_claims:
            yesterday = now - timedelta(days=1)
            day_before = now - timedelta(days=2)
            if day_before <= user_daily_claims[user] <= yesterday + timedelta(hours=2):
                user_streaks[user] = user_streaks.get(user, {})
                user_streaks[user]["daily"] = user_streaks[user].get("daily", 0) + 1
                streak_days = user_streaks[user]["daily"]
                if streak_days >= 7:
                    streak_bonus = DAILY_REWARD
                    if "daily_streak" not in user_achievements.get(user, set()):
                        if user not in user_achievements:
                            user_achievements[user] = set()
                        user_achievements[user].add("daily_streak")
                else:
                    streak_bonus = streak_days * 50
            else:
                if user in user_streaks and "daily" in user_streaks[user]:
                    user_streaks[user]["daily"] = 0
        else:
            user_streaks[user] = user_streaks.get(user, {})
            user_streaks[user]["daily"] = 1
        total_reward = base_reward + streak_bonus
        user_balances[user] += total_reward
        user_daily_claims[user] = now
        embed = discord.Embed(
            title="💸 Daily Reward!",
            description=f"{ctx.author.mention} received ${base_reward}!",
            color=0x2ecc71
        )
        if streak_bonus > 0:
            streak_days = user_streaks[user]["daily"]
            embed.add_field(name=f"🔥 {streak_days}-Day Streak", value=f"+${streak_bonus}", inline=False)
            embed.add_field(name="Total Reward", value=f"${total_reward}", inline=True)
            if streak_days == 7 and "daily_streak" in user_achievements.get(user, set()):
                achievement = ACHIEVEMENTS["daily_streak"]
                embed.add_field(name="🏆 Achievement!", value=f"{achievement['emoji']} **{achievement['name']}** - {achievement['description']}", inline=False)
        embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
        embed.set_footer(text="Paradox Casino | Return daily!")
        await ctx.send(embed=embed)
    else:
        time_left = timedelta(days=1) - (now - user_daily_claims[user])
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        embed = discord.Embed(
            title="⏳ Daily Claimed",
            description=f"{ctx.author.mention}, already claimed!",
            color=0xe74c3c
        )
        embed.add_field(name="Next Reward", value=f"{hours}h {minutes}m {seconds}s", inline=False)
        embed.set_footer(text="Paradox Casino | Time is a paradox")
        await ctx.send(embed=embed)

    levels_gained = add_xp(user, 5)  # Award 5 XP for daily claim
    if levels_gained > 0:
        await ctx.send(f"🎉 {ctx.author.mention} leveled up to level {user_levels[user]}! +500 coins.")

@bot.command()
async def top(ctx):
    if not user_winnings:
        await ctx.send('🏆 No winnings yet! Start playing!')
        return
    sorted_winners = sorted(user_winnings.items(), key=lambda x: x[1], reverse=True)[:5]
    embed = discord.Embed(
        title="🏆 Leaderboard - Top Winners",
        description="Biggest winners in Paradox Casino!",
        color=0xf1c40f
    )
    for i, (user_id, winnings) in enumerate(sorted_winners, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        try:
            user = await bot.fetch_user(user_id)
            username = user.name
        except discord.errors.HTTPException as e:
            if e.status == 429:
                username = f"User {user_id} (Rate Limited)"
            else:
                username = f"User {user_id}"
        except:
            username = f"User {user_id}"
        embed.add_field(name=f"{medal} #{i}: {username}", value=f"${winnings}", inline=False)
    embed.set_footer(text="Paradox Casino | Reach the top!")
    await ctx.send(embed=embed)

@bot.command()
async def achievements(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = target.id
    if user_id not in user_achievements or not user_achievements[user_id]:
        await ctx.send(f"{target.mention} has no achievements yet! Start playing!")
        return
    embed = discord.Embed(
        title=f"🏆 {target.name}'s Achievements",
        description="Earned in Paradox Casino",
        color=0x9b59b6
    )
    earned = user_achievements[user_id]
    for achievement_id, details in ACHIEVEMENTS.items():
        status = "✅" if achievement_id in earned else "❌"
        embed.add_field(name=f"{details['emoji']} {details['name']} {status}", value=details['description'], inline=False)
    embed.set_footer(text="Paradox Casino | Collect them all!")
    await ctx.send(embed=embed)

@bot.command()
async def give(ctx, recipient: discord.Member, amount: int):
    sender_id = ctx.author.id
    recipient_id = recipient.id
    if sender_id not in user_balances:
        user_balances[sender_id] = STARTING_BALANCE
    if recipient_id not in user_balances:
        user_balances[recipient_id] = STARTING_BALANCE
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    if sender_id == recipient_id:
        await ctx.send("❓ Can't give to yourself!")
        return
    if amount > user_balances[sender_id]:
        await ctx.send(f"❌ Insufficient funds! Balance: ${user_balances[sender_id]}.")
        return
    user_balances[sender_id] -= amount
    user_balances[recipient_id] += amount
    embed = discord.Embed(
        title="💸 Money Transfer",
        description=f"{ctx.author.mention} gave ${amount} to {recipient.mention}!",
        color=0x2ecc71
    )
    embed.add_field(name=f"{ctx.author.name}'s Balance", value=f"${user_balances[sender_id]}", inline=True)
    embed.add_field(name=f"{recipient.name}'s Balance", value=f"${user_balances[recipient_id]}", inline=True)
    embed.set_footer(text="Paradox Casino | Share the wealth")
    await ctx.send(embed=embed)

@bot.command(name="paradox")
async def paradox_help(ctx):
    embed = discord.Embed(
        title="🎰 Paradox Casino Machine - Commands",
        description="Enjoy these games in the mysterious Paradox Casino!",
        color=0x3498db
    )
    embed.add_field(name="!bet [amount] [lines]", value="Bet on the slot machine (1-3 lines)", inline=False)
    embed.add_field(name="!balance", value="Check your balance", inline=False)
    embed.add_field(name="!daily", value="Claim daily reward with streak bonuses", inline=False)
    embed.add_field(name="!wheel [amount]", value="Spin the wheel of fortune", inline=False)
    embed.add_field(name="!top", value="View the leaderboard", inline=False)
    embed.add_field(name="!achievements [user]", value="View achievements", inline=False)
    embed.add_field(name="!give [user] [amount]", value="Give coins to another user", inline=False)
    embed.add_field(name="!tictactoe [user]", value="Start a tic-tac-toe game (optional opponent)", inline=False)
    embed.add_field(name="!move [row] [col]", value="Make a move in tic-tac-toe (0-2)", inline=False)
    embed.add_field(name="!rps [amount]", value="Play Rock, Paper, Scissors with a bet", inline=False)
    embed.add_field(name="!blackjack [amount]", value="Play Blackjack against the dealer", inline=False)
    embed.add_field(name="!trivia", value="Answer a trivia question for coins", inline=False)
    embed.add_field(name="!hangman", value="Play Hangman to guess a word", inline=False)
    embed.add_field(name="!guess [letter]", value="Guess a letter in Hangman", inline=False)
    embed.add_field(name="!guessnumber", value="Start a number guessing game", inline=False)
    embed.add_field(name="!guessnum [number]", value="Guess a number (1-100)", inline=False)
    embed.add_field(name="!profile", value="View your level, XP, and VIP status", inline=False)
    embed.add_field(name="!jackpot", value="Check the current progressive jackpot", inline=False)
    embed.add_field(name="!paradox", value="Show this help message", inline=False)
    embed.set_footer(text="Paradox Casino | Where probability defies reality")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    print(f"Error for {ctx.author}: {error}")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing argument! Type `!paradox` for help.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument! Type `!paradox` for help.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Wait {error.retry_after:.1f} seconds.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found!")
    else:
        await ctx.send("❌ An error occurred. Check logs!")

def load_data():
    """Load user data from JSON file on startup."""
    global jackpot, user_balances, user_winnings, user_daily_claims, user_streaks, user_achievements, betting_cooldowns, user_xp, user_levels
    try:
        with open('user_data.json', 'r') as f:
            data = json.load(f)
            jackpot = data.get('jackpot', 1000)
            user_balances = {int(k): v for k, v in data.get('balances', {}).items()}
            user_winnings = {int(k): v for k, v in data.get('winnings', {}).items()}
            user_daily_claims = {int(k): datetime.fromisoformat(v) for k, v in data.get('daily_claims', {}).items()}
            user_streaks = {int(k): v for k, v in data.get('streaks', {}).items()}
            user_achievements = {int(k): set(v) for k, v in data.get('achievements', {}).items()}
            betting_cooldowns = {int(k): datetime.fromisoformat(v) for k, v in data.get('cooldowns', {}).items()}
            user_xp = {int(k): v for k, v in data.get('xp', {}).items()}
            user_levels = {int(k): v for k, v in data.get('levels', {}).items()}
    except FileNotFoundError:
        print("No data found, starting fresh.")

async def save_data():
    """Periodically save user data to JSON file."""
    while True:
        data = {
            'jackpot': jackpot,
            'balances': user_balances,
            'winnings': user_winnings,
            'daily_claims': {k: v.isoformat() for k, v in user_daily_claims.items()},
            'streaks': user_streaks,
            'achievements': {k: list(v) for k, v in user_achievements.items()},
            'cooldowns': {k: v.isoformat() for k, v in betting_cooldowns.items()},
            'xp': user_xp,
            'levels': user_levels
        }
        with open('user_data.json', 'w') as f:
            json.dump(data, f)
        print(f"Saved data at {datetime.now()}")
        await asyncio.sleep(300)

async def keep_alive():
    while True:
        print(f"Bot alive at {datetime.now()}")
        await asyncio.sleep(300)

async def start_bot():
    try:
        print("Starting bot...")
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN not set!")
        await bot.start(token)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print(f"Rate limited! Waiting {e.response.headers.get('Retry-After', 5)}s...")
            await asyncio.sleep(float(e.response.headers.get('Retry-After', 5)))
            await start_bot()
        else:
            print(f"HTTPException: {e}")
            raise e
    except KeyboardInterrupt:
        print("Stopped by user. Cleaning up...")
        await bot.close()
    except Exception as e:
        print(f"Unexpected error: {e}")
        await bot.close()

if __name__ == "__main__":
    load_data()
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    loop.create_task(keep_alive())
    loop.create_task(save_data())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        loop.create_task(bot.close())
        for task in asyncio.all_tasks(loop):
            if not task.done():
                task.cancel()
        loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

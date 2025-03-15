import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
import os
import json
from flask import Flask, request
import threading

# Flask setup for UptimeRobot
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

SLOTS = ['🍒', '🍋', '🍇', '🔔', '💎', '7️⃣']

user_balances = {}
user_winnings = {}
user_daily_claims = {}
user_streaks = {}
betting_cooldowns = {}
user_achievements = {}

WIN_MESSAGES = [
    "You're on fire! 🔥", "Lucky spin! 🍀", "The Paradox Casino is feeling generous today! 💸",
    "Winner winner chicken dinner! 🍗", "Cha-ching! 💰", "The odds are in your favor! ✨",
    "Jackpot energy! ⚡", "Your luck is through the roof! 🚀"
]

LOSS_MESSAGES = [
    "Better luck next time! 🎲", "So close, yet so far! 📏", "The Paradox machines are being stubborn today! 😤",
    "Don't give up! Your big win is coming! ✨", "That's how they get you! 🎯", "The house always wins... or does it? 🤔",
    "Time to break the losing paradox! 🔄", "Fortune favors the persistent! 🌟"
]

ACHIEVEMENTS = {
    "first_win": {"name": "Paradox Novice", "description": "Win your first slot game", "emoji": "🏆"},
    "big_winner": {"name": "Paradox Master", "description": "Win over 1000 coins in a single spin", "emoji": "💎"},
    "jackpot": {"name": "Paradox Breaker", "description": "Hit the jackpot", "emoji": "🎯"},
    "broke": {"name": "Rock Bottom", "description": "Lose all your money", "emoji": "📉"},
    "comeback": {"name": "Phoenix Rising", "description": "Win after having less than 100 coins", "emoji": "🔄"},
    "high_roller": {"name": "Paradox Whale", "description": "Bet the maximum amount", "emoji": "💵"},
    "daily_streak": {"name": "Time Traveler", "description": "Claim rewards for 7 days in a row", "emoji": "⏰"},
    "legendary": {"name": "Legendary Gambler", "description": "Win 5 times in a row", "emoji": "👑"}
}

# Utility functions
def spin_slots(lines):
    return [[random.choice(SLOTS) for _ in range(3)] for _ in range(lines)]

def check_win(slots):
    winnings = 0
    jackpot = False
    winning_lines = []
    for i, line in enumerate(slots):
        if line.count(line[0]) == 3:
            multiplier = JACKPOT_MULTIPLIER if line[0] == JACKPOT_SYMBOL else 1
            line_win = 100 * multiplier
            winnings += line_win
            winning_lines.append((i, line_win))
            if line[0] == JACKPOT_SYMBOL:
                jackpot = True
    return winnings, jackpot, winning_lines

def format_slot_display(slots, winning_lines=None):
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

def check_achievements(user, bet_amount, win_amount, jackpot, balance, win_streak=0):
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
    return achievements_earned

# Tic-Tac-Toe game setup
tictactoe_games = {}  # Dictionary to store games by channel ID

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

@bot.command()
async def tictactoe(ctx, opponent: discord.Member = None):
    channel_id = ctx.channel.id
    if channel_id in tictactoe_games:
        await ctx.send("❌ A game is already in progress in this channel!")
        return
    game = TicTacToe()
    tictactoe_games[channel_id] = game
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
    channel_id = ctx.channel.id
    if channel_id not in tictactoe_games:
        await ctx.send("❌ No game in progress! Start one with !tictactoe.")
        return
    game = tictactoe_games[channel_id]
    if not game.game_active:
        await ctx.send("❌ The game is not active!")
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
        del tictactoe_games[channel_id]
        await ctx.send(f"🏆 {ctx.author.mention if player == winner else 'Bot'} wins! Game over.")
        return
    elif game.is_full():
        game.game_active = False
        del tictactoe_games[channel_id]
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
            del tictactoe_games[channel_id]
            await ctx.send("🤖 Bot wins! Game over.")
            return
        elif game.is_full():
            game.game_active = False
            del tictactoe_games[channel_id]
            await ctx.send("🤝 It's a draw! Game over.")
            return
    game.current_player = "O" if player == "X" else "X"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="!paradox for commands"))
    bot.loop.create_task(casino_announcements())

async def casino_announcements():
    await bot.wait_until_ready()
    announcements = [
        {"title": "🎰 Feeling Lucky?", "description": f"The Paradox slots are hot! Try your luck with `!bet` and aim for the {JACKPOT_SYMBOL} jackpot!"},
        {"title": "💰 Daily Rewards", "description": "Don't forget to claim your `!daily` reward! Consecutive days build up your streak bonus!"},
        {"title": "🎡 Wheel of Fortune", "description": "Spin the `!wheel` for a chance to multiply your coins!"},
        {"title": "🪨📜✂️ Rock-Paper-Scissors", "description": "Challenge the bot with `!rps` to double your bet!"}
    ]
    announcement_index = 0
    while not bot.is_closed():
        for guild in bot.guilds:
            if guild.system_channel:
                current_announcement = announcements[announcement_index]
                embed = discord.Embed(
                    title=current_announcement["title"],
                    description=current_announcement["description"],
                    color=0xf1c40f
                )
                embed.set_footer(text="Paradox Casino Machine | Type !paradox for help")
                try:
                    await guild.system_channel.send(embed=embed)
                except:
                    pass
        announcement_index = (announcement_index + 1) % len(announcements)
        print(f"Sent announcement at {datetime.now()}")
        await asyncio.sleep(3600 * 12)

@bot.command()
async def balance(ctx):
    user = ctx.author.id
    if user not in user_balances:
        user_balances[user] = 1000
    embed = discord.Embed(
        title="💰 Paradox Balance",
        description=f"{ctx.author.mention}, your balance is: ${user_balances[user]}",
        color=0x2ecc71
    )
    if user in user_winnings:
        embed.add_field(name="Total Winnings", value=f"${user_winnings.get(user, 0)}", inline=True)
    embed.set_footer(text="Paradox Casino Machine | The odds are mysterious")
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def bet(ctx, amount: int, lines: int = 1):
    user = ctx.author.id
    if user in betting_cooldowns and datetime.utcnow() - betting_cooldowns[user] < timedelta(seconds=3):
        remaining = 3 - (datetime.utcnow() - betting_cooldowns[user]).total_seconds()
        await ctx.send(f"⏳ {ctx.author.mention}, please wait {remaining:.1f} seconds between bets!")
        return
    betting_cooldowns[user] = datetime.utcnow()
    if user not in user_balances:
        user_balances[user] = 1000
    if user not in user_winnings:
        user_winnings[user] = 0
    if user not in user_streaks:
        user_streaks[user] = {"wins": 0, "losses": 0}
    if amount < MIN_BET or amount > MAX_BET:
        await ctx.send(f'❌ Invalid bet! Bet between ${MIN_BET} and ${MAX_BET}.')
        return
    if lines < 1 or lines > MAX_LINES:
        await ctx.send(f'❌ Invalid number of lines! Choose between 1 and {MAX_LINES}.')
        return
    total_bet = amount * lines
    if total_bet > user_balances[user]:
        await ctx.send(f'❌ Insufficient funds! Your balance is ${user_balances[user]}.')
        return
    if amount >= 100:
        embed = discord.Embed(title="🎰 Paradox Machine", description="Spinning...", color=0xf1c40f)
        message = await ctx.send(embed=embed)
        for _ in range(5):
            await asyncio.sleep(0.5)
            fake_slots = [[random.choice(SLOTS) for _ in range(3)] for _ in range(lines)]
            fake_display = '\n'.join([' '.join(line) for line in fake_slots])
            embed.description = f"```\n{fake_display}\n```"
            await message.edit(embed=embed)
        await asyncio.sleep(1.0)
    slots = spin_slots(lines)
    winnings, jackpot, winning_lines = check_win(slots)
    user_balances[user] -= total_bet
    user_balances[user] += winnings
    if winnings > 0:
        user_winnings[user] += winnings
        user_streaks[user]["wins"] += 1
        user_streaks[user]["losses"] = 0
    else:
        user_streaks[user]["losses"] += 1
        user_streaks[user]["wins"] = 0
    earned_achievements = check_achievements(user, amount, winnings, jackpot, user_balances[user], user_streaks[user]["wins"])
    slot_display = format_slot_display(slots, winning_lines)
    if winnings > 0:
        embed = discord.Embed(
            title="🎰 Paradox Winner!",
            description=f"{random.choice(WIN_MESSAGES)}\nBet ${total_bet}, won ${winnings}!",
            color=0xf1c40f
        )
    else:
        embed = discord.Embed(
            title="🎰 Paradox Says No!",
            description=f"{random.choice(LOSS_MESSAGES)}\nBet ${total_bet}, lost.",
            color=0x95a5a6
        )
    embed.add_field(name="Your Spin", value=f"```\n{slot_display}\n```", inline=False)
    if user_streaks[user]["wins"] >= 3:
        embed.add_field(name="🔥 Win Streak", value=f"{user_streaks[user]['wins']} wins in a row!", inline=True)
    elif user_streaks[user]["losses"] >= 5:
        embed.add_field(name="📉 Losing Streak", value=f"{user_streaks[user]['losses']} losses in a row... 😢", inline=True)
    embed.add_field(name="Balance", value=f"${user_balances[user]}", inline=True)
    if jackpot:
        embed.add_field(name="🎯 PARADOX JACKPOT!", value="You've broken the paradox! The big win is yours!", inline=False)
    if earned_achievements:
        achievement_text = "\n".join([
            f"{ACHIEVEMENTS[a]['emoji']} **{ACHIEVEMENTS[a]['name']}** - {ACHIEVEMENTS[a]['description']}"
            for a in earned_achievements
        ])
        embed.add_field(name="🏆 Achievements Unlocked!", value=achievement_text, inline=False)
    embed.set_footer(text="Paradox Casino Machine | Where luck defies logic")
    if amount >= 100:
        await message.edit(embed=embed)
    else:
        await ctx.send(embed=embed)
    if user_streaks[user]["wins"] == 5:
        await ctx.send(f"🔥 **INCREDIBLE!** {ctx.author.mention} has broken the Paradox with 5 wins in a row! 🔥")
    elif user_streaks[user]["losses"] == 7:
        await ctx.send(f"😱 {ctx.author.mention} might want to take a break from the Paradox machines... That's 7 losses in a row!")

@bot.command()
async def daily(ctx):
    user = ctx.author.id
    now = datetime.utcnow()
    if user not in user_balances:
        user_balances[user] = 1000
    if user in user_daily_claims and now - user_daily_claims[user] < timedelta(days=1):
        time_left = timedelta(days=1) - (now - user_daily_claims[user])
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        embed = discord.Embed(
            title="⏳ Daily Paradox Reward Already Claimed",
            description=f"{ctx.author.mention}, you've already claimed your daily reward!",
            color=0xe74c3c
        )
        embed.add_field(name="Time until next reward", value=f"{hours}h {minutes}m {seconds}s", inline=False)
        embed.set_footer(text="Paradox Casino Machine | Time is a paradox")
        await ctx.send(embed=embed)
    else:
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
                    streak_bonus = (streak_days * 50)
            else:
                if user in user_streaks and "daily" in user_streaks[user]:
                    user_streaks[user]["daily"] = 0
        else:
            user_streaks[user] = user_streaks.get(user, {})
            user_streaks[user]["daily"] = 1
        total_reward = DAILY_REWARD + streak_bonus
        user_balances[user] = user_balances.get(user, 1000) + total_reward
        user_daily_claims[user] = now
        embed = discord.Embed(
            title="💸 Daily Paradox Reward Claimed!",
            description=f"{ctx.author.mention} received ${DAILY_REWARD}!",
            color=0x2ecc71
        )
        if streak_bonus > 0:
            streak_days = user_streaks[user]["daily"]
            embed.add_field(name=f"🔥 {streak_days}-Day Streak Bonus", value=f"+${streak_bonus}", inline=False)
            embed.add_field(name="Total Reward", value=f"${total_reward}", inline=True)
            if streak_days == 7 and "daily_streak" in user_achievements.get(user, set()):
                achievement = ACHIEVEMENTS["daily_streak"]
                embed.add_field(
                    name=f"🏆 Achievement Unlocked!",
                    value=f"{achievement['emoji']} **{achievement['name']}** - {achievement['description']}",
                    inline=False
                )
        embed.add_field(name="New Balance", value=f"${user_balances[user]}", inline=True)
        embed.set_footer(text="Paradox Casino Machine | Return daily for more rewards")
        await ctx.send(embed=embed)

@bot.command()
async def top(ctx):
    if not user_winnings:
        await ctx.send('🏆 No winnings recorded yet! Start playing the Paradox machines!')
        return
    sorted_winners = sorted(user_winnings.items(), key=lambda x: x[1], reverse=True)[:5]
    embed = discord.Embed(
        title="🏆 Paradox Leaderboard - Top Winners 🏆",
        description="The biggest winners in the Paradox Casino!",
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
        embed.add_field(
            name=f"{medal} #{i}: {username}",
            value=f"${winnings}",
            inline=False
        )
    embed.set_footer(text="Paradox Casino Machine | Will you reach the top?")
    await ctx.send(embed=embed)

@bot.command()
async def achievements(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = target.id
    if user_id not in user_achievements or not user_achievements[user_id]:
        await ctx.send(f"{target.mention} hasn't earned any Paradox achievements yet! Start playing to earn some.")
        return
    embed = discord.Embed(
        title=f"🏆 {target.name}'s Paradox Achievements",
        description="Achievements earned in the Paradox Casino",
        color=0x9b59b6
    )
    earned = user_achievements[user_id]
    for achievement_id, details in ACHIEVEMENTS.items():
        status = "✅" if achievement_id in earned else "❌"
        embed.add_field(
            name=f"{details['emoji']} {details['name']} {status}",
            value=details['description'],
            inline=False
        )
    embed.set_footer(text="Paradox Casino Machine | Collect them all!")
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def wheel(ctx, amount: int):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000
    if amount < MIN_BET or amount > MAX_BET:
        await ctx.send(f'❌ Invalid bet! Bet between ${MIN_BET} and ${MAX_BET}.')
        return
    if amount > user_balances[user_id]:
        await ctx.send(f'❌ Insufficient funds! Your balance is ${user_balances[user_id]}.')
        return
    user_balances[user_id] -= amount
    wheel = [
        (0, 20), (0.5, 15), (1, 30), (1.5, 15), (2, 10), (3, 7), (5, 2), (10, 1)
    ]
    weights = [segment[1] for segment in wheel]
    result = random.choices(wheel, weights=weights, k=1)[0]
    multiplier = result[0]
    winnings = int(amount * multiplier)
    user_balances[user_id] += winnings
    wheel_msg = await ctx.send("🎡 Spinning the Paradox Wheel of Fortune...")
    wheel_emojis = ['💰', '✨', '💎', '🔔', '⭐️', '🎯', '🎪', '🎨']
    for _ in range(3):
        await asyncio.sleep(0.7)
        await wheel_msg.edit(content=f"🎡 Spinning the Paradox Wheel of Fortune... {random.choice(wheel_emojis)}")
    if multiplier == 0:
        result_text = f"❌ The Paradox Wheel took your ${amount}!"
        color = 0xe74c3c
    elif multiplier < 1:
        result_text = f"⚠️ You got back ${winnings} (lost ${amount - winnings})"
        color = 0xe67e22
    elif multiplier == 1:
        result_text = f"🔄 The Paradox Wheel returned your ${winnings}"
        color = 0x3498db
    else:
        result_text = f"✨ The Paradox Wheel blessed you with ${winnings} ({multiplier}x your bet)!"
        color = 0x2ecc71
    embed = discord.Embed(
        title="🎡 Paradox Wheel of Fortune Results",
        description=result_text,
        color=color
    )
    embed.add_field(name="New Balance", value=f"${user_balances[user_id]}", inline=True)
    embed.set_footer(text="Paradox Casino Machine | Round and round it goes...")
    await ctx.send(embed=embed)

@bot.command()
async def give(ctx, recipient: discord.Member, amount: int):
    sender_id = ctx.author.id
    recipient_id = recipient.id
    if sender_id not in user_balances:
        user_balances[sender_id] = 1000
    if recipient_id not in user_balances:
        user_balances[recipient_id] = 1000
    if amount <= 0:
        await ctx.send("❌ Amount must be positive!")
        return
    if sender_id == recipient_id:
        await ctx.send("❓ You can't give money to yourself in the Paradox Casino!")
        return
    if amount > user_balances[sender_id]:
        await ctx.send(f"❌ You don't have enough Paradox coins! Your balance is ${user_balances[sender_id]}")
        return
    user_balances[sender_id] -= amount
    user_balances[recipient_id] += amount
    embed = discord.Embed(
        title="💸 Paradox Money Transfer",
        description=f"{ctx.author.mention} gave ${amount} to {recipient.mention}!",
        color=0x2ecc71
    )
    embed.add_field(name=f"{ctx.author.name}'s Balance", value=f"${user_balances[sender_id]}", inline=True)
    embed.add_field(name=f"{recipient.name}'s Balance", value=f"${user_balances[recipient_id]}", inline=True)
    embed.set_footer(text="Paradox Casino Machine | Share the wealth")
    await ctx.send(embed=embed)

@bot.command()
async def rps(ctx, choice: str, amount: int):
    user_id = ctx.author.id
    if user_id not in user_balances:
        user_balances[user_id] = 1000
    if amount < MIN_BET or amount > MAX_BET:
        await ctx.send(f'❌ Invalid bet! Bet between ${MIN_BET} and ${MAX_BET}.')
        return
    if amount > user_balances[user_id]:
        await ctx.send(f'❌ Insufficient funds! Your balance is ${user_balances[user_id]}.')
        return
    choices = ['rock', 'paper', 'scissors']
    if choice.lower() not in choices:
        await ctx.send('❌ Invalid choice! Choose rock, paper, or scissors.')
        return
    bot_choice = random.choice(choices)
    user_choice = choice.lower()
    result = None
    if user_choice == bot_choice:
        result = 'tie'
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'paper' and bot_choice == 'rock') or \
         (user_choice == 'scissors' and bot_choice == 'paper'):
        result = 'win'
        user_balances[user_id] += amount
    else:
        result = 'lose'
        user_balances[user_id] -= amount
    emojis = {'rock': '🪨', 'paper': '📜', 'scissors': '✂️'}
    embed = discord.Embed(
        title="🪨📜✂️ Rock-Paper-Scissors",
        description=f"{ctx.author.mention} chose {emojis[user_choice]} {user_choice}\nBot chose {emojis[bot_choice]} {bot_choice}",
        color=0x3498db
    )
    if result == 'win':
        embed.add_field(name="Result", value=f"You win! +${amount}", inline=False)
    elif result == 'lose':
        embed.add_field(name="Result", value=f"You lose! -${amount}", inline=False)
    else:
        embed.add_field(name="Result", value="It's a tie!", inline=False)
    embed.add_field(name="Balance", value=f"${user_balances[user_id]}", inline=True)
    embed.set_footer(text="Paradox Casino Machine | Play again?")
    await ctx.send(embed=embed)

@bot.command(name="paradox")
async def paradox_help(ctx):
    embed = discord.Embed(
        title="🎰 Paradox Casino Machine - Commands",
        description="Try your luck with these commands in the mysterious Paradox Casino!",
        color=0x3498db
    )
    embed.add_field(name="!bet [amount] [lines]", value="Bet on the Paradox slot machine (1-3 lines)", inline=False)
    embed.add_field(name="!balance", value="Check your current Paradox balance", inline=False)
    embed.add_field(name="!daily", value="Claim daily Paradox reward (with streak bonuses)", inline=False)
    embed.add_field(name="!wheel [amount]", value="Spin the Paradox wheel of fortune", inline=False)
    embed.add_field(name="!top", value="View the Paradox leaderboard", inline=False)
    embed.add_field(name="!achievements [user]", value="View your or another user's Paradox achievements", inline=False)
    embed.add_field(name="!give [user] [amount]", value="Give Paradox coins to another user", inline=False)
    embed.add_field(name="!tictactoe [user]", value="Start a tic-tac-toe game (optional opponent)", inline=False)
    embed.add_field(name="!move [row] [col]", value="Make a move in tic-tac-toe (0-2)", inline=False)
    embed.add_field(name="!rps [choice] [amount]", value="Play rock-paper-scissors against the bot to win double your bet!", inline=False)
    embed.add_field(name="!paradox", value="Show this help message", inline=False)
    embed.set_footer(text="Paradox Casino Machine | Where probability defies reality")
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    print(f"Command error for {ctx.author}: {error}")
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument! Type `!paradox` for help.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument! Make sure you're using the correct format. Type `!paradox` for help.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Please wait {error.retry_after:.1f} seconds before using this command again.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found! Please specify a valid member.")
    else:
        await ctx.send("❌ An unexpected error occurred. Check the logs!")

def load_data():
    global user_balances, user_winnings, user_daily_claims, user_streaks, user_achievements, betting_cooldowns
    try:
        with open('user_data.json', 'r') as f:
            data = json.load(f)
            user_balances = {int(k): v for k, v in data.get('balances', {}).items()}
            user_winnings = {int(k): v for k, v in data.get('winnings', {}).items()}
            user_daily_claims = {int(k): datetime.fromisoformat(v) for k, v in data.get('daily_claims', {}).items()}
            user_streaks = {int(k): v for k, v in data.get('streaks', {}).items()}
            user_achievements = {int(k): set(v) for k, v in data.get('achievements', {}).items()}
            betting_cooldowns = {int(k): datetime.fromisoformat(v) for k, v in data.get('cooldowns', {}).items()}
    except FileNotFoundError:
        print("No user data found, starting fresh.")

async def save_data_once():
    data = {
        'balances': user_balances,
        'winnings': user_winnings,
        'daily_claims': {k: v.isoformat() for k, v in user_daily_claims.items()},
        'streaks': user_streaks,
        'achievements': {k: list(v) for k, v in user_achievements.items()},
        'cooldowns': {k: v.isoformat() for k, v in betting_cooldowns.items()}
    }
    with open('user_data.json', 'w') as f:
        json.dump(data, f)
    print(f"Saved user data at {datetime.now()}")

async def save_data():
    while True:
        await save_data_once()
        await asyncio.sleep(300)

async def keep_alive():
    while True:
        print(f"Bot is alive at {datetime.now()}")
        await asyncio.sleep(300)

async def start_bot():
    try:
        print("Starting bot...")
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable not set!")
        await bot.start(token)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print(f"Rate limited! Waiting for {e.response.headers.get('Retry-After', 5)} seconds...")
            await asyncio.sleep(float(e.response.headers.get('Retry-After', 5)))
            await start_bot()
        else:
            print(f"HTTPException occurred: {e}")
            raise e
    except KeyboardInterrupt:
        print("Bot stopped by user. Cleaning up...")
        await save_data_once()
        await bot.close()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        await save_data_once()
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
        loop.run_until_complete(save_data_once())
        loop.run_until_complete(bot.close())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
import os
import discord, asyncio
from dotenv import load_dotenv
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get
from datetime import datetime
from collections import defaultdict

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.members = True  # Subscribe to the privileged members intent.
client = commands.Bot(command_prefix='.', intents=intents)
client.remove_command('help')

AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio')

# Define Legacy Categories to preserve historical grouping
# Using list of tuples to maintain order of categories in display
LEGACY_CATEGORIES = [
    ('Other AOE sounds', {'301', '302', 'agu', 'bling', 'brain', 'brush', 'crap', 'dog', 'door', 'eh', 'eh2', 'fine', 'gg', 'hey', 'hey2', 'holo', 'lilai', 'ma', 'order', 'perv', 'pogo', 'thx'}),
    ('Additional taunts', {'2ja', '41', '69', 'ah', 'ah2', 'ahnia', 'baan', 'bb', 'bb2', 'black', 'call', 'da', 'dc', 'deserve', 'dick', 'dick2', 'dick3', 'die', 'die2', 'dio', 'dunno', 'fine2', 'fine3', 'g', 'gan', 'gan2', 'gan3', 'gibai', 'go', 'go2', 'guan', 'hehe', 'imp', 'in', 'hard', 'iyo', 'ja', 'jizz', 'jizz2', 'justice', 'lager', 'luv', 'maja', 'majaja', 'me', 'myaoe', 'nene', 'nice', 'no', 'no2', 'nodick', 'oyo', 'quack', 'reward', 'roger', 'say', 'spag', 'turk', 'up', 'wait', 'wifi', 'wp', 'yahoo', 'yay', 'yay2', 'where', 'zawarudo'}),
    ('May 2025', {'afk', 'ate', 'fish', 'ja', 'jizz3', 'kaka', 'micro', 'red', 'start'}),
    ('Aug 2025', {'air', 'barracks', 'boring', 'boring2', 'boring3', 'fire', 'nowood'}),
    ('Sep 2025', {'zz', 'zzz'}),
    ('Oct 2025', {'jan', 'respect', 'sit', 'forgot'}),
    ('Nov 2025', {'100'})
]

# Flatten legacy categories for easy lookup
LEGACY_LOOKUP = {}
for cat_name, items in LEGACY_CATEGORIES:
    for item in items:
        LEGACY_LOOKUP[item] = cat_name

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.listening, name='.help'))
    print('TauntBot onboard.')
    print(f'Registered {len(client.commands)} commands (excluding help).')

async def play_taunt(ctx):
    botMessage = ''
    if ctx.message.author.voice == None:
        channel = discord.utils.get(ctx.guild.channels, name='General')
        if channel:
            botMessage = await ctx.send(f'{ctx.message.author.mention} You have to join voice channel to hear the taunt!')
        else:
            channel = discord.utils.get(ctx.guild.channels, name='Click here to speak')
            botMessage = await ctx.send(f'{ctx.message.author.mention} 你要進語音才聽得到喔')
            if not channel:
                await asyncio.sleep(5)
                # Cleanup command and bot message right before function return
                await botMessage.delete()
                await ctx.message.delete()
                return
    else:
        channel = ctx.message.author.voice.channel

    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        try:
            voice = await channel.connect()
        except:
            print('Bot already connected.')

    # Dynamic file path based on command name
    tauntCode = ctx.command.name
    tauntUrl = os.path.join(AUDIO_DIR, f'{tauntCode}.ogg')
    
    if os.path.exists(tauntUrl):
        source = FFmpegPCMAudio(tauntUrl)

        try:
            player = voice.play(source)
        except:
            print('Another taunt is playing. Dropping latter request.')

        while voice.is_playing():
            await asyncio.sleep(60)
        else:
            await voice.disconnect()
            print('Bot peace out.')
    else:
        print(f'File not found: {tauntUrl}')

    # Cleanup command (and bot message)
    if botMessage != '':
        await botMessage.delete()
    await ctx.message.delete()
    print('Cleared commands.')

# Dynamic Command Registration
if os.path.exists(AUDIO_DIR):
    for filename in os.listdir(AUDIO_DIR):
        if filename.endswith('.ogg'):
            command_name = filename[:-4] # Remove .ogg extension
            # Create a new command object for each file, using the generic handler
            cmd = commands.Command(play_taunt, name=command_name)
            client.add_command(cmd)

@client.command(pass_context=True)
async def help(ctx):
    channel = ctx.message.channel
    embed = discord.Embed(color = discord.Color.orange())
    
    helpMsg = 'Simply type a dot ( . ) followed by one of the commands below. The bot will enter voice channel and shout out the taunt.\n Example: type \" .14 \" -> bot will say \"Start the game already\"'
    embed.add_field(name='Usage', value=helpMsg, inline=False)
    
    # Organize commands
    categorized_commands = defaultdict(list)
    date_based_categories = set()
    
    for command in client.commands:
        if command.name == 'help' or command.name == '0':
            continue
            
        cmd_name = command.name
        
        # Check Legacy
        if cmd_name in LEGACY_LOOKUP:
            cat = LEGACY_LOOKUP[cmd_name]
            categorized_commands[cat].append(cmd_name)
        else:
            # Determine Date Category
            try:
                filepath = os.path.join(AUDIO_DIR, f"{cmd_name}.ogg")
                if os.path.exists(filepath):
                    creation_time = os.path.getctime(filepath)
                    dt = datetime.fromtimestamp(creation_time)
                    
                    if dt.year < 2025:
                        categorized_commands["Standard Taunts"].append(cmd_name)
                    else:
                        cat_name = dt.strftime("%b %Y") # e.g. "Dec 2025"
                        categorized_commands[cat_name].append(cmd_name)
                        date_based_categories.add((creation_time, cat_name)) # Store tuples for sorting
                else:
                    categorized_commands["Uncategorized"].append(cmd_name)
            except Exception as e:
                print(f"Error categorizing {cmd_name}: {e}")
                categorized_commands["Uncategorized"].append(cmd_name)
    
    # Build Embed
    
    # 1. Standard Taunts (Pre-2025, non-legacy)
    if categorized_commands["Standard Taunts"]:
         cmds = sorted(categorized_commands["Standard Taunts"])
         embed.add_field(name="Standard Taunts", value=', '.join(cmds), inline=False)

    # 2. Legacy Categories (In Order)
    for cat_name, _ in LEGACY_CATEGORIES:
        if cat_name in categorized_commands and categorized_commands[cat_name]:
            cmds = sorted(categorized_commands[cat_name])
            embed.add_field(name=cat_name, value=', '.join(cmds), inline=False)

    # 3. Date Categories (Chronological)
    # Filter out categories that match legacy names if any overlap (unlikely with this logic, but good practice)
    processed_cats = {c[0] for c in LEGACY_CATEGORIES}
    
    # Sort by timestamp
    sorted_date_cats = sorted(list(date_based_categories), key=lambda x: x[0])
    
    for _, cat_name in sorted_date_cats:
        if cat_name not in processed_cats and categorized_commands[cat_name]:
            cmds = sorted(categorized_commands[cat_name])
            embed.add_field(name=cat_name, value=', '.join(cmds), inline=False)
            processed_cats.add(cat_name) # Mark processed
            
    # 3. Uncategorized (New stuff that failed date check?)
    if categorized_commands["Uncategorized"]:
         cmds = sorted(categorized_commands["Uncategorized"])
         embed.add_field(name="Uncategorized", value=', '.join(cmds), inline=False)

    await channel.send(embed=embed)

@client.command(name='0')
async def leave(ctx):
    server = ctx.message.guild.voice_client
    if server:
        await server.disconnect()

if __name__ == "__main__":
    client.run(TOKEN)

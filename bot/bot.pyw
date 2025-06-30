import os
import discord, asyncio
from dotenv import load_dotenv
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.members = True  # Subscribe to the privileged members intent.
client = commands.Bot(command_prefix='.', intents=intents)
client.remove_command('help')

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.listening, name='.help'))
    # await client.change_presence(status=discord.Status.idle, activity=discord.Game(name="你媽的奶奶"))
    print('TauntBot onboard.')

@client.command(aliases=['1', '2', '2ja', '3', '4', '5', '6', '7', '8', '9', '11', '12', '13', '14', '18', '23', '24', '29', '30', '34', '35', '41', '69', '104', '105', '301', '302', 'afk', 'agu', 'ah', 'ah2', 'ahnia', 'ate' , 'baan', 'bb', 'bb2', 'brain', 'bling', 'brush', 'call', 'crap', 'da', 'da2', 'deserve', 'dick', 'dick2', 'dick3', 'die', 'die2', 'dio', 'dog', 'door', 'dunno', 'eh', 'eh2', 'fine', 'fine2', 'fine3', 'fish', 'g', 'gan', 'gan2', 'gan3', 'gg', 'gibai', 'go', 'go2', 'guan', 'hard', 'hehe', 'hey', 'hey2', 'imp', 'in', 'iyo', 'ja', 'jizz', 'jizz2', 'jizz3', 'justice', 'kaka', 'lilai', 'lager', 'luv', 'ma', 'maja', 'majaja', 'me', 'micro', 'myaoe', 'nene', 'nice', 'no', 'no2', 'nodick', 'oyo', 'perv', 'pogo', 'quack', 'red', 'reward', 'roger', 'say', 'spag', 'start', 'thx', 'turk', 'up', 'wait', 'where', 'wifi', 'yahoo', 'yay', 'yay2', 'zawarudo'])
async def taunt(ctx):
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

    tauntCode = ctx.message.content.replace('.','')
    tauntUrl = 'audio/' + tauntCode + '.ogg'
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

    # Cleanup command (and bot message)
    if botMessage != '':
        await botMessage.delete()
    await ctx.message.delete()
    print('Cleared commands.')

@client.command(pass_context=True)
async def help(ctx):
    channel = ctx.message.channel
    
    embed = discord.Embed(color = discord.Color.orange())
    
    helpMsg = 'Simply type a dot ( . ) followed by AOE2 in-game taunt code. The bot will enter voice channel and shout out the taunt.\n Example: type \" .14 \" -> bot will say \"Start the game already\"'
    embed.add_field(name='Usage', value=helpMsg, inline=False)
    
    otherAoeSounds = '301/302 (MBL wololo), agu, bling, brain, brush, crap, dog, door, eh, eh2, fine, gg, hey, hey2, lilai, ma, perv, pogo, thx'
    embed.add_field(name='Other AOE sounds', value=otherAoeSounds, inline=False)
    
    additionalTaunt = '2ja, 41, 69, ah, ah2, ahnia, baan, bb, bb2, call, da, dick, deserve, dick2, dick3, die, die2, dio, dunno, fine2, fine3, g, gan, gan2, gan3, gibai, go, go2, guan, hehe, imp, in, hard, iyo, jizz, jizz2, justice, lager, luv, maja, majaja, me, myaoe, nene, nice, no, no2, nodick, oyo, quack, reward, roger, say, spag, turk, up, wait, wifi, yahoo, yay, yay2, where, zawarudo'
    embed.add_field(name='Additional taunts', value=additionalTaunt, inline=False)
    
    additionalTaunt = 'afk, ate, fish, ja, jizz3, kaka, micro, red, start'
    embed.add_field(name='05/09/2025', value=additionalTaunt, inline=False)
    
    await channel.send(embed=embed)

@client.command(name='0')
async def leave(ctx):
    server = ctx.message.guild.voice_client
    await server.disconnect()

client.run(TOKEN)

import discord, asyncio
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get

TOKEN = 'ODQ4MTQ5NDQxMjczNjU5NDEy.YLIauA.cIId5X7ZtbpWj7yEYiywrmIwjIM'
client = commands.Bot(command_prefix = '.')

@client.event
async def on_ready():
    print('Bot onboard.')

@client.command(aliases=['1', '2', '3', '4', '5', '6', '7', '8', '9', '11', '12', '13', '14', '18', '23', '29', '30', '34', '35', '104', '105', '301', '302'])
async def taunt(ctx):
    await asyncio.sleep(2)
    await ctx.message.delete()

    if ctx.message.author.voice == None:
        botMessage = await ctx.send(f'{ctx.message.author.mention} 你要進語音才聽得到喔')
        await asyncio.sleep(5)
        await botMessage.delete()
        channel = discord.utils.get(ctx.guild.channels, name='Click here to speak')
        if not channel:
            return
    else:
        channel = ctx.message.author.voice.channel

    if not discord.opus.is_loaded():
        discord.opus.load_opus('libopus.so')
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    tauntCode = ctx.message.content.replace('.','')
    tauntUrl = tauntCode + '.ogg'
    source = FFmpegPCMAudio(tauntUrl)

    player = voice.play(source)

    while voice.is_playing(): # Checks if voice is playing
        await asyncio.sleep(2) # While it's playing it sleeps for 2 second
    else:
        await asyncio.sleep(60) # If it's not playing it waits 60 seconds
        while voice.is_playing(): # and checks once again if the bot is not playing
            break # if it's playing it breaks
        else:
            await voice.disconnect() # if not it disconnects

@client.command(name='.0')
async def leave(ctx):
    server = ctx.message.guild.voice_client
    await server.disconnect()

client.run(TOKEN)

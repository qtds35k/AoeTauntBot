import discord
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get

TOKEN = 'ODQ4MTQ5NDQxMjczNjU5NDEy.YLIauA.cIId5X7ZtbpWj7yEYiywrmIwjIM'
client = commands.Bot(command_prefix = '.')

@client.event
async def on_ready():
    print('Bot onboard.')

@client.command(aliases=['1', '2', '3', '4', '5', '6', '7', '8', '9', '11', '12', '13', '14', '18', '23', '29', '30', '34', '35', '104', '105'])
async def taunt(ctx):
    if ctx.message.author.voice == None:
        await ctx.send(f'{ctx.message.author.mention} 你要先進語音才能打指令')
        return

    if not discord.opus.is_loaded():
        discord.opus.load_opus('libopus.so')

    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    tauntCode = ctx.message.content.replace('.','')
    tauntUrl = tauntCode + '.ogg'
    source = FFmpegPCMAudio(tauntUrl)

    player = voice.play(source)
    return

client.run(TOKEN)

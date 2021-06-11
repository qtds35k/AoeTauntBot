import discord, asyncio
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get

TOKEN = 'ODQ4MTQ5NDQxMjczNjU5NDEy.YLIauA.cIId5X7ZtbpWj7yEYiywrmIwjIM'
client = commands.Bot(command_prefix = '.')
client.remove_command('help')

@client.event
async def on_ready():
    print('Bot onboard.')

@client.command(aliases=['1', '2', '3', '4', '5', '6', '7', '8', '9', '11', '12', '13', '14', '18', '23', '24', '29', '30', '34', '35', '104', '105', '301', '302'])
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

    if not discord.opus.is_loaded():
        discord.opus.load_opus('libopus.so')
    voice = get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        try:
            voice = await channel.connect()
        except:
            print("Bot already connected")

    tauntCode = ctx.message.content.replace('.','')
    tauntUrl = tauntCode + '.ogg'
    source = FFmpegPCMAudio(tauntUrl)

    try:
        player = voice.play(source)
    except:
        print("Another taunt is playing. Dropping request...")

    while voice.is_playing():
        await asyncio.sleep(60)
    else:
        await voice.disconnect()
        print('Bot disconnected')

    # Cleanup command (and bot message)
    if botMessage != '':
        await botMessage.delete()
    await ctx.message.delete()
    print('Commands are cleared')

@client.command(pass_context=True)
async def help(ctx):
    channel = ctx.message.channel
    
    helpMsg = 'Simply type a dot ( . ) followed by AOE2 in-game taunt code. The bot will go into voice channel and shout out the taunt.\n Example: type \" .14 \", bot will say \"Start the game already\"'
    embed = discord.Embed(color = discord.Color.orange())
    embed.add_field(name='Usage', value=helpMsg, inline=False)
    
    await channel.send(embed=embed)

@client.command(name='0')
async def leave(ctx):
    server = ctx.message.guild.voice_client
    await server.disconnect()

client.run(TOKEN)

import discord, asyncio
from discord import FFmpegPCMAudio
from discord.ext import commands
from discord.utils import get

TOKEN = 'ODQ4MTQ5NDQxMjczNjU5NDEy.YLIauA.cIId5X7ZtbpWj7yEYiywrmIwjIM'
client = commands.Bot(command_prefix = '.')
client.remove_command('help')

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.listening, name='.help'))
    # await client.change_presence(status=discord.Status.idle, activity=discord.Game(name="你媽的奶奶"))
    print('TauntBot onboard.')

@client.command(aliases=['1', '2', '3', '4', '5', '6', '7', '8', '9', '11', '12', '13', '14', '18', '23', '24', '29', '30', '34', '35', '69', '104', '105', '301', '302', 'ahnia', 'bling', 'crap', 'dio', 'dog', 'door', 'fine', 'gan', 'gan2', 'gg', 'gibai', 'guan', 'in', 'lilai', 'ma', 'maja', 'majaja', 'me', 'nene', 'perv', 'pogo', 'roger', 'say', 'spag', 'turk', 'yahoo', 'zawarudo'])
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
    tauntUrl = tauntCode + '.ogg'
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
    
    otherAoeSounds = '301/302 (MBL wololo), bling, crap, dog, door, fine, gg, lilai, ma, perv, pogo'
    embed.add_field(name='Other AOE sounds', value=otherAoeSounds, inline=False)
    
    additionalTaunt = '69, ahnia, dio, gan, gan2, gibai, guan, in, maja, majaja, me, nene, roger, say, spag, turk, yahoo, zawarudo'
    embed.add_field(name='Additional taunts', value=additionalTaunt, inline=False)
    
    await channel.send(embed=embed)

@client.command(name='0')
async def leave(ctx):
    server = ctx.message.guild.voice_client
    await server.disconnect()

client.run(TOKEN)

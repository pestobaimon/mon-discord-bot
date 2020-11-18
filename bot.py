import discord, os, sys
import youtube_dl
import math
import yt_search
import json
from discord.ext import commands
from discord.utils import get
from asyncio import sleep
from valorant_ranks import ranks
import traceback


bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_command_error(ctx, error):
    # if command has local error handler, return
    if hasattr(ctx.command, 'on_error'):
        return

    # get the original exception
    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        await ctx.send("command not found")

    if isinstance(error, commands.BotMissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = f'I need the **{fmt}** permission(s) to run this command.'
        await ctx.send(_message)


    if isinstance(error, commands.DisabledCommand):
        await ctx.send('This command has been disabled.')


    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please retry in {}s.".format(math.ceil(error.retry_after)))


    if isinstance(error, commands.MissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        if len(missing) > 2:
            fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        _message = 'You need the **{}** permission(s) to use this command.'.format(fmt)
        await ctx.send(_message)


    if isinstance(error, commands.UserInputError):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Missing arguments")
        else:
            await ctx.send("Invalid input.")


    if isinstance(error, commands.NoPrivateMessage):
        try:
            await ctx.author.send('This command cannot be used in direct messages.')
        except discord.Forbidden:
            pass


    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")


    await ctx.send("use `!help` for more info on a command")
    # ignore all other exception types, but print them to stderr
    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)

    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

@bot.command()
async def join(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        voice.move_to(channel)
    else:
        await channel.connect()


@bot.command(pass_context=True, aliases=['aggro','hello'])
async def whatsup(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        voice.move_to(channel)
    else:
        await channel.connect()

    source = discord.FFmpegPCMAudio(source='./effects/fuckoff.mp3')
    voice = get(bot.voice_clients, guild=ctx.guild)
    voice.play(source, after=lambda e: print('done playing FUCK OFF'))

    while voice.is_playing():
        await sleep(1)
    await voice.disconnect()


@bot.command(pass_context=True, aliases=['cry','sob','nogf'])
async def sadboi(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        voice.move_to(channel)
    else:
        await channel.connect()
    source = discord.FFmpegPCMAudio(source='./effects/sadviolin.mp3')

    voice = get(bot.voice_clients, guild=ctx.guild)
    voice.play(source, after=lambda e: print('done playing SAD VIOLIN'))

    while voice.is_playing():
        await sleep(1)
    await voice.disconnect()


@bot.command(pass_context=True, aliases=['l','goaway','fuckoff'])
async def leave(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await ctx.send("bye bye, you use me like a fucking slave and then throw me away like this huh")
        await voice.disconnect()
    else:
        await ctx.send("I'm not in a voice channel, dumbass")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('hello bot'):
        await message.channel.send('Hi baby!')

    await bot.process_commands(message)


@bot.command()
async def rank(ctx, name: str):
    with open('valorant_players.json') as json_file:
        player_dict = json.load(json_file)
    if name in player_dict:
        rank_emoji = discord.utils.get(ctx.guild.emojis, name=player_dict[name]["rank"])
        await ctx.send(f"***{name}***'s rank is {str(rank_emoji)}")
    else:
        await ctx.send("player not found")

@bot.command()
async def setrank(ctx, name:str, rank:str):
    if rank not in ranks:
        await ctx.send("invalid rank!")
        return

    with open('valorant_players.json') as json_file:
        player_dict = json.load(json_file)
    if name in player_dict:
        player_dict[name]["rank"] = rank
        with open('valorant_players.json', 'w') as outfile:
            json.dump(player_dict, outfile)
        rank_emoji = discord.utils.get(ctx.guild.emojis, name=rank)
        await ctx.send(f"***{name}***'s rank is set to {str(rank_emoji)}")
    else:
        await ctx.send(f"***{name}***  is not found in the database. \n"
                       f"please use `!add_valoplayer` to add this player to the db")
    # except:
    #     print("could not open db file")
    #     await ctx.send("database service error")

@bot.command()
async def add_valoplayer(ctx, name:str, rank:str):
    if rank not in ranks:
        await ctx.send("please enter a valid rank! \n "
                 "example of valid ranks: \n"
                 "diamond3, silver2, immortal1, radiant, etc..")
        return
    try:
        with open('valorant_players.json') as json_file:
            player_dict = json.load(json_file)
            if name not in player_dict:
                player_dict[name] = {"rank": rank}
                with open('valorant_players.json', 'w') as outfile:
                    json.dump(player_dict, outfile)
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=rank)
                await ctx.send(name + "'s rank is set to " + str(rank_emoji))
            else:
                await ctx.send(name + " already exists the database!")
    except:
        print("could not open db file")
        await ctx.send("database service error")


@bot.command()
async def play(ctx, *args):
    author = ctx.message.author
    channel = author.voice.channel
    key_in = " ".join(args[:])
    song_path = "./songs/"
    song_exists = os.path.isfile(song_path + "song.mp3")
    try:
        if song_exists:
            os.remove(song_path + "song.mp3")
    except PermissionError:
        print("Song is playing. Can't delete")
        return

    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        voice.move_to(channel)
    else:
        await channel.connect()

    if key_in.startswith("https://www.youtube.com/") or key_in.startswith("www.youtube.com"):
        url = key_in
    else:
        yt = yt_search.build("AIzaSyCyhMTYRkOV9-vTkeXfMPqBqE70EE52zR0")
        search_result = yt.search(key_in, sMax=10, sType=["video"])
        url = 'https://www.youtube.com/watch?v=' + search_result.videoId[0]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '/Users/katsumonn/PycharmProjects/MonBot/songs/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    await ctx.send('playing '+url)
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        print("downloading audio\n")
        ydl.download([url])

    for file in os.listdir(song_path):
        if file.endswith(".mp3"):
            os.rename(song_path + file, song_path + "song.mp3")
            print("renamed")
    source = discord.FFmpegPCMAudio(source='songs/song.mp3')
    voice = get(bot.voice_clients, guild=ctx.guild)
    voice.play(source, after=lambda e: print('done playing yt song'))


bot.run('Nzc4NDcwOTUzMTA4ODk3ODQz.X7Sdkg.QzBdCSH4pMcDArga7JNhHSNiWQI')

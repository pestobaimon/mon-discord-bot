import json
import math
import traceback
from asyncio import sleep

import discord
import os
import sys
import youtube_dl
import yt_search
from discord.ext import commands
from discord.utils import get

from valorant_ranks import Rank

bot = commands.Bot(command_prefix="!", help_command=None)


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
async def help(ctx, args=None):
    if not args:
        await ctx.send("```"
                       "general commands:\n"
                       "    play [song name or YT url]      #plays songs on youtube\n"
                       "    join                            #makes monbot join the voice channel\n"
                       "    leave                           #makes monbot leave the channel\n"
                       "    whatsup                         #monbot is cranky, try not to disturb it\n"
                       "    sadboi                          #a command for sad bois\n"
                       "valorant commands:\n"
                       "    addvalo [in-game name] [rank]   #adds your valorant info to bot's database. use !help addvalo for more info\n"
                       "    rank @[name]                    #gets rank. leave @[name] empty to get your own rank\n"
                       "    rankup                          #increases your rank by 1\n"
                       "    derank                          #decreases your rank by 1\n"
                       "    setname [name]                  #set your valorant name\n"
                       "```")
    else:
        if args == "addvalo":
            await ctx.send("```"
                           "addvalo [in-game name] [rank]   #adds your valorant info to bot's database\n\n"
                           "[in-game name] is your name in the game, duh.\n\n"
                           "rank list:\n"
                           "iron1,     iron2,     iron3,\n"
                           "silver1,   silver2,   silver3,\n"
                           "gold1,     gold2,     gold3,\n"
                           "platinum1, platinum2, platinum3,\n"
                           "diamond1,  diamond2,  diamond3,\n"
                           "immortal1, immortal2, immortal3,\n"
                           "radiant, unranked"
                           "```")
        else:
            await ctx.send("command not found")


@bot.command()
async def join(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        voice.move_to(channel)
    else:
        await channel.connect()


@bot.command(pass_context=True, aliases=['aggro', 'hello'])
async def whatsup(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        voice.move_to(channel)
    else:
        await channel.connect()

    source = discord.FFmpegPCMAudio(source='./effects/fuckoff.mp3', executable="C:\\ffmpeg\\bin\\ffmpeg.exe")
    voice = get(bot.voice_clients, guild=ctx.guild)
    voice.play(source, after=lambda e: print('done playing FUCK OFF'))

    while voice.is_playing():
        await sleep(1)
    await voice.disconnect()


@bot.command(pass_context=True, aliases=['cry', 'sob', 'nogf'])
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


@bot.command(pass_context=True, aliases=['l', 'goaway', 'fuckoff'])
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
async def rank(ctx, name: str = None):
    with open('valorant_players.json') as json_file:
        player_dict = json.load(json_file)
    if name and name[0:2]=="<@" and name[-1]==">":
        authid = name[3:-1]
        print(name)
        if authid in player_dict:
            rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
            await ctx.send(
                f"{ctx.author.mention}'s name is ***{player_dict[authid]['name']}*** with rank {str(rank_emoji)}")
            return
    elif not name:
        authid = str(ctx.author.id)
        if authid in player_dict:
            rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
            await ctx.send(
                f"{ctx.author.mention}'s name is ***{player_dict[authid]['name']}*** with rank {str(rank_emoji)}")
            return
    else:
        await ctx.send("mention a user to see rank `rank @name`")
        return
    await ctx.send(f"{name}  is not found in the database. \n"
                   f"please use `!addvalo` to add this player to the db")


@bot.command()
async def setrank(ctx, rank: str, user: str = None):
    if user:
        if ctx.author.guild_permissions.administrator:
            authid = user[3:-1]
            with open('valorant_players.json') as json_file:
                player_dict = json.load(json_file)
            if authid in player_dict:
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
                await ctx.send(
                    f"{user}'s name is ***{player_dict[authid]['name']}*** with rank {str(rank_emoji)}")
                return
            else:
                await ctx.send(f"{user}  is not found in the database. \n"
                               f"please use `!addvalo @[discord name]` to add this player to the db")
        else:
            await ctx.send("Eyyy u no admin. what u doin illegal m8")
    else:
        if rank not in Rank.__members__:
            await ctx.send("invalid rank!")
            return
        with open('valorant_players.json') as json_file:
            player_dict = json.load(json_file)
        authid = str(ctx.author.id)
        if authid in player_dict:
            player_dict[authid]["rank"] = Rank[rank].value
            with open('valorant_players.json', 'w') as outfile:
                json.dump(player_dict, outfile)
            rank_emoji = discord.utils.get(ctx.guild.emojis, name=rank)
            await ctx.send(f"{ctx.author.mention}'s rank is set to {str(rank_emoji)}")
        else:
            await ctx.send(f"{ctx.author.mention}  is not found in the database. \n"
                           f"please use `!addvalo` to add this player to the db")


@bot.command()
async def setname(ctx, name: str = None):
    if not name:
        await ctx.send("you forgot to enter your valorant name!\n"
                       "`setname [ingame name]`")
    try:
        with open('valorant_players.json') as json_file:
            player_dict = json.load(json_file)
        authid = str(ctx.author.id)
        if authid in player_dict:
            player_dict[authid]["name"] = name
            with open('valorant_players.json', 'w') as outfile:
                json.dump(player_dict, outfile)
            rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
            await ctx.send(f"{ctx.author.mention}'s valorant name is set to ***{name}***")
        else:
            await ctx.send(f"{ctx.author.mention} is not found in the database. \n"
                           f"please use `!addvalo` to add yourself to the database.")
    except:
        print("could not open db file")
        await ctx.send("database service error")


@bot.command()
async def addvalo(ctx, name: str = None, rank: str = 'unranked', user: str = None):
    if user:
        if ctx.author.guild_permissions.administrator:
            authid = user[3:-1]
            if not name:
                await ctx.send("You forgot to add your ingame name!\n"
                               "`addvalo [name] [rank, if unranked leave empty]`")
                return
            if rank not in Rank.__members__:
                await ctx.send("please enter a valid rank! \n "
                               "example of valid ranks: \n"
                               "diamond3, silver2, immortal1, radiant, etc..")
                return
            with open('valorant_players.json') as json_file:
                player_dict = json.load(json_file)
                if authid not in player_dict:
                    player_dict[authid] = {"name": name, "rank": Rank[rank].value}
                    with open('valorant_players.json', 'w') as outfile:
                        json.dump(player_dict, outfile)
                    rank_emoji = discord.utils.get(ctx.guild.emojis, name=rank)
                    await ctx.send(f"{user} is added to db with rank {str(rank_emoji)}")
                else:
                    rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
                    await ctx.send(f"{user} already exists in the database "
                                   f"as ***{player_dict[authid]['name']}*** with rank {str(rank_emoji)}")
        else:
            await ctx.send("Eyyy u no admin. what u doin illegal m8")
    else:
        if not name:
            await ctx.send("You forgot to add your ingame name!\n"
                           "`addvalo [name] [rank, if unranked leave empty]`")
            return
        if rank not in Rank.__members__:
            await ctx.send("please enter a valid rank! \n "
                           "example of valid ranks: \n"
                           "diamond3, silver2, immortal1, radiant, etc..")
            return
        with open('valorant_players.json') as json_file:
            player_dict = json.load(json_file)
            authid = str(ctx.author.id)
            if authid not in player_dict:
                player_dict[authid] = {"name": name, "rank": Rank[rank].value}
                with open('valorant_players.json', 'w') as outfile:
                    json.dump(player_dict, outfile)
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=rank)
                await ctx.send(f"{ctx.author.mention} is added to db with rank {str(rank_emoji)}")
            else:
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
                await ctx.send(f"{ctx.author.mention} already exists in the database "
                               f"as ***{player_dict[authid]['name']}*** with rank {str(rank_emoji)}")


@bot.command()
async def removevalo(ctx, user: str = None):
    if user:
        if ctx.author.guild_permissions.administrator:
            authid = user[3:-1]
            with open('valorant_players.json') as json_file:
                player_dict = json.load(json_file)
                if authid in player_dict:
                    player_dict.pop(authid)
                    with open('valorant_players.json', 'w') as outfile:
                        json.dump(player_dict, outfile)
                    await ctx.send(f"{user} is removed from the db")
                else:
                    await ctx.send(f"{user} doesn't exist in the database")
        else:
            await ctx.send("Eyyy u no admin. what u doin illegal m8")
    else:
        with open('valorant_players.json') as json_file:
            player_dict = json.load(json_file)
            authid = str(ctx.author.id)
            if authid in player_dict:
                player_dict.pop(authid)
                with open('valorant_players.json', 'w') as outfile:
                    json.dump(player_dict, outfile)
                await ctx.send(f"{ctx.author.mention} is removed from the db")
            else:
                await ctx.send(f"{ctx.author.mention} doesn't exist in the database")

@bot.command()
async def rankup(ctx):
    with open('valorant_players.json') as json_file:
        player_dict = json.load(json_file)
        authid = str(ctx.author.id)
        if authid in player_dict:
            if player_dict[authid]["rank"] < 22:
                player_dict[authid]["rank"] = player_dict[authid]["rank"] + 1
                with open('valorant_players.json', 'w') as outfile:
                    json.dump(player_dict, outfile)
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
                await ctx.send(f"{ctx.author.mention} ranked up to {str(rank_emoji)}!")
            else:
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
                await ctx.send(f"{ctx.author.mention} is ranked {str(rank_emoji)} and cannot rank up anymore!")

        else:
            await ctx.send(f"{ctx.author.mention} is not found in the database. \n"
                           f"please use `!addvalo` to add yourself to the database.")


@bot.command()
async def derank(ctx):
    with open('valorant_players.json') as json_file:
        player_dict = json.load(json_file)
        authid = str(ctx.author.id)
        if authid in player_dict:
            if player_dict[authid]["rank"] > 0:
                player_dict[authid]["rank"] = player_dict[authid]["rank"] - 1
                with open('valorant_players.json', 'w') as outfile:
                    json.dump(player_dict, outfile)
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
                await ctx.send(f"{ctx.author.mention} deranked to {str(rank_emoji)}!")
            else:
                rank_emoji = discord.utils.get(ctx.guild.emojis, name=Rank(player_dict[authid]["rank"]).name)
                await ctx.send(f"{ctx.author.mention} is ranked {str(rank_emoji)} and cannot derank anymore!")

        else:
            await ctx.send(f"{ctx.author.mention} is not found in the database. \n"
                           f"please use `!addvalo` to add yourself to the database.")


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
        'outtmpl': './songs/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    await ctx.send('playing ' + url)
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


bot.run('Nzc4NDcwOTUzMTA4ODk3ODQz.X7Sdkg.F4SGZrC_UKtSMsrOjxFieKnSBsI')

import asyncio
import json
import math
import sys
import threading
import traceback
from enum import Enum
from typing import Dict, List

import discord
from discord.ext import commands
from discord.utils import get
from youtube_dl import YoutubeDL
from youtubesearchpython import SearchVideos

from secret_token import TOKEN
from valorant_ranks import Rank

bot = commands.Bot(command_prefix="!", help_command=None)


class Music:
    def __init__(self, url: str, title: str):
        self.url = url
        self.title = title
        self.queue_embed = discord.Embed(title=title, url=self.url, color=0x00ccff)
        self.queue_embed.set_author(name="Queued")
        self.playing_embed = discord.Embed(title=title, url=self.url,
                                           color=0x00ccff)
        self.playing_embed.set_author(name="Now Playing")
        self.message: discord.Embed = None


class PlayState(Enum):
    stopped = 0
    playing = 1
    paused = 2


class Player:
    def __init__(self):
        self.play_state = PlayState.stopped
        self.current_music: Music = None
        self.music_queue: List[Music] = []
        self.lock = asyncio.Lock()


players: Dict[int, Player] = {}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


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
                       "    play [song name or YT url]      #plays music on youtube. enqueues new music.\n"
                       "    skip                            #skips the current music\n"
                       "    pause                           #pauses the current music\n"
                       "    stop                            #stops the current music\n"
                       "    queue                           #lists the music currently in queue\n"
                       "    join                            #makes monbot join the voice channel\n"
                       "    leave                           #makes monbot leave the channel\n"
                       "    whatsup                         #monbot is cranky, try not to disturb him\n"
                       "    sadboi                          #a command for sad bois\n"
                       "    ping                            #pings monbot to check if he's alive\n"
                       "valorant commands:\n"
                       "    addvalo [in-game name] [rank]   #adds your valorant info to bot's database. use !help addvalo for more info\n"
                       "    rank @[name]                    #gets rank. leave @[name] empty to get your own rank\n"
                       "    rankup                          #increases your rank by 1\n"
                       "    derank                          #decreases your rank by 1\n"
                       "    setname [name]                  #set your valorant name\n"
                       "```")
        return
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
        return


@bot.command()
async def join(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    if not channel:
        await ctx.send("you're not in a voice channel, stoopid human")
        return
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
        players[ctx.guild.id].music_queue = []
        players[ctx.guild.id].play_state = PlayState.stopped
        players[ctx.guild.id].music_playing = None
    else:
        await channel.connect()
        players[ctx.guild.id].music_queue = []
        players[ctx.guild.id].play_state = PlayState.stopped
        players[ctx.guild.id].music_playing = None


@bot.command(pass_context=True, aliases=['aggro', 'hello', 'sup', 'whatup'])
async def whatsup(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    player = players[ctx.guild.id]
    if not channel:
        await ctx.send("you're not in a voice channel, stoopid human")
        return
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        await channel.connect()
    source = discord.FFmpegPCMAudio(source='./effects/fuckoff.mp3')
    voice = get(bot.voice_clients, guild=ctx.guild)
    if player.current_music and player.play_state != PlayState.stopped:
        await stop(ctx)

    voice.play(source, after=lambda e: print('done playing FUCK OFF'))

    while voice.is_playing():
        await asyncio.sleep(1)
    await voice.disconnect()


@bot.command()
async def ping(ctx):
    await ctx.send("***PONG***  my friend,  ***PONG***")


@bot.command(pass_context=True, aliases=['cry', 'sob', 'nogf'])
async def sadboi(ctx):
    author = ctx.message.author
    channel = author.voice.channel
    player = players[ctx.guild.id]
    if not channel:
        await ctx.send("you're not in a voice channel, stoopid human")
        return
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        await channel.connect()
    source = discord.FFmpegPCMAudio(source='./effects/sadviolin.mp3')

    voice = get(bot.voice_clients, guild=ctx.guild)

    if player.current_music and player.player != PlayState.stopped:
        await stop(ctx)

    voice.play(source, after=lambda e: print('done playing SAD VIOLIN'))

    while voice.is_playing():
        await asyncio.sleep(1)
    await voice.disconnect()


@bot.command(pass_context=True, aliases=['l', 'goaway', 'fuckoff'])
async def leave(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
        await ctx.send("bye bye, you use me like a fucking slave and then throw me away like this huh")
        players[ctx.guild.id].music_queue = []
        players[ctx.guild.id].play_state = PlayState.stopped
        players[ctx.guild.id].music_playing = None
        await voice.disconnect()
    else:
        await ctx.send("I'm not in a voice channel, dumbass")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    # if message.content.startswith('hello bot'):
    #     await message.channel.send('Hi baby!')
    if message.guild.id not in players:
        players[message.guild.id] = Player()
    print(players[message.guild.id].play_state.name)
    await bot.process_commands(message)


@bot.command()
async def rank(ctx, name: str = None):
    with open('valorant_players.json') as json_file:
        player_dict = json.load(json_file)
    if name and name[0:2] == "<@" and name[-1] == ">":
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


@bot.command(aliases=['paly', 'pley', 'pely'])
async def play(ctx, *args):
    global players
    player = players[ctx.guild.id]
    async with player.lock:
        author = ctx.message.author
        channel = author.voice.channel
        if not channel:
            await ctx.send("you're not in a voice channel, stoopid human")
            return
        voice = get(bot.voice_clients, guild=ctx.guild)
        if voice:
            same_channel = (channel == voice.channel)
        else:
            same_channel = False
        if not same_channel:
            await join(ctx)

        # combine following args into single string separated by space
        key_in = " ".join(args[:])

        # -----------no param function
        if key_in == '':
            play_state = player.play_state
            if play_state == PlayState.stopped:
                if player.current_music:
                    player.current_music.message = await ctx.send(embed=player.current_music.playing_embed)
                    play_music(ctx, player.current_music)
                    return
                else:
                    await ctx.send("queue empty or no current music")
                    return
            elif play_state == PlayState.paused:
                await resume(ctx)
                return
            elif play_state == PlayState.playing:
                await ctx.send("Music is already playing!")
                return
            else:
                await ctx.send("Error")
                print(f"error play state: {play_state.name} unrecognized")
                return

    # get url and title
    search = SearchVideos(key_in, offset=1, mode="dict", max_results=1)
    search_result = search.result()['search_result']
    url = search_result[0]['link']
    title = search_result[0]['title']

    # create Music Object
    music = Music(url, title)

    # ---------param function
    if player.current_music:
        player.music_queue.append(music)
        music.message = await ctx.send(embed=music.queue_embed)
        print('enqueued song')
        return
    else:
        player.current_music = music
        player.current_music.message = await ctx.send(embed=player.current_music.playing_embed)
        play_music(ctx, player.current_music)
        return


def play_music(ctx, music: Music):
    voice = get(bot.voice_clients, guild=ctx.guild)
    player = players[ctx.guild.id]
    if not voice.is_playing():
        player.play_state = PlayState.playing
        players[ctx.guild.id].music_playing = music
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(music.url, download=False)
        url = info['formats'][0]['url']
        voice.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
                   after=lambda e: asyncio.run_coroutine_threadsafe(check_queue(ctx, voice, music.message), bot.loop))
        voice.source = discord.PCMVolumeTransformer(voice.source, volume=1.0)
        voice.is_playing()


async def check_queue(ctx, voice, prev_play_msg=None):
    global players
    player = players[ctx.guild.id]
    async with player.lock:
        if player.play_state == PlayState.stopped:
            return
        else:
            player.play_state == PlayState.stopped

            #delete ended song message
            if prev_play_msg:
                await prev_play_msg.delete()

            if player.music_queue:
                player.current_music = player.music_queue.pop(0)
                await player.current_music.message.delete()
                player.current_music.message = await ctx.send(embed=player.current_music.playing_embed)
                play_music(ctx, player.current_music)
                return
            else:
                player.current_music = None
                return


@bot.command()
async def skip(ctx, msg=True):
    global players
    player = players[ctx.guild.id]
    async with player.lock:
        voice = get(bot.voice_clients, guild=ctx.guild)
        if voice:
            if msg:
                await ctx.message.add_reaction("👌")
            await stop(ctx, msg=False)
            if player.music_queue:
                player.current_music = player.music_queue.pop(0)
                player.current_music.message = await ctx.send(embed=player.current_music.playing_embed)
                play_music(ctx, player.current_music)
                return
            else:
                player.current_music = None
                await ctx.send("Music queue is empty")
                return


@bot.command()
async def pause(ctx, msg=True):
    player = players[ctx.guild.id]
    async with player.lock:
        voice = get(bot.voice_clients, guild=ctx.guild)
        if voice:
            if player.play_state == PlayState.playing:
                voice.pause()
                players[ctx.guild.id].play_state = PlayState.paused
                if msg:
                    await ctx.message.add_reaction("⏸")
            else:
                await ctx.send("music is not playing")


@bot.command()
async def resume(ctx, msg=True):
    player = players[ctx.guild.id]
    async with player.lock:
        voice = get(bot.voice_clients, guild=ctx.guild)
        if voice:
            if player.play_state == PlayState.paused:
                if msg:
                    await ctx.message.add_reaction("▶")
                voice.resume()
                players[ctx.guild.id].play_state = PlayState.playing
                return
            else:
                await ctx.send("music is not playing")
                return


@bot.command()
async def stop(ctx, msg=True):
    player = players[ctx.guild.id]
    async with player.lock:
        voice = get(bot.voice_clients, guild=ctx.guild)
        if voice:
            if player.play_state == PlayState.playing or player.play_state == PlayState.paused:
                if msg:
                    await ctx.message.add_reaction("🛑")
                await players[ctx.guild.id].music_playing.message.delete()
                if voice.is_playing():
                    voice.stop()
                players[ctx.guild.id].play_state = PlayState.stopped
                return
            elif player.play_state == PlayState.stopped:
                return
            else:
                print(f"Error playstate: {player.play_state.name} unrecognized")
                await ctx.send("Error")


@bot.command(aliases=['v', 'vol'])
async def volume(ctx, vol: int):
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if 0 <= vol <= 100:
            if vol / 100 > voice.source.volume:
                emoji = "🔊"
            else:
                emoji = "🔉"
            voice.source.volume = vol / 100
            await ctx.message.add_reaction(emoji)
            await ctx.send(f"current volume is {vol}")
        else:
            await ctx.send("enter a volume between 0 and 100")


@bot.command(aliases=['q', 'que'])
async def queue(ctx):
    player = players[ctx.guild.id]
    async with player.lock:
        if not player.music_queue:
            await ctx.send("The music queue is currently empty")
        else:
            msg = ""
            for music in player.music_queue:
                msg += music.title + "\n"
            msg = "```" + msg[:-1] + "```"
            await ctx.send(msg)


bot.run(TOKEN)

import discord, os
from discord.ext import commands
from discord.utils import get
from asyncio import sleep
import youtube_dl
import yt_search

bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


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
async def test(ctx):
    print('hi')

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

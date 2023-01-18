import discord
from discord.ext import commands
from config import settings
import re
import unmatched
import random
import string
from datetime import datetime

bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot = commands.Bot(command_prefix=settings['prefix'], intents=bot_intents)
secret = ''
random.seed(datetime.now().timestamp())
admins = []
tournaments = {}


@bot.command()
async def hello(ctx):
    """
    Say hello to Saskia!
    """
    author = ctx.message.author
    await ctx.send(f'Hello, {author.mention}!')


@bot.command()
async def tell_me_secret(ctx):
    """
    Only dragons should use this, not people
    """
    global secret
    secret = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
    with open('secret.txt', 'w') as fout:
        print(secret, file=fout)
    await ctx.send('Узнай его сам!')


@bot.command()
async def obey_my_command(ctx, arg):
    """
    Claim admin rights, if you are worthy
    """
    if arg == secret:
        admins.append(ctx.author)
        await ctx.send('К вашим услугам')
    else:
        await ctx.send('Я так не думаю')


@bot.command()
async def bow(ctx):
    """
    Check if you have admin rights
    """
    if ctx.author in admins:
        await ctx.send('Слушаюсь и повинуюсь')
    else:
        await ctx.send('Я не склонюсь ни перед кем!')


@bot.command()
async def tournament(ctx, arg):
    """
    Start a new tournament, requires admin rights and config file
    """
    if ctx.author not in admins:
        await ctx.send('Недостаточно прав для проведения соревнования')
        return
    if ctx.channel in tournaments:
        await ctx.send('В этом канале уже проходит соревнование')
        return

    try:
        tour = unmatched.Tournament()
        tour.start(arg)
        tournaments[ctx.channel] = tour
    except unmatched.UMException as err:
        await ctx.send('Ошибка при создании соревнования: ' + str(err))
        return
    except Exception as err:
        await ctx.send('Что-то не так, админ, загляни в логи')
        print(err)
        return
    await ctx.send('Турнир ' + arg + ' начался. И пусть победит сильнейший!')


@bot.command()
async def stop_tournament(ctx):
    """
    Stop tournament currently running in this channel, requires admin rights
    """
    if ctx.author not in admins:
        await ctx.send('Недостаточно прав для завершения соревнования')
        return
    if ctx.channel not in tournaments:
        await ctx.send('В этом канале нет соревнования')
        return

    name = tournaments[ctx.channel].name
    winners = '\n'.join(tournaments[ctx.channel].get_winners())
    del tournaments[ctx.channel]
    await ctx.send('Соревнование ' + name + ' завершено. Слава победителям!\n' + winners)


@bot.command()
async def my_rank(ctx):
    """
    Shows your rank in current tournament
    """
    if ctx.channel in tournaments:
        await ctx.reply('Ранг - ' + tournaments[ctx.channel].get_rank(ctx.author.name))
    else:
        await ctx.reply('В этом канале нет соревнования')


@bot.command()
async def what_if(ctx, arg1, arg2):
    """
    Find out what ranks would be if player1 defeats player2
    """
    if ctx.channel in tournaments:
        r1, r2 = tournaments[ctx.channel].check_game(arg1, arg2)
        await ctx.reply('Будет ранг ' + r1 + ' у ' + arg1 + ' и ранг ' + r2 + ' у ' + arg2)
    else:
        await ctx.reply('В этом канале нет соревнования')


def parse_game(message):
    lines = message.content.split('\n')
    if len(lines) < 4:
        return None

    match = re.match('\\s*(?P<wm><@.?[0-9]*?>)\\s*defeated\\s*(?P<lm><@.?[0-9]*?>)', lines[0])
    if match is None:
        return None
    winner_mention = match.group('wm')
    loser_mention = match.group('lm')
    if loser_mention == winner_mention:
        return None
    mentions = message.mentions
    if len(mentions) != 2:
        return None
    winner, loser = mentions
    if winner.mention != winner_mention:
        winner, loser = loser, winner
    if winner.mention != winner_mention:
        # Should never happen but...
        return None

    heroes = lines[1].split(' vs ')
    if len(heroes) < 2:
        return None

    board = lines[2]

    match = re.search('<@.?[0-9]*?>', lines[3])
    if match is None:
        return None
    player1_mention = match.group()
    winner_first = True
    if winner_mention != player1_mention:
        winner_first = False

    return unmatched.Match(winner.name, loser.name, heroes[0], heroes[1], board, winner_first)


def check_message(message, user):
    match = parse_game(message)
    if match is None:
        return False
    name1 = message.author.name
    name2 = user.name
    if match.winner != name1:
        name1, name2 = name2, name1
    if match.winner != name1 or match.loser != name2:
        return False
    tournaments[message.channel].report_match(match)
    return True


@bot.event
async def on_reaction_add(reaction, user):
    if user == reaction.message.author:
        return
    for r in reaction.message.reactions:
        if r.me:
            return
    if reaction.message.channel not in tournaments:
        return

    try:
        if not check_message(reaction.message, user):
            return
    except unmatched.UMException as err:
        await reaction.message.reply("Ошибка при записи матча: " + str(err))
        return
    except Exception as err:
        await reaction.message.reply("Что-то не так, админ, посмотри логи")
        print(err)
        return
    await reaction.message.add_reaction('\U0001F409')


bot.run(settings['token'])

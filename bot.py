import discord
from dotenv import load_dotenv
import os
from discord.ext import commands

from message_analyzer import Message_processor
from score_keeper import ScoreKeeper
from quote_keeper import QuoteKeeper
message_handler = Message_processor()
score_handler = ScoreKeeper()
quote_handler = QuoteKeeper()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
miBot = commands.Bot(intents = discord.Intents.all())

######## COMMANDS ########

@miBot.slash_command(name="info")
async def show_user_info(ctx, user: discord.Option(str, "The Name Of The User You Would Like Info About", required=True, default='Nothing Entered')):
    user_dis = miBot.mem ### Need to find a way to grab the discord user (To allow for proper info pulling)
    created_at = int(ctx.author.created_at.timestamp())
    message_embed = discord.Embed(title=f"Information About: __{user}__", color=0x00aaff, description=f'ID: {ctx.author.id}')
    message_embed.add_field(name=f'Current Roles:', value=ctx.author.roles[0].name, inline=True)
    message_embed.add_field(name=f'Created Account:', value=f"<t:{created_at}:d> (<t:{created_at}:R>)", inline=True)
    message_embed.set_footer()
    message_embed.set_thumbnail(url=ctx.author.avatar)
    await ctx.respond(embed=message_embed)

#### SWEAR COUNT SYSTEM #####
swearcount = miBot.create_group(name="swearcount", description="Base Command For The Swear Score Tracker", guild_ids=[927423272033865841,])

@swearcount.command(name='highscores') # Replies with the top 3 highest scores in the server
async def showscores(ctx):
    top_scores = list()
    top_scores = score_handler.get_top_three()
    message_embed = discord.Embed(title="Top Three Swear Counts In The Server", color=0x00aaff)
    message_embed.set_author(name=miBot.user.name)
    message_embed.add_field(name=f"🟨 - {top_scores[0][0]}", value=f'{top_scores[0][1]} Points', inline=True)
    message_embed.add_field(name=f"⬜ - {top_scores[1][0]}", value=f'{top_scores[1][1]} Points', inline=False)
    message_embed.add_field(name=f"🟫 - {top_scores[2][0]}", value=f'{top_scores[2][1]} Points', inline=False)
    message_embed.set_footer(text='To See Your Own Score Use  /swearcount score')
    await ctx.respond(embed=message_embed)

@swearcount.command(name='score')
async def user_score(ctx, user: discord.Option(str, "The Name Of The User", required=False, default=None)):
    if user == None:
        user = ctx.author.name
    member_score = score_handler.get_member_score(member_name=user)
    if member_score == None:
        message_embed = discord.Embed(title="That User Does Not Exist", color=0x00aaff)
        await ctx.respond(embed = message_embed, ephemeral=True)
    else:
        message_embed = discord.Embed(color=0x00aaff)
        message_embed.add_field(name=f'Your Current Score Is:', value=f"{member_score} Points", inline=True)
        await ctx.respond(embed = message_embed)

#### QUOTE SYSTEM ####
quotes = miBot.create_group(name="quotes", description="Base Command For All Quote Related Requests", guild_ids=[927423272033865841,])

@quotes.command(name= 'add')
async def myscore(ctx, user: discord.Option(str, "The Name Of The User You Wish To Quote", required=True, default='Nothing Entered')):
    c_channel = miBot.get_channel(ctx.channel.id)
    messages = await c_channel.history(limit=25).flatten()
    cached_message = str()
    for message in messages:
        if message.content != '' and message.author.name == user:
            cached_message = message.content
            cached_message = '"' + cached_message + '"'
            break
    if cached_message == "":
        message_embed = discord.Embed(title="That User Does Not Exist", color=0x00aaff)
    else:
        quote_handler.add_quote(quote=cached_message, member=user)
        message_embed = discord.Embed(title="Quote Added", color=0x00aaff)
        message_embed.add_field(name=cached_message, value=f'- {user}', inline=True)
    await ctx.respond(embed=message_embed)

@quotes.command(name='show')
async def show_member_quotes(ctx, user: discord.Option(str, "The Name Of The User You Wish To See Saved Quotes For", required=True, default=None)):
    if user == None:
        user = ctx.author.name
    member_quotes = quote_handler.retrieve_quotes(user)
    if len(member_quotes) == 0:
        message_embed = discord.Embed(title=f"{user} Has No Quoted Messages", color=0x00aaff)
    else:
        message_embed = discord.Embed(title=f"{user}'s Quoted Messages:", color=0x00aaff)    
        for quote in member_quotes:
            message_embed.add_field(name=quote, value=f"- {user}", inline=False)
    await ctx.respond(embed=message_embed)

######## LISTENERS ########
#### BOT LISTENING EVENTS ####
@miBot.event
async def on_ready():
        print(f'[INFO] Mi Bot Has Connected To Discord...')
        score_handler.refresh_scores(guild_members=miBot.get_all_members())
        print(f'[INFO] Swear Counts Loaded')
        quote_handler.refresh_quotes(guild_members=miBot.get_all_members())
        print(f'[INFO] Quotes Loaded')

@miBot.event
async def on_message(message):
    if message.author == miBot.user:
        return
    else:
        message_as_list = message_handler.listify_message(message_raw=message)
        num_swear_words = message_handler.swear_check(message_as_list)
        if  num_swear_words != 0:
            score_handler.alter_score(member_name=message.author.name, num=num_swear_words)

@miBot.event
async def on_member_join(member):
    created_at = int(member.created_at.timestamp())
    message_embed = discord.Embed(title=f"Everyone Welcome __{member.name}__ To The Server", color=0x00aaff, description=f'ID: {member.id}')
    message_embed.add_field(name=f'Current Roles:', value=member.roles[0].name, inline=True)
    message_embed.add_field(name=f'Created Account:', value=f"<t:{created_at}:d> (<t:{created_at}:R>)", inline=True)
    message_embed.set_thumbnail(url=member.avatar)
    await member.guild.system_channel.send(embed=message_embed)

miBot.add_application_command(quotes)
miBot.run(TOKEN)
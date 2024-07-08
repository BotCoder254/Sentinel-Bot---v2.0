import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import datetime
import json
import random
import os
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Sentinel(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = self.load_config()
        self.version = "2.0"
        self.creator = "TELVIN TEUM" #edit at your own risk
        self.start_time = datetime.datetime.utcnow()
        self.current_time = datetime.datetime.utcnow()

    def load_config(self):  #edit this field to generate the config file for the bot 
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "prefix": "!",
                "welcome_message": "Welcome to the server, {member}!",
                "farewell_message": "Goodbye, {member}. We'll miss you!",
                "forbidden_words": ["badword1", "badword2", "badword3"],
                "auto_role": None,
                "custom_commands": {},
                "logging_channel": None,
                "bot_status": "Am On Duty",
                "bot_color": "0x3498db",
                "mod_roles": ["Moderator", "Admin"],
                "user_roles": ["Member"],
                "raid_protection": False,
                "raid_threshold": 5,
                "raid_time_window": 10,
                "anti_spam": False,
                "spam_threshold": 5,
                "spam_time_window": 5
            }

    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    async def generate_banner(self):
        width, height = 800, 300
        image = Image.new('RGB', (width, height), color='#2C2F33')
        draw = ImageDraw.Draw(image)
        font_large = ImageFont.truetype("fonts/arial.ttf", 60)  #choose font in the root folder "fonts/arial.ttf"
        font_small = ImageFont.truetype("fonts/Arialn.ttf", 30)  #choose font in the root folder "fonts/Arialn.ttf"

        # Draw title
        draw.text((width/2, 80), "Sentinel", font=font_large, fill='#FFFFFF', anchor='mm')
        
        # Draw version and creator
        draw.text((width/2, 150), f"v{self.version}", font=font_small, fill='#FFFFFF', anchor='mm')
        draw.text((width/2, 200), f"Coded by {self.creator}", font=font_small, fill='#FFFFFF', anchor='mm')

        # Save the image
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer

bot = Sentinel(command_prefix=lambda _, __: _.config['prefix'], intents=intents)

@bot.event
async def on_ready():  #affter sucessfully deployed the bot 
    banner = await bot.generate_banner()
    print(f"""
    ===============================
    Sentinel Bot Successfully Deployed!
    Version: {bot.version}
    Name: {bot.user.name}
    ID: {bot.user.id}
    Servers: {len(bot.guilds)}
    Users: {sum(guild.member_count for guild in bot.guilds)}
    Channels: {sum(len(guild.channels) for guild in bot.guilds)}
    Coded by: {bot.creator}
    Deployment Time: {bot.start_time.strftime("%Y-%m-%d %H:%M:%S UTC")}
    ===============================
    """)
    await bot.change_presence(activity=discord.Game(name=bot.config['bot_status']))

    # Send deployment message to all guilds
    for guild in bot.guilds:
        if guild.system_channel:
            embed = discord.Embed(title="Sentinel Bot Deployed", color=int(bot.config['bot_color'], 16))
            embed.add_field(name="Version", value=bot.version)
            embed.add_field(name="Prefix", value=bot.config['prefix'])
            embed.add_field(name="Status", value=bot.config['bot_status'])
            embed.set_footer(text=f"Coded by {bot.creator}")
            embed.timestamp = bot.start_time
            file = discord.File(banner, filename="banner.png")
            embed.set_image(url="attachment://banner.png")  # set image to attachment url from discord server 
            await guild.system_channel.send(file=file, embed=embed)

@bot.event
async def on_guild_join(guild):
    if guild.system_channel:
        embed = discord.Embed(title="Sentinel Bot Joined", description="Thanks for adding me to your server!", color=int(bot.config['bot_color'], 16))
        embed.add_field(name="Prefix", value=bot.config['prefix'])
        embed.add_field(name="Help Command", value=f"{bot.config['prefix']}help")
        embed.set_footer(text=f"Coded by {bot.creator}")
        await guild.system_channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    if bot.config['raid_protection']:
        await check_raid(member.guild)
    
    welcome_channel = member.guild.system_channel
    if welcome_channel:
        await welcome_channel.send(bot.config['welcome_message'].format(member=member.mention))
    
    if bot.config['auto_role']:
        role = discord.utils.get(member.guild.roles, name=bot.config['auto_role'])
        if role:
            await member.add_roles(role)

@bot.event
async def on_member_remove(member):
    farewell_channel = member.guild.system_channel
    if farewell_channel:
        await farewell_channel.send(bot.config['farewell_message'].format(member=member.name))

@bot.command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix):
    bot.config['prefix'] = new_prefix
    bot.command_prefix = new_prefix
    bot.save_config()
    await ctx.send(f"Prefix updated to: {new_prefix}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setwelcome(ctx, *, message):
    bot.config['welcome_message'] = message
    bot.save_config()
    await ctx.send("Welcome message updated.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setfarewell(ctx, *, message):
    bot.config['farewell_message'] = message
    bot.save_config()
    await ctx.send("Farewell message updated.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setautorole(ctx, role: discord.Role):
    bot.config['auto_role'] = role.name
    bot.save_config()
    await ctx.send(f"Auto-role set to: {role.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def addcommand(ctx, name, *, response):
    bot.config['custom_commands'][name] = response
    bot.save_config()
    await ctx.send(f"Custom command '{name}' added.")

@bot.command()
@commands.has_permissions(administrator=True)
async def removecommand(ctx, name):
    if name in bot.config['custom_commands']:
        del bot.config['custom_commands'][name]
        bot.save_config()
        await ctx.send(f"Custom command '{name}' removed.")
    else:
        await ctx.send("Command not found.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setlogging(ctx, channel: discord.TextChannel):
    bot.config['logging_channel'] = channel.id
    bot.save_config()
    await ctx.send(f"Logging channel set to: {channel.mention}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setstatus(ctx, *, status):
    bot.config['bot_status'] = status
    bot.save_config()
    await bot.change_presence(activity=discord.Game(name=status))
    await ctx.send(f"Bot status updated to: {status}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setcolor(ctx, color):
    if color.startswith('#'):
        color = color[1:]
    bot.config['bot_color'] = f"0x{color}"
    bot.save_config()
    await ctx.send(f"Bot color updated to: #{color}")

@bot.command()
@commands.has_permissions(administrator=True)
async def toggleraidprotection(ctx):
    bot.config['raid_protection'] = not bot.config['raid_protection']
    bot.save_config()
    status = "enabled" if bot.config['raid_protection'] else "disabled"
    await ctx.send(f"Raid protection {status}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def toggleantispam(ctx):
    bot.config['anti_spam'] = not bot.config['anti_spam']
    bot.save_config()
    status = "enabled" if bot.config['anti_spam'] else "disabled"
    await ctx.send(f"Anti-spam {status}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setraidthreshold(ctx, count: int, seconds: int):
    bot.config['raid_threshold'] = count
    bot.config['raid_time_window'] = seconds
    bot.save_config()
    await ctx.send(f"Raid threshold set to {count} joins in {seconds} seconds.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setspamthreshold(ctx, count: int, seconds: int):
    bot.config['spam_threshold'] = count
    bot.config['spam_time_window'] = seconds
    bot.save_config()
    await ctx.send(f"Spam threshold set to {count} messages in {seconds} seconds.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} has been kicked.')
    await log_action(ctx.guild, f"{ctx.author} kicked {member}", reason)

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been banned.')
    await log_action(ctx.guild, f"{ctx.author} banned {member}", reason)

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user
        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'{user.mention} has been unbanned.')
            await log_action(ctx.guild, f"{ctx.author} unbanned {user}")
            return

@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, duration: int, *, reason=None):
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)

    await member.add_roles(muted_role, reason=reason)
    await ctx.send(f'{member.mention} has been muted for {duration} minutes.')
    await log_action(ctx.guild, f"{ctx.author} muted {member} for {duration} minutes", reason)

    await asyncio.sleep(duration * 60)
    await member.remove_roles(muted_role)
    await ctx.send(f'{member.mention} has been unmuted.')
    await log_action(ctx.guild, f"{member} has been automatically unmuted")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'{len(deleted) - 1} messages have been cleared.', delete_after=5)
    await log_action(ctx.guild, f"{ctx.author} cleared {len(deleted) - 1} messages in {ctx.channel}")

@bot.command()
@commands.has_permissions(administrator=True)
async def slowmode(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f'Slowmode set to {seconds} seconds.')
    await log_action(ctx.guild, f"{ctx.author} set slowmode to {seconds} seconds in {ctx.channel}")

@bot.command()
async def warn(ctx, member: discord.Member, *, reason):
    if not any(role.name in bot.config['mod_roles'] for role in ctx.author.roles):
        await ctx.send("You don't have permission to use this command.")
        return
    await ctx.send(f'{member.mention} has been warned. Reason: {reason}')
    await log_action(ctx.guild, f"{ctx.author} warned {member}", reason)

@bot.command()
async def report(ctx, member: discord.Member, *, reason):
    await ctx.message.delete()
    await ctx.send("Your report has been submitted to the moderators.", delete_after=5)
    await log_action(ctx.guild, f"{ctx.author} reported {member}", reason)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"{guild.name} Server Information", color=int(bot.config['bot_color'], 16))
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="Owner", value=guild.owner)
    embed.add_field(name="Region", value=guild.preferred_locale)
    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Channels", value=len(guild.channels))
    embed.add_field(name="Roles", value=len(guild.roles))
    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    await ctx.send(embed=embed)

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.name for role in member.roles[1:]]
    embed = discord.Embed(title=f"{member.name} User Information", color=int(bot.config['bot_color'], 16))
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined At", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Created At", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "None")
    embed.add_field(name="Top Role", value=member.top_role.name)
    await ctx.send(embed=embed)

@bot.command()
async def botinfo(ctx):
    embed = discord.Embed(title="Sentinel Bot Information", color=int(bot.config['bot_color'], 16))
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.add_field(name="Version", value=bot.version)
    embed.add_field(name="Creator", value=bot.creator)
    embed.add_field(name="Servers", value=len(bot.guilds))
    embed.add_field(name="Users", value=sum(guild.member_count for guild in bot.guilds))
    embed.add_field(name="Commands", value=len(bot.commands))
    current_time = datetime.datetime.utcnow()
    uptime = current_time - bot.start_time
    embed.add_field(name="Uptime", value=str(uptime).split('.')[0])
    embed.set_footer(text=f"Prefix: {bot.config['prefix']}")
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! Latency: {latency}ms")

@bot.command()
async def help1(ctx):
    embed = discord.Embed(title="Sentinel Bot Commands", description="Here are the available commands:", color=int(bot.config['bot_color'], 16))
    
    # User commands
    user_cmds = [
        ('report', 'Report a user to moderators'),
        ('serverinfo', 'Display server information'),
        ('userinfo', 'Display user information'),
        ('botinfo', 'Display bot information'),
        ('ping', 'Check bot latency'),
        ('help', 'Show this help message'),
    ]
    embed.add_field(name="User Commands", value="\n".join(f"`{bot.config['prefix']}{cmd}`: {desc}" for cmd, desc in user_cmds), inline=False)
    
    # Mod commands
    mod_cmds = [
        ('kick', 'Kick a user'),
        ('ban', 'Ban a user'),
        ('unban', 'Unban a user'),
        ('mute', 'Mute a user for a specified duration'),
        ('clear', 'Clear a number of messages'),
        ('slowmode', 'Set slowmode for the channel'),
        ('warn', 'Warn a user'),
    ]
    embed.add_field(name="Moderator Commands", value="\n".join(f"`{bot.config['prefix']}{cmd}`: {desc}" for cmd, desc in mod_cmds), inline=False)
    
    # Admin commands
    admin_cmds = [
        ('setprefix', 'Change the bot prefix'),
        ('setwelcome', 'Set the welcome message'),
        ('setfarewell', 'Set the farewell message'),
        ('setautorole', 'Set the auto-assign role'),
        ('addcommand', 'Add a custom command'),
        ('removecommand', 'Remove a custom command'),
        ('setlogging', 'Set the logging channel'),
        ('setstatus', 'Set the bot status'),
        ('setcolor', 'Set the bot color'),
        ('toggleraidprotection', 'Toggle raid protection'),
        ('toggleantispam', 'Toggle anti-spam protection'),
        ('setraidthreshold', 'Set raid detection threshold'),
        ('setspamthreshold', 'Set spam detection threshold'),
    ]
    embed.add_field(name="Admin Commands", value="\n".join(f"`{bot.config['prefix']}{cmd}`: {desc}" for cmd, desc in admin_cmds), inline=False)
    
    embed.set_footer(text=f"Sentinel v{bot.version} | Coded by {bot.creator}")
    await ctx.send(embed=embed)

# Raid protection
async def check_raid(guild):
    recent_joins = [member for member in guild.members if (datetime.datetime.utcnow() - member.joined_at).total_seconds() < bot.config['raid_time_window']]
    if len(recent_joins) >= bot.config['raid_threshold']:
        for member in recent_joins:
            await member.kick(reason="Raid protection")
        await log_action(guild, f"Raid detected. Kicked {len(recent_joins)} members.")

# Anti-spam
message_history = {}

async def check_spam(message):
    global message_history
    author = message.author
    if author.id not in message_history:
        message_history[author.id] = []
    
    message_history[author.id].append(datetime.datetime.utcnow())
    
    # Remove messages older than the time window
    message_history[author.id] = [msg_time for msg_time in message_history[author.id] if (datetime.datetime.utcnow() - msg_time).total_seconds() < bot.config['spam_time_window']]
    
    if len(message_history[author.id]) > bot.config['spam_threshold']:
        await message.author.timeout(datetime.timedelta(minutes=5), reason="Spam detection")
        await message.channel.send(f"{author.mention} has been muted for 5 minutes due to spamming.")
        await log_action(message.guild, f"Spam detected from {author}. User muted for 5 minutes.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.config['anti_spam']:
        await check_spam(message)

    # Word filter
    if any(word in message.content.lower() for word in bot.config['forbidden_words']):
        await message.delete()
        await message.channel.send(f'{message.author.mention}, please watch your language!', delete_after=10)
        await log_action(message.guild, f"Deleted message from {message.author} due to forbidden words")

    # Custom commands
    if message.content.startswith(bot.config['prefix']):
        command = message.content[len(bot.config['prefix']):].split()[0]
        if command in bot.config['custom_commands']:
            if any(role.name in bot.config['user_roles'] for role in message.author.roles):
                await message.channel.send(bot.config['custom_commands'][command])
            else:
                await message.channel.send("You don't have permission to use this command.")
            return

    await bot.process_commands(message)

async def log_action(guild, action, reason=None):
    if bot.config['logging_channel']:
        channel = guild.get_channel(bot.config['logging_channel'])
        if channel:
            embed = discord.Embed(
                title="Moderation Action",
                description=action,
                color=int(bot.config['bot_color'], 16)
            )
            if reason:
                embed.add_field(name="Reason", value=reason)
            embed.timestamp = datetime.datetime.utcnow()
            await channel.send(embed=embed)

# Replace 'YOUR_TOKEN_HERE' with your actual bot token
bot.run('YOUR_TOKEN_HERE')
import os
import asyncio
import discord
import config
import db
from datetime import datetime, timedelta
from discord import Spotify
import sqlite3

client = discord.Client(intents=discord.Intents.all())
SERVER_ID = config.SERVER_ID

db.create_tables()

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(client.user.id)
  # Get the server we want to monitor
  server = client.get_guild(SERVER_ID)
  print(f'Monitoring {server.name}')
  print('------')

  # Iterate through all guilds the bot is a member of
  for guild in client.guilds:
      # Iterate through all members in the guild
      for member in guild.members:
          # Check if the member is not a bot
          if not member.bot:
              # Insert the member and guild into the user_guild table
              join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              db.insert_user_guild(member.id, guild.id, join_date)

@client.event
async def on_member_join(member):
    # check if the member is not a bot
    if not member.bot:
        # Get the current time as the join date
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Insert the user and guild into the user_guild table
        db.insert_user_guild(member.id, member.guild.id, join_date)


start_times = {}

# Gathering Data

@client.event
async def on_presence_update(before, after):
  if after.guild.id == SERVER_ID:
    
    server = client.get_guild(SERVER_ID)
    db.insert_guild(SERVER_ID, server.name)

    if after.bot:
        return
    
    db.insert_user(after.id, after.name)
    # START PLAYING
    for activity in after.activities:
      # Check if the user is playing a game and that the user wasn't previously playing any game
      if activity.type == discord.ActivityType.playing and after.id not in start_times:
        if  before.activity is None or activity.type != discord.ActivityType.custom:

          # Check if there is a Spotify activity in the tuple (TEMP SOLUTION)
          for act in after.activities:
            if isinstance(act, Spotify):
              break
            else:
              # Insert game to db
              db.insert_game(activity.name)

              current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
              play_time = datetime.now()
              # Add an entry to the start_times dictionary with the user's ID as the key and the current time as the value
              start_times[after.id] = play_time
              # Get the channel object for the channel you want to send the message to
              channel = client.get_channel(config.gameChannelID)
              # Send the message to the channel, including the user's name
              await channel.send(
                f'**{after.name}** started playing **"{activity.name}"** at **"{current_time}"**! (ID: {after.id})'
              )


    # STOP PLAYING
    for activity in before.activities:
      #Check if the user is not playing a game, the previous activity was playing, the start_time is recorded and the current activity is None
      if activity.type == discord.ActivityType.playing and before.id in start_times:
        if after.activity is None or after.activity.type != discord.ActivityType.playing:

          current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      
          # Get the current time
          play_time = datetime.now()
          if before.id in start_times:
            # Get the start time for the user from the start_times dictionary
            start_time = start_times[before.id]          
            # Calculate the total playtime for the session
            total_playtime = play_time - start_time
            # Extract the total number of days, hours, minutes, and seconds from the timedelta
            total_seconds = total_playtime.total_seconds()
            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)

            duration = int(total_seconds)
            start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            stop_time_str = play_time.strftime("%Y-%m-%d %H:%M:%S")

            db.insert_user_game(before.id, activity.name, start_time_str, stop_time_str, duration)
            # Format the timedelta as a string in the HH:MM:SS format
            formatted_playtime = f'{int(days)} days, {int(hours):02}:{int(minutes):02}:{int(seconds):02}'
            start_times.pop(before.id)
          else:
            # The key does not exist in the dictionary
            formatted_playtime = "UNKOWN"
          # Get the channel object for the channel you want to send the message to
          channel = client.get_channel(config.gameChannelID)
          # Send the message to the channel, including the user's name
          await channel.send(
              f'**{before.name}** stopped playing **"{activity.name}"** at **"{current_time}"** after playing for **"{formatted_playtime}"**! (ID: {before.id})'
          )
    
    if after.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd] and before.status not in [discord.Status.online, discord.Status.idle, discord.Status.dnd]:
      # The user just went online
      channel = client.get_channel(config.statusChannelID)
      print('ONLINE Event triggered')
      db.insert_log(after.id, 'NULL', SERVER_ID, "ONLINE")
      if channel is not None:
        await channel.send(f'{after.name} just went online! (ID: {after.id})')

    if after.status == discord.Status.offline and before.status != discord.Status.offline:
      # The user just went offline
      channel = client.get_channel(config.statusChannelID)
      print('OFFLINE Event triggered')
      db.insert_log(before.id, 'NULL', SERVER_ID, "OFFLINE")
      if channel is not None:
        await channel.send(f'{before.name} just went offline! (ID: {before.id})')

    # Remove a user from the dictionary if he became offline before quitting the game
    if before.activity is not None and before.activity.type == discord.ActivityType.playing and before.id in start_times and after.activity is None:
      start_times.pop(before.id)

# ---- COMMANDS ----

@client.event
async def on_message(message):
    if message.author == client.user:
      return
    
    # Messages
    if message.content == "!monitor":
      user_id = message.author.id
      

      # Open the database connection
      conn = sqlite3.connect('discordbot.db')
      cursor = conn.cursor()
      # Get the games played (with the duration) by the user in the last 24 hours
      query = """
      SELECT user_games.game_name, SUM(user_games.duration) AS total_play_time
      FROM user_games
      WHERE user_id = ? AND stop_time >= datetime('now', '-24 hours')
      GROUP BY user_games.game_name
      """

      cursor.execute(query, (user_id,))
      result = cursor.fetchall()

      if result:
          total_seconds = sum(play_time for _, play_time in result)
          total_minutes, seconds = divmod(total_seconds, 60)
          total_hours, minutes = divmod(total_minutes, 60)
          game_names = [game_name for game_name, _ in result]
          game_list = ', '.join(game_names)

          response = f"**{message.author.name}** spent {total_hours} hours, {minutes} minutes, and {seconds} seconds playing {game_list} in the last 24 hours."
      else:
          response = f"No play time data found for **{message.author.name}** in the last 24 hours."

      await message.channel.send(response)

      # Close the database connection
      cursor.close()
      conn.close()
    
    # Detailed Messages
    if message.content == "!monitor detail":
        user_id = message.author.id

        # Open the database connection
        conn = sqlite3.connect('discordbot.db')
        cursor = conn.cursor()

        query = """
        SELECT user_games.game_name, SUM(user_games.duration) AS total_play_time
        FROM user_games
        WHERE user_id = ? AND stop_time >= datetime('now', '-24 hours')
        GROUP BY user_games.game_name
        """

        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        if result:
            playtime_details = []
            total_seconds = 0

            for game_name, play_time in result:
                total_seconds += play_time
                hours, remainder = divmod(play_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                playtime_details.append(f"**{game_name}**: {hours} hours, {minutes} minutes, {seconds} seconds")

            total_minutes, seconds = divmod(total_seconds, 60)
            total_hours, minutes = divmod(total_minutes, 60)

            game_list = "\n".join(playtime_details)
            response = f"**{message.author.name}** spent {total_hours} hours, {minutes} minutes, and {seconds} seconds playing the following games in the last 24 hours:\n\n{game_list}"
        else:
            response = f"No playtime data found for **{message.author.name}** in the last 24 hours."

        await message.channel.send(response)

        # Close the database connection
        cursor.close()
        conn.close()


client.run(config.TOKEN)
import os
import asyncio
import discord
import config
import db
from datetime import datetime, timedelta

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

start_times = {}

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
      if activity.type == discord.ActivityType.playing and not before.activities:
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')

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
      if before.activity is not None and before.activity.type == discord.ActivityType.playing and before.id in start_times and after.activity is None:
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
    
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
    
    if before.status != discord.Status.online and after.status == discord.Status.online:
      # The user just went online
      channel = client.get_channel(config.statusChannelID)
      print('Status Event triggered')
      if channel is not None:
        await channel.send(f'{after.name} just went online! (ID: {after.id})')

client.run(config.TOKEN)
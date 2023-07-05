import discord
import sqlite3
import os
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

client = discord.Client(intents=discord.Intents.all())

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
      WHERE user_id = ? AND stop_time >= datetime('now', '-24 hours','localtime')
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
        WHERE user_id = ? AND stop_time >= datetime('now', '-24 hours','localtime')
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

    #####################         Graph             ##################

    if message.content == "!monitor graph":
      # Open the database connection
      conn = sqlite3.connect('discordbot.db')
      cursor = conn.cursor()

      # Retrieve the user's weekly playtime data from the database
      query = """
      SELECT strftime('%Y-%m-%d', start_time) AS play_date, SUM(duration) AS total_playtime
      FROM user_games
      WHERE user_id = ? AND start_time >= datetime('now', '-7 days','localtime')
      GROUP BY play_date
      ORDER BY play_date
      """
      user_id = message.author.id  # Use the ID of the user who triggered the command
      cursor.execute(query, (user_id,))
      results = cursor.fetchall()

      # Extract the play dates and playtime values
      dates = [row[0] for row in results]
      playtimes = [row[1] / 3600 for row in results]  # Convert playtime from seconds to hours

      # Create a complete list of dates for the week
      start_date = datetime.now() - timedelta(days=6)
      end_date = datetime.now()
      all_dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

      # Fill in the playtime values for the days the user has played
      filled_playtimes = []
      for date in all_dates:
          if date in dates:
              index = dates.index(date)
              filled_playtimes.append(playtimes[index])
          else:
              filled_playtimes.append(0)

      # Plot the data
      plt.plot(all_dates, filled_playtimes, marker='o')
      plt.xlabel(f"Date: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}")
      plt.ylabel('Playtime (hours)')
      plt.title(f"{message.author.name} Weekly Playtime")
      plt.xticks(rotation=45)
      plt.grid(True)

      # Set x-axis labels to weekdays (e.g., Mon, Tue, Wed)
      weekday_labels = [datetime.strptime(date, '%Y-%m-%d').strftime('%a') for date in all_dates]
      plt.gca().set_xticklabels(weekday_labels)

      # Set y-axis ticks in intervals of 0.5 hours
      y_ticks = np.arange(0, max(filled_playtimes) + 0.5, 0.5)
      plt.yticks(y_ticks)

      # Save the plot as an image file
      plot_filename = 'playtime_plot.png'
      plt.savefig(plot_filename, bbox_inches='tight')
      plt.close()

      # Create a discord.File object from the saved image file
      file = discord.File(plot_filename)

      # Send the image file as a message attachment
      await message.channel.send(file=file)

      os.remove(plot_filename)
      # Close the database connection
      cursor.close()
      conn.close()

    if message.content == "!monitor help":
      help_msg = "Monitor has the following commands:\n**!monitor**: Displays the total playtime and a list of games played by the user in the last 24 hours.\n**!monitor detail**: Provides detailed information about the user's playtime for each game played in the last 24 hours.\n**!monitor graph**: Generates and sends a graph showing the user's daily playtime over the past week, highlighting the number of hours played each day."
      await message.channel.send(help_msg)

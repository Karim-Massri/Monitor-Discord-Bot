import sqlite3

def connect():
    connection = sqlite3.connect('discordbot.db')
    return connection

def create_tables():
    connection = connect()
    cursor = connection.cursor()
    # Create the users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY, 
                        username TEXT,
                        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE (id))''')
    # Create the games table
    cursor.execute('''CREATE TABLE IF NOT EXISTS games (
    game_name TEXT PRIMARY KEY);''')
    # Create the user_games table
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_games (
                    user_id INTEGER,
                    game_name TEXT,
                    start_time TIMESTAMP,
                    stop_time TIMESTAMP,
                    duration INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (game_name) REFERENCES games(game_name),
                    UNIQUE (user_id, game_name, start_time))''')

    # Create the guilds table
    cursor.execute('''CREATE TABLE IF NOT EXISTS guilds (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        UNIQUE (id))''')
    # Create the user_guilds table
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_guilds (
                        user_id INTEGER,
                        guild_id INTEGER,
                        join_date TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (guild_id) REFERENCES guilds(id),
                        UNIQUE (user_id, guild_id))''')
    # Create the logs table
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        game_name TEXT DEFAULT 'NULL',
                        guild_id INTEGER,
                        log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        log_type TEXT,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (game_name) REFERENCES games(game_name),
                        FOREIGN KEY (guild_id) REFERENCES guilds(id))''')
    connection.commit()
    connection.close()

def insert_user(id:int, username:str):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('''INSERT OR IGNORE INTO users (id, username) VALUES (?,?)''', (id, username))
    connection.commit()
    connection.close()

def insert_game(name:str):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('''INSERT OR IGNORE INTO games(game_name) VALUES(?)''', (name,))
    connection.commit()
    connection.close()

def insert_user_game(user_id:int, game_name:str, start_time:str, stop_time:str, duration:int):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('''INSERT INTO user_games(user_id, game_name, start_time, stop_time, duration) VALUES(?,?,?,?,?)''', (user_id, game_name, start_time, stop_time, duration))
    connection.commit()
    connection.close()

def insert_guild(id:int, name:str):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('''INSERT OR IGNORE INTO guilds(id, name) VALUES(?,?)''', (id, name))
    connection.commit()
    connection.close()

def insert_user_guild(user_id:int, guild_id:int, join_date:str):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('''INSERT OR IGNORE INTO user_guilds(user_id, guild_id, join_date) VALUES(?,?,?)''', (user_id, guild_id, join_date))
    connection.commit()
    connection.close()

def insert_log(user_id:int, game_name:int, guild_id:int, log_type:str):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute('''INSERT INTO logs(user_id, game_name, guild_id, log_type) VALUES(?,?,?,?)''', (user_id, game_name, guild_id, log_type))
    connection.commit()
    connection.close()

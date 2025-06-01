from core.bot_core import DatingBot
from core.db.connector import Database

def main():
    Database.initialize()
    bot = DatingBot()
    bot.run()

if __name__ == '__main__':
    main()
from core.bot_core import DatingBot
from core.db.connector import Database

def main():
    Database.initialize()
    bot = DatingBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("Bot stopped")
    finally:
        Database.close_all()

if __name__ == '__main__':
    main()
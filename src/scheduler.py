from src.bot import WikiBot
import os
import time
import schedule
from mereheze_bot.bot import WikiBot

class WikiScheduler:
    def __init__(self, config_path):
        self.bot = WikiBot(config_path)
        self.schedules = self.load_schedules()
    
    def load_schedules(self):
        schedules = []
        for wiki in self.bot.config['wikis']:
            for page in wiki['pages']:
                if 'schedule' in page:
                    schedules.append({
                        'schedule': page['schedule'],
                        'wiki': wiki['name'],
                        'page': page['path']
                    })
        return schedules
    
    def setup_schedules(self):
        for item in self.schedules:
            schedule.every().cron(item['schedule']).do(
                self.run_scheduled_update,
                wiki_name=item['wiki'],
                page_path=item['page']
            )
    
    def run_scheduled_update(self, wiki_name, page_path):
        print(f"Running scheduled update for {wiki_name} - {page_path}")
        self.bot.run()
    
    def run(self):
        self.setup_schedules()
        print("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("Scheduler stopped.")

if __name__ == "__main__":
    config_path = os.getenv('CONFIG_PATH', '/app/config/config.yaml')
    scheduler = WikiScheduler(config_path)
    scheduler.run()
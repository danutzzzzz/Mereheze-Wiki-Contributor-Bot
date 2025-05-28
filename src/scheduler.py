#!/usr/bin/env python3
import sys
import os
import time
import schedule
from bot import WikiBot

class WikiScheduler:
    def __init__(self, config_path):
        self.bot = WikiBot(config_path)
        self.schedules = self.load_schedules()
    
    def load_schedules(self):
        """Load all schedules from config"""
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
        """Setup all scheduled jobs"""
        for item in self.schedules:
            schedule.every().cron(item['schedule']).do(
                self.run_scheduled_update,
                wiki_name=item['wiki'],
                page_path=item['page']
            )
            print(f"Scheduled {item['wiki']} - {item['page']} with cron: {item['schedule']}")
    
    def run_scheduled_update(self, wiki_name, page_path):
        """Run update for a specific wiki page"""
        print(f"Running scheduled update for {wiki_name} - {page_path}")
        try:
            self.bot.run_single(wiki_name, page_path)
        except Exception as e:
            print(f"Error updating {wiki_name} - {page_path}: {str(e)}")
    
    def run(self):
        """Main scheduler loop"""
        self.setup_schedules()
        print("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("Scheduler stopped.")

if __name__ == "__main__":
    # Add /app/src to Python path
    sys.path.append('/app/src')
    
    # Get config path from environment or use default
    config_path = os.getenv('CONFIG_PATH', '/app/config/config.yaml')
    
    # Initialize and run scheduler
    scheduler = WikiScheduler(config_path)
    scheduler.run()
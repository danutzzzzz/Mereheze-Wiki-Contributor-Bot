#!/usr/bin/env python3
import sys
import os
import time
from datetime import datetime
from croniter import croniter
from bot import WikiBot

class WikiScheduler:
    def __init__(self, config_path):
        self.bot = WikiBot(config_path)
        self.jobs = []
    
    def setup_schedules(self):
        """Setup all scheduled jobs from config"""
        for wiki in self.bot.config['wikis']:
            for page in wiki['pages']:
                if 'schedule' in page:
                    # Create croniter object for each schedule
                    cron = croniter(page['schedule'], datetime.now())
                    self.jobs.append({
                        'cron': cron,
                        'next_run': cron.get_next(datetime),
                        'wiki': wiki['name'],
                        'page': page['path']
                    })
                    print(f"Scheduled {wiki['name']} - {page['path']} with cron: {page['schedule']}")
    
    def run_pending(self):
        """Run all pending jobs"""
        now = datetime.now()
        for job in self.jobs:
            if now >= job['next_run']:
                print(f"Running scheduled update for {job['wiki']} - {job['page']}")
                try:
                    self.bot.run_single(job['wiki'], job['page'])
                    # Update next run time
                    job['next_run'] = job['cron'].get_next(datetime)
                except Exception as e:
                    print(f"Error updating {job['wiki']} - {job['page']}: {str(e)}")
    
    def run(self):
        """Main scheduler loop"""
        self.setup_schedules()
        print("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                self.run_pending()
                time.sleep(60)  # Check every minute
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
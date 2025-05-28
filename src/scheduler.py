#!/usr/bin/env python3
import sys
import os
import time
from datetime import datetime
from crontab import CronTab
from bot import WikiBot

class WikiScheduler:
    def __init__(self, config_path):
        self.bot = WikiBot(config_path)
        self.cron = CronTab()
        self.jobs = []
    
    def setup_schedules(self):
        """Setup all scheduled jobs from config"""
        for wiki in self.bot.config['wikis']:
            for page in wiki['pages']:
                if 'schedule' in page:
                    job = self.cron.new(
                        command=f'echo "Running {wiki["name"]} - {page["path"]}"',
                        comment=f'{wiki["name"]}_{page["path"]}'
                    )
                    job.setall(page['schedule'])
                    self.jobs.append({
                        'job': job,
                        'wiki': wiki['name'],
                        'page': page['path']
                    })
                    print(f"Scheduled {wiki['name']} - {page['path']} with cron: {page['schedule']}")
    
    def should_run(self, job):
        """Check if a job should run now"""
        return job.schedule().get_next() < datetime.now()
    
    def run_pending(self):
        """Run all pending jobs"""
        for item in self.jobs:
            if self.should_run(item['job']):
                print(f"Running scheduled update for {item['wiki']} - {item['page']}")
                try:
                    self.bot.run_single(item['wiki'], item['page'])
                    # Update last run time
                    item['job'].schedule().get_next()
                except Exception as e:
                    print(f"Error updating {item['wiki']} - {item['page']}: {str(e)}")
    
    def run(self):
        """Main scheduler loop"""
        self.setup_schedules()
        print("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                self.run_pending()
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
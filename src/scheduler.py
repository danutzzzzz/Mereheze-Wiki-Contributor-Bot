#!/usr/bin/env python3
import sys
import os
import time
from datetime import datetime
from croniter import croniter
from bot import WikiBot  # Now safe to import

class WikiScheduler:
    def __init__(self, config_path):
        self.bot = WikiBot(config_path)
        self.jobs = []
    
    def load_schedules(self):
        for wiki in self.bot.config.get('wikis', []):
            for page in wiki.get('pages', []):
                if 'schedule' in page:
                    self.jobs.append({
                        'cron': croniter(page['schedule'], datetime.now()),
                        'next_run': None,
                        'wiki': wiki['name'],
                        'page': page['path'],
                        'schedule_str': page['schedule']
                    })
                    self.update_next_run(self.jobs[-1])

    def update_next_run(self, job):
        job['next_run'] = job['cron'].get_next(datetime)

    def should_run(self, job):
        return datetime.now() >= job['next_run']

    def run_pending(self):
        now = datetime.now()
        for job in self.jobs:
            if self.should_run(job):
                self.bot.logger.info(
                    f"Running {job['wiki']} - {job['page']} "
                    f"(cron: {job['schedule_str']})"
                )
                try:
                    self.bot.run_single(job['wiki'], job['page'])
                    self.update_next_run(job)
                except Exception as e:
                    self.bot.logger.error(
                        f"Failed to update {job['wiki']} - {job['page']}: {str(e)}",
                        exc_info=True
                    )

    def run(self):
        self.load_schedules()
        self.bot.logger.info("Scheduler started. Press Ctrl+C to exit.")
        
        for job in self.jobs:
            self.bot.logger.info(
                f"Scheduled {job['wiki']} - {job['page']} "
                f"with cron: {job['schedule_str']}. "
                f"Next run: {job['next_run']}"
            )
        
        try:
            while True:
                self.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.bot.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.bot.logger.error(f"Scheduler crashed: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    config_path = os.getenv('CONFIG_PATH', '/app/config/config.yaml')
    scheduler = WikiScheduler(config_path)
    scheduler.run()
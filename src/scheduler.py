#!/usr/bin/env python3
import sys
import os
import time
import logging
from datetime import datetime
from croniter import croniter
from bot import WikiBot

class WikiScheduler:
    def __init__(self, config_path):
        self.setup_logging(config_path)
        self.logger = logging.getLogger('scheduler')
        self.bot = WikiBot(config_path, self.logger)
        self.jobs = []
    
    def setup_logging(self, config_path):
        """Configure multi-level logging to console and file"""
        log_dir = os.path.join(os.path.dirname(config_path), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # Console handler (INFO level)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)
        
        # File handler (DEBUG level)
        log_file = os.path.join(log_dir, 'wiki_bot.log')
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)
        
        # TRACE level for detailed debugging (level 5)
        logging.addLevelName(5, 'TRACE')
        def trace(self, message, *args, **kwargs):
            if self.isEnabledFor(5):
                self._log(5, message, args, **kwargs)
        logging.Logger.trace = trace

    def setup_schedules(self):
        """Setup all scheduled jobs from config"""
        self.logger.info("Initializing schedules from config")
        for wiki in self.bot.config['wikis']:
            for page in wiki['pages']:
                if 'schedule' in page:
                    try:
                        cron = croniter(page['schedule'], datetime.now())
                        self.jobs.append({
                            'cron': cron,
                            'next_run': cron.get_next(datetime),
                            'wiki': wiki['name'],
                            'page': page['path'],
                            'schedule_str': page['schedule']
                        })
                        self.logger.info(
                            f"Scheduled {wiki['name']} - {page['path']} "
                            f"with cron: {page['schedule']}. "
                            f"Next run: {self.jobs[-1]['next_run']}"
                        )
                        self.logger.debug(
                            f"Full page config: {page}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Failed to schedule {wiki['name']} - {page['path']}: {str(e)}"
                        )

    def run_pending(self):
        """Run all pending jobs"""
        now = datetime.now()
        self.logger.debug(f"Checking for pending jobs at {now}")
        
        for job in self.jobs:
            self.logger.trace(
                f"Checking job {job['wiki']} - {job['page']}. "
                f"Next scheduled: {job['next_run']}"
            )
            
            if now >= job['next_run']:
                self.logger.info(
                    f"Executing scheduled task for {job['wiki']} - {job['page']} "
                    f"(cron: {job['schedule_str']})"
                )
                try:
                    self.bot.run_single(job['wiki'], job['page'])
                    job['next_run'] = job['cron'].get_next(datetime)
                    self.logger.info(
                        f"Task completed. Next run at {job['next_run']}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Failed to update {job['wiki']} - {job['page']}: {str(e)}",
                        exc_info=True
                    )

    def run(self):
        """Main scheduler loop"""
        self.logger.info("Starting scheduler service")
        self.setup_schedules()
        
        try:
            while True:
                self.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.critical(f"Scheduler crashed: {str(e)}", exc_info=True)
            raise

if __name__ == "__main__":
    # Add /app/src to Python path
    sys.path.append('/app/src')
    
    # Get config path from environment or use default
    config_path = os.getenv('CONFIG_PATH', '/app/config/config.yaml')
    
    # Initialize and run scheduler
    scheduler = WikiScheduler(config_path)
    scheduler.run()
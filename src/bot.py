#!/usr/bin/env python3
import os
import logging
from datetime import datetime
from mwclient import Site
from mwclient.errors import LoginError

class WikiBot:
    def __init__(self, config_path, logger=None):
        self.logger = logger if logger else self._setup_default_logger()
        self.config = self._load_config(config_path)
        self.logger.info("WikiBot initialized")

    def _setup_default_logger(self):
        logger = logging.getLogger('WikiBot')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _load_config(self, path):
        try:
            with open(path, 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error("Config load failed: %s", str(e))
            raise

    def login(self, wiki_config):
        self.logger.info("Attempting login to %s", wiki_config['name'])
        
        try:
            # Simple domain extraction (remove http:// or https://)
            domain = wiki_config['url'].replace('https://', '').replace('http://', '').split('/')[0]
            
            # Basic site connection - NO EXTRA PARAMETERS
            site = Site(domain, path='/w/')
            
            # Basic login - NO EXTRA PARAMETERS
            login_result = site.login(wiki_config['username'], wiki_config['password'])
            
            if login_result:
                self.logger.info("Login successful to %s", wiki_config['name'])
                return site
            else:
                self.logger.error("Login failed (returned False)")
                return None
                
        except LoginError as e:
            self.logger.error("Login failed with error: %s", str(e))
            if hasattr(e, 'args') and len(e.args) > 1 and isinstance(e.args[1], dict):
                error_info = e.args[1]
                self.logger.error("API Error Code: %s", error_info.get('code', 'unknown'))
                self.logger.error("API Error Info: %s", error_info.get('info', 'unknown'))
        except Exception as e:
            self.logger.error("Unexpected login error: %s", str(e))
        
        return None

    def edit_page(self, site, page_path, text):
        try:
            page = site.pages[page_path.lstrip('/')]
            current_text = page.text()
            new_text = f"{current_text}\n{text}\n"  # Simple append
            
            edit_summary = "Bot: Automated update"
            return page.edit(new_text, summary=edit_summary)
        except Exception as e:
            self.logger.error("Edit failed: %s", str(e))
            return False

    def run(self):
        for wiki in self.config.get('wikis', []):
            site = self.login(wiki)
            if not site:
                continue
                
            for page in wiki.get('pages', []):
                result = self.edit_page(site, page['path'], page['text'])
                self.logger.info("Edit %s: %s", 
                                "succeeded" if result else "failed", 
                                page['path'])

if __name__ == "__main__":
    bot = WikiBot(os.getenv('CONFIG_PATH', '/app/config/config.yaml'))
    bot.run()
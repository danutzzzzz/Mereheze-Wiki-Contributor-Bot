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
        self.logger.info("WikiBot initialized for Miraheze")

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
        self.logger.info("Attempting Miraheze login to %s", wiki_config['name'])
        
        try:
            # Miraheze-specific connection
            site = Site(
                'miraheze.org',  # Central auth server
                path='/w/',
                scheme='https',
                host=f"{wiki_config['name'].replace(' ', '_').lower()}.miraheze.org"
            )
            
            # Miraheze requires BotPasswords format (username@botname)
            login_result = site.login(
                wiki_config['username'],
                wiki_config['password']
            )
            
            if login_result:
                self.logger.info("Miraheze login successful to %s", wiki_config['name'])
                return site
            self.logger.error("Login failed (returned False)")
            return None
                
        except LoginError as e:
            self.logger.error("Miraheze login failed: %s", str(e))
            if hasattr(e, 'args') and len(e.args) > 1:
                self.logger.error("API Response: %s", e.args[1])
        except Exception as e:
            self.logger.error("Unexpected error: %s", str(e))
        return None

    def edit_page(self, site, page_path, text):
        try:
            page = site.pages[page_path.lstrip('/')]
            current_text = page.text()
            new_text = f"{current_text}\n{text}\n"
            return page.edit(new_text, summary="Bot: Automated update")
        except Exception as e:
            self.logger.error("Edit failed: %s", str(e))
            return False

    def run_single(self, wiki_name, page_path):
        self.logger.info("Processing %s - %s", wiki_name, page_path)
        
        for wiki in self.config.get('wikis', []):
            if wiki['name'] == wiki_name:
                site = self.login(wiki)
                if not site:
                    return False
                
                for page in wiki.get('pages', []):
                    if page['path'].lstrip('/') == page_path.lstrip('/'):
                        result = self.edit_page(site, page['path'], page['text'])
                        self.logger.info("Edit %s: %s", 
                                       "succeeded" if result else "failed", 
                                       page['path'])
                        return result
        return False

if __name__ == "__main__":
    # Test connection
    bot = WikiBot('config.yaml')
    site = bot.login({'name': 'KnightShift', 
                     'url': 'https://knightshift.miraheze.org',
                     'username': 'AlphaOmega@mwcb',
                     'password': 'your-token'})
    print("Login successful!" if site else "Login failed")
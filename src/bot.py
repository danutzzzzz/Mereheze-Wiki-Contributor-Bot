import os
import yaml
import logging
from datetime import datetime
from mwclient import Site
from mwclient.errors import LoginError

class WikiBot:
    def __init__(self, config_path, logger=None):
        self.logger = logger if logger else logging.getLogger('bot')
        self.config = self.load_config(config_path)
        
    def load_config(self, path):
        self.logger.debug(f"Loading config from {path}")
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            raise

    def login(self, wiki_config):
        self.logger.debug(f"Attempting login to {wiki_config['name']}")
        try:
            site = Site(wiki_config['url'], path='/w/')
            login_result = site.login(wiki_config['username'], wiki_config['password'])
            self.logger.info(
                f"Login {'successful' if login_result else 'failed'} "
                f"to {wiki_config['name']} as {wiki_config['username']}"
            )
            return site if login_result else None
        except LoginError as e:
            self.logger.error(f"Login failed for {wiki_config['name']}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected login error for {wiki_config['name']}: {str(e)}")
            return None

    def process_text(self, text):
        """Replace template variables in text"""
        processed = text.replace('{{ current_date }}', datetime.now().strftime('%Y-%m-%d'))
        self.logger.trace(f"Processed text: {processed}")
        return processed
    
    def contribute(self, site, page_path, text):
        self.logger.debug(f"Preparing to edit {page_path}")
        try:
            page = site.pages[page_path]
            current_text = page.text()
            processed_text = self.process_text(text)
            
            new_text = f"{current_text}\n{processed_text}"
            
            self.logger.info(f"Editing page {page_path}")
            self.logger.debug(f"Current page length: {len(current_text)} chars")
            self.logger.trace(f"Current content:\n{current_text}")
            self.logger.debug(f"New content length: {len(new_text)} chars")
            
            edit_result = page.edit(new_text, summary="Bot: Automated update")
            self.logger.info(
                f"Edit {'succeeded' if edit_result else 'failed'} "
                f"for {page_path}"
            )
            return edit_result
        except Exception as e:
            self.logger.error(f"Edit failed for {page_path}: {str(e)}")
            raise

    def run_single(self, wiki_name, page_path):
        """Update a single wiki page"""
        self.logger.debug(f"Running single update for {wiki_name} - {page_path}")
        for wiki in self.config['wikis']:
            if wiki['name'] == wiki_name:
                site = self.login(wiki)
                if not site:
                    return False
                
                for page in wiki['pages']:
                    if page['path'] == page_path:
                        try:
                            self.logger.debug(f"Found matching page config: {page}")
                            return self.contribute(site, page['path'], page['text'])
                        except Exception as e:
                            self.logger.error(
                                f"Error updating {wiki_name} - {page_path}: {str(e)}",
                                exc_info=True
                            )
                            return False
        self.logger.warning(f"No matching page found: {wiki_name} - {page_path}")
        return False
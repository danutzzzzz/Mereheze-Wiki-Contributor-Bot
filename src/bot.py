#!/usr/bin/env python3
import os
import re
import time
import yaml
import logging
from datetime import datetime
from mwclient import Site
from mwclient.errors import LoginError

class WikiBot:
    def __init__(self, config_path, logger=None):
        self.logger = logger if logger else self._setup_default_logger()
        self.config = self._load_config(config_path)
        self.edit_delay = 5  # seconds between edits
        self.logger.info("WikiBot initialized with %d wiki configurations", 
                        len(self.config['wikis']))

    def _setup_default_logger(self):
        """Setup default logger if none provided"""
        logger = logging.getLogger('WikiBot')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _load_config(self, path):
        """Load and validate configuration file"""
        self.logger.debug("Loading configuration from %s", path)
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config or 'wikis' not in config:
                raise ValueError("Invalid configuration: missing 'wikis' section")
            
            for wiki in config['wikis']:
                self._validate_wiki_config(wiki)
            
            return config
        except Exception as e:
            self.logger.error("Failed to load configuration: %s", str(e))
            raise

    def _validate_wiki_config(self, wiki_config):
        """Validate individual wiki configuration"""
        required_fields = ['name', 'url', 'username', 'password', 'pages']
        for field in required_fields:
            if field not in wiki_config:
                raise ValueError(f"Missing required field in wiki config: {field}")
        
        if not re.match(r'^https?://', wiki_config['url']):
            raise ValueError(f"Invalid URL format for {wiki_config['name']}. Must start with http:// or https://")

        if '@' not in wiki_config['username']:
            self.logger.warning("Username '%s' doesn't appear to be a BotPassword (missing @)", 
                              wiki_config['username'])

    def _normalize_url(self, url):
        """Normalize wiki URL to extract domain"""
        url = url.strip()
        if url.startswith('http://'):
            domain = url[7:]
        elif url.startswith('https://'):
            domain = url[8:]
        else:
            domain = url
        return domain.rstrip('/')

    def login(self, wiki_config):
        """Login to a wiki using BotPassword with basic authentication"""
        self.logger.debug("Attempting login to %s as %s", 
                        wiki_config['name'], wiki_config['username'])
        
        try:
            domain = self._normalize_url(wiki_config['url'])
            self.logger.debug("Connecting to: %s", domain)
            
            # Basic site connection
            site = Site(domain, path='/w/')
            
            # Simple login without advanced parameters
            login_result = site.login(
                wiki_config['username'],
                wiki_config['password']
            )
            
            if login_result:
                self.logger.info("Successfully logged into %s", wiki_config['name'])
                # Verify we can get a token
                try:
                    edit_token = site.get_token('csrf')
                    self.logger.debug("Obtained edit token")
                    return site
                except Exception as e:
                    self.logger.error("Failed to get edit token for %s: %s", 
                                    wiki_config['name'], str(e))
                    return None
            else:
                self.logger.error("Login failed for %s - check credentials", 
                                wiki_config['name'])
                return None
                
        except LoginError as e:
            self.logger.error("Authentication failed for %s: %s", 
                            wiki_config['name'], str(e))
        except Exception as e:
            self.logger.error("Unexpected error logging into %s: %s", 
                            wiki_config['name'], str(e), exc_info=True)
        return None

    def process_text(self, text):
        """Process template variables in text"""
        processed = text.replace('{{ current_date }}', datetime.now().strftime('%Y-%m-%d'))
        self.logger.trace("Processed text: %s", processed)
        return processed

    def contribute(self, site, page_path, text):
        """Edit a wiki page with rate limiting and error handling"""
        try:
            page_path = page_path.lstrip('/')
            self.logger.debug("Preparing to edit: %s", page_path)
            
            page = site.pages[page_path]
            current_text = page.text()
            processed_text = self.process_text(text)
            new_text = f"{current_text}\n{processed_text}"
            
            self.logger.debug("Revision info - current: %s, length: %d", 
                            page.revision, len(current_text))
            
            # Rate limiting
            time.sleep(self.edit_delay)
            
            edit_summary = "Bot: Automated update"
            self.logger.info("Attempting edit to %s", page_path)
            
            edit_result = page.edit(new_text, summary=edit_summary)
            
            if edit_result:
                self.logger.info("Successfully edited %s. New revision: %s", 
                               page_path, page.revision)
                return True
            else:
                self.logger.warning("Edit to %s returned False (no change made)", 
                                  page_path)
                return False
                
        except Exception as e:
            self.logger.error("Failed to edit %s: %s", page_path, str(e), exc_info=True)
            return False

    def run_single(self, wiki_name, page_path):
        """Update a single wiki page with full error handling"""
        self.logger.info("Starting update for %s - %s", wiki_name, page_path)
        
        for wiki in self.config['wikis']:
            if wiki['name'] == wiki_name:
                site = self.login(wiki)
                if not site:
                    return False
                
                for page_config in wiki['pages']:
                    if page_config['path'].lstrip('/') == page_path.lstrip('/'):
                        try:
                            self.logger.debug("Found page config: %s", page_config)
                            return self.contribute(site, page_path, page_config['text'])
                        except Exception as e:
                            self.logger.error("Error updating %s: %s", 
                                           page_path, str(e), exc_info=True)
                            return False
        
        self.logger.warning("Configuration not found for %s - %s", wiki_name, page_path)
        return False

    def run(self):
        """Run updates for all configured wikis and pages"""
        self.logger.info("Starting batch update of all wikis")
        success_count = 0
        
        for wiki in self.config['wikis']:
            site = self.login(wiki)
            if not site:
                continue
                
            for page in wiki['pages']:
                try:
                    if self.contribute(site, page['path'], page['text']):
                        success_count += 1
                except Exception as e:
                    self.logger.error("Error updating %s: %s", 
                                   page['path'], str(e), exc_info=True)
                    continue
        
        self.logger.info("Batch update completed. %d/%d edits succeeded",
                        success_count, sum(len(w['pages']) for w in self.config['wikis']))
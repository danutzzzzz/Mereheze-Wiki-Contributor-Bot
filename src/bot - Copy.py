#!/usr/bin/env python3
import os
import logging
import requests
from datetime import datetime

class WikiBot:
    def __init__(self, config_path, logger=None):
        self.logger = logger if logger else self._setup_default_logger()
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'MerehezeBot/1.0'})
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

    def _get_login_token(self, api_url):
        try:
            response = self.session.get(
                api_url,
                params={
                    'action': 'query',
                    'meta': 'tokens',
                    'type': 'login',
                    'format': 'json'
                }
            )
            response.raise_for_status()
            return response.json()['query']['tokens']['logintoken']
        except Exception as e:
            self.logger.error("Failed to get login token: %s", str(e))
            return None

    def login(self, wiki_config):
        self.logger.info("Attempting login to %s", wiki_config['name'])
        
        try:
            api_url = f"{wiki_config['url']}/w/api.php"
            
            # Step 1: Get login token
            token = self._get_login_token(api_url)
            if not token:
                return None
            
            # Step 2: Perform login
            login_params = {
                'action': 'login',
                'lgname': wiki_config['username'],
                'lgpassword': wiki_config['password'],
                'lgtoken': token,
                'format': 'json'
            }
            
            response = self.session.post(api_url, data=login_params)
            response.raise_for_status()
            result = response.json()
            
            if result.get('login', {}).get('result') == 'Success':
                self.logger.info("Login successful to %s", wiki_config['name'])
                return api_url  # Return API endpoint for subsequent calls
                
            self.logger.error("Login failed: %s", result.get('login', {}).get('reason', 'Unknown error'))
            return None
                
        except Exception as e:
            self.logger.error("Login error: %s", str(e), exc_info=True)
            return None

    def edit_page(self, api_url, page_path, text):
        try:
            # Get CSRF token
            token_response = self.session.get(
                api_url,
                params={
                    'action': 'query',
                    'meta': 'tokens',
                    'format': 'json'
                }
            )
            token_response.raise_for_status()
            token = token_response.json()['query']['tokens']['csrftoken']
            
            # Perform edit
            edit_params = {
                'action': 'edit',
                'title': page_path.lstrip('/'),
                'text': text,
                'summary': 'Bot: Automated update',
                'token': token,
                'format': 'json'
            }
            
            response = self.session.post(api_url, data=edit_params)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                self.logger.error("Edit failed: %s", result['error']['info'])
                return False
            return True
            
        except Exception as e:
            self.logger.error("Edit failed: %s", str(e), exc_info=True)
            return False

    def run_single(self, wiki_name, page_path):
        self.logger.info("Processing %s - %s", wiki_name, page_path)
        
        for wiki in self.config.get('wikis', []):
            if wiki['name'] == wiki_name:
                api_url = self.login(wiki)
                if not api_url:
                    return False
                
                for page in wiki.get('pages', []):
                    if page['path'].lstrip('/') == page_path.lstrip('/'):
                        result = self.edit_page(api_url, page['path'], page['text'])
                        self.logger.info("Edit %s: %s", 
                                       "succeeded" if result else "failed", 
                                       page['path'])
                        return result
        return False

# ==============================================
# MAIN EXECUTION BLOCK (for direct testing only)
# ==============================================
if __name__ == "__main__":
    """Standalone test mode for debugging login issues"""
    import argparse
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Test WikiBot login')
    parser.add_argument('--wiki', required=True, help='Wiki name')
    parser.add_argument('--url', required=True, help='Wiki URL')
    parser.add_argument('--user', required=True, help='Bot username')
    parser.add_argument('--token', required=True, help='Bot password token')
    args = parser.parse_args()

    # Initialize and test
    bot = WikiBot(None)  # No config file needed for testing
    test_wiki = {
        'name': args.wiki,
        'url': args.url,
        'username': args.user,
        'password': args.token
    }
    
    if bot.login(test_wiki):
        print("✅ Login successful!")
    else:
        print("❌ Login failed")
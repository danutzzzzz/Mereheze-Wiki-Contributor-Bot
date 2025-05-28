import os
import yaml
from datetime import datetime
from mwclient import Site
from mwclient.errors import LoginError

class WikiBot:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        
    def load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    def login(self, wiki_config):
        try:
            site = Site(wiki_config['url'], path='/w/')
            site.login(wiki_config['username'], wiki_config['password'])
            return site
        except LoginError as e:
            print(f"Login failed for {wiki_config['name']}: {str(e)}")
            return None
    
    def process_text(self, text):
        """Replace template variables in text"""
        return text.replace('{{ current_date }}', datetime.now().strftime('%Y-%m-%d'))
    
    def contribute(self, site, page_path, text):
        page = site.pages[page_path]
        current_text = page.text()
        processed_text = self.process_text(text)
        
        new_text = f"{current_text}\n{processed_text}"
        page.edit(new_text, summary="Bot: Automated update")
    
    def run_single(self, wiki_name, page_path):
        """Update a single wiki page"""
        for wiki in self.config['wikis']:
            if wiki['name'] == wiki_name:
                site = self.login(wiki)
                if not site:
                    return
                
                for page in wiki['pages']:
                    if page['path'] == page_path:
                        try:
                            self.contribute(site, page['path'], page['text'])
                            print(f"Updated {wiki_name} - {page_path}")
                        except Exception as e:
                            print(f"Error updating {wiki_name} - {page_path}: {str(e)}")
                        return
    
    def run(self):
        """Update all configured wikis and pages"""
        for wiki in self.config['wikis']:
            site = self.login(wiki)
            if not site:
                continue
                
            for page in wiki['pages']:
                try:
                    self.contribute(site, page['path'], page['text'])
                    print(f"Updated {wiki['name']} - {page['path']}")
                except Exception as e:
                    print(f"Error updating {wiki['name']} - {page['path']}: {str(e)}")
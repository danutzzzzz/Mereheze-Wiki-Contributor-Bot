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
    
    def run(self):
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

if __name__ == "__main__":
    config_path = os.getenv('CONFIG_PATH', '/app/config/config.yaml')
    bot = WikiBot(config_path)
    bot.run()
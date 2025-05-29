#!/usr/bin/env python3
import os
import logging
import requests
import re
from datetime import datetime
from string import Template
from typing import Dict, Optional, Any

class WikiBot:
    def __init__(self, config_path: str, logger: Optional[logging.Logger] = None):
        """Initialize the WikiBot with configuration and logger."""
        self.logger = logger if logger else self._setup_default_logger()
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MerehezeBot/1.0 (https://github.com/your/repo)',
            'Accept': 'application/json'
        })
        self.logger.info("WikiBot initialized for Miraheze")

    def _setup_default_logger(self) -> logging.Logger:
        """Set up a default logger if none is provided."""
        logger = logging.getLogger('WikiBot')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(path, 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error("Config load failed: %s", str(e))
            raise

    def _get_login_token(self, api_url: str) -> Optional[str]:
        """Get login token using BotPassword-specific endpoint."""
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

    def login(self, wiki_config: Dict[str, Any]) -> Optional[str]:
        """Perform BotPassword authentication for Miraheze."""
        self.logger.info("Attempting BotPassword login to %s", wiki_config['name'])
        
        try:
            api_url = f"{wiki_config['url'].rstrip('/')}/w/api.php"
            
            # Step 1: Get login token
            token = self._get_login_token(api_url)
            if not token:
                return None
            
            # Step 2: Perform BotPassword login
            login_data = {
                'action': 'login',
                'lgname': wiki_config['username'],
                'lgpassword': wiki_config['password'],
                'lgtoken': token,
                'format': 'json'
            }
            
            response = self.session.post(api_url, data=login_data)
            response.raise_for_status()
            result = response.json()
            
            if result.get('login', {}).get('result') == 'Success':
                self.logger.info("BotPassword login successful")
                return api_url
                
            error_info = result.get('login', {})
            self.logger.error("Login failed: %s", error_info.get('reason', 'Unknown error'))
            if error_info.get('result') == 'Failed':
                self.logger.error("Additional info: %s", error_info.get('message', ''))
            return None
                
        except Exception as e:
            self.logger.error("Login error: %s", str(e), exc_info=True)
            return None

    def _get_csrf_token(self, api_url: str) -> Optional[str]:
        """Get CSRF token for edits."""
        try:
            response = self.session.get(
                api_url,
                params={
                    'action': 'query',
                    'meta': 'tokens',
                    'format': 'json'
                }
            )
            response.raise_for_status()
            return response.json()['query']['tokens']['csrftoken']
        except Exception as e:
            self.logger.error("Failed to get CSRF token: %s", str(e))
            return None

    def _process_template(self, text: str, template_data: Dict[str, Any]) -> str:
        """
        Process custom templates in the text using provided data.
        Uses [[[template]]] syntax for client-side templates to avoid conflict
        with MediaWiki's server-side templates.
        """
        try:
            # Replace our custom client-side templates
            def replace_custom_template(match):
                template_name = match.group(1).strip().lower()
                
                # Handle date/time templates
                if template_name == 'current datetime':
                    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                elif template_name == 'current date':
                    return datetime.now().strftime('%Y-%m-%d')
                
                # Handle other templates from template_data
                if template_name in template_data:
                    return str(template_data[template_name])
                
                # If no replacement found, keep the original
                return match.group(0)
            
            # Process our custom templates (using [[[...]]] syntax)
            processed_text = re.sub(
                r'\[\[\[(.*?)\]\]\]',
                replace_custom_template,
                text,
                flags=re.DOTALL
            )
            
            return processed_text
        except Exception as e:
            self.logger.error(f"Template processing error: {str(e)}")
            return text

    def edit_page(self, api_url: str, page_path: str, text: str, template_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Edit a wiki page with optional template processing.
        
        Args:
            api_url: The API URL of the wiki
            page_path: Path of the page to edit
            text: The text to put on the page
            template_data: Optional dictionary of template parameters
            
        Returns:
            True if edit was successful, False otherwise
        """
        try:
            self.logger.info(f"Preparing to edit: {page_path}")
            
            # Process templates if data is provided
            processed_text = self._process_template(text, template_data or {})
            
            if processed_text != text:
                self.logger.debug("Template processing completed")
            
            # Get CSRF token
            token = self._get_csrf_token(api_url)
            if not token:
                self.logger.error("Cannot get edit token")
                return False
                
            # Prepare edit
            edit_data = {
                'action': 'edit',
                'title': page_path.lstrip('/'),
                'text': processed_text,
                'summary': 'Bot: Automated update',
                'token': token,
                'format': 'json',
                'bot': True
            }
            
            response = self.session.post(api_url, data=edit_data)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                self.logger.error(f"Edit failed! API error: {result['error']['info']}")
                return False
            
            # Detailed success logging
            if 'edit' in result:
                if result['edit']['result'] == 'Success':
                    self.logger.info(f"✅ Edit successful! Page: {page_path}")
                    self.logger.info(f"🔗 Page URL: {api_url.replace('api.php', 'index.php')}?title={page_path.replace(' ', '_')}")
                    self.logger.debug(f"Edit details: {result['edit']}")
                    return True
                else:
                    self.logger.error(f"Edit returned unexpected result: {result['edit']['result']}")
                    return False
            
            self.logger.error("Unexpected API response format")
            self.logger.debug(f"Full API response: {result}")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Edit failed for {page_path}: {str(e)}", exc_info=True)
            return False

    def run_single(self, wiki_name: str, page_path: str, template_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Handle single page update with template processing.
        
        Args:
            wiki_name: Name of the wiki from config
            page_path: Path of the page to edit
            template_data: Optional dictionary of template parameters
            
        Returns:
            True if edit was successful, False otherwise
        """
        self.logger.info("Processing %s - %s", wiki_name, page_path)
        
        for wiki in self.config.get('wikis', []):
            if wiki['name'] == wiki_name:
                api_url = self.login(wiki)
                if not api_url:
                    return False
                
                for page in wiki.get('pages', []):
                    if page['path'].lstrip('/') == page_path.lstrip('/'):
                        return self.edit_page(
                            api_url,
                            page['path'],
                            page['text'],
                            template_data
                        )
        return False

    def get_page_content(self, api_url: str, page_title: str) -> Optional[str]:
        """
        Retrieve the current content of a wiki page.
        
        Args:
            api_url: The API URL of the wiki
            page_title: Title of the page to retrieve
            
        Returns:
            The page content as string, or None if failed
        """
        try:
            params = {
                'action': 'query',
                'prop': 'revisions',
                'rvprop': 'content',
                'titles': page_title,
                'format': 'json'
            }
            
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return None
                
            page = next(iter(pages.values()))  # Get first page
            if 'missing' in page:
                return None
                
            revisions = page.get('revisions', [])
            if not revisions:
                return None
                
            return revisions[0].get('*', '')
            
        except Exception as e:
            self.logger.error(f"Failed to get page content for {page_title}: {str(e)}")
            return None
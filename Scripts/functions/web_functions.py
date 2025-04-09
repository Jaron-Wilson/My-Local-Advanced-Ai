"""
Web content extraction function implementations
"""
import re
import requests
from bs4 import BeautifulSoup

def clean_text(text):
    """Clean extracted text by removing extra whitespace and unwanted characters"""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with single newline
    return text.strip()

def read_webpage(url):
    """Read and summarize the content of a webpage"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
            element.decompose()
        
        # Extract main content (adjust selectors based on common website structures)
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        
        if (main_content):
            paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3'])
            content = '\n'.join(p.get_text() for p in paragraphs)
        else:
            content = soup.get_text()
        
        cleaned_content = clean_text(content)
        return {"content": cleaned_content[:2000]}  # Limit content length
    except Exception as e:
        return {"error": f"Failed to read webpage: {str(e)}"}

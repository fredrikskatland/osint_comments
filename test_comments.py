import requests
from bs4 import BeautifulSoup
import re
import sys

def check_for_comments(url):
    print(f"Checking for comments on {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,nb;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Print the HTML structure to help identify comment sections
        print("\nPage structure:")
        for tag in soup.find_all(['div', 'section', 'article']):
            if tag.get('id') or tag.get('class'):
                print(f"{tag.name}: id={tag.get('id')}, class={tag.get('class')}")
        
        # Look for comment section or comment count elements
        print("\nLooking for comment sections:")
        
        # Common comment section selectors
        comment_selectors = [
            '#comments', '.comments-section', '.disqus_thread', '.comment-container', '.article-comments',
            '[id*="comment"]', '[class*="comment"]', '[data-testid*="comment"]',
            '.discussion', '.conversation', '.responses', '.feedback',
            '[id*="disqus"]', '[class*="disqus"]'
        ]
        
        for selector in comment_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                for element in elements:
                    print(f"  Element: {element.name}, id={element.get('id')}, class={element.get('class')}")
        
        # Look for text containing "kommentar" or "comment"
        print("\nLooking for text containing 'kommentar' or 'comment':")
        comment_texts = []
        for text in soup.stripped_strings:
            if re.search(r'kommentar|comment', text, re.IGNORECASE):
                comment_texts.append(text)
        
        for text in comment_texts:
            print(f"  Found text: {text}")
        
        # Look for comment count indicators
        print("\nLooking for comment count indicators:")
        count_selectors = [
            '.comment-count', '.comments-count', '.comment-number', 
            'span[data-comment-count]', '[data-testid*="comment-count"]',
            '[class*="comment-count"]', '[id*="comment-count"]'
        ]
        
        for selector in count_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"Found {len(elements)} elements with selector: {selector}")
                for element in elements:
                    print(f"  Element: {element.name}, id={element.get('id')}, class={element.get('class')}, text={element.text.strip()}")
        
        # Check for text indicating comments like "X kommentarer" anywhere on the page
        comment_text_elem = soup.find(string=re.compile(r'\d+\s*kommentar(er)?', re.IGNORECASE))
        if comment_text_elem:
            print(f"\nFound text with comment count: {comment_text_elem}")
            match = re.search(r'(\d+)\s*kommentar', comment_text_elem, re.IGNORECASE)
            if match:
                comment_count = int(match.group(1))
                print(f"Extracted comment count: {comment_count}")
        
        # Save the HTML to a file for manual inspection
        with open('page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nSaved HTML to page.html for manual inspection")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = "https://e24.no/internasjonal-oekonomi/i/dR0wPX/stoltenberg-frykter-trippelskvis-for-norge"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    check_for_comments(url)

import json
import re
import sys
import os
import glob
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def extract_urls(text):
    if not text:
        return []
    # Regex to find HTTP/HTTPS URLs (avoids trailing closing parenthesis or brackets often found in Markdown)
    url_pattern = re.compile(r'https?://[^\s<>"\])]+')
    return url_pattern.findall(text)

def process_url(url):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    is_twitter = domain in ['x.com', 'www.x.com', 'twitter.com', 'www.twitter.com']
    
    target_url = url
    if is_twitter:
        # Rewrite to fixupx.com
        target_url = url.replace(domain, 'fixupx.com', 1)
        
    try:
        # Provide a User-Agent to ensure websites (like fixupx) return the HTML meant for scrapers/bots
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TelegramBot/1.0'}
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if is_twitter:
            # We look for the og:description meta tag which fixupx uses to output the tweet text
            meta_desc = soup.find('meta', property='og:description')
            if not meta_desc:
                # Sometimes it uses 'name' instead of 'property'
                meta_desc = soup.find('meta', attrs={'name': 'og:description'})
                
            if meta_desc and meta_desc.has_attr('content'):
                return meta_desc['content']
            else:
                return "No tweet description found"
        else:
            # For standard URLs, just extract <title>
            title_tag = soup.find('title')
            if title_tag:
                return title_tag.text.strip()
            return "No title found in page"
            
    except requests.RequestException as e:
        return f"Error fetching URL: {str(e)}"
    except Exception as e:
        return f"Error parsing page: {str(e)}"

def main():
    if len(sys.argv) < 2:
        files = glob.glob(os.path.join("backup", "backup_*.json"))
        if not files:
            print("Usage: python parse_urls.py <path_to_backup_json_file>")
            sys.exit(1)
        input_file = sorted(files)[-1]
        print(f"No file supplied. Auto-selected latest backup: {input_file}")
    else:
        input_file = sys.argv[1]
        
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    print(f"Loading '{input_file}'...")
    with open(input_file, 'r', encoding='utf-8') as f:
        messages = json.load(f)

    results = []
    seen_urls = set() # Avoid hitting the same URL multiple times

    print(f"Evaluating {len(messages)} messages for URLs...")
    for msg in messages:
        text = msg.get('text', '')
        date = msg.get('date')
        
        urls = extract_urls(text)
        for url in urls:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            print(f"Processing URL: {url}")
            description = process_url(url)
            
            results.append({
                "original_url": url,
                "date": date,
                "description": description
            })

    os.makedirs('backup', exist_ok=True)
    output_file = os.path.join("backup", f"parsed_urls_{os.path.basename(input_file)}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print(f"\nDone! Extracted {len(results)} unique URLs and saved to '{output_file}'.")

if __name__ == '__main__':
    main()
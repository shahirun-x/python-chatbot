import requests
import json
from bs4 import BeautifulSoup
import os

def scrape_real_python(url):
    """
    Scrapes a tutorial from realpython.com, extracts the main content,
    cleans it, and saves it to a JSON file.
    """
    print(f"Scraping URL: {url}")
    
    try:
        # Step 1: Download the webpage
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
        
        # Step 2: Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Step 3: Find the main article content
        # Real Python articles are typically within a <div> with the class "article-body"
        article_body = soup.find('div', class_='article-body')
        
        if not article_body:
            print("Error: Could not find the main article content.")
            return

        # Step 4: Extract and clean the text
        print("Extracting and cleaning text...")
        text_content = article_body.get_text(separator='\n', strip=True)
        
        # A simple cleanup to remove excessive blank lines
        lines = [line for line in text_content.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        # Step 5: Save the content in a structured format
        output_data = {
            "source": url,
            "content": cleaned_text
        }
        
        # Save to a file in a 'scraped_data' folder to keep things tidy
        output_dir = 'scraped_data'
        os.makedirs(output_dir, exist_ok=True)
        filename = url.split('/')[-2] + '.json' # e.g., 'python-dicts.json'
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        print(f"Successfully saved content to: {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # The URL of the article we want to scrape
    target_url = "https://realpython.com/python-dicts/"
    scrape_real_python(target_url)
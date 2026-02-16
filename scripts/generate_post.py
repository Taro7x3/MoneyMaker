import os
import re
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def get_product_details(url, associate_tag):
    """
    Given an Amazon URL, fetch the page, handle retries, and extract product details.
    """
    # 1. URL Normalization: Extract ASIN and create a clean, canonical URL.
    asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if not asin_match:
        print(f"Warning: Could not find a valid ASIN in URL: {url}. Skipping.")
        return None
    asin = asin_match.group(1)
    normalized_url = f"https://www.amazon.co.jp/dp/{asin}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    # 2. Retry Logic: Attempt to fetch the page up to 3 times.
    for attempt in range(3):
        try:
            print(f"Fetching (Attempt {attempt + 1}/3): {normalized_url}")
            response = requests.get(normalized_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Check if we got a CAPTCHA page by looking for its title.
            if "Amazon CAPTCHA" in response.text:
                print(f"Warning: CAPTCHA detected for {normalized_url}. Retrying after a delay...")
                time.sleep(2 * (attempt + 1)) # Increase delay with each retry
                continue

            soup = BeautifulSoup(response.content, 'html.parser')

            # 3. Robust Data Extraction
            title_element = soup.select_one('#productTitle')
            title = title_element.get_text(strip=True) if title_element else None

            price_element = soup.select_one('.a-price .a-offscreen')
            price = price_element.get_text(strip=True) if price_element else None

            image_element = soup.select_one('#landingImage')
            image_url = image_element['src'] if image_element else None
            
            # If we can't find the title or price, it's not a valid product page.
            if not title or not price:
                print(f"Warning: Could not extract title or price for {normalized_url}. Skipping.")
                return None
            
            affiliate_url = f"https://www.amazon.co.jp/dp/{asin}/?tag={associate_tag}"

            print(f"Success: Found '{title}'")
            return {
                "title": title,
                "price": price,
                "url": affiliate_url,
                "image_url": image_url,
            }

        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL {normalized_url} on attempt {attempt + 1}: {e}")
            time.sleep(2 * (attempt + 1))
            
    print(f"Failed to fetch {normalized_url} after 3 attempts.")
    return None

def generate_post_from_urls():
    """
    Reads a list of URLs from urls.txt and generates a Markdown post.
    """
    associate_tag = os.getenv("ASSOCIATE_TAG")
    if not associate_tag:
        print("Error: ASSOCIATE_TAG not found in environment variables.")
        return

    try:
        with open("urls.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Info: urls.txt not found. Skipping post generation.")
        return
        
    if not urls:
        print("Info: urls.txt is empty. Skipping post generation.")
        return

    print(f"Found {len(urls)} URLs. Fetching details...")
    products = []
    for url in urls[:5]: # Process up to 5 URLs
        details = get_product_details(url, associate_tag)
        if details:
            products.append(details)
        time.sleep(1) # Be respectful and wait 1 second between requests
    
    if not products:
        print("Error: Could not fetch valid details for any of the URLs provided.")
        return

    # --- Generate Markdown Content ---
    today = datetime.now().strftime("%Y-%m-%d")
    post_title = f"【{today}更新】編集部おすすめガジェットランキングTOP{len(products)}"
    filename = f"{today}-recommended-gadgets-ranking.md"
    
    markdown_content = f"""---
title: "{post_title}"
date: {datetime.now().isoformat()}
draft: false
tags: ["Ranking", "Gadget", "Recommendation"]
categories: ["Automated Ranking"]
---

AIエージェントのクローと編集部が厳選した、おすすめガジェットランキングTOP{len(products)}を自動生成しました。日々の価格変動をチェックして、賢い買い物をサポートします！

"""

    for i, product in enumerate(products):
        rank = i + 1
        markdown_content += f"""
## 第{rank}位：{product['title']}

![{product['title']}]({product['image_url']})

**価格:** {product['price']}

[Amazonで詳しく見る]({product['url']})
***
"""
    
    # --- Write to File ---
    output_path = os.path.join("content", "posts", filename)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"Successfully generated post from URL list: {output_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")


if __name__ == "__main__":
    generate_post_from_urls()

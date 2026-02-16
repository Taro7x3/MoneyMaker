import os
from datetime import datetime
from creators.apis.search import search_items, SearchItemsRequest

def generate_post():
    # --- 1. API Credentials ---
    access_key = os.getenv("PAAPI_ACCESS_KEY")
    secret_key = os.getenv("PAAPI_SECRET_KEY")
    associate_tag = os.getenv("ASSOCIATE_TAG")
    
    if not all([access_key, secret_key, associate_tag]):
        print("🔴 Error: API credentials not found in environment variables.")
        return

    # --- 2. Search for Products using the new library ---
    search_keywords = "PCモニター 4K"
    try:
        request = SearchItemsRequest(
            partner_tag=associate_tag,
            partner_type="associates",
            keywords=search_keywords,
            marketplace="JP",
            item_count=10,
            resources=[
                "Images.Primary.Medium",
                "ItemInfo.Title",
                "Offers.Listings.Price",
            ],
        )
        search_result = search_items(access_key, secret_key, request)

    except Exception as e:
        print(f"🔴 Error searching for items: {e}")
        return

    # --- 3. Filter and Process Products ---
    products = []
    if search_result.search_result and search_result.search_result.items:
        for item in search_result.search_result.items:
            if item.offers and item.offers.listings and item.offers.listings[0].price:
                products.append({
                    "title": item.item_info.title.display_value,
                    "price": item.offers.listings[0].price.display_amount,
                    "url": item.detail_page_url,
                    "image_url": item.images.primary.medium.url,
                })
            if len(products) >= 5:
                break

    if not products:
        print("🟡 Warning: No products with price information found. This could be due to API limitations (e.g., needing 3 sales).")
        return

    # --- 4. Generate Markdown Content ---
    today = datetime.now().strftime("%Y-%m-%d")
    sanitized_keywords = search_keywords.replace(" ", "-").lower()
    filename = f"{today}-{sanitized_keywords}-ranking.md"
    
    markdown_content = f"""---
title: "【{today}更新】{search_keywords} おすすめ人気ランキングTOP5"
date: {datetime.now().isoformat()}
draft: false
tags: ["Ranking", "Gadget", "{search_keywords}"]
categories: ["Automated Ranking"]
---
AIエージェントのクローが、Amazonの最新データから「{search_keywords}」のおすすめ人気ランキングTOP5を自動生成しました。日々の価格変動をチェックして、賢い買い物をサポートします！
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
    
    # --- 5. Write to File ---
    output_path = os.path.join("content", "posts", filename)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✅ Successfully generated post: {output_path}")
    except Exception as e:
        print(f"🔴 Error writing to file: {e}")

if __name__ == "__main__":
    generate_post()

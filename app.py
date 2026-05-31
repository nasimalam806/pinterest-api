from flask import Flask, request, jsonify
import requests
import re
import html
import concurrent.futures # 🔥 NAYA IMPORT: Superfast speed ke liye

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Pinterest Wrapper API is Running!"

# ==========================================
# 1. ORIGINAL FETCH ENDPOINT (UNTOUCHED)
# ==========================================
@app.route('/fetch')
def fetch_pin():
    link = request.args.get('url')
    if not link:
        return jsonify({"status": False, "error": "URL parameter missing hai."}), 400
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        res = requests.get(link, headers=headers, allow_redirects=True)
        html_content = res.text
        html_content = html_content.replace("\\/", "/")
        
        title = "Pinterest Download"
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title = title_match.group(1).replace(" | Pinterest", "").strip()
        title = html.escape(title)

        description = ""
        desc_match = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html_content) or \
                     re.search(r'<meta[^>]*content="([^"]+)"[^>]*property="og:description"', html_content)
        if desc_match:
            description = desc_match.group(1).strip()
            if len(description) > 150:
                description = description[:147] + "..."
        description = html.escape(description)

        video_matches = re.findall(r'(https://[^"\'\s]+\.mp4)', html_content)
        if video_matches:
            video_url = video_matches[0] 
            for v in video_matches:
                if "720p" in v or "1080p" in v or "v1.pinimg.com" in v:
                    video_url = v
            return jsonify({"status": True, "type": "video", "title": title, "description": description, "media_url": video_url})

        image_url = None
        og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_content) or \
                   re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html_content)
        if og_match:
            image_url = og_match.group(1).strip().replace("/736x/", "/originals/").replace("/564x/", "/originals/").split('?')[0]

        if not image_url:
            image_matches = re.findall(r'(https://i\.pinimg\.com/originals/[^"\'\s>]+)', html_content)
            if image_matches:
                image_url = image_matches[0].split('?')[0]

        if image_url:
            return jsonify({"status": True, "type": "image", "title": title, "description": description, "media_url": image_url})

        return jsonify({"status": False, "error": "Link se media nikal nahi paya."})
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500


# ==========================================
# 🔥 FAST PARALLEL PROCESSING HELPER (NAYA)
# ==========================================
def process_single_pin(item):
    pin_url = item.get("url")
    title = item.get("title", "Pinterest Search")
    media_type = "image"
    media_url = item.get("image", "") # Default low-res image fallback
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        # Sirf 2 second ka timeout taki API atke nahi
        pin_html_res = requests.get(pin_url, headers=headers, allow_redirects=True, timeout=2.5)
        html_content = pin_html_res.text.replace("\\/", "/")
        
        video_matches = re.findall(r'(https://[^"\'\s]+\.mp4)', html_content)
        if video_matches:
            media_type = "video"
            media_url = video_matches[0]
            for v in video_matches:
                if "720p" in v or "1080p" in v or "v1.pinimg.com" in v:
                    media_url = v
                    break
        else:
            og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_content) or \
                       re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html_content)
            if og_match:
                media_url = og_match.group(1).strip().replace("/736x/", "/originals/").replace("/564x/", "/originals/").split('?')[0]
                
    except Exception:
        pass # Agar ek link timeout ho jaye toh ignore karo aur default image bhej do
        
    return {
        "type": media_type,
        "media_url": media_url,
        "title": title,
        "pin_url": pin_url
    }

# ==========================================
# 2. UPDATED: PINTEREST SEARCH ENDPOINT (20-25 Results Ek Sath)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    try:
        # Ab hum API se 25 results mangwayenge
        api_url = f"https://pinterest-api-bay.vercel.app/search/pins?q={query}&count=25&compact=true"
        response = requests.get(api_url).json()
        
        if "items" in response and len(response["items"]) > 0:
            final_results = []
            items_to_process = response["items"][:25] # 25 ki limit
            
            # 🔥 MULTI-THREADING (10 links ek sath process honge)
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Map array ko process karta hai aur list return karta hai
                results = executor.map(process_single_pin, items_to_process)
                for res in results:
                    final_results.append(res)
            
            if final_results:
                return jsonify({"status": True, "results": final_results})
            else:
                return jsonify({"status": False, "error": "Media extract nahi ho paya."})
        else:
            return jsonify({"status": False, "error": "No results found for this keyword."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
    

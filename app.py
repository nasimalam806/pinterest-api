from flask import Flask, request, jsonify
import requests
import re
import json

app = Flask(__name__)

# ==========================================
# 1. PINTEREST SEARCH ENDPOINT (25 Results)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    try:
        api_url = f"https://pinterest-api-bay.vercel.app/search/pins?q={query}&count=25&compact=true"
        response = requests.get(api_url).json()
        
        if "items" in response and len(response["items"]) > 0:
            final_results = []
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            for item in response["items"][:25]:
                pin_url = item.get("url")
                title = item.get("title", "Pinterest Search")
                
                try:
                    pin_html_res = requests.get(pin_url, headers=headers, allow_redirects=True, timeout=5)
                    html_content = pin_html_res.text.replace("\\/", "/")
                    
                    video_matches = re.findall(r'(https://[^"\'\s]+\.mp4)', html_content)
                    media_type = "image"
                    media_url = item.get("image", "") 
                    
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
                            
                    final_results.append({
                        "type": media_type,
                        "media_url": media_url,
                        "title": title,
                        "pin_url": pin_url
                    })
                except Exception:
                    pass 
            
            if final_results:
                return jsonify({"status": True, "results": final_results})
            else:
                return jsonify({"status": False, "error": "Media extract nahi ho paya."})
        else:
            return jsonify({"status": False, "error": "No results found for this keyword."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500


# ==========================================
# 2. PINTEREST FETCH ENDPOINT (Download by Link)
# ==========================================
@app.route('/fetch')
def fetch_pin():
    url = request.args.get('url')
    if not url:
        return jsonify({"status": False, "error": "URL parameter is missing."}), 400
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        html_content = res.text.replace("\\/", "/")
        
        media_type = "image"
        media_url = ""
        title = "Pinterest Download"
        description = ""
        
        title_match = re.search(r'<meta property="og:title" content="(.*?)"', html_content)
        if title_match: 
            title = title_match.group(1)
            
        desc_match = re.search(r'<meta property="og:description" content="(.*?)"', html_content)
        if desc_match: 
            description = desc_match.group(1)
            
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
        
        if media_url:
            return jsonify({
                "status": True, 
                "media_url": media_url, 
                "type": media_type, 
                "title": title, 
                "description": description
            })
        else:
            return jsonify({"status": False, "error": "Could not extract media from this link."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

# ==========================================
# 2. UPDATED: PINTEREST SEARCH ENDPOINT (With Video Support)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    try:
        # 1. Pehle Vercel API se top search result nikalenge
        api_url = f"https://pinterest-api-bay.vercel.app/search/pins?q={query}&count=1&compact=true"
        response = requests.get(api_url).json()
        
        if "items" in response and len(response["items"]) > 0:
            top_item = response["items"][0]
            pin_url = top_item.get("url")
            title = top_item.get("title", "Pinterest Search")
            
            # 2. Ab us specific Pin ke link ko deep-scrape karenge video dhoondhne ke liye
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            }
            pin_html_res = requests.get(pin_url, headers=headers, allow_redirects=True)
            html_content = pin_html_res.text.replace("\\/", "/")
            
            # 3. Video check karna
            video_matches = re.findall(r'(https://[^"\'\s]+\.mp4)', html_content)
            media_type = "image"
            media_url = top_item.get("image", "") # Fallback image
            
            if video_matches:
                media_type = "video"
                media_url = video_matches[0]
                # High quality video dhundhna
                for v in video_matches:
                    if "720p" in v or "1080p" in v or "v1.pinimg.com" in v:
                        media_url = v
                        break
            else:
                # Agar video nahi hai, toh original high-quality image dhoondhna
                og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_content) or \
                           re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html_content)
                if og_match:
                    media_url = og_match.group(1).strip().replace("/736x/", "/originals/").replace("/564x/", "/originals/").split('?')[0]

            return jsonify({
                "status": True, 
                "type": media_type,
                "media_url": media_url,
                "title": title,
                "pin_url": pin_url
            })
        else:
            return jsonify({"status": False, "error": "No results found for this keyword."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

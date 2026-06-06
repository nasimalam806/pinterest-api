import requests
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# ULTIMATE CUSTOM SCRAPER (No Vercel API, Supports HD Video & Image)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    final_results = []
    
    try:
        # STEP 1: Bypass Pinterest Search Block using DuckDuckGo
        ddg_url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://duckduckgo.com/"
        }
        
        # 'site:pinterest.com/pin/ keyword' search karke seedha pins nikalenge
        data = {"q": f"site:pinterest.com/pin/ {query}"}
        ddg_res = requests.post(ddg_url, headers=headers, data=data, timeout=10)
        
        # Regex se saare Pin IDs extract karna
        pin_ids = re.findall(r'pinterest\.[a-z\.]+/pin/(\d+)', ddg_res.text)
        
        # Duplicates hatana but order maintain rakhna
        unique_pins = []
        for pid in pin_ids:
            if pid not in unique_pins:
                unique_pins.append(pid)
                
        # STEP 2: Har ek Pin ke andar ghuskar Video ya HD Photo nikalna
        for pid in unique_pins[:15]:  # 🔥 Maximum 15 results nikalenge!
            pin_url = f"https://www.pinterest.com/pin/{pid}/"
            try:
                # Pin ka page fetch karna (fast timeout ke sath)
                p_res = requests.get(pin_url, headers=headers, timeout=4)
                html = p_res.text.replace("\\/", "/")
                
                media_type = "image"
                media_url = ""
                
                # 🎥 CHECK FOR VIDEO (MP4)
                video_matches = re.findall(r'(https://[^"\'\s]+\.mp4)', html)
                if video_matches:
                    media_type = "video"
                    media_url = video_matches[0]
                    # Sabse highest quality (720p/1080p) dhundhna
                    for v in video_matches:
                        if "720p" in v or "1080p" in v or "v1.pinimg.com" in v:
                            media_url = v
                            break
                else:
                    # 🖼️ CHECK FOR HD IMAGE
                    og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html) or \
                               re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
                    if og_match:
                        # Low quality ko High Quality me convert karna
                        media_url = og_match.group(1).replace("/736x/", "/originals/").replace("/564x/", "/originals/").split('?')[0]
                        
                # Title nikalna
                title_match = re.search(r'<title>(.*?)</title>', html)
                title = title_match.group(1).replace(" | Pinterest", "") if title_match else f"{query} Pin"
                
                # Agar video/image mil gaya toh list me daal do
                if media_url:
                    final_results.append({
                        "type": media_type,
                        "media_url": media_url,
                        "title": title.strip(),
                        "pin_url": pin_url
                    })
                    
            except Exception:
                continue # Agar koi ek pin load hone me fail ho, toh next par jao
                
        if len(final_results) > 0:
            return jsonify({"status": True, "results": final_results})
        else:
            return jsonify({"status": False, "error": "No media found in the scraped pins."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

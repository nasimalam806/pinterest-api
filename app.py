import requests
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# ULTIMATE PINTEREST SEARCH (With Failsafe Fallback)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    final_results = []
    
    try:
        # 🚀 METHOD 1: Smart Googlebot HTML Scraper (For 15 Results)
        # Pinterest Googlebot ko block nahi karta, isliye hum Google crawler bankar jayenge
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }
        search_url = f"https://www.pinterest.com/search/pins/?q={query}"
        res = requests.get(search_url, headers=headers, timeout=8)
        
        # Regex se saari image links dhundhna
        img_pattern = r'https://i\.pinimg\.com/(?:originals|736x|564x|474x|236x)/[a-fA-F0-9/]+\.(?:jpg|png)'
        raw_images = re.findall(img_pattern, res.text)
        
        seen_images = set()
        for img in raw_images:
            # Low quality image ko High Quality (originals) me convert karna
            hd_img = re.sub(r'/(?:736x|564x|474x|236x)/', '/originals/', img)
            
            if hd_img not in seen_images:
                seen_images.add(hd_img)
                final_results.append({
                    "type": "image",
                    "media_url": hd_img,
                    "title": f"Pinterest Search: {query}",
                    "pin_url": f"https://www.pinterest.com/search/pins/?q={query}"
                })
                
            if len(final_results) >= 15: # Hume 15 results chahiye
                break
                
    except Exception as e:
        pass # Agar Method 1 fail hota hai, toh rona nahi hai, aage badhna hai

    # 🚀 METHOD 2: THE FAILSAFE (Agar Method 1 se 5 se kam results aaye, toh purani API use karega)
    if len(final_results) < 5:
        try:
            final_results = [] # Purane aade-adhure results clear karna
            api_url = f"https://pinterest-api-bay.vercel.app/search/pins?q={query}"
            vercel_res = requests.get(api_url, timeout=8).json()
            
            if "items" in vercel_res:
                for item in vercel_res["items"][:15]:
                    img_url = item.get("image", "")
                    if img_url:
                        # Vercel wali choti image ko HD karna
                        hd_img = img_url.replace("236x", "originals").replace("474x", "originals")
                        final_results.append({
                            "type": "image",
                            "media_url": hd_img,
                            "title": item.get("title", f"{query}"),
                            "pin_url": item.get("url", "https://www.pinterest.com")
                        })
        except Exception as e:
            pass

    # Final Output Bhejna
    if final_results:
        return jsonify({"status": True, "results": final_results[:15]})
    else:
        return jsonify({"status": False, "error": "No results found. Pinterest Server Down."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

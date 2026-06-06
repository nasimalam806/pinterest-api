import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==========================================
# ULTIMATE PINTEREST SEARCH (3x Multi-Search Hack)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    final_results = []
    seen_urls = set()
    
    # 🔥 SMART HACK: API sirf 5 result deti hai, isliye hum 3 variations search karenge!
    search_queries = [
        query, 
        f"{query} photos", 
        f"{query} aesthetic"
    ]
    
    try:
        for q in search_queries:
            # Purani working API jisme se 5 result aate the
            api_url = f"https://pinterest-api-bay.vercel.app/search/pins?q={q}&compact=true"
            res = requests.get(api_url, timeout=7).json()
            
            if "items" in res:
                for item in res["items"]:
                    img_url = item.get("image", "")
                    if img_url:
                        # Low-quality image ko original (High Quality) banayenge
                        hd_img = img_url.replace("236x", "originals").replace("474x", "originals")
                        
                        # Duplicate image check
                        if hd_img not in seen_urls:
                            seen_urls.add(hd_img)
                            final_results.append({
                                "type": "image",
                                "media_url": hd_img,
                                "title": item.get("title", f"{query} Image"),
                                "pin_url": item.get("url", "https://www.pinterest.com")
                            })
                            
                    # Agar 15 results poore ho gaye toh break
                    if len(final_results) >= 15:
                        break
                        
            if len(final_results) >= 15:
                break
                
        if len(final_results) > 0:
            return jsonify({"status": True, "results": final_results})
        else:
            return jsonify({"status": False, "error": "No results found. API might be down."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

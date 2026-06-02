# ==========================================
# 2. ULTIMATE PINTEREST SEARCH (No 3rd Party API, No Limits)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    try:
        # 🚀 Vercel API hata diya hai, ab seedha Pinterest se data nikalenge
        url = f"https://in.pinterest.com/search/pins/?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        
        # Pinterest ke hidden JSON data ko HTML se extract karna
        match = re.search(r'<script id="__PWS_DATA__" type="application/json">(.*?)</script>', res.text)
        
        if not match:
            return jsonify({"status": False, "error": "Pinterest data block or layout changed."})
            
        import json # Failsafe
        data = json.loads(match.group(1))
        pins_dict = data.get("props", {}).get("initialReduxState", {}).get("pins", {})
        
        final_results = []
        
        for pin_id, pin_data in pins_dict.items():
            if len(final_results) >= 15: # 🔥 Yahan humne limit 15 set ki hai!
                break
                
            # Original (High Quality) Image URL nikalna
            images = pin_data.get("images", {})
            media_url = images.get("orig", {}).get("url")
            
            if not media_url:
                continue
                
            title = pin_data.get("title", "")
            if not title:
                title = pin_data.get("grid_title", "Pinterest Search")
                
            pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
            
            final_results.append({
                "type": "image", # Fast search ke liye images support
                "media_url": media_url,
                "title": title,
                "pin_url": pin_url
            })
            
        if final_results:
            return jsonify({"status": True, "results": final_results})
        else:
            return jsonify({"status": False, "error": "No results found for this keyword."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

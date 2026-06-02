# ==========================================
# 2. ULTIMATE PINTEREST SEARCH (Internal AJAX API Bypass)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    try:
        import urllib.parse
        import json
        
        # Pinterest ka hidden backend server jo direct data bhejta hai
        options = {"query": query, "scope": "pins", "bookmarks": [""], "page_size": 25}
        data_param = {"options": options, "context": {}}
        encoded_data = urllib.parse.quote(json.dumps(data_param))
        
        url = f"https://www.pinterest.com/resource/BaseSearchResource/get/?source_url=/search/pins/?q={query}&data={encoded_data}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res_data = res.json()
        
        # Data me se list nikalna
        results = res_data.get("resource_response", {}).get("data", {}).get("results", [])
        
        final_results = []
        
        for item in results:
            if len(final_results) >= 15: # 🔥 Limit 15 kar di gayi hai (Bot 10 dikhayega)
                break
                
            images = item.get("images", {})
            media_url = images.get("orig", {}).get("url")
            
            # Agar image URL nahi mila toh chhod do
            if not media_url:
                continue
                
            title = item.get("title", "")
            if not title:
                title = item.get("grid_title", "Pinterest Search")
                
            pin_id = item.get("id")
            pin_url = f"https://www.pinterest.com/pin/{pin_id}/"
            
            final_results.append({
                "type": "image", 
                "media_url": media_url,
                "title": title,
                "pin_url": pin_url
            })
            
        if len(final_results) > 0:
            return jsonify({"status": True, "results": final_results})
        else:
            return jsonify({"status": False, "error": "No results found for this keyword."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

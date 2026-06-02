# ==========================================
# 2. UPDATED: PINTEREST SEARCH ENDPOINT (Super Fast - up to 15 Results)
# ==========================================
@app.route('/search_api')
def search_pins():
    query = request.args.get('q')
    if not query:
        return jsonify({"status": False, "error": "Query parameter is missing."}), 400
    
    try:
        # Vercel API se restrict parameters hata diye hain taaki max results aayein
        api_url = f"https://pinterest-api-bay.vercel.app/search/pins?q={query}"
        response = requests.get(api_url).json()
        
        if "items" in response and len(response["items"]) > 0:
            final_results = []
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            }
            
            # Loop chalana max 15 results ke liye
            for item in response["items"][:15]:
                pin_url = item.get("url")
                title = item.get("title", "Pinterest Search")
                media_url = item.get("image", "") 
                media_type = "image"
                
                try:
                    # 🔥 SMART TRICK: Image ko bina deep scrape kiye sidha HD/Original me convert karna
                    if media_url and "236x" in media_url:
                        hd_image_url = media_url.replace("236x", "originals")
                    elif media_url and "564x" in media_url:
                        hd_image_url = media_url.replace("564x", "originals")
                    else:
                        hd_image_url = media_url

                    # Sirf video check karne ke liye fast request (Timeout 3 sec rakha hai taaki server hang na ho)
                    pin_html_res = requests.get(pin_url, headers=headers, allow_redirects=True, timeout=3)
                    html_content = pin_html_res.text.replace("\\/", "/")
                    
                    video_matches = re.findall(r'(https://[^"\'\s]+\.mp4)', html_content)
                    
                    if video_matches:
                        media_type = "video"
                        media_url = video_matches[0]
                        for v in video_matches:
                            # Sabse acchi quality ka video dhundhna
                            if "720p" in v or "1080p" in v or "v1.pinimg.com" in v:
                                media_url = v
                                break
                    else:
                        # Agar video nahi hai, toh upar banayi HD image use karenge
                        media_url = hd_image_url
                            
                    # List me add karna
                    final_results.append({
                        "type": media_type,
                        "media_url": media_url,
                        "title": title,
                        "pin_url": pin_url
                    })
                except Exception:
                    # Agar kisi pin me error aaye ya timeout ho, toh backup image bhej do aur aage badho
                    if media_url:
                        final_results.append({
                            "type": "image",
                            "media_url": media_url.replace("236x", "originals"),
                            "title": title,
                            "pin_url": pin_url
                        })
            
            if final_results:
                return jsonify({"status": True, "results": final_results})
            else:
                return jsonify({"status": False, "error": "Media extract nahi ho paya."})
        else:
            return jsonify({"status": False, "error": "No results found for this keyword."})
            
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

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
# 3. PINTEREST PROFILE ENDPOINT (Ultimate Fix)
# ==========================================
@app.route('/profile_api')
def fetch_profile():
    username = request.args.get('user')
    if not username:
        return jsonify({"status": False, "error": "Username parameter is missing."}), 400
        
    username = username.replace("@", "")
    url = f"https://www.pinterest.com/{username}/"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }
        res = requests.get(url, headers=headers, timeout=10)
        html = res.text
        
        name = username
        title_match = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html) or \
                      re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            raw_name = title_match.group(1)
            name = re.split(r' - | \| | \(', raw_name)[0].strip()
            if name.lower() == "pinterest": 
                name = username
                
        bio = ""
        bio_match = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html)
        if bio_match:
            bio = bio_match.group(1).replace('&quot;', '"').replace('&#39;', "'").strip()
            if "See what" in bio and "has discovered on Pinterest" in bio:
                bio = ""
        
        if not bio:
            about_match = re.search(r'"about"\s*:\s*"([^"]+)"', html, re.IGNORECASE)
            if about_match:
                bio = about_match.group(1).replace('\\u0026', '&').replace('\\"', '"').replace('\\n', ' ').strip()

        pic_url = ""
        pic_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if pic_match:
            raw_pic = pic_match.group(1)
            pic_url = raw_pic.replace("\\/", "/").replace("&amp;", "&").replace("280x280", "originals").replace("736x", "originals")

        followers = "0"
        following = "0"
        total_pins = "0"
        
        f_match = re.search(r'"follower_?Count"\s*:\s*(\d+)', html, re.IGNORECASE)
        if f_match: followers = f_match.group(1)
        
        fw_match = re.search(r'"following_?Count"\s*:\s*(\d+)', html, re.IGNORECASE)
        if fw_match: following = fw_match.group(1)
        
        p_match = re.search(r'"pin_?Count"\s*:\s*(\d+)', html, re.IGNORECASE)
        if p_match: total_pins = p_match.group(1)

        if followers == "0" and following == "0" and total_pins == "0" and not pic_url:
            return jsonify({"status": False, "error": "Profile fetch nahi ho paayi. Shayad Pinterest ne block kiya hai ya user exist nahi karta."})

        return jsonify({
            "status": True,
            "username": username,
            "name": name,
            "bio": bio,
            "followers": followers,
            "following": following,
            "total_pins": total_pins,
            "pic_url": pic_url,
            "profile_url": url
        })
        
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500
# ==========================================
# 4. INSTAGRAM FETCH ENDPOINT (Ensta - Guest Mode)
# ==========================================
@app.route('/insta_fetch')
def fetch_insta():
    url = request.args.get('url')
    if not url:
        return jsonify({"status": False, "error": "URL parameter is missing."}), 200
    
    try:
        from ensta import Guest
        import re
        
        # Ensta ko chalane ke liye URL se "shortcode" nikalna zaroori hai
        # Example: https://www.instagram.com/p/DZXoa7LIasL/ -> DZXoa7LIasL
        match = re.search(r"(?:p|reel|tv|reels)/([^/?#&]+)", url)
        if not match:
            return jsonify({"status": False, "error": "Instagram link invalid hai ya shortcode nahi mil raha."}), 200
        
        shortcode = match.group(1)
        
        # Bina login wala Ensta instance (Guest Mode)
        guest = Guest()
        
        # Post ki details fetch karne ka try
        # Note: Agar Instagram Guest mode ko block karega, toh yahan Exception aayega
        post_data = guest.post(shortcode)
        
        if not post_data:
            return jsonify({"status": False, "error": "Ensta ne data return nahi kiya. Shayad Login required hai."}), 200
            
        # Video ya Image URL nikalna
        media_url = ""
        media_type = "image"
        
        # Ensta object ke attributes check kar rahe hain
        if hasattr(post_data, 'video_url') and post_data.video_url:
            media_url = post_data.video_url
            media_type = "video"
        elif hasattr(post_data, 'display_url') and post_data.display_url:
            media_url = post_data.display_url
            
        if not media_url:
            return jsonify({"status": False, "error": "Post mil gayi par media URL extract nahi ho paya."}), 200
            
        return jsonify({
            "status": True,
            "type": media_type,
            "media_url": media_url,
            "title": f"Insta Media: {shortcode}",
            "source_url": url
        }), 200
        
    except ImportError:
        return jsonify({"status": False, "error": "Server par 'ensta' install nahi hai. Pehle 'pip install ensta' run karein."}), 200
    except Exception as e:
        # Agar block hota hai ya Ensta fail hota hai, toh error JSON mein aayega, server crash nahi hoga
        return jsonify({"status": False, "error": f"Ensta failed: {str(e)}"}), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

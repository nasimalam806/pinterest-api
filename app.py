from flask import Flask, request, jsonify
import requests
import re
import json
import urllib.parse

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
# 3. PINTEREST PROFILE ENDPOINT (Internal AJAX Bypass)
# ==========================================
@app.route('/profile_api')
def fetch_profile():
    username = request.args.get('user')
    if not username:
        return jsonify({"status": False, "error": "Username parameter is missing."}), 400
        
    username = username.replace("@", "").strip()
    
    try:
        # Pinterest ka internal backend server jo sirf JSON data bhejta hai
        options = {"username": username}
        data_param = {"options": options, "context": {}}
        encoded_data = urllib.parse.quote(json.dumps(data_param))
        
        # Hidden API URL
        url = f"https://www.pinterest.com/resource/UserResource/get/?source_url=/{username}/&data={encoded_data}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        res = requests.get(url, headers=headers, timeout=10)
        res_data = res.json()
        
        user_data = res_data.get("resource_response", {}).get("data", {})
        
        if not user_data:
            return jsonify({"status": False, "error": "User not found or data blocked."})
            
        # Extract Exact & Accurate Stats directly from Database Payload
        name = user_data.get("full_name", username)
        bio = user_data.get("about", "")
        followers = str(user_data.get("follower_count", "0"))
        following = str(user_data.get("following_count", "0"))
        total_pins = str(user_data.get("pin_count", "0"))
        
        # Extract Image (High Quality guaranteed)
        pic_url = user_data.get("image_xlarge_url", "")
        if pic_url:
            pic_url = pic_url.replace("280x280", "originals").replace("736x", "originals")
            
        return jsonify({
            "status": True,
            "username": username,
            "name": name.strip(),
            "bio": bio,
            "followers": followers,
            "following": following,
            "total_pins": total_pins,
            "pic_url": pic_url,
            "profile_url": f"https://www.pinterest.com/{username}/"
        })
        
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

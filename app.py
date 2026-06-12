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
# 4. INSTAGRAM FETCH ENDPOINT (V8 Final Fix & Cloudflare Bypass)
# ==========================================
@app.route('/insta_fetch')
def fetch_insta():
    url = request.args.get('url')
    if not url:
        return jsonify({"status": False, "error": "URL parameter is missing."}), 400
    
    try:
        # V8 API ke liye alag-alag servers aur unke strictly matching origins
        cobalt_servers = [
            {"api": "https://api.cobalt.tools/", "origin": "https://cobalt.tools"},
            {"api": "https://api.w0n.st/", "origin": "https://w0n.st"},
            {"api": "https://cobalt.wuk.sh/", "origin": "https://cobalt.wuk.sh"}
        ]
        
        payload = {"url": url}
        res = None
        last_error = "Sabhi servers fail ho gaye."
        
        for server in cobalt_servers:
            # Har request ke sath frontend origin match karna zaroori hai V8 mein
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": server["origin"],
                "Referer": server["origin"] + "/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            
            try:
                res = requests.post(server["api"], json=payload, headers=headers, timeout=12)
                if res.status_code == 200:
                    break # Success! Loop se bahar niklo
                else:
                    # Agar error aata hai to debug ke liye save karo
                    last_error = f"Server {server['api']} Error {res.status_code}: {res.text[:100]}"
            except Exception as e:
                last_error = f"Server {server['api']} timeout ya connect nahi hua."
                continue
                
        # Agar saare servers fail ho gaye 200 OK dene mein
        if not res or res.status_code != 200:
            return jsonify({"status": False, "error": f"Bhai download fail ho gaya. Detail: {last_error}"})
            
        data = res.json()
        
        # --- V8 API Response Handle Karna (Added 'tunnel') ---
        
        if data.get("status") == "picker":
            items = data.get("picker", [])
            media_urls = [item.get("url") for item in items]
            return jsonify({
                "status": True,
                "type": "carousel",
                "media_urls": media_urls, 
                "title": "Instagram Carousel",
                "source_url": url
            })
        
        # V8 mein proxied content ke liye 'tunnel' use hota hai
        elif data.get("status") in ["redirect", "stream", "success", "tunnel"]:
            media_url = data.get("url")
            media_type = "video" if "mp4" in media_url or "reel" in url.lower() else "image"
            return jsonify({
                "status": True,
                "type": media_type,
                "media_url": media_url, 
                "title": "Instagram Media",
                "source_url": url
            })
        else:
            return jsonify({"status": False, "error": f"Media nikal nahi paya. API Status: {data.get('status', 'Unknown')}"})

    except Exception as e:
        return jsonify({"status": False, "error": f"Python Code Error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

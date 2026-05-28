from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Pinterest Wrapper API is Running!"

@app.route('/fetch')
def fetch_pin():
    link = request.args.get('url')
    if not link:
        return jsonify({"status": False, "error": "URL parameter missing hai."}), 400
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        res = requests.get(link, headers=headers, allow_redirects=True)
        html_content = res.text
        html_content = html_content.replace("\\/", "/")
        
        title = "Pinterest Download"
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title = title_match.group(1).replace(" | Pinterest", "").strip()

        # 1. VIDEO CHECK (.mp4) - (Yeh bilkul sahi kaam kar raha hai)
        video_matches = re.findall(r'(https://[^"\'\s]+\.mp4)', html_content)
        
        if video_matches:
            video_url = video_matches[0] 
            for v in video_matches:
                if "720p" in v or "1080p" in v or "v1.pinimg.com" in v:
                    video_url = v
            
            return jsonify({
                "status": True, 
                "type": "video", 
                "title": title,
                "media_url": video_url
            })

        # 2. FIXED IMAGE CHECK (Meta Tag Target - No Logo Mistakes)
        image_url = None
        
        # Yeh regex strictly 'og:image' tag me se sirf main post ki photo nikalega, chahe attributes ka order kuch bhi ho
        og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_content) or \
                   re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html_content)
        
        if og_match:
            image_url = og_match.group(1).strip()
            # Image ko hamesha high-quality (originals) me badalna agar wo choti size me ho
            image_url = image_url.replace("/736x/", "/originals/").replace("/564x/", "/originals/")
            image_url = image_url.split('?')[0] # Faltu query params saaf karna

        # Fallback: Agar kisi wajah se meta tag fail ho, toh hi purana originals wala tareeka chalega
        if not image_url:
            image_matches = re.findall(r'(https://i\.pinimg\.com/originals/[^"\'\s>]+)', html_content)
            if image_matches:
                image_url = image_matches[0].split('?')[0]

        if image_url:
            return jsonify({
                "status": True, 
                "type": "image", 
                "title": title,
                "media_url": image_url
            })

        return jsonify({"status": False, "error": "Link se media nikal nahi paya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

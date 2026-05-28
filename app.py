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

        # 1. Sabse pehle VIDEO (.mp4) dhoondhna
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

        # 2. Agar video NAHI hai, tab MAIN IMAGE dhoondhna (Meta Tag ke through)
        og_image_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html_content)
        
        if og_image_match:
            image_url = og_image_match.group(1)
            # Agar image 736x size ki hai, toh usko 'originals' (High Quality) me convert karne ka try karenge
            image_url = image_url.replace("736x", "originals")
            
            return jsonify({
                "status": True, 
                "type": "image", 
                "title": title,
                "media_url": image_url
            })
            
        # 3. Fallback: Agar Meta tag bhi na mile
        image_matches = re.findall(r'(https://i\.pinimg\.com/(?:originals|736x)/[^"\'\s]+\.(?:jpg|jpeg|png|gif|webp))', html_content)
        if image_matches:
            return jsonify({
                "status": True, 
                "type": "image", 
                "title": title,
                "media_url": image_matches[0]
            })

        return jsonify({"status": False, "error": "Link se media nikal nahi paya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

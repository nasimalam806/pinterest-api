from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Pinterest True Hybrid API is Running!"

@app.route('/fetch')
def fetch_pin():
    link = request.args.get('url')
    if not link:
        return jsonify({"status": False, "error": "URL parameter missing hai."}), 400
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        # Step 1: Link ko open karna taaki original lamba link mil jaye
        res = requests.get(link, headers=headers, allow_redirects=True)
        expanded_link = res.url
        html_content = res.text.replace("\\/", "/")
        
        title = "Pinterest Download"
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title = title_match.group(1).replace(" | Pinterest", "").strip()

        # ---------- PART 1: VIDEO CHECK (Best from 2nd code) ----------
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

        # ---------- PART 2: IMAGE CHECK (Best from 1st code - Vercel API) ----------
        # Expanded link se ID nikalna
        pin_id = None
        for part in expanded_link.split('/'):
            if part.isdigit():
                pin_id = part
                break
                
        if pin_id:
            api_url = f"https://pinterest-api-bay.vercel.app/pin/{pin_id}?compact=true"
            # Vercel API se exact data mangwana (No logo mistakes)
            response = requests.get(api_url).json()
            
            if "image" in response:
                return jsonify({
                    "status": True, 
                    "type": "image",
                    "title": response.get("title", title),
                    "media_url": response["image"]
                })
        
        return jsonify({"status": False, "error": "Link se media nikal nahi paya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

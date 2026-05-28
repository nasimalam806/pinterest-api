from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Pinterest Hybrid Wrapper API is Running!"

@app.route('/fetch')
def fetch_pin():
    link = request.args.get('url')
    if not link:
        return jsonify({"status": False, "error": "URL parameter missing hai."}), 400
    
    try:
        # Step 1: Link ko expand karna agar pin.it hai
        if "pin.it" in link:
            expand_req = requests.get(link, allow_redirects=True)
            link = expand_req.url

        # Step 2: Vercel API ke liye ID nikalna
        pin_id = None
        for part in link.split('/'):
            if part.isdigit():
                pin_id = part
                break

        # Browser headers (HTML scrape ke liye)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        # HTML download karna
        res = requests.get(link, headers=headers, allow_redirects=True)
        html_content = res.text.replace("\\/", "/")
        
        title = "Pinterest Download"
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title = title_match.group(1).replace(" | Pinterest", "").strip()

        # ---------- PART 1: VIDEO CHECK (From 2nd Code) ----------
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

        # ---------- PART 2: IMAGE CHECK (From 1st Code - Vercel API) ----------
        if pin_id:
            api_url = f"https://pinterest-api-bay.vercel.app/pin/{pin_id}?compact=true"
            response = requests.get(api_url).json()
            
            if "image" in response:
                return jsonify({
                    "status": True, 
                    "type": "image",
                    "title": response.get("title", title), # Agar API me title na ho toh HTML wala use karega
                    "media_url": response["image"]
                })
        
        return jsonify({"status": False, "error": "Link se valid media (video/image) nahi mil paya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

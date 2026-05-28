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
        
        # Request bhejna aur expand karna
        res = requests.get(link, headers=headers, allow_redirects=True)
        html_content = res.text.replace("\\/", "/")
        
        title = "Pinterest Download"
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title = title_match.group(1).replace(" | Pinterest", "").strip()

        # ---------- 1. VIDEO CHECK (Working perfect) ----------
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

        # ---------- 2. STRICT ORIGINAL IMAGE CHECK ----------
        # Hum strictly Vercel aur baaki sab chhod kar sirf 'originals' folder scan karenge
        image_matches = re.findall(r'(https://i\.pinimg\.com/originals/[^"\'\s>]+)', html_content)
        
        if image_matches:
            # Agar bohot saare mil gaye toh pehla wala hi main image hota hai
            image_url = image_matches[0].split('?')[0].split('"')[0].split("'")[0]
            
            return jsonify({
                "status": True, 
                "type": "image", 
                "title": title,
                "media_url": image_url
            })
            
        # Agar by chance originals me na mile, toh second strict check:
        # Hum sirf un images ko lenge jinka resolution format likha hota hai (logos me resolution nahi hota)
        fallback_matches = re.findall(r'(https://i\.pinimg\.com/(?:736x|564x|474x)/[^"\'\s>]+\.(?:jpg|jpeg|png))', html_content)
        if fallback_matches:
             image_url = fallback_matches[0].split('?')[0].split('"')[0].split("'")[0]
             return jsonify({
                "status": True, 
                "type": "image", 
                "title": title,
                "media_url": image_url
            })


        return jsonify({"status": False, "error": "Link se valid media nikal nahi paya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

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
        # Browser jaisi request bhejne ke liye Headers (taaki Pinterest block na kare)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        
        # Link ko open karke page ka pura code (HTML) download karna
        res = requests.get(link, headers=headers, allow_redirects=True)
        html_content = res.text
        
        # Title nikalna (Agar mil jaye toh)
        title = "Pinterest Download"
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title = title_match.group(1).replace(" | Pinterest", "")

        # 1. Sabse pehle VIDEO dhoondhna (.mp4 files)
        video_matches = re.findall(r'(https://[^"]+\.mp4)', html_content)
        
        if video_matches:
            # Agar bahut saari quality mili toh 720p/HD wali select karna
            video_url = video_matches[0]
            for v in video_matches:
                if "720" in v or "1080" in v or "v1.pinimg.com/videos" in v:
                    video_url = v
                    break
            
            # URL me agar ajeeb slashes (\/) hon toh unko theek karna
            video_url = video_url.replace("\\/", "/")
            
            return jsonify({
                "status": True, 
                "type": "video", 
                "title": title,
                "media_url": video_url
            })

        # 2. Agar video NAHI hai, toh ORIGINAL IMAGE dhoondhna
        image_matches = re.findall(r'(https://i\.pinimg\.com/originals/[^"]+\.(?:jpg|png|gif))', html_content)
        
        if image_matches:
            image_url = image_matches[0].replace("\\/", "/")
            return jsonify({
                "status": True, 
                "type": "image", 
                "title": title,
                "media_url": image_url
            })
            
        # Agar dono nahi mile
        return jsonify({"status": False, "error": "Link se media nikal nahi paya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

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

        # 1. VIDEO CHECK (.mp4)
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

        # 2. BULLETPROOF IMAGE CHECK (With Live Validation for Telegram)
        image_matches = re.findall(r'(https://i\.pinimg\.com/[^"\'\s>]+\.(?:jpg|jpeg|png))', html_content)
        
        if image_matches:
            # Duplicate links hata kar list choti karna taaki fast chale
            image_matches = list(set(image_matches))
            valid_image_url = None
            
            # Step A: Pehle 'originals' (HQ) check karna
            for img in image_matches:
                if "/originals/" in img:
                    try:
                        # Link ko live check karna ki wo actual Image hai ya Error page
                        head_res = requests.head(img, timeout=2)
                        if head_res.status_code == 200 and 'image' in head_res.headers.get('Content-Type', ''):
                            valid_image_url = img
                            break
                    except:
                        continue
            
            # Step B: Agar HQ valid nahi hai, toh '736x' (Medium) check karna
            if not valid_image_url:
                for img in image_matches:
                    if "/736x/" in img:
                        try:
                            head_res = requests.head(img, timeout=2)
                            if head_res.status_code == 200 and 'image' in head_res.headers.get('Content-Type', ''):
                                valid_image_url = img
                                break
                        except:
                            continue
                            
            # Step C: Fallback, jo bhi pehli valid image mil jaye
            if not valid_image_url:
                for img in image_matches:
                    try:
                        head_res = requests.head(img, timeout=2)
                        if head_res.status_code == 200 and 'image' in head_res.headers.get('Content-Type', ''):
                            valid_image_url = img
                            break
                    except:
                        continue

            if valid_image_url:
                return jsonify({
                    "status": True, 
                    "type": "image", 
                    "title": title,
                    "media_url": valid_image_url
                })

        return jsonify({"status": False, "error": "Link se valid media nahi mil paya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

from flask import Flask, request, jsonify
import requests

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
        if "pin.it" in link:
            expand_req = requests.get(link, allow_redirects=True)
            link = expand_req.url
            
        pin_id = None
        for part in link.split('/'):
            if part.isdigit():
                pin_id = part
                break
                
        if not pin_id:
            return jsonify({"status": False, "error": "Pin ID extract nahi ho paya."}), 400
            
        api_url = f"https://pinterest-api-bay.vercel.app/pin/{pin_id}?compact=true"
        response = requests.get(api_url).json()
        
        # NAYA LOGIC: Pehle video check karo, agar nahi hai toh image do
        if "video" in response and response["video"]:
            return jsonify({
                "status": True, 
                "type": "video",  # TBC ko batane ke liye ki ye video hai
                "title": response.get("title", "Pinterest Video"),
                "media_url": response["video"]
            })
        elif "image" in response and response["image"]:
            return jsonify({
                "status": True, 
                "type": "image",  # TBC ko batane ke liye ki ye image hai
                "title": response.get("title", "Pinterest Image"),
                "media_url": response["image"]
            })
        else:
            return jsonify({"status": False, "error": "Media nahi mila."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

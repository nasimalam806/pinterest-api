from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Pinterest Wrapper API is Running!"

@app.route('/fetch')
def fetch_pin():
    # URL parameter se link lenge (e.g., /fetch?url=https://pin.it/...)
    link = request.args.get('url')
    
    if not link:
        return jsonify({"status": False, "error": "Bhai, URL parameter missing hai."}), 400
    
    try:
        # 1. Agar pin.it shortlink hai, toh usko expand karenge
        if "pin.it" in link:
            expand_req = requests.get(link, allow_redirects=True)
            link = expand_req.url
            
        # 2. Link me se 15-18 digit ka Pin ID nikalna
        pin_id = None
        for part in link.split('/'):
            if part.isdigit():
                pin_id = part
                break
                
        if not pin_id:
            return jsonify({"status": False, "error": "Link se Pin ID extract nahi ho paya."}), 400
            
        # 3. Main Vercel API ko hit karke data nikalna
        api_url = f"https://pinterest-api-bay.vercel.app/pin/{pin_id}?compact=true"
        response = requests.get(api_url).json()
        
        # 4. TBC ke liye Clean JSON return karna
        if "image" in response:
            return jsonify({
                "status": True, 
                "title": response.get("title", "Pinterest Download"),
                "media_url": response["image"]
            })
        else:
            return jsonify({"status": False, "error": "Media nahi mila ya API ne error diya."})

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
    
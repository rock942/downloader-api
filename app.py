from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import yt_dlp
import re

app = Flask(__name__)
# CORS enabled for frontend-backend communication
CORS(app) 

# SECURITY: Strict URL validation
URL_REGEX = re.compile(r'^(https?://)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$')

# ROUTE 1: Yeh tumhari website ka UI (index.html) show karega
@app.route('/')
def home():
    # Flask automatically 'templates' folder ke andar index.html ko dhoondh lega
    return render_template('index.html')

# ROUTE 2: Yeh API videos ke direct download links nikalegi
@app.route('/api/extract', methods=['POST'])
def extract_media():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'success': False, 'error': 'Link nahi mila. Kripya URL enter karein.'}), 400
        
    url = data['url'].strip()

    if not URL_REGEX.match(url):
        return jsonify({'success': False, 'error': 'URL galat hai. Sahi link copy karke daalein.'}), 400

    # SPEED & SECURITY SETTINGS: yt-dlp configurations
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'nocheckcertificate': True,
        'extract_flat': False, # Pura data extract karne ke liye
        'socket_timeout': 15,  # SPEED HACK: Agar koi link 15 second mein load na ho, toh server hang nahi hoga
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Unknown Video')
            thumbnail = info.get('thumbnail', '')
            formats = info.get('formats', [])
            
            clean_formats = []
            for f in formats:
                if f.get('url') and f.get('ext') in ['mp4', 'm4a', 'mp3']:
                    clean_formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('format_note') or f.get('resolution', 'Audio'),
                        'filesize': f.get('filesize', 0),
                        'url': f.get('url') 
                    })

            # Sort formats by filesize (Best quality on top)
            clean_formats = sorted(clean_formats, key=lambda x: x['filesize'] or 0, reverse=True)

            return jsonify({
                'success': True,
                'title': title,
                'thumbnail': thumbnail,
                'formats': clean_formats[:8] # Top 8 best qualities show karega
            })

    except Exception as e:
        print(f"Internal Error: {e}") 
        return jsonify({
            'success': False, 
            'error': 'Is video ka link extract nahi ho paya. Kripya koi aur link try karein.'
        }), 400

if __name__ == '__main__':
    # Local par testing ke liye debug=True hai
    app.run(debug=True, port=5000)

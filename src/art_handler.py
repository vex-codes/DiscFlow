import requests
from PIL import Image, ImageDraw, ImageOps
from io import BytesIO
from PySide6.QtGui import QPixmap, QImage

def fetch_album_art(artist, album):
    """
    Fetches album art URL from iTunes Search API.
    Tries to get a high-resolution version.
    """
    if not artist or not album:
        return None
        
    try:
        # Search for the specific song first
        query = f"{artist} {album}"
        url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data['resultCount'] > 0:
            artwork_url = data['results'][0].get('artworkUrl100')
            if artwork_url:
                return artwork_url.replace('100x100bb', '600x600bb')
        
        # Fallback to album search if song not found
        url = f"https://itunes.apple.com/search?term={query}&entity=album&limit=1"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if data['resultCount'] > 0:
            artwork_url = data['results'][0].get('artworkUrl100')
            if artwork_url:
                return artwork_url.replace('100x100bb', '600x600bb')
                
    except Exception as e:
        print(f"Error fetching art: {e}")
    
    return None

def process_art_to_circle(image_data_or_url):
    """
    Downloads image (if URL) or takes bytes, crops to circle, 
    and returns a QPixmap.
    """
    try:
        if isinstance(image_data_or_url, str):
            response = requests.get(image_data_or_url, timeout=5)
            img = Image.open(BytesIO(response.content))
        else:
            img = Image.open(BytesIO(image_data_or_url))
            
        # Convert to RGBA
        img = img.convert("RGBA")
        
        # Create circular mask
        size = (min(img.size), min(img.size))
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        
        # Crop and apply mask
        output = ImageOps.fit(img, size, centering=(0.5, 0.5))
        output.putalpha(mask)
        
        # Convert to QPixmap
        data = output.tobytes("raw", "RGBA")
        qim = QImage(data, output.size[0], output.size[1], QImage.Format_RGBA8888)
        return QPixmap.fromImage(qim)
        
    except Exception as e:
        print(f"Error processing art: {e}")
        return None

from PIL import Image, ImageDraw

def create_default_art():
    # Create a 300x300 transparent image
    size = (300, 300)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw black vinyl record
    draw.ellipse((10, 10, 290, 290), fill='black')
    
    # Draw grooves (subtle grey circles)
    for i in range(20, 100, 5):
        draw.ellipse((10+i, 10+i, 290-i, 290-i), outline=(30, 30, 30))
        
    # Draw white label
    draw.ellipse((100, 100, 200, 200), fill='white')
    
    # Save
    img.save('assets/default_art.png')

if __name__ == "__main__":
    create_default_art()

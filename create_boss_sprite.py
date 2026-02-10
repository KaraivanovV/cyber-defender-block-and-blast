from PIL import Image
import base64
import io

# The boss sprite provided by the user - a purple/blue cyclops creature
# Creating a simple version based on the description
# Since I can't access the exact image, I'll create a placeholder
# The user should replace this with their actual image file

# For now, create a simple 64x64 purple boss sprite
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
pixels = img.load()

# Simple purple cyclops shape
for y in range(64):
    for x in range(64):
        # Create a circular purple body
        dx = x - 32
        dy = y - 32
        dist = (dx**2 + dy**2) ** 0.5
        
        if dist < 25:
            # Purple body
            pixels[x, y] = (150, 100, 255, 255)
        elif dist < 28:
            # Black outline
            pixels[x, y] = (0, 0, 0, 255)
        
        # Eye area (make it lighter)
        if 20 < x < 44 and 20 < y < 35 and dist < 25:
            pixels[x, y] = (180, 140, 255, 255)

img.save('assets/boss_first.png')
print("Boss sprite created at assets/boss_first.png")
print("NOTE: This is a placeholder. Please replace with your actual boss sprite image.")

import sys
import subprocess
import os

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

img_path = os.path.join("static", "logo.png")
img = Image.open(img_path)
width, height = img.size

# A imagem original gerada pela IA é quadrada (provavelmente 1024x1024).
# Vamos cortar 30% do topo e 30% do fundo para deixá-la puramente retangular (widescreen).
top = height * 0.30
bottom = height * 0.70

cropped_img = img.crop((0, top, width, bottom))
cropped_img.save(img_path)
print("Imagem recortada com sucesso!")

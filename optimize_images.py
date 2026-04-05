import os
from PIL import Image

# Konfiguracja
MEDIA_DIR = 'media'
QUALITY = 75  # Jakość 0-100 (75 to złoty środek)
MAX_WIDTH = 1920

def optimize():
    saved_total = 0
    print(f"--> Rozpoczynam optymalizację w: {MEDIA_DIR}")

    for filename in os.listdir(MEDIA_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filepath = os.path.join(MEDIA_DIR, filename)
            old_size = os.path.getsize(filepath)

            try:
                with Image.open(filepath) as img:
                    # 1. Zmniejsz wymiary, jeśli obraz jest gigantyczny
                    if img.width > MAX_WIDTH:
                        ratio = MAX_WIDTH / float(img.width)
                        new_height = int(float(img.height) * float(ratio))
                        img = img.resize((MAX_WIDTH, new_height), Image.Resampling.LANCZOS)

                    # 2. Skompresuj i zapisz (z zachowaniem formatu)
                    if filename.lower().endswith('.png'):
                        img.save(filepath, optimize=True)
                    else:
                        img.save(filepath, quality=QUALITY, optimize=True)

                new_size = os.path.getsize(filepath)
                saved = old_size - new_size
                saved_total += saved
                
                if saved > 0:
                    print(f"[OK] {filename}: {old_size//1024}KB -> {new_size//1024}KB (Zaoszczędzone: {saved//1024}KB)")
                else:
                    print(f"[-] {filename}: Już zoptymalizowany.")

            except Exception as e:
                print(f"[BŁĄD] Nie można przetworzyć {filename}: {e}")

    print(f"\n--> GOTOWE! Całkowity zysk: {saved_total // (1024*1024)} MB")

if __name__ == "__main__":
    optimize()

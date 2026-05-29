import imageio.v3 as iio
import os, sys
import subprocess

# Tesseract kullan (EasyOCR'dan 5-10x daha hizli CPU'da)
try:
    import pytesseract
    from PIL import Image
    import numpy as np
    USE_TESSERACT = True
except ImportError:
    USE_TESSERACT = False

# EasyOCR fallback
try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

video_file = "Stake.com Animated Bonus Drop Template (30).mp4"

if not os.path.exists(video_file):
    print(f"HATA: '{video_file}' bulunamadi!")
    sys.exit(1)

print("Video okunuyor...")
frames = iio.imread(video_file, plugin="pyav")
total = len(frames)
print(f"Toplam {total} frame bulundu")

# Sadece son kismi tara (kod orada gorunuyor)
START_FRAME = 200
STEP = 5

all_texts = {}
scan_count = (total - START_FRAME) // STEP
print(f"Taranacak frame sayisi: {scan_count} (frame {START_FRAME}-{total}, adim {STEP})")

if USE_TESSERACT:
    print("Tesseract OCR kullaniliyor (hizli)...")
    
    for i in range(START_FRAME, total, STEP):
        img = Image.fromarray(frames[i])
        
        # Goruntu isleme: gri + kontrast artir
        img_gray = img.convert('L')
        img_np = np.array(img_gray)
        
        # Threshold uygula
        _, thresh = __import__('cv2').threshold(img_np, 127, 255, __import__('cv2').THRESH_BINARY)
        
        # Ayrica ters threshold da dene
        _, thresh_inv = __import__('cv2').threshold(img_np, 127, 255, __import__('cv2').THRESH_BINARY_INV)
        
        for img_variant in [img_np, thresh, thresh_inv]:
            text = pytesseract.image_to_string(Image.fromarray(img_variant), config='--psm 6')
            for line in text.split('\n'):
                line = line.strip()
                if len(line) > 3:
                    if line not in all_texts:
                        all_texts[line] = i
        
        if (i - START_FRAME) % 20 == 0:
            print(f"  Ilerleme: frame {i}/{total}...")

elif HAS_EASYOCR:
    import torch
    USE_GPU = torch.cuda.is_available()
    print(f"EasyOCR kullaniliyor (GPU: {USE_GPU})...")
    reader = easyocr.Reader(['en'], gpu=USE_GPU)
    
    for i in range(START_FRAME, total, STEP):
        results = reader.readtext(frames[i])
        for (bbox, text, confidence) in results:
            text_clean = text.strip()
            if confidence > 0.25 and len(text_clean) > 3:
                if text_clean not in all_texts:
                    all_texts[text_clean] = i
        
        if (i - START_FRAME) % 15 == 0:
            print(f"  Ilerleme: frame {i}/{total}...")
else:
    print("HATA: Ne tesseract ne de easyocr yuklu!")
    print("Kur: pip3 install pytesseract Pillow opencv-python-headless")
    print("Ve: sudo apt install tesseract-ocr")
    sys.exit(1)

print("\n" + "=" * 60)
print("TUM BULUNAN METINLER:")
print("=" * 60)
for text, frame_num in sorted(all_texts.items()):
    print(f"  Frame {frame_num:3d}: {text}")

print("\n" + "=" * 60)
print("STAKE / COM ICEREN METINLER:")
print("=" * 60)
found = False
for text, frame_num in sorted(all_texts.items()):
    if 'stake' in text.lower() or 'stak' in text.lower() or 'stakecom' in text.lower().replace('.', '').replace(' ', ''):
        print(f"  Frame {frame_num:3d}: {text}")
        found = True

if not found:
    print("  Bulunamadi. Tum metinlere yukaridan bakin.")

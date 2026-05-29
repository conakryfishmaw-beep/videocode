import imageio.v3 as iio
import cv2
import numpy as np
from PIL import Image
import os, sys

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

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


def unwarp_arc_text(img):
    """Yarim ay/kavisli metni duzlestir (polar transform)"""
    h, w = img.shape[:2]
    
    # Merkez nokta (yarim ayin merkezi)
    cx, cy = w // 2, h // 2
    
    # Polar koordinatlara cevir (kavisli yaziyi duzlestirir)
    max_radius = min(cx, cy)
    
    # Farkli yaricap ve aci araliklari dene
    results = []
    
    # Yontem 1: Tam polar transform
    polar = cv2.linearPolar(img, (cx, cy), max_radius, cv2.WARP_FILL_OUTLIERS)
    results.append(polar)
    
    # Yontem 2: Log-polar
    log_polar = cv2.logPolar(img, (cx, cy), max_radius / np.log(max_radius), cv2.WARP_FILL_OUTLIERS)
    results.append(log_polar)
    
    # Yontem 3: Ust yarim daireyi duzlestir
    # Sadece ust yarisi al ve warp
    top_half = img[0:cy, :]
    results.append(top_half)
    
    # Yontem 4: Alt yarim daireyi duzlestir
    bottom_half = img[cy:, :]
    results.append(bottom_half)
    
    return results


def preprocess_frame(frame):
    """Frame'i OCR icin hazirla"""
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    
    variants = []
    
    # Orijinal gri
    variants.append(gray)
    
    # Kontrast artir (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    variants.append(enhanced)
    
    # Binary threshold
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    variants.append(binary)
    
    # Inverse binary
    _, binary_inv = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
    variants.append(binary_inv)
    
    # Adaptive threshold
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    variants.append(adaptive)
    
    return variants


def ocr_image(img):
    """Bir goruntuden metin oku"""
    texts = set()
    
    if HAS_TESSERACT:
        # Farkli PSM modlari dene
        for psm in [6, 7, 11, 12]:
            try:
                config = f'--psm {psm} --oem 3'
                text = pytesseract.image_to_string(Image.fromarray(img), config=config)
                for line in text.split('\n'):
                    line = line.strip()
                    if len(line) > 5:
                        texts.add(line)
            except:
                pass
    
    return texts


# Ana tarama
START_FRAME = 200
STEP = 5
all_texts = {}

scan_count = (total - START_FRAME) // STEP
print(f"\nTaranacak frame sayisi: {scan_count}")
print("Kavisli metin duzlestirme + OCR uygulanacak...\n")

for i in range(START_FRAME, total, STEP):
    frame = frames[i]
    
    # 1. Normal OCR (tum frame)
    for variant in preprocess_frame(frame):
        texts = ocr_image(variant)
        for t in texts:
            if t not in all_texts:
                all_texts[t] = i
    
    # 2. Kavisli metin duzlestir ve OCR
    for variant in preprocess_frame(frame):
        unwarped_list = unwarp_arc_text(variant)
        for unwarped in unwarped_list:
            texts = ocr_image(unwarped)
            for t in texts:
                if t not in all_texts:
                    all_texts[t] = i
    
    # 3. Sadece alt yarisi tara (kod genelde altta)
    h = frame.shape[0]
    bottom = frame[h//2:, :]
    for variant in preprocess_frame(bottom):
        texts = ocr_image(variant)
        for t in texts:
            if t not in all_texts:
                all_texts[t] = i
    
    if (i - START_FRAME) % 10 == 0:
        print(f"  Frame {i}/{total}... ({len(all_texts)} metin bulundu)")

# Sonuclari filtrele
print("\n" + "=" * 60)
print("STAKE / STAKECOM ICEREN METINLER:")
print("=" * 60)
found_stake = []
for text, frame_num in sorted(all_texts.items()):
    tl = text.lower().replace(' ', '').replace('.', '')
    if 'stake' in tl or 'stak' in tl or 'stke' in tl:
        found_stake.append((frame_num, text))
        print(f"  Frame {frame_num:3d}: {text}")

if not found_stake:
    print("  Direkt 'stake' bulunamadi.")

# Uzun metinleri goster (kod genelde uzun olur)
print("\n" + "=" * 60)
print("UZUN METINLER (>15 karakter, muhtemel kod):")
print("=" * 60)
for text, frame_num in sorted(all_texts.items(), key=lambda x: -len(x[0])):
    if len(text) > 15:
        print(f"  Frame {frame_num:3d} ({len(text):2d} chr): {text}")

print(f"\nToplam {len(all_texts)} benzersiz metin bulundu.")

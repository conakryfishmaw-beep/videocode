import easyocr
import imageio.v3 as iio
import os, sys

print("EasyOCR yukleniyor (ilk seferde model indirecek)...")
reader = easyocr.Reader(['en'], gpu=False)

video_file = "Stake.com Animated Bonus Drop Template (30).mp4"

if not os.path.exists(video_file):
    print(f"HATA: '{video_file}' bulunamadi!")
    sys.exit(1)

print("Video okunuyor...")
frames = iio.imread(video_file, plugin="pyav")
print(f"Toplam {len(frames)} frame bulundu")

all_texts = {}

print("OCR taramasi basliyor (CPU, biraz zaman alacak)...")
for i in range(0, len(frames), 2):
    results = reader.readtext(frames[i])
    for (bbox, text, confidence) in results:
        text_clean = text.strip()
        if confidence > 0.25 and len(text_clean) > 3:
            if text_clean not in all_texts or all_texts[text_clean][1] < confidence:
                all_texts[text_clean] = (i, confidence)

    if (i % 20) == 0:
        print(f"  Ilerleme: {i}/{len(frames)} frame...")

print("\n" + "=" * 60)
print("TUM BULUNAN METINLER (guven > 0.25):")
print("=" * 60)
for text, (frame_num, conf) in sorted(all_texts.items(), key=lambda x: -x[1][1]):
    print(f"  Frame {frame_num:3d} [{conf:.2f}]: {text}")

print("\n" + "=" * 60)
print("STAKE ICEREN METINLER:")
print("=" * 60)
for text, (frame_num, conf) in sorted(all_texts.items(), key=lambda x: -x[1][1]):
    if 'stake' in text.lower() or 'stak' in text.lower():
        print(f"  Frame {frame_num:3d} [{conf:.2f}]: {text}")

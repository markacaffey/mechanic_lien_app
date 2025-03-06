import fitz

pdf_path = r"C:\Users\marka\Desktop\Mechanic Lien Work Space\Momentum_BMW_Mini_WP0AA2A79BL011198_MV-265-M-2.pdf"

try:
    doc = fitz.open(pdf_path)
    print("✅ PDF opened successfully!")
    doc.close()
except Exception as e:
    print("❌ Error opening PDF:", e)

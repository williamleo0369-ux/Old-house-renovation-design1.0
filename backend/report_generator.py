
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_report_image(symbol, close_price, change_pct, open_price, high, low):
    """
    Generates a daily report image with a red gradient background.
    """
    width, height = 800, 600
    
    # Create Red Gradient Background
    # Start: Dark Red (#8B0000), End: Bright Red (#FF0000)
    # We can simulate gradient by drawing lines or just use a solid color for simplicity and speed,
    # or create a simple vertical gradient.
    image = Image.new('RGB', (width, height), color='#8B0000')
    draw = ImageDraw.Draw(image)
    
    # Simple Gradient
    for y in range(height):
        r = int(139 + (255 - 139) * (y / height)) # 139 is 0x8B
        draw.line([(0, y), (width, y)], fill=(r, 0, 0))

    # Load Font (Try to load a system font, fallback to default)
    try:
        # MacOS path
        title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 60)
        text_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
        small_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
    except IOError:
        try:
            # Linux/Container path (e.g., DejaVuSans)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except IOError:
            # Fallback
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

    # Draw Text
    draw.text((50, 50), f"今日战报: {symbol}", font=title_font, fill="white")
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((50, 130), date_str, font=small_font, fill="#FFDDDD")

    # Main Price
    price_color = "white"
    draw.text((50, 200), f"收盘价: {close_price}", font=title_font, fill=price_color)
    
    # Change Pct
    pct_text = f"涨跌幅: {change_pct}%"
    draw.text((50, 280), pct_text, font=text_font, fill="yellow" if change_pct >= 0 else "green")

    # Details Box
    draw.rectangle([(40, 350), (760, 550)], outline="white", width=2)
    
    draw.text((60, 370), f"开盘: {open_price}", font=text_font, fill="white")
    draw.text((60, 430), f"最高: {high}", font=text_font, fill="white")
    draw.text((60, 490), f"最低: {low}", font=text_font, fill="white")

    # Add Watermark
    draw.text((550, 550), "QuantVisual Monitor", font=small_font, fill="#FFAAAA")

    # Save to BytesIO
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

if __name__ == "__main__":
    # Test
    img = generate_report_image("512100", 2.45, 1.25, 2.42, 2.48, 2.41)
    with open("test_report.png", "wb") as f:
        f.write(img.getbuffer())
    print("Test image saved as test_report.png")

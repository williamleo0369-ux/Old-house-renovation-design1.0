
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_report_image(symbol, close_price, change_pct, open_price, high, low, name=""):
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

    # Load Font (Priority: Local bundled font -> System -> Fallback)
    try:
        # 1. Try Local Bundled Font (Best for portability/Render)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Try OTF first (Noto Sans CJK)
        font_path = os.path.join(current_dir, "static", "fonts", "NotoSansCJKsc-Regular.otf")
        
        if os.path.exists(font_path):
            title_font = ImageFont.truetype(font_path, 60)
            text_font = ImageFont.truetype(font_path, 36)
            small_font = ImageFont.truetype(font_path, 24)
        else:
             # Try TTF (Fallback if user provided NotoSansSC-Bold.ttf manually)
             font_path_ttf = os.path.join(current_dir, "static", "fonts", "NotoSansSC-Bold.ttf")
             if os.path.exists(font_path_ttf):
                title_font = ImageFont.truetype(font_path_ttf, 60)
                text_font = ImageFont.truetype(font_path_ttf, 36)
                small_font = ImageFont.truetype(font_path_ttf, 24)
             else:
                raise IOError("Local font not found")
            
    except IOError:
        try:
            # 2. MacOS System Font
            title_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 60)
            text_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
            small_font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
        except IOError:
            try:
                # 3. Linux/Container path (e.g., DejaVuSans - No Chinese support usually)
                # Trying to find ANY Chinese font on Linux if possible
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 60)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 36)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 24)
            except IOError:
                # 4. Last Resort (Will show boxes for Chinese)
                print("Warning: No Chinese font found. Text may be garbled.")
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()

    # Draw Text
    draw.text((50, 40), f"今日战报: {symbol}", font=title_font, fill="white")
    
    # Name (if provided)
    current_y = 110
    if name:
        draw.text((50, current_y), name, font=text_font, fill="#EEEEEE")
        current_y += 40
    else:
        current_y += 10 # small padding if no name
        
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    draw.text((50, current_y), date_str, font=small_font, fill="#FFDDDD")
    
    current_y += 50 # Gap to price

    # Main Price
    price_color = "white"
    draw.text((50, current_y), f"收盘价: {close_price}", font=title_font, fill=price_color)
    
    # Change Pct
    pct_text = f"涨跌幅: {change_pct}%"
    draw.text((50, current_y + 80), pct_text, font=text_font, fill="yellow" if change_pct >= 0 else "green")

    # Details Box
    box_y = current_y + 150
    draw.rectangle([(40, box_y), (760, box_y + 200)], outline="white", width=2)
    
    draw.text((60, box_y + 20), f"开盘: {open_price}", font=text_font, fill="white")
    draw.text((60, box_y + 80), f"最高: {high}", font=text_font, fill="white")
    draw.text((60, box_y + 140), f"最低: {low}", font=text_font, fill="white")

    # Add Watermark
    draw.text((550, 550), "QuantVisual Monitor", font=small_font, fill="#FFAAAA")

    # Save to BytesIO
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

if __name__ == "__main__":
    # Test
    img = generate_report_image("512100", 2.45, 1.25, 2.42, 2.48, 2.41, name="中证500ETF")
    with open("test_report.png", "wb") as f:
        f.write(img.getbuffer())
    print("Test image saved as test_report.png")

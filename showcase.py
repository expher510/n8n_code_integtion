"""
Product Showcase Video Generator
==================================
للاستخدام في n8n Execute Command Node:

    python3 showcase.py \
      --title "احدث اجهزة كهربائية\nبالاسواق" \
      --discount "خصومات تصل الى 20٪" \
      --badge "ضمان\nسنتين" \
      --phone "+20-100-000-0000" \
      --website "www.example.com" \
      --image "/tmp/product.png" \
      --music "/tmp/music.mp3" \
      --output "/tmp/output.mp4"

متطلبات:
    pip install pillow
    apt install ffmpeg
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# 1. ARGUMENTS — بيجيب المتغيرات من n8n
# ============================================================
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--title',    default='احدث اجهزة\nكهربائية بالاسواق')
    parser.add_argument('--discount', default='خصومات تصل الى 20٪')
    parser.add_argument('--badge',    default='ضمان\nسنتين')
    parser.add_argument('--phone',    default='+123-456-7890')
    parser.add_argument('--website',  default='www.example.com')
    parser.add_argument('--image',    default='')
    parser.add_argument('--music',    default='')
    parser.add_argument('--output',   default='/tmp/showcase.mp4')
    parser.add_argument('--width',    type=int, default=1280)
    parser.add_argument('--height',   type=int, default=720)
    parser.add_argument('--duration', type=int, default=6)
    parser.add_argument('--fps',      type=int, default=30)
    parser.add_argument('--bg_left',  default='98,70,180')
    parser.add_argument('--bg_right', default='15,15,45')
    parser.add_argument('--music_volume', type=float, default=0.20)
    return parser.parse_args()


# ============================================================
# 2. FONT
# ============================================================
def load_font(size):
    candidates = [
        '/tmp/arabic.ttf',
        '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf',
        '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
        '/usr/share/fonts/truetype/arabeyes/ae_AlBattar.ttf',
        '/usr/share/fonts/opentype/noto/NotoNaskhArabic-Bold.otf',
        'C:/Windows/Fonts/arial.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()


def download_font_if_needed():
    if not os.path.exists('/tmp/arabic.ttf'):
        print('📥 بيحمّل الخط العربي...')
        result = subprocess.run([
            'wget', '-q', '-O', '/tmp/arabic.ttf',
            'https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoNaskhArabic/NotoNaskhArabic-Bold.ttf'
        ], capture_output=True)
        if result.returncode == 0:
            print('✅ الخط جاهز')
        else:
            print('⚠️  هيستخدم خط افتراضي')


# ============================================================
# 3. HELPERS
# ============================================================
def ease_out(t):
    return 1 - (1 - t) ** 3


def parse_color(s):
    return tuple(int(x) for x in s.split(','))


def create_bg(w, h, cl, cr):
    img = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(img)
    for x in range(w):
        if x < w * 0.6:
            r2 = x / (w * 0.6)
            c = (
                int(cl[0] * (1 - r2 * 0.3)),
                int(cl[1] * (1 - r2 * 0.3)),
                int(cl[2] * (1 - r2 * 0.1)),
                255
            )
        else:
            r2 = (x - w * 0.6) / (w * 0.4)
            c = (
                int(cl[0] * 0.7 * (1-r2) + cr[0] * r2),
                int(cl[1] * 0.7 * (1-r2) + cr[1] * r2),
                int(cl[2] * 0.9 * (1-r2) + cr[2] * r2),
                255
            )
        d.line([(x, 0), (x, h)], fill=c)
    return img


def draw_badge(draw, cx, cy, r, lines, font):
    if r < 5:
        return
    draw.ellipse([cx-r-8, cy-r-8, cx+r+8, cy+r+8], fill=(160, 130, 10))
    draw.ellipse([cx-r,   cy-r,   cx+r,   cy+r  ], fill=(200, 160, 20))
    total_h = sum(font.getbbox(l)[3] for l in lines) + (len(lines)-1) * 4
    y = cy - total_h // 2
    for line in lines:
        b = font.getbbox(line)
        draw.text((cx - (b[2]-b[0])//2, y), line, font=font, fill=(255, 255, 255))
        y += b[3] + 4


# ============================================================
# 4. FRAME
# ============================================================
def make_frame(t, args, prod, cl, cr):
    W, H, D = args.width, args.height, args.duration

    # خلفية
    frame = create_bg(W, H, cl, cr)

    # زخرفة دوائر
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.ellipse([W*.45, -H*.3,  W*1.2, H*1.3], fill=(30, 20, 70, 80))
    od.ellipse([W*.55,  H*.3,  W*1.1, H*1.1], fill=(20, 15, 50, 60))
    frame = Image.alpha_composite(frame, ov)

    ft = load_font(72)
    fd = load_font(48)
    fb = load_font(32)
    fc = load_font(30)

    # --- صورة المنتج (slide من الشمال) ---
    ip = min(1.0, t / (D * 0.4))
    io = int((1 - ease_out(ip)) * -W * 0.5)
    if prod:
        pw = int(W * 0.42)
        ph = int(prod.height * pw / prod.width)
        rs = prod.resize((pw, ph), Image.LANCZOS)
        px = int(W * 0.02) + io
        py = (H - ph) // 2
        frame.paste(rs, (px, py), rs if rs.mode == 'RGBA' else None)

    tl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)

    # --- نصوص (slide من فوق + fade) ---
    tp = min(1.0, max(0.0, (t - D*.2) / (D*.4)))
    to = int((1 - ease_out(tp)) * -H * 0.3)
    ta_val = int(ease_out(tp) * 255)

    RIGHT_X = int(W * 0.95)
    title_y = int(H * 0.15) + to

    for i, line in enumerate(args.title.replace('\\n', '\n').split('\n')):
        b = ft.getbbox(line)
        tw = b[2] - b[0]
        td.text((RIGHT_X - tw, title_y + i*90), line,
                font=ft, fill=(255, 255, 255, ta_val))

    b = fd.getbbox(args.discount)
    dw = b[2] - b[0]
    td.text((RIGHT_X - dw, int(H*.55) + to), args.discount,
            font=fd, fill=(220, 160, 40, ta_val))

    # --- معلومات اتصال (fade) ---
    cp = min(1.0, max(0.0, (t - D*.5) / (D*.3)))
    ca = int(ease_out(cp) * 255)

    contact_y = int(H * 0.68)
    for i, txt in enumerate([args.phone, args.website]):
        b = fc.getbbox(txt)
        tw = b[2] - b[0]
        td.text((RIGHT_X - tw, contact_y + i*42), txt,
                font=fc, fill=(200-i*20, 200-i*20, 200-i*20, ca))

    frame = Image.alpha_composite(frame, tl)

    # --- badge (scale in) ---
    bp = min(1.0, max(0.0, (t - D*.1) / (D*.3)))
    bs = ease_out(bp)
    if bs > 0.05:
        bl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(bl)
        draw_badge(bd,
                   int(W * 0.08), int(H * 0.18),
                   int(70 * bs),
                   args.badge.replace('\\n', '\n').split('\n'),
                   load_font(int(32 * bs)))
        frame = Image.alpha_composite(frame, bl)

    return frame.convert('RGB')


# ============================================================
# 5. VIDEO
# ============================================================
def generate_video(args, prod, cl, cr):
    total = args.duration * args.fps
    tmp   = tempfile.mkdtemp()
    video_no_audio = os.path.join(tmp, 'video_raw.mp4')

    print(f'🎬 بيرسم {total} frame...')
    for i in range(total):
        make_frame(i / args.fps, args, prod, cl, cr).save(
            os.path.join(tmp, f'frame_{i:05d}.png')
        )
        if i % args.fps == 0:
            print(f'   {i//args.fps}/{args.duration} ثانية ({int(i/total*100)}%)')

    print('🎞️  FFmpeg — بيعمل الفيديو...')
    subprocess.run([
        'ffmpeg', '-y',
        '-framerate', str(args.fps),
        '-i', os.path.join(tmp, 'frame_%05d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-crf', '18',
        '-movflags', '+faststart',
        video_no_audio
    ], capture_output=True)

    return tmp, video_no_audio


# ============================================================
# 6. AUDIO MIX
# ============================================================
def add_music(video_path, music_path, output_path, volume=0.20):
    if not os.path.exists(music_path):
        print('⚠️  الموسيقى مش موجودة — هيحفظ بدون صوت')
        shutil.copy(video_path, output_path)
        return

    print('🎵 بيضيف الموسيقى...')
    result = subprocess.run([
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', music_path,
        '-filter_complex',
        f'[1:a]volume={volume},'
        f'afade=t=in:st=0:d=1,'
        f'afade=t=out:st=4:d=2[music];'
        f'[music]apad[audio]',
        '-map', '0:v',
        '-map', '[audio]',
        '-shortest',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        output_path
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print('✅ الموسيقى اتضافت')
    else:
        print(f'⚠️  مشكلة في الموسيقى — بيحفظ بدون صوت')
        print(result.stderr[-200:])
        shutil.copy(video_path, output_path)


# ============================================================
# 7. MAIN
# ============================================================
def main():
    args = parse_args()

    print('='*50)
    print('🎬 Product Showcase Generator')
    print('='*50)
    print(f'   العنوان:  {args.title.replace(chr(10), " ").replace("\\n", " ")}')
    print(f'   الخصم:    {args.discount}')
    print(f'   الصورة:   {args.image or "مفيش"}')
    print(f'   الموسيقى: {args.music or "مفيش"}')
    print(f'   Output:   {args.output}')
    print()

    # تحميل الخط
    download_font_if_needed()

    # ألوان
    cl = parse_color(args.bg_left)
    cr = parse_color(args.bg_right)

    # صورة المنتج
    prod = None
    if args.image and os.path.exists(args.image):
        prod = Image.open(args.image).convert('RGBA')
        print(f'✅ صورة المنتج محملة')
    else:
        print('⚠️  بدون صورة منتج')

    # عمل الفيديو
    tmp, video_raw = generate_video(args, prod, cl, cr)

    # إضافة الموسيقى
    add_music(video_raw, args.music, args.output, args.music_volume)

    # تنظيف
    shutil.rmtree(tmp)

    # النتيجة النهائية
    if os.path.exists(args.output):
        size = os.path.getsize(args.output) / 1024 / 1024
        print()
        print(f'✅ الفيديو جاهز: {args.output}')
        print(f'   الحجم: {size:.1f} MB')
        # بيطبع المسار عشان n8n يقدر ياخده
        print(f'OUTPUT_PATH:{args.output}')
    else:
        print('❌ فشل في عمل الفيديو')
        sys.exit(1)


if __name__ == '__main__':
    main()

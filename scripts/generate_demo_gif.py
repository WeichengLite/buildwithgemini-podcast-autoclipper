import os
from PIL import Image, ImageDraw, ImageFont

def create_demo_gif(output_path="demo.gif"):
    width, height = 800, 450
    frames = []
    num_frames = 30

    for i in range(num_frames):
        # Create base canvas
        img = Image.new("RGB", (width, height), color="#0b0f19")
        draw = ImageDraw.Draw(img)

        # Header
        draw.rectangle([(0, 0), (width, 50)], fill="#111827")
        draw.text((20, 15), "🎙️ Podcast AutoClipper Studio", fill="#7c3aed")
        draw.rectangle([(620, 15), (780, 35)], fill="#1f2937", outline="#374151")
        draw.text((630, 18), "● Agent Connected", fill="#22c55e")

        # Sidebar
        draw.rectangle([(0, 50), (200, height)], fill="#111827", outline="#1f2937")
        draw.text((15, 65), "ACTIVE EPISODE", fill="#9ca3af")
        draw.rectangle([(15, 85), (185, 115)], fill="#1f2937", outline="#7c3aed")
        draw.text((25, 93), "ep_001: Quantum AI", fill="#ffffff")

        # Nav Items
        nav_items = ["✨ Full Post-Production", "🎨 AI Cover Art", "🎬 Video Teaser (Omni)", "🎵 Spotify Intro Page"]
        for idx, item in enumerate(nav_items):
            y = 135 + idx * 35
            fill_col = "#7c3aed" if idx == (i // 7) % 4 else "#1f2937"
            text_col = "#ffffff" if idx == (i // 7) % 4 else "#9ca3af"
            draw.rectangle([(15, y), (185, y + 28)], fill=fill_col, outline="#374151")
            draw.text((25, y + 6), item, fill=text_col)

        # Hero Banner
        draw.rectangle([(215, 65), (785, 125)], fill="#1f2937", outline="#374151")
        draw.text((230, 75), "Episode ep_001: Quantum AI & Deep Learning", fill="#ffffff")
        draw.text((230, 98), "Guest: Demis Hassabis | Duration: 34:12 | Status: Ready", fill="#9ca3af")

        # Media Grid Box 1 (Cover Art)
        draw.rectangle([(215, 140), (485, 290)], fill="#1f2937", outline="#374151")
        draw.text((225, 150), "🎨 Episode Cover Art", fill="#7c3aed")
        draw.rectangle([(235, 175), (465, 275)], fill="#312e81", outline="#7c3aed")
        draw.text((280, 215), "PROMOTIONAL\n  COVER ART", fill="#d8b4fe")

        # Media Grid Box 2 (Omni Video Teaser)
        draw.rectangle([(500, 140), (785, 290)], fill="#1f2937", outline="#374151")
        draw.text((510, 150), "🎬 Video Teaser (Omni Model)", fill="#4f46e5")
        draw.rectangle([(515, 175), (770, 275)], fill="#111827", outline="#4f46e5")
        
        # Animated Video Bar
        progress = (i / num_frames) * 235
        draw.rectangle([(525, 255), (525 + progress, 260)], fill="#22c55e")
        draw.text((580, 210), "▶ PLAYING OMNI TRAILER", fill="#22c55e")

        # Bottom Console
        draw.rectangle([(215, 305), (785, 435)], fill="#1f2937", outline="#374151")
        draw.text((225, 315), "💻 AI Studio Assistant Console", fill="#9ca3af")
        
        # Simulated Console text typing
        msg = "Generating show notes & video trailer for ep_001..."
        chars_to_show = int((i / num_frames) * len(msg))
        draw.text((225, 345), "👤 User: Generate full package for ep_001", fill="#ffffff")
        draw.text((225, 375), f"🎙️ Agent: {msg[:chars_to_show]}█", fill="#a7f3d0")

        frames.append(img)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0
    )
    print(f"Generated optimized looping GIF at {output_path}")

if __name__ == "__main__":
    create_demo_gif("/home/user/build-with-gemini/podcast-autoclipper/demo.gif")
    create_demo_gif("/home/user/build-with-gemini/demo.gif")

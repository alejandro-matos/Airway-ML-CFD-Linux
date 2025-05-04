import os
import math
from PIL import Image, ImageDraw
import customtkinter as ctk

__all__ = ["create_icon", "load_ctk_icon"]

def create_icon(icon_type: str, size: tuple[int,int] = (24, 24)) -> Image.Image:
    """
    Generate a custom icon as a PIL Image.

    Args:
        icon_type: One of 'save', 'document', or 'eye'.
        size: (width, height) in pixels.
    Returns:
        A PIL.Image.Image in RGBA mode.
    """
    width, height = size
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if icon_type == 'save':
        color = (41, 98, 255)
        draw.rectangle([(2, 2), (width - 2, height - 2)], outline=color, width=2)
        draw.rectangle([(5, 2), (width - 5, 7)], fill=color)
        draw.rectangle([(6, 9), (width - 6, height - 6)], outline=color)
        draw.rectangle([(8, 3), (14, 6)], fill=(255, 255, 255))

    elif icon_type == 'document':
        outline = (12, 30, 30)
        back_fill = (221, 126, 50)
        front_fill = (252, 207, 49)
        back_tab = [
            (4, 4),
            (width // 2 - 2, 4),
            (width // 2 + 3, 9),
            (width - 4, 9),
            (width - 4, height - 4),
            (4, height - 4)
        ]
        draw.polygon(back_tab, fill=back_fill, outline=outline, width=2)
        front_face = [
            (4, 9),
            (width - 4, 9),
            (width - 4, height - 4),
            (4, height - 4)
        ]
        draw.polygon(front_face, fill=front_fill, outline=outline, width=2)

    elif icon_type == 'eye':
        cx, cy = width / 2, height / 2
        ew, eh = width - 2, height / 3
        # Outer eye shape
        outer = [
            (
                cx + (ew / 2) * math.cos(math.radians(a)),
                cy + (eh / 2) * math.sin(math.radians(a))
            ) for a in range(0, 360, 5)
        ]
        draw.polygon(outer, fill=(0, 0, 0))
        # Inner white
        iw, ih = ew * 0.7, eh * 0.7
        inner = [
            (
                cx + (iw / 2) * math.cos(math.radians(a)),
                cy + (ih / 2) * math.sin(math.radians(a))
            ) for a in range(0, 360, 5)
        ]
        draw.polygon(inner, fill=(255, 255, 255))
        # Pupil
        r = min(iw, ih) * 0.4
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(0, 0, 0))

    else:
        raise ValueError(f"Unknown icon type: {icon_type}")

    return img


def load_ctk_icon(name: str, width: int) -> ctk.CTkImage | None:
    """
    Load a PNG file from the components/images folder and wrap it as a CTkImage.

    Args:
        name: base filename without extension (e.g. 'eye').
        width: desired width, height scaled to maintain aspect ratio.
    Returns:
        A CTkImage or None if loading fails.
    """
    try:
        # Locate the images folder relative to this file
        folder = os.path.join(os.path.dirname(__file__), '..', 'components', 'icons')
        icon_path = os.path.join(os.path.abspath(folder), f"{name}.png")
        img = Image.open(icon_path)
        orig_w, orig_h = img.size
        height = int(width * (orig_h / orig_w))
        return ctk.CTkImage(light_image=img, dark_image=img, size=(width, height))
    except Exception as e:
        print(f"Error loading icon {name}: {e}")
        return None

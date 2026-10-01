#!/usr/bin/env python3
"""
Turns the owner's supplied photos into optimised web assets.

Sources live in the project root (as received). Outputs go to
site/assets/img/photos/ as compressed JPEGs at a consistent 4:3 ratio, so a
before/after pair always lines up in the comparison slider.

Only photos WITHOUT burned-in text are used. Several of the supplied files
are design mock-ups with labels and arrow buttons baked into the pixels —
those cannot go on the site, because the label would be duplicated by the
site's own caption and the fake arrow button would not do anything.

Run:  python3 tools/process_photos.py
"""
import os
from PIL import Image, ImageOps

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# The client's original photos are deliberately NOT in this repository.
# They are phone photos of real customers' homes, plus screenshots of the
# owner's own registrar and Cloudflare accounts, so they have no business
# sitting in a public repo. Only the cropped, web-sized results in
# site/assets/img/photos/ are committed, and those are what the site uses.
#
# To re-run this script, put the originals in source-photos/ (gitignored).
SRC = os.path.join(ROOT, "source-photos")
OUT = os.path.join(ROOT, "site", "assets", "img", "photos")
os.makedirs(OUT, exist_ok=True)

TARGET_W, TARGET_H = 1400, 1050          # 4:3
QUALITY = 82


def crop_to_ratio(im, ratio=TARGET_W / TARGET_H, anchor=(0.5, 0.5)):
    """Centre-ish crop to the target ratio without distorting anything."""
    w, h = im.size
    cur = w / h
    if abs(cur - ratio) < 0.001:
        return im
    if cur > ratio:                       # too wide -> trim sides
        new_w = int(round(h * ratio))
        x = int((w - new_w) * anchor[0])
        return im.crop((x, 0, x + new_w, h))
    new_h = int(round(w / ratio))         # too tall -> trim top/bottom
    y = int((h - new_h) * anchor[1])
    return im.crop((0, y, w, y + new_h))


def emit(src, name, anchor=(0.5, 0.5), crop_box=None):
    path = src if os.path.isabs(src) else os.path.join(SRC, src)
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")   # phone photos carry rotation
    if crop_box:
        im = im.crop(crop_box)
    im = crop_to_ratio(im, anchor=anchor)
    # Never upscale: several sources are tiles cut out of a grid and blowing
    # them up to the nominal width just makes them soft.
    out_w = min(TARGET_W, im.size[0])
    out_h = int(round(out_w / (TARGET_W / TARGET_H)))
    im = im.resize((out_w, out_h), Image.LANCZOS)
    dest = os.path.join(OUT, name)
    im.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    kb = os.path.getsize(dest) / 1024
    flag = "" if out_w >= 1000 else "   (small source)"
    print(f"  {name:26s} {out_w}x{out_h}  {kb:6.0f} KB   <- {os.path.basename(src)}{flag}")
    return dest


# The four supplied files with no text burned into them.
KITCHEN_CLEAN = "0B39C986-1651-4D88-9AEB-F2A444300BDE.jpg"
KITCHEN_MESSY = "IMG_0724.jpeg"
LIVING_ROOM = "1C8AE8CD-CB6C-4AA0-851D-51A8D792FB82.jpg"
BATHROOM_CLEAN = "49438F9A-C750-4954-BA7E-041713C957DC.jpg"

# Real before/after pairs, split out of the supplied 4-panel strip.
# The strip has BEFORE/AFTER pills baked into the top ~96px of each panel,
# so those rows are cropped away and the site adds its own labels.
STRIP = "D81567AC-BDC9-4791-9EB1-744C46239EBA.jpg"
STRIP_LABEL_H = 96


def strip_panel(index):
    im = Image.open(os.path.join(SRC, STRIP))
    w, h = im.size
    pw = w // 4
    return (index * pw, STRIP_LABEL_H, (index + 1) * pw, h)


# Grids of un-labelled tiles supplied by the owner. Each grid is split into
# equal tiles; the index is row-major from the top-left.
GRIDS = {
    "A": ("13A6B804-A887-4BAA-A80C-9B4B2BA6E8BB.jpg", 3, 2),
    "C": ("FC05260E-DD6F-4536-BD26-6AECAB4A046E.jpg", 4, 2),
}


def grid_tile(grid_key, index):
    """Crop box for one tile of a grid (1-based, row-major)."""
    fname, cols, rows = GRIDS[grid_key]
    im = Image.open(os.path.join(SRC, fname))
    w, h = im.size
    tw, th = w // cols, h // rows
    r, c = divmod(index - 1, cols)
    return fname, (c * tw, r * th, (c + 1) * tw, (r + 1) * th)


def emit_tile(grid_key, index, name, anchor=(0.5, 0.5)):
    fname, box = grid_tile(grid_key, index)
    return emit(fname, name, anchor=anchor, crop_box=box)


# The equipment photo. Cropped hard so the Ninja extractor and tools are the
# subject: the supplied frame shows a fully branded van the business does not
# own, and the owner asked that it not be presented as their vehicle.
EQUIPMENT = "75435170-23E8-4872-9FC5-A94B0155A073.jpg"
EQUIPMENT_BOX = None  # computed at run time from the image size


def emit_equipment(name):
    im = Image.open(os.path.join(SRC, EQUIPMENT))
    w, h = im.size
    box = (int(w * 0.365), int(h * 0.16), int(w * 0.79), h)
    return emit(EQUIPMENT, name, anchor=(0.5, 0.72), crop_box=box)


def main():
    print("Section photos:")
    emit(LIVING_ROOM, "living-room.jpg")
    emit(KITCHEN_CLEAN, "kitchen.jpg")
    emit(BATHROOM_CLEAN, "bathroom.jpg")

    print("\nBefore / after pairs (same room, same angle):")
    # Kitchen: both sources are already 4:3 and shot from the same spot.
    emit(KITCHEN_MESSY, "ba-kitchen-before.jpg")
    emit(KITCHEN_CLEAN, "ba-kitchen-after.jpg")

    # Sofa and bathroom pairs come out of the strip; anchor high so the
    # stained cushion / vanity stays in frame after the 4:3 crop.
    for i, name in ((2, "ba-sofa-before.jpg"), (3, "ba-sofa-after.jpg")):
        emit(STRIP, name, anchor=(0.5, 0.35), crop_box=strip_panel(i))
    for i, name in ((0, "ba-bathroom-before.jpg"), (1, "ba-bathroom-after.jpg")):
        emit(STRIP, name, anchor=(0.5, 0.55), crop_box=strip_panel(i))

    print("\nSection photos from the un-labelled grids:")
    emit_tile("C", 1, "office.jpg")            # office carpet vacuuming
    emit_tile("A", 2, "carpet-extraction.jpg") # extraction close-up, no people
    emit_tile("C", 4, "windows.jpg")           # interior window squeegee
    emit_tile("C", 5, "hallway.jpg")           # common area / hallway
    emit_tile("A", 5, "move-out.jpg")          # empty room
    emit_tile("C", 8, "clinic.jpg")            # treatment room
    emit_tile("A", 1, "upholstery.jpg")        # sofa extraction

    print("\nEquipment:")
    emit_equipment("equipment.jpg")

    total = sum(os.path.getsize(os.path.join(OUT, f))
                for f in os.listdir(OUT) if f.endswith(".jpg"))
    print(f"\n{len(os.listdir(OUT))} files, {total/1024:.0f} KB total")


if __name__ == "__main__":
    main()

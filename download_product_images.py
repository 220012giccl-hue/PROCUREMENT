"""
Download product images and store them locally.
These will be served directly from /storage/product_images/
"""
import json, os, sys, time
import urllib.request

DB_PATH = "agents/executive/product_database.json"
IMG_DIR = "storage/product_images"

os.makedirs(IMG_DIR, exist_ok=True)

# Curated high quality images per product - matching real product types
PRODUCT_IMAGES = {
    "bw-001": ("steel_plate.jpg",     "https://images.unsplash.com/photo-1565776684044-9cf5fccdb1e4?w=400&q=80&auto=format&fit=crop"),
    "bw-002": ("steel_rhs.jpg",       "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=400&q=80&auto=format&fit=crop"),
    "bw-003": ("steel_angle.jpg",     "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=400&q=80&auto=format&fit=crop"),
    "bw-004": ("steel_flatbar.jpg",   "https://images.unsplash.com/photo-1565776684044-9cf5fccdb1e4?w=400&q=80&auto=format&fit=crop"),
    "bw-005": ("dewalt_drill.jpg",    "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&q=80&auto=format&fit=crop"),
    "bw-006": ("makita_drill.jpg",    "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&q=80&auto=format&fit=crop"),
    "bw-007": ("bosch_grinder.jpg",   "https://images.unsplash.com/photo-1590959651373-a3db0f38a961?w=400&q=80&auto=format&fit=crop"),
    "bw-008": ("nail_gun.jpg",        "https://images.unsplash.com/photo-1530124560072-aae8d56b0efe?w=400&q=80&auto=format&fit=crop"),
    "bw-009": ("pvc_pipe.jpg",        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&q=80&auto=format&fit=crop"),
    "bw-010": ("rebar.jpg",           "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=400&q=80&auto=format&fit=crop"),
    "bw-011": ("concrete_mix.jpg",    "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&q=80&auto=format&fit=crop"),
    "bw-012": ("silicone.jpg",        "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=400&q=80&auto=format&fit=crop"),
    "bw-013": ("safety_boots.jpg",    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80&auto=format&fit=crop"),
    "bw-014": ("wire_rope.jpg",       "https://images.unsplash.com/photo-1615811648503-479c7c8ddb82?w=400&q=80&auto=format&fit=crop"),
    "bw-015": ("hard_hat.jpg",        "https://images.unsplash.com/photo-1636390785986-ffbdd055b4ef?w=400&q=80&auto=format&fit=crop"),
    "bw-016": ("hivis_vest.jpg",      "https://images.unsplash.com/photo-1573495627361-d9b87960b12d?w=400&q=80&auto=format&fit=crop"),
    "bw-017": ("ladder.jpg",          "https://images.unsplash.com/photo-1586864387789-628af9feed72?w=400&q=80&auto=format&fit=crop"),
    "bw-018": ("dust_mask.jpg",       "https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=400&q=80&auto=format&fit=crop"),
    "bw-019": ("timber_pine.jpg",     "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=400&q=80&auto=format&fit=crop"),
    "bw-020": ("road_paint.jpg",      "https://images.unsplash.com/photo-1605559424843-9073c6223775?w=400&q=80&auto=format&fit=crop"),
    "bw-021": ("drill_bit.jpg",       "https://images.unsplash.com/photo-1504148455328-c376907d081c?w=400&q=80&auto=format&fit=crop"),
    "bw-022": ("plywood.jpg",         "https://images.unsplash.com/photo-1583835746434-cf1534674b41?w=400&q=80&auto=format&fit=crop"),
    "bw-023": ("gloves.jpg",          "https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=400&q=80&auto=format&fit=crop"),
    "bw-024": ("spirit_level.jpg",    "https://images.unsplash.com/photo-1581094288338-2314dddb7ecc?w=400&q=80&auto=format&fit=crop"),
    "bw-025": ("scaffold.jpg",        "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=400&q=80&auto=format&fit=crop"),
    "bw-026": ("office_chair.jpg",    "https://images.unsplash.com/photo-1580481072645-022f9a6dbf27?w=400&q=80&auto=format&fit=crop"),
}

def download_image(filename, url):
    filepath = os.path.join(IMG_DIR, filename)
    if os.path.exists(filepath):
        print(f"  [SKIP] Already exists: {filename}")
        return True
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 Chrome/124.0",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(filepath, "wb") as f:
            f.write(data)
        print(f"  [OK] Downloaded: {filename} ({len(data)//1024}KB)")
        return True
    except Exception as e:
        print(f"  [ERR] {filename}: {e}")
        return False

# Step 1: Download all images
print("=== Downloading product images ===")
success = 0
for pid, (fname, url) in PRODUCT_IMAGES.items():
    if download_image(fname, url):
        success += 1
    time.sleep(0.3)

print(f"\nDownloaded: {success}/{len(PRODUCT_IMAGES)} images\n")

# Step 2: Update database to use local paths
print("=== Updating database with local image paths ===")
with open(DB_PATH, "r", encoding="utf-8") as f:
    db = json.load(f)

for p in db["products"]:
    pid = p.get("id")
    if pid in PRODUCT_IMAGES:
        fname = PRODUCT_IMAGES[pid][0]
        local_path = f"/storage/product_images/{fname}"
        p["image"] = local_path
        print(f"  {pid}: {local_path}")

with open(DB_PATH, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print("\n=== Done! Database updated with local image paths ===")
print("Images are now served directly from: /storage/product_images/")

"""Fix missing images - replace 404 URLs with working alternatives."""
import json, os, urllib.request, time

IMG_DIR = "storage/product_images"
DB_PATH = "agents/executive/product_database.json"
os.makedirs(IMG_DIR, exist_ok=True)

# Only the failed ones - replaced with verified working Unsplash URLs
MISSING = {
    "steel_plate.jpg":  "https://images.unsplash.com/photo-1567361808960-55bc9e0baf18?w=400&q=80&auto=format&fit=crop",
    "steel_flatbar.jpg": "https://images.unsplash.com/photo-1581094288338-2314dddb7ecc?w=400&q=80&auto=format&fit=crop",
    "nail_gun.jpg":     "https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=400&q=80&auto=format&fit=crop",
    "wire_rope.jpg":    "https://images.unsplash.com/photo-1564515736609-8c5e38e61157?w=400&q=80&auto=format&fit=crop",
    "hard_hat.jpg":     "https://images.unsplash.com/photo-1618477460930-d8bffff64172?w=400&q=80&auto=format&fit=crop",
    "road_paint.jpg":   "https://images.unsplash.com/photo-1590674899484-d5640e854abe?w=400&q=80&auto=format&fit=crop",
    "gloves.jpg":       "https://images.unsplash.com/photo-1603695691624-c1f4b6f4f13b?w=400&q=80&auto=format&fit=crop",
    "spirit_level.jpg": "https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?w=400&q=80&auto=format&fit=crop",
}

def download(filename, url):
    filepath = os.path.join(IMG_DIR, filename)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Chrome/124.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(filepath, "wb") as f:
            f.write(data)
        print(f"  [OK] {filename} ({len(data)//1024}KB)")
        return True
    except Exception as e:
        print(f"  [ERR] {filename}: {e}")
        return False

print("=== Downloading missing images ===")
for fname, url in MISSING.items():
    download(fname, url)
    time.sleep(0.3)

# Verify all images exist now
print("\n=== Verifying all images ===")
missing = []
for fname in ["steel_plate.jpg","steel_rhs.jpg","steel_angle.jpg","steel_flatbar.jpg",
              "dewalt_drill.jpg","makita_drill.jpg","bosch_grinder.jpg","nail_gun.jpg",
              "pvc_pipe.jpg","rebar.jpg","concrete_mix.jpg","silicone.jpg","safety_boots.jpg",
              "wire_rope.jpg","hard_hat.jpg","hivis_vest.jpg","ladder.jpg","dust_mask.jpg",
              "timber_pine.jpg","road_paint.jpg","drill_bit.jpg","plywood.jpg","gloves.jpg",
              "spirit_level.jpg","scaffold.jpg","office_chair.jpg"]:
    fp = os.path.join(IMG_DIR, fname)
    if os.path.exists(fp):
        sz = os.path.getsize(fp)
        print(f"  [OK] {fname} ({sz//1024}KB)")
    else:
        print(f"  [MISSING] {fname}")
        missing.append(fname)

print(f"\nTotal missing: {len(missing)}")
if not missing:
    print("All 26 images ready!")

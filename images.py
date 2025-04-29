import requests
from bs4 import BeautifulSoup
import os
from PIL import Image
from io import BytesIO
import csv
import sqlite3
import urllib3
import re

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URLs
BASE_URL = "https://balatrogame.fandom.com"
JOKER_LIST_URL = f"{BASE_URL}/wiki/Jokers"

# Setup folders
base_folder = "static/jokers"
os.makedirs(base_folder, exist_ok=True)
rarities = ["Common", "Uncommon", "Rare", "Legendary"]
for rarity in rarities:
    os.makedirs(os.path.join(base_folder, rarity.lower()), exist_ok=True)

# Setup CSV file
csv_file = open("jokers.csv", mode='w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Joker Name", "Rarity"])  # Header

# Setup SQLite database
db_conn = sqlite3.connect('scoreboard.db')
c = db_conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS jokers (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    rarity TEXT
)
''')
db_conn.commit()

# Headers for HTTP requests
headers = {"User-Agent": "Mozilla/5.0"}

# Rarity Mapping (Expand later if needed)
joker_rarity_map = {
    "Four Fingers": "Common",
    "Thumb": "Common",
    "Eight Ball": "Common",
    "Odd Todd": "Common",
    "Even Steven": "Common",
    "Blueprint": "Uncommon",
    "Hiker": "Uncommon",
    "The Arm": "Uncommon",
    "Hack": "Uncommon",
    "The Soul": "Uncommon",
    "Brainstorm": "Rare",
    "Egg": "Rare",
    "Seance": "Rare",
    "Erosion": "Rare",
    "Misprint": "Rare",
    "Joker": "Legendary",
    "The Ankh": "Legendary",
    "Midas Mask": "Legendary",
    "Astronomer": "Legendary",
    "The Immortal": "Legendary"
}

# Step 1: Fetch main Joker page
print("Fetching Joker list page...")
response = requests.get(JOKER_LIST_URL, headers=headers, verify=False)
soup = BeautifulSoup(response.content, "html.parser")

# Step 2: Find all <a> links to individual Jokers
all_links = soup.find_all('a', href=True)

joker_links = []
pattern = re.compile(r'^/wiki/[^:]+$')  # Exclude special pages like /wiki/File:Something

for link in all_links:
    href = link['href']
    text = link.get_text(strip=True)
    if pattern.match(href) and text and text not in ['Jokers', 'Cards', 'Pages']:
        full_link = BASE_URL + href
        joker_links.append((text, full_link))

# Remove duplicates
joker_links = list(dict(joker_links).items())

print(f"Found {len(joker_links)} Joker candidates.")

downloaded = 0
expected_jokers = []
downloaded_jokers = set()

# Step 3: Visit each Joker page
for joker_name, link in joker_links:
    expected_jokers.append(joker_name)

    filename_clean = joker_name.lower().replace(" ", "_").replace("'", "").replace(",", "").replace("!", "").replace("?", "").replace("-", "_")
    filename_clean = filename_clean.replace("__", "_")

    rarity = joker_rarity_map.get(joker_name, "Common")  # Default to Common if unknown

    try:
        response = requests.get(link, headers=headers, verify=False)
        page_soup = BeautifulSoup(response.content, "html.parser")

        # Find main Joker card image inside an <aside>
        infobox = page_soup.find('aside')
        if not infobox:
            print(f"❗ No infobox for {joker_name}")
            continue

        img_tag = infobox.find('img')
        if not img_tag:
            print(f"❗ No image for {joker_name}")
            continue

        img_url = img_tag.get('data-src') or img_tag.get('src')
        if not img_url:
            print(f"❗ No img URL for {joker_name}")
            continue

        if img_url.startswith("//"):
            img_url = "https:" + img_url

        # Download the Joker image
        img_response = requests.get(img_url, headers=headers, verify=False)
        if img_response.status_code == 200:
            img_data = Image.open(BytesIO(img_response.content))
            img_data = img_data.convert("RGBA")
            img_data = img_data.resize((100, 100))

            save_path = os.path.join(base_folder, rarity.lower(), f"{filename_clean}.png")
            img_data.save(save_path, "PNG")
            downloaded_jokers.add(filename_clean)

            print(f"✅ Downloaded {joker_name} into {rarity} folder.")

            # Save to CSV
            csv_writer.writerow([joker_name, rarity])

            # Save to database
            try:
                c.execute('INSERT INTO jokers (name, rarity) VALUES (?, ?)', (joker_name, rarity))
            except sqlite3.IntegrityError:
                pass  # Ignore duplicates

            downloaded += 1
        else:
            print(f"❗ Failed to download image for {joker_name}")

    except Exception as e:
        print(f"❗ Error scraping {joker_name}: {e}")

# Finalize
db_conn.commit()
db_conn.close()
csv_file.close()

# Step 4: Check for missing Jokers
print("\n🔎 Checking for missing Jokers...")
missing_jokers = []
for joker_name in expected_jokers:
    filename_clean = joker_name.lower().replace(" ", "_").replace("'", "").replace(",", "").replace("!", "").replace("?", "").replace("-", "_")
    filename_clean = filename_clean.replace("__", "_")
    
    if filename_clean not in downloaded_jokers:
        missing_jokers.append(joker_name)

if missing_jokers:
    print("❗ Missing images for the following Jokers:")
    for joker in missing_jokers:
        print(f" - {joker}")
else:
    print("✅ All Joker images downloaded successfully!")

print(f"\n✅ Completed: {downloaded} Jokers downloaded, resized, categorized, and recorded!")

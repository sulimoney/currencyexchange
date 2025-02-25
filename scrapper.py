import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from deep_translator import GoogleTranslator

# Define the save directory
save_dir = "exchange_rates"
os.makedirs(save_dir, exist_ok=True)  # Ensure directory exists

# URL of the exchange rate page
url = "https://www.alsoug.com/currency"

# Headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Fetch the page
response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the first table in the page
    table = soup.find("table")

    if table:
        rows = table.find_all("tr")

        # Prepare CSV filename with today's date
        today_date = datetime.today().strftime('%Y-%m-%d')
        filename = os.path.join(save_dir, f"exchange_rates_{today_date}.csv")

        # Extract table data and translate
        translator = GoogleTranslator(source="auto", target="en")
        data = []
        
        for row in rows:
            columns = row.find_all(["th", "td"])
            row_text = [col.text.strip() for col in columns]

            # Translate each column if it's Arabic
            translated_row = [translator.translate(text) for text in row_text]
            data.append(translated_row)

        # Convert to DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, header=False, encoding="utf-8")

        print(f"✅ Exchange rates (translated) saved to {filename} successfully!")
    else:
        print("⚠️ No exchange rate table found.")
else:
    print(f"❌ Failed to access the page. Status code: {response.status_code}")

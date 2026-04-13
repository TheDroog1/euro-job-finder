import requests
import json
import os
from datetime import datetime

# CONFIGURAZIONE
SOURCES = {
    "arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
}

def fetch_arbeitnow():
    print("Scansionando Arbeitnow...")
    try:
        response = requests.get(SOURCES["arbeitnow"], timeout=10)
        data = response.json()
        jobs = []
        for j in data.get("data", []):
            # Filtro base: tech/design e junior/intern
            text = (j["title"] + j["description"]).lower()
            title_lower = j["title"].lower()
            is_senior = any(x in title_lower for x in ['senior', 'lead', 'manager', 'head', 'principal', 'staff'])
            is_junior = any(x in text for x in ['junior', 'intern', 'stage', 'apprendistato', 'trainee', 'graduate', 'tirocinio'])
            
            if not is_senior:
                jobs.append({
                    "id": j["slug"],
                    "title": j["title"],
                    "company": j["company_name"],
                    "location": j["location"],
                    "url": j["url"],
                    "source": "Arbeitnow",
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "is_junior": is_junior
                })
        return jobs
    except Exception as e:
        print(f"Errore Arbeitnow: {e}")
        return []

def main():
    all_curated_jobs = []
    
    # Aggiungi risultati da varie fonti
    all_curated_jobs.extend(fetch_arbeitnow())
    
    # Salva i risultati in data/jobs.json
    os.makedirs("data", exist_ok=True)
    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_curated_jobs, f, ensure_ascii=False, indent=2)
    
    print(f"Scansione completata. Trovati {len(all_curated_jobs)} lavori.")

if __name__ == "__main__":
    main()

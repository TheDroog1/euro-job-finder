import urllib.request
import json
import re
import os
from datetime import datetime

# ============================================================
# SCOUT v6 - ULTRA-FILTERED ENGINE (UX/UI + FRONTEND + IT/EN)
# ============================================================

def is_it_or_en(text):
    """Semplice rilevamento lingua: cerca parole comuni IT/EN"""
    text = text.lower()
    it_words = ['requisiti', 'esperienza', 'azienda', 'lavoro', 'cercasi', 'offriamo']
    en_words = ['experience', 'requirements', 'skills', 'apply', 'looking for', 'work', 'job']
    # Se ha parole IT o EN allora è ok. Altrimenti scarta (es: tedesco, francese stretto)
    return any(w in text for w in it_words) or any(w in text for w in en_words)

def is_relevant_role(title):
    """Filtra solo ruoli UX/UI, Design o Frontend"""
    t = title.lower()
    # Ruoli desiderati
    targets = ['ux', 'ui', 'design', 'frontend', 'front-end', 'product designer', 'researcher', 'grafic']
    # Esclusioni (Senior/Lead/Management)
    exclusions = ['senior', 'lead', 'head', 'manager', 'director', 'direttore', 'principal', 'architect']
    
    if any(ex in t for ex in exclusions): return False
    return any(tr in t for tr in targets)

def is_in_europe(location):
    """Filtra le nazioni fuori Europa più comuni che gli aggregatori potrebbero includere per errore."""
    loc = location.lower()
    # Nazioni/Continenti da escludere
    non_eu = ['india', 'usa', 'united states', 'america', 'canada', 'australia', 'brazil', 'china', 
              'japan', 'singapore', 'mexico', 'remote us', 'remote usa', 'africa', 'asia', 
              'new york', 'california', 'texas', 'san francisco']
    if any(n in loc for n in non_eu): 
        return False
    return True

def fetch_jobstobedone():
    """TUTTI i lavori da JTBD (già filtrati alla fonte con descrizione)"""
    print("📡 Scansionando Jobstobedone.works (Premium Source)...")
    try:
        req = urllib.request.Request("https://www.jobstobedone.works/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r: html = r.read().decode('utf-8')
        
        # Regex migliorata per catturare anche la descrizione
        matches = re.finditer(r'\\\"title\\\":\\\"(.*?)\\\",\\\"company\\\":\\\"(.*?)\\\",\\\"description\\\":\\\"(.*?)\\\",\\\"url\\\":\\\"(.*?)\\\",.*?\\\"location\\\":\\\"(.*?)\\\",.*?\\\"is_closed\\\":(true|false)', html)
        
        jobs = []
        for match in matches:
            title, company, desc, job_url, location, is_closed = match.groups()
            if is_closed == 'true': continue
            
            # Pulizia descrizione (rimozione escape e limitazione)
            clean_desc = desc.replace('\\n', '\n').replace('\\u0026', '&').replace('\\"', '"')
            
            jobs.append({
                "id": "jtbd-" + re.sub(r'[^a-z0-9]', '', title.lower())[:40],
                "title": title.replace('\\u0026', '&'),
                "company": company.replace('\\u0026', '&'),
                "location": location,
                "url": job_url.replace('\\u0026', '&'),
                "source": "✨ Jobstobedone",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "is_junior": True,
                "description": clean_desc if clean_desc else "Annuncio curato per Junior Profile."
            })
        print(f"   ✅ Trovati {len(jobs)} lavori (JTBD con descrizioni)")
        return jobs
    except Exception as e: print(f"   ❌ Errore JTBD: {e}"); return []

def fetch_devjobsscanner():
    print("📡 Scansionando DevJobScanner...")
    queries = ["ux%20junior", "frontend%20junior", "product%20designer%20junior"]
    jobs = []
    for q in queries:
        try:
            url = f"https://www.devjobsscanner.com/search/?search={q}&location=Europe"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r: html = r.read().decode('utf-8')
            matches = re.finditer(r'\\"company\\":\\"(.*?)\\".*?\\"location\\":\\"(.*?)\\".*?\\"title\\":\\"(.*?)\\".*?\\"url\\":\\"(.*?)\\"', html)
            for m in matches:
                company, location, title, job_url = m.groups()
                if not is_relevant_role(title): continue
                if not is_in_europe(location): continue
                # Qui non abbiamo la descrizione facile, ma il titolo è quasi sempre EN/IT su DJS
                jobs.append({
                    "id": "djs-" + "".join(filter(str.isalnum, title.lower()))[:15] + "-" + str(len(jobs)),
                    "title": title.replace('\\u0026', '&'),
                    "company": company.replace('\\u0026', '&'),
                    "location": location.replace('\\/', '/'),
                    "url": job_url.replace('\\/', '/'),
                    "source": "💻 DevScanner",
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "is_junior": True,
                    "description": f"Role via DevScanner. Location: {location}"
                })
        except Exception as e: print(f"   ❌ Errore DevScanner: {e}")
    return jobs

def fetch_bebee():
    print("📡 Scansionando beBee (EU Search)...")
    urls = [
        "https://bebee.com/it/jobs/role/user-experience-ux",
        "https://bebee.com/hu/jobs/role/product-designer",
        "https://bebee.com/uk/jobs/role/user-experience-ux",
        "https://bebee.com/jobs?q=junior+ux+designer+europe"
    ]
    jobs, seen_ids = [], set()
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response: html = response.read().decode('utf-8')
            slugs = re.findall(r'([a-zA-Z0-9-]{10,}-[0-9]{8})', html)
            for slug in slugs:
                if slug in seen_ids or 'global-error' in slug: continue
                seen_ids.add(slug)
                title = slug.split('--')[0].replace('-', ' ').title()
                if not is_relevant_role(title): continue
                
                # beBee di solito aggiusta in base all'endpoint o dominio, usiamo un fallback generico per location
                jobs.append({
                    "id": f"bebee-{slug[-8:]}",
                    "title": title, "company": "beBee Network", "location": "Europe / Remote",
                    "url": f"https://bebee.com/job/{slug}", "source": "🐝 beBee",
                    "date": datetime.now().strftime("%d/%m/%Y"), "is_junior": True,
                    "description": "Portati alla pagina originale per i dettagli (IT/EN supportati)."
                })
        except Exception as e: print(f"   ❌ Errore beBee: {e}")
    return jobs

def fetch_uiuxjobsboard():
    print("📡 Scansionando UIUXJobsBoard...")
    try:
        req = urllib.request.Request("https://uiuxjobsboard.com/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response: html = response.read().decode('utf-8')
        jobs = []
        matches = re.finditer(r'\\"title\\",\\"(.*?)\\",\\"slug\\",\\"([0-9a-zA-Z-]+)\\"', html)
        for match in matches:
            title, slug = match.groups()
            if not is_relevant_role(title): continue
            
            jobs.append({
                "id": "uiux-" + slug[:20],
                "title": title.replace('\\u0026', '&'), "company": "Design Agency", "location": "Europe / Remote",
                "url": f"https://uiuxjobsboard.com/jobs/{slug}", "source": "🎨 UIUX Jobs",
                "date": datetime.now().strftime("%d/%m/%Y"), "is_junior": True,
                "description": "Specialized UI/UX design board posting."
            })
        return jobs
    except Exception as e: print(f"   ❌ Errore UIUX: {e}"); return []

def main():
    all_jobs = []
    all_jobs.extend(fetch_jobstobedone())
    all_jobs.extend(fetch_devjobsscanner())
    all_jobs.extend(fetch_uiuxjobsboard())
    all_jobs.extend(fetch_bebee())
    
    seen_urls, unique_jobs = set(), []
    for j in all_jobs:
        if j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            unique_jobs.append(j)
    
    os.makedirs("data", exist_ok=True)
    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, ensure_ascii=False, indent=2)
    print(f"\n🎯 Scansione completata. {len(unique_jobs)} lavori filtrati salvati.")

if __name__ == "__main__":
    main()

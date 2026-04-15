import urllib.request
import json
import re
import os
from datetime import datetime

# ============================================================
# SCOUT v4 - Raccoglie lavori REALI tramite SCRAPING
# Fonti: Jobstobedone + DevJobScanner + UIUXJobsBoard
# ============================================================


def fetch_jobstobedone():
    """Scraping dei lavori curati da jobstobedone.works"""
    print("📡 Scansionando Jobstobedone.works...")
    try:
        req = urllib.request.Request(
            "https://www.jobstobedone.works/",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
        
        # Il sito usa Next.js e inserisce i dati nel HTML come JSON escaped
        matches = re.finditer(
            r'\\\"title\\\":\\\"(.*?)\\\",\\\"company\\\":\\\"(.*?)\\\".*?\\\"url\\\":\\\"(.*?)\\\".*?\\\"location\\\":\\\"(.*?)\\\".*?\\\"is_closed\\\":(true|false)',
            html
        )
        
        jobs = []
        for match in matches:
            title, company, job_url, location, is_closed = match.groups()
            
            # Salta le candidature chiuse
            if is_closed == 'true':
                continue
            
            # Decodifica unicode
            title = title.replace('\\u0026', '&')
            company = company.replace('\\u0026', '&')
            job_url = job_url.replace('\\u0026', '&')
            
            jobs.append({
                "id": "jtbd-" + re.sub(r'[^a-z0-9]', '', title.lower())[:40],
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "source": "Jobstobedone",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "is_junior": True,
                "description": f"Curated entry-level design job from jobstobedone.works"
            })
        
        print(f"   ✅ Trovati {len(jobs)} lavori da Jobstobedone")
        return jobs
    except Exception as e:
        print(f"   ❌ Errore Jobstobedone: {e}")
        return []


def fetch_devjobsscanner():
    """Scraping massivo da DevJobScanner (Aggregatore di LinkedIn e altri)"""
    print("📡 Scansionando DevJobScanner...")
    try:
        # Cerchiamo UX designer in Europa/Italia (generico)
        req = urllib.request.Request(
            "https://www.devjobsscanner.com/search/?search=ux%20junior",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        matches = re.finditer(r'\\"company\\":\\"(.*?)\\".*?\\"location\\":\\"(.*?)\\".*?\\"title\\":\\"(.*?)\\".*?\\"url\\":\\"(.*?)\\"', html)
        jobs = []
        for match in matches:
            company, location, title, job_url = match.groups()
            
            # Pulisci eventuale escape
            title = title.replace('\\u0026', '&')
            company = company.replace('\\u0026', '&')
            
            # Filtri (già pre-filtrati su junior tramite la search, ma controlliamo doppiamente)
            if 'senior' in title.lower() or 'lead' in title.lower() or 'head' in title.lower():
                continue
                
            jobs.append({
                "id": "djs-" + "".join(filter(str.isalnum, title.lower()))[:20] + "-" + str(len(jobs)),
                "title": title,
                "company": company,
                "location": location.replace('\\/', '/'),
                "url": job_url.replace('\\/', '/'),
                "source": "💻 DevScanner",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "is_junior": True,
                "description": "Lavoro UX trovato da DevJobScanner (" + company + ")"
            })
            
        print(f"   ✅ Trovati {len(jobs)} lavori (pre-filtrati Junior) da DevJobScanner")
        return jobs
    except Exception as e:
        print(f"   ❌ Errore DevJobScanner: {e}")
        return []

def fetch_uiuxjobsboard():
    """Scraping specializzato per UI/UX da uiuxjobsboard.com"""
    print("📡 Scansionando UIUXJobsBoard...")
    try:
        req = urllib.request.Request(
            "https://uiuxjobsboard.com/",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        jobs = []
        matches = re.finditer(r'\\"title\\",\\"(.*?)\\",\\"slug\\",\\"([0-9a-zA-Z-]+)\\"', html)
        for match in matches:
            title, slug = match.groups()
            title = title.replace('\\u0026', '&')
            
            # Filtro base
            if 'senior' in title.lower() or 'lead' in title.lower() or 'head' in title.lower():
                continue
                
            jobs.append({
                "id": "uiux-" + slug[:20],
                "title": title,
                "company": "UIUXJobsBoard",
                "location": "Vedi Dettagli",
                "url": f"https://uiuxjobsboard.com/jobs/{slug}",
                "source": "🎨 UIUX Jobs",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "is_junior": True,
                "description": "Portati alla pagina sorgente per i dettagli completi su azienda e location."
            })
            
        print(f"   ✅ Trovati {len(jobs)} lavori (Entry/Mid) da UIUXJobsBoard")
        return jobs
    except Exception as e:
        print(f"   ❌ Errore UIUXJobsBoard: {e}")
        return []

def fetch_bebee():
    """Scraping avanzato Bebee via regex su JSON idratazione"""
    print("📡 Scansionando beBee (IT + Global)...")
    urls = [
        "https://bebee.com/it/jobs/role/user-experience-ux",
        "https://bebee.com/jobs?q=junior+product+designer",
        "https://bebee.com/jobs?q=ux+intern+budapest"
    ]
    
    jobs = []
    seen_ids = set()
    
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')
            
            # Regex magica per catturare gli slug di beBee
            slugs = re.findall(r'([a-zA-Z0-9-]{10,}-[0-9]{8})', html)
            
            for slug in slugs:
                if slug in seen_ids or 'global-error' in slug:
                    continue
                seen_ids.add(slug)
                
                # Crea un titolo leggibile dallo slug
                title = slug.split('--')[0].replace('-', ' ').title()
                if 'At' in title: title = title.split(' At ')[0]
                
                # Filtro Junior/Senior
                t_lower = title.lower()
                if 'senior' in t_lower or 'lead' in t_lower or 'direttore' in t_lower:
                    continue
                
                jobs.append({
                    "id": f"bebee-{slug[-8:]}",
                    "title": title,
                    "company": "beBee Network",
                    "location": "Vedi Originale",
                    "url": f"https://bebee.com/job/{slug}",
                    "source": "🐝 beBee",
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "is_junior": True,
                    "description": "Annuncio trovato via beBee. Clicca per i dettagli completi."
                })
        except Exception as e:
            print(f"   ❌ Errore beBee URL {url}: {e}")
            
    print(f"   ✅ Trovati {len(jobs)} lavori da beBee")
    return jobs

def main():
    all_jobs = []
    
    all_jobs.extend(fetch_jobstobedone())
    all_jobs.extend(fetch_devjobsscanner())
    all_jobs.extend(fetch_uiuxjobsboard())
    all_jobs.extend(fetch_bebee())
    
    # Rimuovi duplicati per URL
    seen_urls = set()
    unique_jobs = []
    for j in all_jobs:
        if j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            unique_jobs.append(j)
    
    # Salva i risultati
    os.makedirs("data", exist_ok=True)
    with open("data/jobs.json", "w", encoding="utf-8") as f:
        json.dump(unique_jobs, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎯 Scansione completata. {len(unique_jobs)} lavori unici salvati in data/jobs.json")


if __name__ == "__main__":
    main()

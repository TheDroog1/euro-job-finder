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
    """Scraping specializzato per beBee.com (estrae dai JSON di idratazione)"""
    print("📡 Scansionando beBee...")
    try:
        url = "https://bebee.com/it/jobs/role/user-experience-ux"
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        jobs = []
        # beBee usa "jobTitle" e "jobSlug" o "title" e "slug" in base al template
        matches = re.finditer(r'\\"(?:jobT|t)itle\\":\\"(.*?)\\",\\"(?:jobS|s)lug\\":\\"(.*?)\\"', html)
        
        for m in matches:
            title, slug = m.groups()
            title = title.replace('\\u0026', '&')
            
            # Filtro Junior/Senior + Parole chiave UX
            t_lower = title.lower()
            if 'senior' in t_lower or 'lead' in t_lower:
                continue
            
            # Solo se pertinente a UX/Design
            if not any(x in t_lower for x in ['ux', 'ui', 'design', 'user experience', 'grafic']):
                continue
                
            jobs.append({
                "id": "bebee-" + slug[:30],
                "title": title,
                "company": "beBee Network",
                "location": "Italia / Remote",
                "url": f"https://bebee.com/it/job/{slug}",
                "source": "🐝 beBee",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "is_junior": True,
                "description": "Annuncio trovato via beBee. Clicca per visualizzare l'offerta."
            })
            
        print(f"   ✅ Trovati {len(jobs)} lavori da beBee")
        return jobs
    except Exception as e:
        print(f"   ❌ Errore beBee: {e}")
        return []

def fetch_recruitee():
    """Scraping mirato per UX Studio e altre agenzie su Recruitee"""
    print("📡 Scansionando UX Studio (Recruitee)...")
    sources = [
        {"name": "UX Studio", "url": "https://uxstudio.recruitee.com/"}
    ]
    jobs = []
    for src in sources:
        try:
            req = urllib.request.Request(src["url"], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode('utf-8')
            
            # Estrazione link e titoli
            matches = re.finditer(r'href="/o/(.*?)".*?>(.*?)</a>', html)
            for m in matches:
                slug, title = m.groups()
                title = re.sub('<[^>]*>', '', title).strip() # Pulizia tag HTML
                
                # Filtro Junior/Intern
                t_lower = title.lower()
                if 'senior' in t_lower or 'lead' in t_lower:
                    continue
                
                if any(x in t_lower for x in ['junior', 'intern', 'stage', 'entry', 'trainee']):
                    jobs.append({
                        "id": f"rec-{src['name'].lower()}-{slug[:20]}",
                        "title": title,
                        "company": src["name"],
                        "location": "Budapest / Hybrid",
                        "url": f"{src['url']}o/{slug}",
                        "source": "🏢 Agency Hub",
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "is_junior": True,
                        "description": f"Posizione aperta presso l'agenzia {src['name']}."
                    })
        except Exception as e:
            print(f"   ❌ Errore {src['name']}: {e}")
            
    print(f"   ✅ Trovati {len(jobs)} lavori da Recruitee Agencies")
    return jobs

def main():
    all_jobs = []
    
    all_jobs.extend(fetch_jobstobedone())
    all_jobs.extend(fetch_devjobsscanner())
    all_jobs.extend(fetch_uiuxjobsboard())
    all_jobs.extend(fetch_bebee())
    all_jobs.extend(fetch_recruitee())
    
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

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
        "https://bebee.com/jobs?q=ux+designer&l=Italy",
        "https://bebee.com/jobs?q=product+designer&l=Europe",
        "https://bebee.com/jobs?q=junior+ux+designer&l=Europe"
    ]
    jobs, seen_urls = [], set()
    
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
            
            # Estraiamo i dati strutturati (JSON-LD)
            ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
            
            # Estraiamo tutti i link esterni dalla pagina (LinkedIn, InfoJobs, Glassdoor, etc.)
            external_links = re.findall(r'href=[\"\'](https?://(?:[a-z]+\.)?(?:linkedin|infojobs|glassdoor|indeed|simplyhired|monster|jobrapido|careerbuilder|workable|lever|greenhouse)\.[a-z.]+/[^\"]+)[\"\']', html, re.IGNORECASE)
            
            # Pulizia e deduplicazione link esterni
            clean_external = []
            for link in external_links:
                l = link.replace('\\u0026', '&').replace('\\', '').split('"')[0].split("'")[0]
                if l not in clean_external: clean_external.append(l)

            job_idx = 0
            for ld_text in ld_matches:
                try:
                    data = json.loads(ld_text.strip())
                    if not isinstance(data, dict) or data.get('@type') != 'JobPosting': continue
                    
                    title = data.get('title', 'Unknown Title')
                    company = data.get('hiringOrganization', {}).get('name', 'Cloud Source')
                    location = data.get('jobLocation', {}).get('address', {}).get('addressLocality', 'Europe')
                    desc = data.get('description', 'Dettagli nell\'annuncio')
                    
                    if not is_relevant_role(title): continue
                    
                    # Logica associazione: beBee elenca i link esterni nello stesso ordine delle card/JSON-LD
                    raw_url = data.get('url', url)
                    final_url = raw_url
                    
                    if job_idx < len(clean_external):
                        # Se il link esterno sembra sensato, usiamolo
                        final_url = clean_external[job_idx]
                        job_idx += 1
                    
                    if final_url in seen_urls: continue
                    seen_urls.add(final_url)
                    
                    jobs.append({
                        "id": hashlib.md5(final_url.encode()).hexdigest()[:12],
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": final_url,
                        "source": "🔗 Sorgente Diretta" if "bebee.com" not in final_url else "🐝 beBee (Interno)",
                        "date": datetime.now().strftime("%d/%m/%Y"),
                        "is_junior": is_junior(title, desc),
                        "description": clean_html(desc)[:500] if desc else "Dettagli completi disponibili al link."
                    })
                except: continue
                
        except Exception as e:
            print(f"   ⚠️ Errore beBee ({url[:30]}...): {e}")
            
    return jobs


def fetch_uiuxjobsboard():
    print("📡 Scansionando UIUXJobsBoard (Metadati JSON)...")
    try:
        req = urllib.request.Request("https://uiuxjobsboard.com/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response: html = response.read().decode('utf-8')
        jobs = []
        # Estraiamo i dati dal blocco JSON di NextJS/Hydration che è più affidabile
        matches = re.finditer(r'\\"title\\",\\"(.*?)\\",.*?\\"slug\\",\\"(.*?)\\"', html)
        for match in matches:
            title, slug = match.groups()
            if not is_relevant_role(title): continue
            
            jobs.append({
                "id": "uiux-" + slug[:15],
                "title": title.replace('\\u0026', '&'), 
                "company": "UIUX Board 🎨", "location": "Remote / EU",
                "url": f"https://uiuxjobsboard.com/job/{slug}", 
                "source": "🎨 UIUX Jobs",
                "date": datetime.now().strftime("%d/%m/%Y"), "is_junior": True,
                "description": f"Postazione specializzata per Design. Titolo: {title}"
            })
        return jobs
    except Exception as e: print(f"   ❌ Errore UIUX: {e}"); return []

def main():
    all_jobs = []
    all_jobs.extend(fetch_jobstobedone())
    all_jobs.extend(fetch_devjobsscanner())
    all_jobs.extend(fetch_bebee())
    all_jobs.extend(fetch_uiuxjobsboard())
    
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

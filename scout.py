import urllib.request
import json
import re
import os
from datetime import datetime

# ============================================================
# SCOUT v5 - 100% EUROPE PAN-GLOBAL ENGINE
# Fonti: Jobstobedone + DevJobScanner + UIUXJobsBoard + beBee
# ============================================================

def fetch_jobstobedone():
    """Scraping dei lavori curati da jobstobedone.works (Focus Europa)"""
    print("📡 Scansionando Jobstobedone.works (Europe Curated)...")
    try:
        req = urllib.request.Request("https://www.jobstobedone.works/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r: html = r.read().decode('utf-8')
        matches = re.finditer(r'\\\"title\\\":\\\"(.*?)\\\",\\\"company\\\":\\\"(.*?)\\\".*?\\\"url\\\":\\\"(.*?)\\\".*?\\\"location\\\":\\\"(.*?)\\\".*?\\\"is_closed\\\":(true|false)', html)
        jobs = []
        for match in matches:
            title, company, job_url, location, is_closed = match.groups()
            if is_closed == 'true': continue
            jobs.append({
                "id": "jtbd-" + re.sub(r'[^a-z0-9]', '', title.lower())[:40],
                "title": title.replace('\\u0026', '&'),
                "company": company.replace('\\u0026', '&'),
                "location": location,
                "url": job_url.replace('\\u0026', '&'),
                "source": "✨ Jobstobedone",
                "date": datetime.now().strftime("%d/%m/%Y"),
                "is_junior": True,
                "description": f"Curated entry-level design job from Europe-wide sources."
            })
        print(f"   ✅ Trovati {len(jobs)} lavori (Curated)")
        return jobs
    except Exception as e:
        print(f"   ❌ Errore Jobstobedone: {e}"); return []

def fetch_devjobsscanner():
    """Massive Aggregator (LinkedIn/TotalJobs/Indeed) - Pan-European Search"""
    print("📡 Scansionando DevJobScanner (Pan-Europe Aggregator)...")
    queries = ["ux%20junior", "product%20designer%20junior", "ui%20intern"]
    jobs = []
    for q in queries:
        try:
            url = f"https://www.devjobsscanner.com/search/?search={q}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as r: html = r.read().decode('utf-8')
            matches = re.finditer(r'\\"company\\":\\"(.*?)\\".*?\\"location\\":\\"(.*?)\\".*?\\"title\\":\\"(.*?)\\".*?\\"url\\":\\"(.*?)\\"', html)
            for m in matches:
                company, location, title, job_url = m.groups()
                if any(x in title.lower() for x in ['senior', 'lead', 'head']): continue
                jobs.append({
                    "id": "djs-" + "".join(filter(str.isalnum, title.lower()))[:15] + "-" + str(len(jobs)),
                    "title": title.replace('\\u0026', '&'),
                    "company": company.replace('\\u0026', '&'),
                    "location": location.replace('\\/', '/'),
                    "url": job_url.replace('\\/', '/'),
                    "source": "💻 DevScanner",
                    "date": datetime.now().strftime("%d/%m/%Y"),
                    "is_junior": True,
                    "description": f"Aggregated role via DevScanner. Location: {location}"
                })
        except Exception as e: print(f"   ❌ Errore DevScanner [{q}]: {e}")
    print(f"   ✅ Trovati {len(jobs)} lavori (Massive Europe)")
    return jobs

def fetch_bebee():
    """Pan-European beBee Scanner (Bypassing JS constraints across EU domains)"""
    print("📡 Scansionando beBee (Total Europe Coverage: IT, DE, UK, ES, HU)...")
    urls = [
        "https://bebee.com/it/jobs/role/user-experience-ux",
        "https://bebee.com/hu/jobs/role/product-designer",
        "https://bebee.com/uk/jobs/role/user-experience-ux",
        "https://bebee.com/de/jobs/role/user-experience-ux",
        "https://bebee.com/es/jobs/role/user-experience-ux",
        "https://bebee.com/jobs?q=junior+ux+designer+europe",
        "https://bebee.com/jobs?q=junior+product+designer+budapest"
    ]
    jobs, seen_ids = [], set()
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            with urllib.request.urlopen(req, timeout=15) as response: html = response.read().decode('utf-8')
            slugs = re.findall(r'([a-zA-Z0-9-]{10,}-[0-9]{8})', html)
            for slug in slugs:
                if slug in seen_ids or 'global-error' in slug: continue
                seen_ids.add(slug)
                title = slug.split('--')[0].replace('-', ' ').title()
                if any(x in title.lower() for x in ['senior', 'lead', 'direttore', 'head']): continue
                jobs.append({
                    "id": f"bebee-{slug[-8:]}",
                    "title": title, "company": "beBee Network", "location": "Europe / Remote",
                    "url": f"https://bebee.com/job/{slug}", "source": "🐝 beBee",
                    "date": datetime.now().strftime("%d/%m/%Y"), "is_junior": True,
                    "description": "Portati alla pagina originale per i dettagli sull'azienda e sede specifica."
                })
        except Exception as e: print(f"   ❌ Errore beBee [{url[:30]}...]: {e}")
    print(f"   ✅ Trovati {len(jobs)} lavori (All Europe)")
    return jobs

def fetch_uiuxjobsboard():
    """Global Design Board (US/EU/Remote)"""
    print("📡 Scansionando UIUXJobsBoard (Design Focus)...")
    try:
        req = urllib.request.Request("https://uiuxjobsboard.com/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response: html = response.read().decode('utf-8')
        jobs = []
        matches = re.finditer(r'\\"title\\",\\"(.*?)\\",\\"slug\\",\\"([0-9a-zA-Z-]+)\\"', html)
        for match in matches:
            title, slug = match.groups()
            if any(x in title.lower() for x in ['senior', 'lead']): continue
            jobs.append({
                "id": "uiux-" + slug[:20],
                "title": title.replace('\\u0026', '&'), "company": "Design Agency", "location": "Remote / Europe",
                "url": f"https://uiuxjobsboard.com/jobs/{slug}", "source": "🎨 UIUX Jobs",
                "date": datetime.now().strftime("%d/%m/%Y"), "is_junior": True,
                "description": "Specialized UI/UX design board posting."
            })
        print(f"   ✅ Trovati {len(jobs)} lavori (Design Global)")
        return jobs
    except Exception as e: print(f"   ❌ Errore UIUXJobsBoard: {e}"); return []

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
    print(f"\n🎯 Sync 100% Europa completato: {len(unique_jobs)} lavori unici salvati.")

if __name__ == "__main__":
    main()

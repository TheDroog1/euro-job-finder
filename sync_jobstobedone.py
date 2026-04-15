import urllib.request
import json
import re

url = "https://www.jobstobedone.works/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
except Exception as e:
    print(f"Error fetching: {e}")
    exit(1)

matches = re.finditer(r'\\\"title\\\":\\\"(.*?)\\\",\\\"company\\\":\\\"(.*?)\\\".*?\\\"url\\\":\\\"(.*?)\\\".*?\\\"location\\\":\\\"(.*?)\\\"', html)

new_jobs = []
for match in matches:
    title, company, job_url, location = match.groups()
    new_jobs.append({
        "id": "jtd-" + "".join(e for e in title if e.isalnum()).lower(),
        "title": title.replace('\\u0026', '&'),
        "company": company.replace('\\u0026', '&'),
        "location": location.replace('\\u0026', '&'),
        "url": job_url,
        "source": "Jobstobedone Website",
        "date": "14/04/2026",
        "is_junior": True,
        "description": "Selezionato dallo Scout - origin: jobstobedone.works"
    })
    
print(f"Found {len(new_jobs)} jobs via regex.")

try:
    with open("data/jobs.json", "r") as f:
        data = json.load(f)
except Exception:
    data = []

existing_urls = {j.get("url") for j in data}
added = 0
for nj in new_jobs:
    if nj["url"] not in existing_urls:
        data.insert(0, nj)
        added += 1

with open("data/jobs.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Added {added} jobs from jobstobedone.works")

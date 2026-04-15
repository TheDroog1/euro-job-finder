import urllib.request, re, json
url = "https://uxstudio.recruitee.com/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode('utf-8')
        # Check for job links and titles
        matches = re.finditer(r'href="/o/(.*?)".*?>(.*?)</a>', html)
        for m in matches:
            slug, title = m.groups()
            title = re.sub('<[^>]*>', '', title).strip() # clean tags
            if 'Junior' in title or 'Intern' in title or 'Stage' in title:
                print(f"Found: {title} @ https://uxstudio.recruitee.com/o/{slug}")
except Exception as e: print("Error:", e)

import urllib.request

url = "https://bebee.com/it/jobs/role/user-experience-ux"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
}

try:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        print("Status Code:", response.getcode())
        content = response.read().decode('utf-8')
        print("Content Length:", len(content))
        if "Junior" in content or "Stage" in content or "UX" in content:
            print("Found Job-related keywords!")
        # Let's see some snippets
        import re
        # Look for typical job card structure
        jobs = re.findall(r'href="/it/job/(.*?)"', content)
        print("Found links:", len(jobs))
        if jobs: print("Example:", jobs[0])
except Exception as e:
    print("Error:", e)

import urllib.request, json, re

def test_uiux():
    req = urllib.request.Request("https://uiuxjobsboard.com/", headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8')
            
            # Find all JSON-like string blobs
            # In Remix it's like ,"title","Product Designer","slug","1435526-..."
            matches = re.finditer(r'\\"title\\",\\"(.*?)\\",\\"slug\\",\\"([0-9a-zA-Z-]+)\\"', html)
            count = 0
            for m in matches:
                print("UIUX:", m.group(1), f"https://uiuxjobsboard.com/jobs/{m.group(2)}")
                count += 1
            print("UIUX Total:", count)
    except Exception as e: print("UIUX error:", e)

test_uiux()

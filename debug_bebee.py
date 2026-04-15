import urllib.request, re

def debug():
    url = "https://bebee.com/it/jobs/role/user-experience-ux"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    with urllib.request.urlopen(req) as r:
        html = r.read().decode('utf-8')
        
    # Look for any links to /job/
    # format is usually like "href":"/it/job/slug" or similar
    links = re.findall(r'href\\":\\"(.*?job.*?)\\"', html)
    print("Found links:", len(links))
    for l in links[:10]: print("Link:", l)
    
    # Look for any text between quotes after "children"
    texts = re.findall(r'children\\":\\"(.*?)\\"', html)
    print("Found texts:", len(texts))
    for t in texts[:20]: print("Text:", t)

debug()

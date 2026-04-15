import urllib.request
import re

url = "https://bebee.com/it/jobs/role/user-experience-ux"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# Cerchiamo tutti i link dei lavori: di solito <a href="/job/..." ...>
# O la parola "company" vicina a un nome lavorativo
print("HTML LENGTH:", len(html))

# Salviamo l'html
with open("bebee_test.html", "w") as f:
    f.write(html)
print("Saved to bebee_test.html")

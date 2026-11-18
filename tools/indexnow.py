#!/usr/bin/env python3
"""
IndexNow ping for dianasimpsonhernandez.com and frameworks.dianasimpsonhernandez.com.

Run AFTER `git push` has gone live (GitHub Pages takes ~1 min):
    python3 tools/indexnow.py            # submit every URL in both sitemaps
    python3 tools/indexnow.py --dry-run  # print what would be sent

Reads the sitemaps from the two local clones (~/Sites/dsimpsonh.github.io, ~/Sites/frameworks),
so it always submits exactly what you just pushed. Bing shares IndexNow submissions with the
other participating engines. Python standard library only.
"""
from __future__ import annotations
import json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITES = os.path.dirname(HERE)
HOSTS = {
    "dianasimpsonhernandez.com": os.path.join(SITES, "dsimpsonh.github.io"),
    "frameworks.dianasimpsonhernandez.com": os.path.join(SITES, "frameworks"),
}

def key_for(repo: str) -> str:
    keys = [f[:-4] for f in os.listdir(repo) if re.fullmatch(r"[0-9a-f]{32}\.txt", f)]
    if len(keys) != 1: sys.exit(f"expected exactly one IndexNow key file in {repo}, found {keys}")
    return keys[0]

def urls_for(repo: str) -> list[str]:
    xml = open(os.path.join(repo, "sitemap.xml"), encoding="utf-8").read()
    return re.findall(r"<loc>([^<]+)</loc>", xml)

def main() -> None:
    dry = "--dry-run" in sys.argv
    total = 0
    for host, repo in HOSTS.items():
        key, urls = key_for(repo), urls_for(repo)
        assert urls, f"no URLs in {repo}/sitemap.xml"
        body = {"host": host, "key": key, "keyLocation": f"https://{host}/{key}.txt", "urlList": urls}
        total += len(urls)
        if dry:
            print(json.dumps(body, indent=1)); continue
        req = urllib.request.Request("https://api.indexnow.org/indexnow", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"✓ {host}: {len(urls)} URLs → HTTP {r.status}")
        except urllib.error.HTTPError as e:
            # 202 = accepted, key pending verification; 403 = key file not live yet; 422 = URL/host mismatch
            print(f"✗ {host}: HTTP {e.code} {e.reason}"); sys.exit(1)
    print(f"done: {total} URLs")

if __name__ == "__main__":
    main()

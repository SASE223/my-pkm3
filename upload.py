import urllib.request, json, base64, os

# Read token from env file
env_path = os.path.expanduser("~/.hermes/.env")
token = ""
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("GITHUB_TOKEN=***            token = line.split("=", 1)[1].strip().strip("'").strip('"')
            break
if not token:
    print("ERROR: No GITHUB_TOKEN in env")
    exit(1)

OWNER = "SASE223"
REPO = "my-pkm3"

def gh(path, method="GET", data=None):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())

print("Step 1: Get main SHA...")
refs = gh(f"/repos/{OWNER}/{REPO}/git/ref/heads/main")
main_sha = refs["object"]["sha"]
print(f"  main SHA: {main_sha}")

print("Step 2: Create secretary-chat branch...")
try:
    result = gh(f"/repos/{OWNER}/{REPO}/git/refs", "POST",
                {"ref": "refs/heads/secretary-chat", "sha": main_sha})
    print(f"  Created: {result['ref']}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    if "Reference already exists" in body:
        print("  Branch already exists, getting its SHA...")
        ref = gh(f"/repos/{OWNER}/{REPO}/git/ref/heads/secretary-chat")
        print(f"  Existing SHA: {ref['object']['sha']}")
    else:
        print(f"  Error {e.code}: {body}")
        raise

print("Step 3: Upload index.html...")
with open("/home/sase/my-pkm3-chat/index.html", "rb") as f:
    content_b64 = base64.b64encode(f.read()).decode()

try:
    result = gh(f"/repos/{OWNER}/{REPO}/contents/index.html", "PUT", {
        "message": "feat: add secretary chat panel — Hermes Agent API integration",
        "content": content_b64,
        "branch": "secretary-chat"
    })
    print(f"  Uploaded: {result['content']['path']} ({result['content']['size']} bytes)")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    if "sha" in body.lower():
        print("  File exists, need to get its SHA first...")
        existing = gh(f"/repos/{OWNER}/{REPO}/contents/index.html?ref=secretary-chat")
        sha = existing["sha"]
        result = gh(f"/repos/{OWNER}/{REPO}/contents/index.html", "PUT", {
            "message": "feat: add secretary chat panel — Hermes Agent API integration",
            "content": content_b64,
            "branch": "secretary-chat",
            "sha": sha
        })
        print(f"  Updated: {result['content']['path']} ({result['content']['size']} bytes)")
    else:
        print(f"  Error {e.code}: {body}")
        raise

print("\nDone! Branch: secretary-chat")

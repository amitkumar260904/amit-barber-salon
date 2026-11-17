import os
import sys
import json
import base64
import urllib.request
import urllib.error
import subprocess

def push_via_git(repo_url):
    print(f"[*] Initializing local Git repository...")
    commands = [
        ["git", "init"],
        ["git", "config", "user.name", "Amit Developer"],
        ["git", "config", "user.email", "amit.developer@example.com"],
        ["git", "add", "."],
        ["git", "commit", "-m", "Initial commit: Amit Luxury Barber & Salon booking app"],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "remove", "origin"], # in case already exists
        ["git", "remote", "add", "origin", repo_url],
        ["git", "push", "-u", "origin", "main", "--force"]
    ]
    for cmd in commands:
        try:
            print(f"Executing: {' '.join(cmd)}")
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 and "remove" not in cmd:
                print(f"Warning / Error: {res.stderr.strip()}")
            else:
                if res.stdout.strip():
                    print(res.stdout.strip())
        except Exception as e:
            print(f"Error executing {cmd[0]}: {e}")

def push_via_api(token, repo_name="amit-barber-salon", description="Amit Luxury Barber & Salon Booking App"):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Amit-Barber-Salon-App"
    }

    # 1. Get authenticated user
    try:
        req = urllib.request.Request("https://api.github.com/user", headers=headers)
        with urllib.request.urlopen(req) as resp:
            user_data = json.loads(resp.read().decode())
            username = user_data["login"]
            print(f"[+] Authenticated as GitHub user: {username}")
    except Exception as e:
        print(f"[-] Authentication failed with GitHub token: {e}")
        return

    # 2. Check if repo exists or create it
    repo_url = f"https://api.github.com/user/repos"
    payload = json.dumps({
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False
    }).encode("utf-8")

    try:
        req = urllib.request.Request(repo_url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            print(f"[+] Successfully created repository: {username}/{repo_name}")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            print(f"[*] Repository {username}/{repo_name} already exists. Proceeding with file upload...")
        else:
            print(f"[-] Error creating repo: {e}")

    # 3. Upload files (index.html, README.md, .gitignore)
    files_to_upload = ["index.html", "README.md", ".gitignore"]
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for filename in files_to_upload:
        filepath = os.path.join(base_dir, filename)
        if not os.path.exists(filepath):
            continue

        with open(filepath, "rb") as f:
            content_bytes = f.read()
            content_b64 = base64.b64encode(content_bytes).decode("utf-8")

        # Check if file already exists to get SHA
        sha = None
        file_api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{filename}"
        try:
            req = urllib.request.Request(file_api_url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                existing_file = json.loads(resp.read().decode())
                sha = existing_file.get("sha")
        except urllib.error.HTTPError:
            pass

        put_payload = {
            "message": f"Add {filename} for Amit Barber & Salon web app",
            "content": content_b64,
            "branch": "main"
        }
        if sha:
            put_payload["sha"] = sha

        req = urllib.request.Request(file_api_url, data=json.dumps(put_payload).encode("utf-8"), headers=headers, method="PUT")
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"[+] Successfully pushed {filename} to {username}/{repo_name}")
        except Exception as e:
            print(f"[-] Failed to push {filename}: {e}")

    # 4. Enable GitHub Pages
    pages_api_url = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    pages_payload = json.dumps({
        "source": {"branch": "main", "path": "/"}
    }).encode("utf-8")

    try:
        req = urllib.request.Request(pages_api_url, data=pages_payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            print(f"[+] Successfully enabled GitHub Pages!")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"[*] GitHub Pages is already active for this repository.")
        else:
            print(f"[*] Pages configuration note: {e}")

    live_url = f"https://{username}.github.io/{repo_name}/"
    print("\n==========================================================")
    print(f"🎉 SUCCESS! Your Barber Salon website is on GitHub:")
    print(f"📁 Repository: https://github.com/{username}/{repo_name}")
    print(f"🌐 Live Website URL: {live_url}")
    print("==========================================================")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("ghp_"):
        push_via_api(sys.argv[1])
    elif len(sys.argv) > 1 and "github.com" in sys.argv[1]:
        push_via_git(sys.argv[1])
    else:
        print("Usage:")
        print("  python github_push.py <GITHUB_PERSONAL_ACCESS_TOKEN>   (Direct 1-click Push & Live Pages)")
        print("  python github_push.py <GITHUB_REPO_URL>                (Via Git CLI)")

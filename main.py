"""ChromeProfil - Flow Launcher plugin to search and open Chrome profiles.

Speaks Flow Launcher's JSON-RPC v1 directly (no dependencies): Flow runs
`python main.py '{"method": ..., "parameters": [...]}'` and reads JSON from stdout.
"""
import json
import os
import subprocess
import sys

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
ICON = os.path.join(PLUGIN_DIR, "Images", "icon.png")
USER_DATA = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")


def load_profiles():
    """Return the profiles listed in Chrome's Local State, most recently used first."""
    with open(os.path.join(USER_DATA, "Local State"), encoding="utf-8") as f:
        info = json.load(f)["profile"]["info_cache"]
    profiles = []
    for directory, p in info.items():
        picture = os.path.join(USER_DATA, directory, "Google Profile Picture.png")
        profiles.append({
            "dir": directory,
            "name": p.get("name") or directory,
            "account": p.get("gaia_name", ""),
            "email": p.get("user_name", ""),
            "icon": picture if os.path.isfile(picture) else ICON,
            "active_time": p.get("active_time", 0),
        })
    profiles.sort(key=lambda p: p["active_time"], reverse=True)
    return profiles


def score(query, profile):
    """0 = no match. Name prefix beats word prefix beats substring; name beats account/email."""
    best = 0
    for weight, field in ((3, profile["name"]), (2, profile["account"]), (1, profile["email"])):
        text = field.lower()
        if not text:
            continue
        if text.startswith(query):
            s = 100
        elif any(word.startswith(query) for word in text.replace("@", " ").replace(".", " ").split()):
            s = 70
        elif query in text:
            s = 40
        else:
            continue
        best = max(best, s * weight)
    return best


def find_chrome():
    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
                with winreg.OpenKey(hive, key) as k:
                    path = winreg.QueryValue(k, None)
                if os.path.isfile(path):
                    return path
            except OSError:
                pass
    except ImportError:
        pass
    for base in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        path = os.path.join(os.environ.get(base, ""), "Google", "Chrome", "Application", "chrome.exe")
        if os.path.isfile(path):
            return path
    return "chrome.exe"


def result(title, subtitle, icon=ICON, action=None, score=0):
    r = {"Title": title, "SubTitle": subtitle, "IcoPath": icon, "Score": score}
    if action:
        r["JsonRPCAction"] = action
    return r


def query(text):
    text = text.strip().lower()
    try:
        profiles = load_profiles()
    except (OSError, KeyError, ValueError) as e:
        return [result("Couldn't read Chrome profiles", str(e))]

    results = []
    for i, p in enumerate(profiles):
        s = score(text, p) if text else 0
        if text and not s:
            continue
        subtitle = " - ".join(x for x in (p["account"], p["email"]) if x) or p["dir"]
        # Keep most-recently-used order when the query is empty or scores tie.
        results.append(result(
            p["name"], subtitle, p["icon"],
            {"method": "open_profile", "parameters": [p["dir"]]},
            s * 100 + (len(profiles) - i),
        ))
    if not results:
        results.append(result("No matching Chrome profile", f'Nothing matches "{text}"'))
    return results


def open_profile(directory):
    subprocess.Popen(
        [find_chrome(), f"--profile-directory={directory}"],
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
        close_fds=True,
    )


def main():
    request = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"method": "query", "parameters": [""]}
    method, params = request.get("method"), request.get("parameters") or [""]
    if method == "query":
        print(json.dumps({"result": query(params[0])}))
    elif method == "open_profile":
        open_profile(params[0])


if __name__ == "__main__":
    main()

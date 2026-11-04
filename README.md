# ChromeProfil

A [Flow Launcher](https://www.flowlauncher.com/) plugin that searches your Google Chrome profiles and opens the one you pick.

```
cp work      → opens Chrome with your "Work" profile
cp           → lists every profile, most recently used first
```

Searches profile names, Google account names and emails. Shows each profile's picture when Chrome has one.

## Install

1. Copy this folder to `%APPDATA%\FlowLauncher\Plugins\ChromeProfil`.
2. Restart Flow Launcher.

Needs Python (Flow Launcher will offer to set it up the first time). No pip packages.

## How it works

Profiles come from `%LOCALAPPDATA%\Google\Chrome\User Data\Local State`. Picking one runs
`chrome.exe --profile-directory="<Profile N>"`.

The action keyword is `cp`; change it in Flow Launcher's plugin settings.

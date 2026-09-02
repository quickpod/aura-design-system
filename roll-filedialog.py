#!/usr/bin/env python3
"""Roll the kdialog file-dialog wrapper into aura.py copies + call sites."""
import os, re, sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
BLOCK = open(os.path.join(SCRATCH, "filedialog_block.py")).read()
MARK = "_FiledialogShim"
REPOS = "/home/ubuntu/quickopen/repos"

# (aura.py path, [files with filedialog call sites], import statement)
PKG = [  # <repo>/<pkg> layout -> relative import
    ("aiquick-security", "aqsec"), ("aiquick-vpn", "aiquickvpn"),
    ("archive-pro", "archivepro"), ("auth-keeper", "authkeeper"),
    ("backup-toolkit", "backupkit"), ("budget-book", "budgetbook"),
    ("cloud-sync", "cloudsync"), ("crypt-box", "cryptbox"),
    ("db-explorer", "dbkit"), ("disk-cleaner", "diskkit"),
    ("feed-hub", "feedhub"), ("file-toolkit", "filekit"),
    ("find-all", "findall"), ("git-deck", "gitdeck"),
    ("grab-it", "grabit"), ("hardware-info", "hwinfo"),
    ("image-toolkit", "imgtoolkit"), ("localllm-studio", "localllm"),
    ("media-toolkit", "mediakit"), ("music-organizer", "musickit"),
    ("note-nest", "notenest"), ("pdf-toolkit", "pdftoolkit"),
    ("plain-text-editor", "plaintexteditor"), ("qr-toolkit", "qrkit"),
    ("recall-deck", "recalldeck"), ("screen-studio", "screenkit"),
    ("ssh-deck", "sshdeck"), ("text-data-toolkit", "textkit"),
    ("voice-type", "voicetype"),
]
TARGETS = []
for repo, pkg in PKG:
    TARGETS.append((f"{REPOS}/{repo}/{pkg}/aura.py",
                    [f"{REPOS}/{repo}/{pkg}/gui.py"],
                    "from .aura import filedialog"))
TARGETS.append((f"{REPOS}/infra-monitor/aura.py",
                [f"{REPOS}/infra-monitor/gmtray.py"],
                "from aura import filedialog"))
TARGETS.append((f"{REPOS}/securevault/src/aura.py",
                [f"{REPOS}/securevault/src/svgui.py",
                 f"{REPOS}/securevault/src/svpassgui.py",
                 f"{REPOS}/securevault/src/svwizard.py"],
                "from aura import filedialog"))

IMP_RE = re.compile(r"^(\s*)from tkinter import .*\bfiledialog\b.*$")
appended, imported, problems = [], [], []

for aura_path, guis, stmt in TARGETS:
    if not os.path.isfile(aura_path):
        problems.append(f"MISSING aura: {aura_path}"); continue
    src = open(aura_path).read()
    if MARK in src:
        pass  # already rolled
    else:
        if not src.endswith("\n"):
            src += "\n"
        open(aura_path, "w").write(src + BLOCK)
        appended.append(aura_path)
    for g in guis:
        if not os.path.isfile(g):
            problems.append(f"MISSING gui: {g}"); continue
        lines = open(g).read().splitlines(keepends=True)
        if any(stmt in ln for ln in lines):
            continue
        out, hits = [], 0
        for ln in lines:
            out.append(ln)
            m = IMP_RE.match(ln.rstrip("\n"))
            if m:
                out.append(f"{m.group(1)}{stmt}  "
                           "# noqa: F811 - Aura kdialog-native pickers\n")
                hits += 1
        if hits == 0:
            problems.append(f"NO tkinter-filedialog import line in {g}")
            continue
        open(g, "w").write("".join(out))
        imported.append(f"{g} (+{hits})")

print("aura.py copies appended:", len(appended))
for p in appended: print("  A", p)
print("call-site files updated:", len(imported))
for p in imported: print("  I", p)
if problems:
    print("PROBLEMS:")
    for p in problems: print("  !", p)
    sys.exit(1)

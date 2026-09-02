#!/usr/bin/env python3
"""Harness for the aura kdialog file-dialog wrapper (0.6.9 item 1).
Fake kdialog on PATH: records argv, returns a scripted rc/stdout.
Tk fallback is asserted by monkeypatching aura._tk_filedialog (no X needed)."""
import os, sys, json, stat, tempfile, importlib, types
HERE = os.path.dirname(os.path.abspath(__file__))
AURA = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/quickopen/repos/securevault/src/aura.py"
fails = 0
def check(name, cond, extra=""):
    global fails
    print(("PASS " if cond else "FAIL ") + name + (("  " + extra) if extra and not cond else ""))
    if not cond: fails += 1

tmp = tempfile.mkdtemp()
fake = os.path.join(tmp, "kdialog"); log = os.path.join(tmp, "argv.json"); script = os.path.join(tmp, "script")
with open(fake, "w") as f:
    f.write("#!/bin/sh\nprintf '%s\\n' \"$@\" > '" + log + "'\n. '" + script + "'\nprintf '%s' \"$OUT\"\nexit $RC\n")
os.chmod(fake, 0o755)
def scripted(rc, out):
    with open(script, "w") as f: f.write("RC=%d\nOUT='%s'\n" % (rc, out))
def argv():
    return open(log).read().split("\n")[:-1]

os.environ["PATH"] = tmp + ":" + os.environ.get("PATH", "")
os.environ["DISPLAY"] = ":99"
os.environ.pop("AURA_TK_FILEDIALOG", None)
sys.path.insert(0, os.path.dirname(AURA))
spec = importlib.util.spec_from_file_location("aura_t", AURA)
aura = importlib.util.module_from_spec(spec); spec.loader.exec_module(aura)
check("shim exported", hasattr(aura, "filedialog") and type(aura.filedialog).__name__ == "_FiledialogShim")
check("kdialog probed", aura._fd_kdialog() == fake, str(aura._fd_kdialog()))

# stub the Tk fallback so we can assert when it is reached
calls = []
stub = types.SimpleNamespace(
    askopenfilename=lambda **o: calls.append(("open", o)) or "/tk/open",
    askopenfilenames=lambda **o: calls.append(("opens", o)) or ("/tk/a", "/tk/b"),
    asksaveasfilename=lambda **o: calls.append(("save", o)) or "/tk/save",
    askdirectory=lambda **o: calls.append(("dir", o)) or "/tk/dir",
    Open="TKOPENCLASS")
aura._tk_filedialog = stub

# 1. open OK with filter + title + initialdir
scripted(0, "/home/x/f.txt\n")
r = aura.filedialog.askopenfilename(title="Pick", initialdir="~/Documents",
                                    filetypes=[("Text", "*.txt"), ("All", "*.*")])
a = argv()
check("open returns kdialog path", r == "/home/x/f.txt", repr(r))
check("open argv title", a[:2] == ["--title", "Pick"], repr(a))
check("open argv mode+dir", "--getopenfilename" in a and os.path.expanduser("~/Documents") in a, repr(a))
check("open filter (*.* -> *)", a[-2:] == ["*.txt|Text", "*|All"], repr(a[-2:]))
check("no tk call", not calls)
# 2. cancel -> "" like Tk
scripted(1, "")
r = aura.filedialog.askopenfilename()
check("cancel returns empty", r == "" and not calls, repr(r))
check("default start dir is :aura", ":aura" in argv())
# 3. kdialog failure -> Tk fallback with the same kwargs
scripted(2, "")
r = aura.filedialog.askopenfilename(title="T", filetypes=[("A", "*.a")])
check("rc2 falls back to Tk", r == "/tk/open" and calls and calls[-1] == ("open", {"title": "T", "filetypes": [("A", "*.a")]}), repr((r, calls)))
calls.clear()
# 4. multiple
scripted(0, "/a/1\n/a/2\n")
r = aura.filedialog.askopenfilenames(initialdir="/a")
check("multiple returns tuple", r == ("/a/1", "/a/2"), repr(r))
check("multiple argv", "--multiple" in argv() and "--separate-output" in argv())
r = aura.filedialog.askopenfilename(multiple=True)
check("multiple=True routes to names", r == ("/a/1", "/a/2") and "--multiple" in argv())
# 5. save with defaultextension + initialfile
scripted(0, "/home/x/vault")
r = aura.filedialog.asksaveasfilename(initialdir="/home/x", initialfile="vault.sv", defaultextension=".sv")
check("save appends defaultextension", r == "/home/x/vault.sv", repr(r))
check("save start = dir/initialfile", "/home/x/vault.sv" in argv() and "--getsavefilename" in argv(), repr(argv()))
scripted(0, "/home/x/vault.zip")
r = aura.filedialog.asksaveasfilename(defaultextension=".sv")
check("save keeps typed extension", r == "/home/x/vault.zip", repr(r))
scripted(1, "")
check("save cancel empty", aura.filedialog.asksaveasfilename(defaultextension=".sv") == "")
# 6. directory
scripted(0, "/mnt/usb")
check("askdirectory", aura.filedialog.askdirectory(initialdir="/mnt") == "/mnt/usb" and "--getexistingdirectory" in argv())
# 7. passthrough attrs
check("passthrough attr", aura.filedialog.Open == "TKOPENCLASS")
# 8. parent with winfo_id -> --attach
class P:  # fake Tk widget
    def winfo_id(self): return 0x1234
scripted(0, "/p")
aura.filedialog.askopenfilename(parent=P())
check("parent -> --attach", argv()[argv().index("--attach") + 1] == str(0x1234) if "--attach" in argv() else False, repr(argv()))
# 9. kdialog absent -> Tk
aura._FD_PROBED = False; aura._FD_KDIALOG = None
os.environ["PATH"] = "/nonexistent"
calls.clear()
check("no kdialog -> tk", aura.filedialog.askopenfilename() == "/tk/open" and calls)
# 10. env override
os.environ["PATH"] = tmp; os.environ["AURA_TK_FILEDIALOG"] = "1"; aura._FD_PROBED = False; aura._FD_KDIALOG = None
calls.clear()
check("AURA_TK_FILEDIALOG forces tk", aura.filedialog.askdirectory() == "/tk/dir" and calls)
# 11. no DISPLAY -> tk
os.environ.pop("AURA_TK_FILEDIALOG"); os.environ.pop("DISPLAY"); aura._FD_PROBED = False; aura._FD_KDIALOG = None
check("no DISPLAY -> tk", aura._fd_kdialog() is None)
print("RESULT: %d failures" % fails); sys.exit(1 if fails else 0)

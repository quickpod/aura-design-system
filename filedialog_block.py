

# =========================================================================
# Native file dialogs — kdialog first, tkinter.filedialog fallback (0.6.9)
# =========================================================================
# The stock Tk pickers on Linux are the bare Motif-style dialogs: no Places
# sidebar, no drives, unthemed (owner report, 0.6.9 round).  Quick OS ships
# kdialog (stage 51 installs it for the install gate), whose pickers are the
# native KDE ones — Places sidebar, drives, previews — for free.
#
# Drop-in use (call sites keep the exact tkinter.filedialog API and cancel
# semantics — cancel returns "" / empty tuple just like Tk):
#     from aura import filedialog        # flat apps  (import aura)
#     from .aura import filedialog       # package apps (from . import aura)
# added AFTER any `from tkinter import ... filedialog ...` line so the name
# shadows the stock module.  Anything beyond the four ask* functions passes
# through to tkinter.filedialog unchanged.
#
# Set AURA_TK_FILEDIALOG=1 to force the stock Tk dialogs (tests, debugging).

import os as _fd_os
import shutil as _fd_shutil
import subprocess as _fd_subprocess
import tkinter.filedialog as _tk_filedialog

_FD_KDIALOG = None                      # cached shutil.which() result
_FD_PROBED = False


def _fd_kdialog():
    """Absolute path to kdialog, or None.  Needs a graphical session."""
    global _FD_KDIALOG, _FD_PROBED
    if not _FD_PROBED:
        _FD_PROBED = True
        if ((_fd_os.environ.get("DISPLAY") or _fd_os.environ.get("WAYLAND_DISPLAY"))
                and not _fd_os.environ.get("AURA_TK_FILEDIALOG")):
            _FD_KDIALOG = _fd_shutil.which("kdialog")
    return _FD_KDIALOG


def _fd_filter(filetypes):
    """Tk ``filetypes`` [(label, pattern-or-tuple), ...] -> kdialog filter.

    kdialog wants newline-separated ``"pat1 pat2|Label"`` lines, and Tk's
    catch-all ``*.*`` must become ``*`` (KDE matches literally otherwise)."""
    lines = []
    for entry in (filetypes or ()):
        try:
            label, pats = entry[0], entry[1]
        except Exception:
            continue
        if isinstance(pats, (list, tuple)):
            pats = " ".join(str(p) for p in pats)
        pats = " ".join("*" if p in ("*.*", "*") else p
                        for p in str(pats).split()) or "*"
        lines.append("%s|%s" % (pats, label))
    return "\n".join(lines)


def _fd_start(opts, want_file=False):
    """kdialog startDir argument from Tk ``initialdir``/``initialfile``.

    ``:aura`` is kdialog's remembered last-used directory (per label) — the
    same remember-where-I-was behaviour Tk gives when no dir is passed."""
    d = _fd_os.path.expanduser(str(opts.get("initialdir") or ""))
    f = str(opts.get("initialfile") or "") if want_file else ""
    if f:
        return _fd_os.path.join(d or _fd_os.getcwd(), f)
    return d or ":aura"


def _fd_run(mode_args, opts):
    """Run kdialog -> stdout str on OK, '' on user cancel, None on failure
    (the caller then falls back to the stock Tk dialog)."""
    argv = [_FD_KDIALOG]
    title = opts.get("title")
    if title:
        argv += ["--title", str(title)]
    parent = opts.get("parent")
    if parent is not None:
        try:                            # X11 only; harmless when it fails
            argv += ["--attach", str(int(parent.winfo_id()))]
        except Exception:
            pass
    argv += mode_args
    try:
        p = _fd_subprocess.run(argv, stdout=_fd_subprocess.PIPE,
                               stderr=_fd_subprocess.DEVNULL)
    except Exception:
        return None
    if p.returncode == 0:
        return p.stdout.decode("utf-8", "replace").rstrip("\n")
    if p.returncode == 1:               # Cancel / Esc — Tk returns "" here
        return ""
    return None                         # anything else: fall back to Tk


def askopenfilename(**opts):
    """tkinter.filedialog.askopenfilename, native (kdialog) when possible."""
    if opts.get("multiple"):
        return askopenfilenames(**{k: v for k, v in opts.items()
                                   if k != "multiple"})
    if _fd_kdialog():
        args = ["--getopenfilename", _fd_start(opts)]
        flt = _fd_filter(opts.get("filetypes"))
        if flt:
            args.append(flt)
        r = _fd_run(args, opts)
        if r is not None:
            return r
    return _tk_filedialog.askopenfilename(**opts)


def askopenfilenames(**opts):
    """tkinter.filedialog.askopenfilenames, native (kdialog) when possible."""
    if _fd_kdialog():
        args = ["--getopenfilename", _fd_start(opts)]
        flt = _fd_filter(opts.get("filetypes"))
        if flt:
            args.append(flt)
        args += ["--multiple", "--separate-output"]
        r = _fd_run(args, opts)
        if r is not None:
            return tuple(p for p in r.split("\n") if p)
    return _tk_filedialog.askopenfilenames(**opts)


def asksaveasfilename(**opts):
    """tkinter.filedialog.asksaveasfilename, native (kdialog) when possible.

    kdialog (KF >= 5.72) confirms overwrite itself; ``defaultextension`` is
    appended when the user typed a bare name, exactly like Tk."""
    if _fd_kdialog():
        args = ["--getsavefilename", _fd_start(opts, want_file=True)]
        flt = _fd_filter(opts.get("filetypes"))
        if flt:
            args.append(flt)
        r = _fd_run(args, opts)
        if r is not None:
            ext = str(opts.get("defaultextension") or "")
            if r and ext and not _fd_os.path.splitext(r)[1]:
                r += ext
            return r
    return _tk_filedialog.asksaveasfilename(**opts)


def askdirectory(**opts):
    """tkinter.filedialog.askdirectory, native (kdialog) when possible."""
    if _fd_kdialog():
        r = _fd_run(["--getexistingdirectory", _fd_start(opts)], opts)
        if r is not None:
            return r
    return _tk_filedialog.askdirectory(**opts)


class _FiledialogShim(object):
    """tkinter.filedialog stand-in: the four ask* prefer kdialog; anything
    else (askopenfile, the dialog classes, ...) passes through untouched."""
    askopenfilename = staticmethod(askopenfilename)
    askopenfilenames = staticmethod(askopenfilenames)
    asksaveasfilename = staticmethod(asksaveasfilename)
    askdirectory = staticmethod(askdirectory)

    def __getattr__(self, name):
        return getattr(_tk_filedialog, name)


filedialog = _FiledialogShim()

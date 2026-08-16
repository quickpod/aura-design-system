# Aura App Layout Language

**The structural spec every enhanced QuickOpen catalog app follows.** It is
derived from the Quick OS desktop's Aura DS (deep blue-black dark + pale light,
accent `#5b86f7`, hairline borders, pill/chip language) and from the layout
conventions shared by leading commercial desktop apps (Notion, Obsidian,
Notepad++, Todoist, 1Password, Postman, 7-Zip, …). Goal: **feature-rich but
not complex** — adopt the benchmark product's daily-use layout, curate away its
pro-complexity, and keep every surface themed in BOTH Aura modes.

Everything named here exists in the vendored `aura.py` (regenerated from
`aura.template.py`, ≥ the version emitted 2026-08-16). An agent enhancing an
app applies this document without re-deriving decisions; re-vendor `dist/aura.py`
into the app being upgraded (per-app at upgrade time — never mass re-vendor).

---

## 1. Window anatomy (the five zones)

```
┌──────────┬────────────────────────────────────────────────┐
│          │  Header: page title            [header_actions]│
│ Sidebar  ├────────────────────────────────────────────────┤ ← 2px accent beam
│          │  Toolbar: [＋ Primary] [action] │ … [⌕ search]  │
│  nav     ├────────────────────────────────────────────────┤
│  pills   │                                                │
│          │  Content (lists / editor / panes)              │
│ sidebar_ │                                                │
│  body    │                                                │
│          ├────────────────────────────────────────────────┤
│ footer   │  Status bar: state pill        [status actions]│
└──────────┴────────────────────────────────────────────────┘
```

Every app is an `aura.AuraApp`. The five zones and who owns them:

1. **Sidebar** (`AuraApp` builds it) — brand row (icon + app name), nav pills
   (`add_section`), then `app.sidebar_body` (app-owned; see §3), then the
   footer (Dark-mode switch + tagline/version). **Collapsible**: Ctrl+\ /
   `toggle_sidebar()` is wired by the framework. Width 248.
2. **Header** — the current section label as page title; `header_actions`
   holds at most 3 window-global controls (live status chip, Lock, ☰ menu).
   Never put per-view actions here — they go in the toolbar.
3. **Toolbar** (`aura.Toolbar`, the tier most legacy apps were missing) — one
   per section that has actions, packed directly above the content
   (`tb.pack(fill="x", pady=(0, 10))`). Order convention: the **primary
   creation/run action left-most** (`kind="primary"`, label `＋ New …` / `Run`),
   then contextual secondaries, `add_separator()` between groups, **search and
   view controls right** (`add_search`, `add_right`). Height 44, buttons
   height 32. Simple form-shaped sections (settings-like panels) may skip the
   toolbar rather than hold a lone button.
4. **Content** — the section frame from `add_section`. Shapes:
   - **List-detail** (vault, feeds, sessions, jobs): `ttk.Panedwindow`
     (already Aura-styled), list pane left (min ~260px), detail right.
   - **Table**: `ttk.Treeview` (Aura-styled: row height 34, accent-soft
     selection), always paired with `aura.AuraScrollbar`.
   - **Editor**: `tk.Text` registered via `aura.track(w, "text")`, inside a
     radius-10 hairline `CTkFrame` wrap (`fg_color=field`).
   - **Forms**: `aura.Card` stacks; label column left, field right.
5. **Status bar** — `set_status/set_error/set_success/set_working` only;
   `statusbar.actions` holds persistent utilities (Open folder, progress bar,
   Cancel). Errors NEVER appear as raw dialogs when the status bar can carry
   them; dialogs are reserved for confirmations and data-loss questions.

## 2. Raw-tk hygiene (the mixed-surface rule)

CustomTkinter widgets theme themselves. Every raw `tk`/`ttk` widget MUST be
either an Aura-styled ttk class (Treeview, Notebook, Panedwindow, Separator)
or registered with `aura.track(widget, "listbox"|"text"|"canvas"|"menu")`.
`aura.SectionLabel`/`Heading`/`Caption` must sit on CTk parents (transparent
frames), never on plain `ttk.Frame` — that is what produced the light label
boxes in old dark-mode screenshots. Acceptance: flip the theme both ways at
runtime and eyeball every pane — **no unthemed rectangle in either mode**.

## 3. `sidebar_body` — library navigation

Apps whose benchmark keeps a library in the sidebar (tags, folders, pinned
items, workspaces) put it in `app.sidebar_body` (transparent frame between the
nav pills and the footer): an `aura.SectionLabel` header plus ghost-style rows
(buttons `anchor="w"`, `kind="ghost"`-like colors, muted text, count captions
right). Selection state mirrors `_NavItem`: accent-soft fill + text color.
Keep it to ONE library — the sidebar is navigation, not a dashboard.

## 4. Theme behavior (owner rule — no exceptions)

- A fresh install **follows the OS**: the app's config module accepts
  `("system", "light", "dark")` and `get_theme()` returns `"system"` when
  unset. `AuraApp` then live-follows Aura Dark/Light via darkdetect.
- The sidebar Dark-mode switch and any in-app choice is an explicit override
  and is persisted; Settings offers the three-way System/Light/Dark choice.
- Both modes must be complete: dual-theme screenshots
  (`publish/scripts/capture-screenshots.py`) are part of done.

## 5. Typography & spacing

From `aura.py` tokens only — no ad-hoc values: `font(role=...)` for
title 19 / heading 15 / body 12 / caption 11 / section 11-caps;
`spaced()` for section labels. Content padding 24 (`TOKENS.geometry.pad`),
card padding 16, control gaps 8, group gaps 10–12. Monospace surfaces
(editors, logs, code) use Consolas/DejaVu Sans Mono per the app's existing
convention.

## 6. Empty states & imagery

Every list/detail surface that can be empty shows an `aura.EmptyState`
instead of a blank pane: glyph or illustration + one-line title + one-line
caption + at most ONE primary action (the same action as the toolbar primary).
The detail pane of a list-detail view gets a quieter variant (no action, or a
keyboard hint like "Select a note or press Ctrl+N").

Illustrations (optional, tasteful, sparing — an empty-state image beats
decorating every panel): AI-generated per app via the image-gen worker, in the
Aura palette (deep blue-black + `#5b86f7` accent). Ship a per-theme pair
(`assets/<name>-dark.png` / `-light.png`) sized to the display size (~300×200,
Lanczos-downscaled, tens of KB) and pass both to
`EmptyState(image=(light, dark))` — CTkImage swaps them with the theme.
Note AI provenance in the app repo (README or assets/README). Do NOT touch
app icons — they are approved and out of scope.

## 7. Keyboard shortcuts baseline

Bound via `bind_all` in the app's menu builder; shown in menu accelerators.

| Keys | Meaning (when the concept exists) |
|---|---|
| Ctrl+N | New item (note, connection, job, request…) |
| Ctrl+S | Save / apply current item |
| Ctrl+F | Focus the toolbar search |
| Ctrl+P | Quick switcher / open-by-name (library apps) |
| Ctrl+, | Settings dialog |
| Ctrl+\ | Toggle sidebar (framework-provided) |
| F2 | Rename selected item |
| Delete | Delete selected item (with confirm) |
| Escape | Clear search / close dialog (framework-provided in both) |
| F5 | Refresh / re-run, where the app has that verb |

Editors additionally: Ctrl+B/I bold/italic, Ctrl+K insert link, Ctrl+E cycle
edit/preview modes (Markdown apps).

## 8. Settings dialog convention

Ctrl+, and a menu entry open ONE `aura.Dialog` titled "Settings"
(size ≈ 520×420): rows of label + control grouped under `SectionLabel`s;
the three-way theme choice lives here; a single Close button (settings apply
immediately — no OK/Apply pair). App-specific preferences that used to live
loose in panels migrate here.

## 9. Menus

Native menubars stay banned (`AuraApp` converts `config(menu=...)` into the
☰ header dropdown). Keep File / View / Help cascades with accelerator text
matching §7. Context menus (`tk.Menu` + `aura.track(menu, "menu")`) on
right-click for list rows: the benchmark's row verbs (Open, Rename, Pin,
Delete…).

## 10. What "feature-rich but not complex" means here

For each app: name its leading commercial benchmark, adopt the benchmark's
**layout** and its **top daily-use features**, and explicitly refuse its pro
tail. Curation rules of thumb:

- ≤ 7 nav pills; merge or demote anything beyond that.
- One primary action per toolbar; if you can't pick one, the section is
  doing too much.
- No plugins/marketplaces, no sync/accounts, no multi-window, no
  scripting — QuickOpen apps are local, single-window, ordinary-user tools.
- Existing data formats and on-disk locations are compatibility surfaces:
  never migrate or break them.

## Reference implementation

`repos/note-nest` (NoteNest 1.1.0, benchmarked against Obsidian/Apple Notes)
is the worked example of every rule above — read its `notenest/gui.py` before
enhancing another app.

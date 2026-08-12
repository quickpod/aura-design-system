# Aura Design System

**One coherent visual language for the whole QuickOpen / AIQuick surface** — the
OS shell (Plasma), the desktop apps (tkinter/CustomTkinter), and the web
(quickopen.ai + artifacts). Everything is *generated* from a single source of
truth, so a change made once ripples everywhere.

Identity: **"deep space + light"** — calm dark layers, one vivid brand accent
(`#5b86f7`), hairline borders, pill/chip language, and the signature 2px accent
beam under app headers.

```
aura-tokens.json  ──►  generate.py  ──►  dist/aura.py            (33 apps vendor this)
 (source of truth)                       dist/AuraDark.colors    (Plasma shell)
                                         dist/AuraLight.colors   (Plasma shell)
                                         dist/aura.css           (web)
                                         dist/aura-swatches.html (visual reference)
```

---

## 1. The tokens (`aura-tokens.json`)

The canonical file. Token categories:

| Category | Keys | Purpose |
|----------|------|---------|
| `brand` | `accent`, `accent-strong`, `accent-edge`, `beam` | The single brand accent family. **`accent = #5b86f7` in BOTH dark and light** (v1 reconciles the old light-mode `#2f5fe0` divergence to one accent). |
| `radius` | `sm md lg pill` | Corner radii. |
| `space` | `1 2 3 4 5 6 8` | Spacing scale (px). |
| `type` | `family-ui`, `family-mono`, `scale`, `weight` | Typography. |
| `elevation` | `0 1 2 3` | Shadow ramp. |
| `semantic` | `ok warn danger info` | Status colors (mode-independent brand values). |
| `modes.dark` / `modes.light` | `bg bg2 surface surface2 surface3 border border2 text muted faint field accent on-accent ok warn danger` | The two full palettes. |

## 2. The generator (`generate.py`)

Reads the tokens and emits everything into `dist/`. **Idempotent** — re-running
produces byte-identical output. It hardcodes no color beyond what the tokens
define.

Token → output mapping:

- **`dist/aura.py`** — the apps' theme module. `generate.py` fills three markers
  in `aura.template.py` (which holds *all* of aura.py's logic) from the tokens:
  the `TOKENS["dark"]` / `TOKENS["light"]` palette dicts and `DEFAULT_ACCENT`
  (← `brand.accent`). `accent` / `on-accent` are derived at runtime by
  `aura._resolve()`, so they stay out of the base dicts. `_light_variant()` is
  the identity (single accent for both modes), so a per-app accent passed to
  `apply(accent=…)` composes unchanged over the light palette too.
- **`dist/AuraDark.colors` / `dist/AuraLight.colors`** — KDE/Plasma color-schemes.
  Each mode maps to `[Colors:Window|View|Button|Selection|Tooltip|Header|Complementary]`,
  `[WM]`, `[General]`. `accent → DecorationFocus/DecorationHover` and the
  `[Colors:Selection]` background; `on-accent →` Selection foreground; semantic
  tokens → `ForegroundPositive/Neutral/Negative`.
- **`dist/aura.css`** — CSS custom properties (`--aura-*`). `:root` = light + all
  non-mode tokens (brand, radius, space, type, elevation, semantic); dark applies
  via `@media (prefers-color-scheme: dark)` and explicit `:root[data-theme="dark"]`
  / `:root[data-theme="light"]` overrides.
- **`dist/aura-swatches.html`** — self-contained visual reference of every token
  in both modes.

### How to change a token and regenerate

```sh
# 1. edit aura-tokens.json  (e.g. bump the brand accent)
# 2. regenerate every consumer
python3 branding/aura-design-system/generate.py
# 3. propagate dist/aura.py into the apps (all 33 share the identical file)
for f in $(find repos -name aura.py); do cp branding/aura-design-system/dist/aura.py "$f"; done
# 4. run the app test suites (headless) to confirm nothing regressed
```

The Plasma `.colors` and `aura.css` are picked up by their consumers (see
Follow-ups).

## 3. The three consumers

1. **Plasma shell** — `AuraDark.colors` / `AuraLight.colors` are the canonical KDE
   color-schemes. They should be synced to
   `aiquick-os/branding/aura-plasma/color-schemes/` (see Follow-ups — coordinate
   with the shell agent; not copied here to avoid clashing).
2. **Desktop apps** — every app vendors `<pkg>/aura.py`, a byte-identical copy of
   `dist/aura.py`. Apps follow the **system** Dark/Light by default (see below).
3. **Web** — `aura.css` supplies `--aura-*` variables for quickopen.ai + artifacts.

### Apps follow the system theme

`aura.py` defaults to `theme="system"`: `apply()` and `AuraApp` resolve the mode
from the OS via `darkdetect` (which reads the GNOME `color-scheme` gsettings key /
`org.freedesktop.appearance` portal on Linux, the registry on Windows, the
defaults domain on macOS), with a direct `gsettings` probe as fallback and a safe
`dark` default. An explicit `"light"`/`"dark"` (an app's persisted user choice)
overrides. `AuraApp` also starts a best-effort `darkdetect` listener so an open
window re-themes live when the user flips the OS scheme; a manual in-app toggle
becomes an explicit override and stops following.

### New apps are Aura-coherent automatically

`publish/scripts/scaffold-app.py` seeds every newly scaffolded app with the
canonical `dist/aura.py` (copied to `<pkg>/aura.py`), adds the Aura runtime deps
(`customtkinter`, `darkdetect`) to `requirements.txt`, and writes a `gui.py` stub
that builds an `AuraApp` defaulting to `theme="system"`. **Re-run `generate.py` to
refresh what future scaffolds receive** — the scaffolder always copies the current
`dist/aura.py`.

## 4. Palettes

Swatch reference (open `dist/aura-swatches.html` for the visual version):

| Token | Dark | Light |
|-------|------|-------|
| `bg` | `#0f1115` | `#f5f7fb` |
| `bg2` | `#14171c` | `#eef1f6` |
| `surface` | `#1a1e24` | `#ffffff` |
| `surface2` | `#222731` | `#f3f5f9` |
| `surface3` | `#2a3039` | `#e8ecf3` |
| `border` | `#2b313b` | `#d3d9e6` |
| `border2` | `#3a424f` | `#c8d0dc` |
| `text` | `#f1f3f7` | `#1a2130` |
| `muted` | `#9aa4b2` | `#5b657a` |
| `faint` | `#6f7a89` | `#808b9b` |
| `field` | `#14171c` | `#ffffff` |
| `accent` | `#5b86f7` | `#5b86f7` |
| `on-accent` | `#ffffff` | `#ffffff` |
| `ok` | `#37c56f` | `#17914b` |
| `warn` | `#f0b429` | `#b0700a` |
| `danger` | `#e5484d` | `#cf2d3a` |

Brand / semantic (mode-independent): `accent #5b86f7`, `accent-strong #3a5fd0`,
`accent-edge #7d93d6`, `beam #5b86f7`, `info #5b86f7`.

## Files

```
branding/aura-design-system/
├── aura-tokens.json     source of truth (v1.0.0)
├── aura.template.py     aura.py logic with palette/accent punched out as markers
├── generate.py          the generator (idempotent)
├── README.md            this file
└── dist/                generated — do not edit by hand
    ├── aura.py
    ├── AuraDark.colors
    ├── AuraLight.colors
    ├── aura.css
    └── aura-swatches.html
```

## Follow-ups

- **Plasma sync**: copy `dist/AuraDark.colors` / `dist/AuraLight.colors` to
  `aiquick-os/branding/aura-plasma/color-schemes/` — coordinate with the shell
  agent (that tree is theirs; the OS side wires `org.freedesktop.appearance` +
  the GNOME `color-scheme` gsettings key that `darkdetect` reads).
- **Web wiring**: include `dist/aura.css` in quickopen.ai + the artifact template
  and switch hardcoded colors to the `--aura-*` variables.
- **App default follow**: `aura.py` follows the OS whenever an app passes
  `"system"`/`None`. Apps currently pass a persisted concrete theme via
  `<config>.get_theme()`; to make a *fresh* install follow the OS, have that
  return `"system"` when unset (a small per-app config change — `aiquick-security`,
  `fire-guard`, and `plain-text-editor` have tests asserting the old hardcoded
  default that would then update).
```

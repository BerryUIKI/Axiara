"""i18n_svg.py — regenerate localized diagram SVGs for all Axiara locales.

Usage (from repo root):
    python docs/dev/i18n_svg.py            # regenerate all locales from EN sources
    python docs/dev/i18n_svg.py --locale de-DE   # only one locale
    python docs/dev/i18n_svg.py --extract  # re-extract dicts from committed SVGs

How it works:
- EN light SVGs (assets/axiara-{kind}.svg) are the sources of truth.
- docs/dev/i18n_dicts.py holds per-locale string maps (single source of
  truth for translations; re-generate with --extract after hand-fixing files).
- For each locale x kind: regex-replace <text>…</text> bodies in the EN svg
  via the dict, then ET-round-trip to match the committed SVG byte format.
  The dark twin is derived via the VI palette map.
- Files are written with LF line endings (repo convention, core.autocrlf=input).
- zh-CN (-zh) is a hand-written baseline (Chinese <title>/<desc>, distinct
  format) and is NOT managed by this generator.

When translations change: edit docs/dev/i18n_dicts.py, then run
`python docs/dev/i18n_svg.py` to regenerate all locale SVGs.
"""
import io
import os
import re
import sys
import argparse
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # same dir as i18n_dicts.py
import i18n_dicts  # noqa: E402

# zh-CN (-zh) is a hand-written baseline; the generator manages the 8
# locales derived from EN sources.
LOCALES = ["zh-TW", "ja-JP", "ko-KR", "de-DE", "es-ES", "fr-FR", "pt-BR", "ru-RU"]
KINDS = ["architecture", "modes", "setup-decision"]

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)  # so tostring() emits the same format as committed SVGs

# VI palette light -> dark (see docs/developer/VI-GUIDE.md §2)
DARK_MAP = {
    "#E1F5EE": "#04342C", "#1D9E75": "#5DCAA5", "#04342C": "#E1F5EE", "#0F6E56": "#9FE1CB",
    "#EAF3DE": "#173404", "#639922": "#97C459", "#27500A": "#C0DD97", "#3B6D11": "#97C459",
    "#F6F9EE": "#0E2402", "#A8C97E": "#618D3A", "#EEEDFE": "#26215C", "#7F77DD": "#AFA9EC",
    "#3C3489": "#CECBF6", "#534AB7": "#AFA9EC", "#F7F6FE": "#1C1848", "#B3ADEB": "#7A71C9",
    "#FAEEDA": "#412402", "#BA7517": "#EF9F27", "#633806": "#FAC775", "#854F0B": "#EF9F27",
    "#FDF6EA": "#2F1B02", "#D6A96B": "#B97B2A", "#EFFAF6": "#04241C", "#6EC6A6": "#3E9C7D",
    "#888780": "#9E9D98",
}

_TEXT_RE = re.compile(r"(<text[^>]*>)([^<]*)(</text>)")


def _write(path, content):
    """Write with LF line endings (repo convention)."""
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _normalize(xml_str):
    """ET round-trip to match the committed SVG byte format (xmlns prefix,
    self-closing tags, attr order) so regeneration produces zero format churn."""
    return ET.tostring(ET.fromstring(xml_str), encoding="unicode")


def to_dark(src, dst):
    c = io.open(src, encoding="utf-8").read()
    ph = {}
    for i, (l, d) in enumerate(DARK_MAP.items()):
        tok = f"__D{i}__"
        c = c.replace(l, tok)
        ph[tok] = d
    for tok, d in ph.items():
        c = c.replace(tok, d)
    _write(dst, c)


def localize(kind, loc, trans):
    """Replace <text> bodies (literal dict keys), then normalize formatting."""
    path = os.path.join(BASE, "assets", f"axiara-{kind}.svg")
    src = io.open(path, encoding="utf-8").read()

    def repl(m):
        return m.group(1) + trans.get(m.group(2), m.group(2)) + m.group(3)

    localized, n = _TEXT_RE.subn(repl, src)
    out = _normalize(localized)
    light = os.path.join(BASE, "assets", f"axiara-{kind}-{loc}.svg")
    _write(light, out)
    to_dark(light, light.replace(".svg", "-dark.svg"))
    return n


def extract_dicts():
    """Re-derive i18n_dicts.py from the committed localized SVGs."""
    def bodies(f):
        return [m.group(2) for m in _TEXT_RE.finditer(io.open(f, encoding="utf-8").read())]

    out = ["# Auto-extracted translation dicts. Regenerate via:",
           "#   python scripts/dev/i18n_svg.py --extract",
           "TRANSLATIONS = {"]
    for loc in LOCALES:
        out.append(f"    {loc!r}: {{")
        for kind in KINDS:
            en = bodies(os.path.join(BASE, "assets", f"axiara-{kind}.svg"))
            tr = bodies(os.path.join(BASE, "assets", f"axiara-{kind}-{loc}.svg"))
            pairs = {e: t for e, t in zip(en, tr) if e and t and e != t}
            out.append(f"        # {kind}")
            for k, v in sorted(pairs.items()):
                out.append(f"        {k!r}: {v!r},")
        out.append("    },")
    out.append("}")
    dst = os.path.join(BASE, "scripts", "dev", "i18n_dicts.py")
    _write(dst, "\n".join(out) + "\n")
    print("i18n_dicts.py re-extracted")


def main():
    ap = argparse.ArgumentParser(description="Regenerate localized Axiara diagram SVGs")
    ap.add_argument("--locale", help="only regenerate this locale (default: all)")
    ap.add_argument("--extract", action="store_true", help="re-extract dicts from committed SVGs, then exit")
    args = ap.parse_args()

    if args.extract:
        extract_dicts()
        return

    locales = [args.locale] if args.locale else LOCALES
    for loc in locales:
        if loc not in i18n_dicts.TRANSLATIONS:
            print(f"!! unknown locale {loc}; have {list(i18n_dicts.TRANSLATIONS)}")
            continue
        for kind in KINDS:
            n = localize(kind, loc, i18n_dicts.TRANSLATIONS[loc])
            print(f"  {kind}-{loc}: {n} strings localized + dark generated")
    print("done.")


if __name__ == "__main__":
    main()

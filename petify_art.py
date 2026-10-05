"""
petify_art.py — original flat illustrations for the PetsAIHealth redesign.

Every drawing here is made from simple shapes for this project (no third-party
artwork, no known characters). Palette follows petify_ui: royal blue, orange,
lavender, peach. Pure string builders, no Streamlit import.
"""
from __future__ import annotations

BLUE, BLUE2, ORANGE = "#1237C9", "#2F55F0", "#FF6B2C"
INK, LAV, LAV2 = "#0B1B4B", "#E7EAFB", "#C9D0F5"
PEACH, CREAM, WHITE = "#FFDCC7", "#FFF1E8", "#FFFFFF"
FUR, FUR2, FUR3 = "#E9A56B", "#C97C3F", "#F6D3AE"      # warm dog fur
GREY, GREY2 = "#B8C0DA", "#8F99BC"                       # cool cat fur


def _svg(vb: str, body: str, cls: str = "", label: str = "") -> str:
    return (f'<svg class="pn-art {cls}" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{label}" preserveAspectRatio="xMidYMid slice" style="display:block;width:100%;height:100%">{body}</svg>')


# ── small parts ──────────────────────────────────────────────────────────────
def _dog_head(x, y, s=1.0, sleepy=False) -> str:
    eyes = (f'<path d="M-26 -4q8 7 16 0M10 -4q8 7 16 0" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>'
            if sleepy else
            f'<circle cx="-18" cy="-4" r="6" fill="{INK}"/><circle cx="18" cy="-4" r="6" fill="{INK}"/>'
            f'<circle cx="-16" cy="-6" r="2" fill="#fff"/><circle cx="20" cy="-6" r="2" fill="#fff"/>')
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M-50 -30c-22 -4 -30 26 -22 52c6 -6 14 -12 22 -16z" fill="{FUR2}"/>'
            f'<path d="M50 -30c22 -4 30 26 22 52c-6 -6 -14 -12 -22 -16z" fill="{FUR2}"/>'
            f'<ellipse cx="0" cy="0" rx="52" ry="48" fill="{FUR}"/>'
            f'<ellipse cx="0" cy="22" rx="30" ry="22" fill="{FUR3}"/>'
            f'{eyes}<ellipse cx="0" cy="12" rx="10" ry="7" fill="{INK}"/>'
            f'<path d="M0 19v8M-8 30q8 7 16 0" stroke="{INK}" stroke-width="3.5" fill="none" stroke-linecap="round"/></g>')


def _cat_head(x, y, s=1.0, sleepy=False) -> str:
    eyes = (f'<path d="M-24 0q8 7 16 0M8 0q8 7 16 0" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round"/>'
            if sleepy else
            f'<ellipse cx="-17" cy="0" rx="6.5" ry="8" fill="{INK}"/><ellipse cx="17" cy="0" rx="6.5" ry="8" fill="{INK}"/>'
            f'<circle cx="-15" cy="-3" r="2.3" fill="#fff"/><circle cx="19" cy="-3" r="2.3" fill="#fff"/>')
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M-48 -18l6 -44l36 24z" fill="{GREY2}"/><path d="M48 -18l-6 -44l-36 24z" fill="{GREY2}"/>'
            f'<path d="M-40 -26l3 -22l17 11z" fill="{PEACH}"/><path d="M40 -26l-3 -22l-17 11z" fill="{PEACH}"/>'
            f'<ellipse cx="0" cy="0" rx="52" ry="44" fill="{GREY}"/>'
            f'<path d="M-6 -42h12l-3 14h-6z" fill="{GREY2}"/>'
            f'{eyes}<path d="M-5 12h10l-5 7z" fill="{ORANGE}"/>'
            f'<path d="M0 19q-1 8 -9 8M0 19q1 8 9 8" stroke="{INK}" stroke-width="3" fill="none" stroke-linecap="round"/>'
            f'<path d="M-52 10l-22 -4M-52 18l-22 6M52 10l22 -4M52 18l22 6" stroke="{INK}" stroke-width="2" stroke-linecap="round" opacity=".55"/></g>')


def _bunny_head(x, y, s=1.0) -> str:
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<ellipse cx="-22" cy="-52" rx="13" ry="38" fill="#EDEFF9" transform="rotate(-8 -22 -52)"/>'
            f'<ellipse cx="22" cy="-52" rx="13" ry="38" fill="#EDEFF9" transform="rotate(8 22 -52)"/>'
            f'<ellipse cx="-22" cy="-50" rx="6" ry="27" fill="{PEACH}" transform="rotate(-8 -22 -50)"/>'
            f'<ellipse cx="22" cy="-50" rx="6" ry="27" fill="{PEACH}" transform="rotate(8 22 -50)"/>'
            f'<ellipse cx="0" cy="0" rx="46" ry="40" fill="#F6F7FD"/>'
            f'<circle cx="-16" cy="-2" r="5.5" fill="{INK}"/><circle cx="16" cy="-2" r="5.5" fill="{INK}"/>'
            f'<circle cx="-14.5" cy="-4" r="1.8" fill="#fff"/><circle cx="17.5" cy="-4" r="1.8" fill="#fff"/>'
            f'<path d="M-5 10h10l-5 6z" fill="{ORANGE}"/>'
            f'<path d="M0 16v6M-7 24q7 6 14 0" stroke="{INK}" stroke-width="3" fill="none" stroke-linecap="round"/></g>')


def _heart(x, y, s=1.0, fill=ORANGE) -> str:
    return (f'<path transform="translate({x} {y}) scale({s})" d="M0 14C-26 -4 -22 -26 -8 -26c6 0 8 3 8 6c0 -3 2 -6 8 -6c14 0 18 22 -8 40z" fill="{fill}"/>')


def _sparkle(x, y, s=1.0, fill="#fff") -> str:
    return (f'<path transform="translate({x} {y}) scale({s})" d="M0 -12q1.5 10.5 12 12q-10.5 1.5 -12 12q-1.5 -10.5 -12 -12q10.5 -1.5 12 -12z" fill="{fill}"/>')


def _paw(x, y, s=1.0, fill=ORANGE) -> str:
    return (f'<g transform="translate({x} {y}) scale({s})" fill="{fill}"><ellipse cx="0" cy="8" rx="11" ry="9"/>'
            f'<ellipse cx="-13" cy="-6" rx="5" ry="6.5"/><ellipse cx="-4.5" cy="-13" rx="5" ry="6.5"/>'
            f'<ellipse cx="4.5" cy="-13" rx="5" ry="6.5"/><ellipse cx="13" cy="-6" rx="5" ry="6.5"/></g>')


def _bg(c1: str, c2: str, id_: str) -> str:
    return (f'<defs><linearGradient id="{id_}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/>'
            f'<stop offset="1" stop-color="{c2}"/></linearGradient></defs><rect width="400" height="220" fill="url(#{id_})"/>')


def _blobs(c: str = "#ffffff", o: float = .35) -> str:
    return (f'<circle cx="352" cy="26" r="70" fill="{c}" opacity="{o*.6}"/><circle cx="26" cy="206" r="58" fill="{c}" opacity="{o*.5}"/>'
            f'<circle cx="300" cy="190" r="34" fill="{c}" opacity="{o*.4}"/>')


# ── scenes (400 x 220) ───────────────────────────────────────────────────────
def scene(kind: str, species: str = "dog") -> str:
    head = {"dog": _dog_head, "cat": _cat_head}.get(species)
    if kind == "symptoms":
        pet = (head or _dog_head)(150, 128, 1.15)
        body = (_bg(LAV, LAV2, "gs") + _blobs()
                + f'<path d="M92 214c10 -34 38 -44 58 -44s48 10 58 44z" fill="{BLUE}"/>'
                + pet
                + f'<g transform="translate(262 40)"><rect width="116" height="74" rx="22" fill="#fff"/><path d="M26 74l-8 22l30 -22z" fill="#fff"/>'
                  f'<text x="58" y="52" text-anchor="middle" font-family="Sora,Inter,sans-serif" font-weight="800" font-size="46" fill="{BLUE}">?</text></g>'
                + f'<g transform="translate(300 142)"><rect width="22" height="64" rx="11" fill="#fff" stroke="{INK}" stroke-width="3"/>'
                  f'<circle cx="11" cy="64" r="15" fill="{ORANGE}" stroke="{INK}" stroke-width="3"/><rect x="7" y="24" width="8" height="40" rx="4" fill="{ORANGE}"/>'
                  f'<path d="M24 14h10M24 28h10M24 42h10" stroke="{INK}" stroke-width="3" stroke-linecap="round"/></g>'
                + _sparkle(60, 50, 1.2, "#fff") + _sparkle(364, 168, .9, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-symptoms", "symptoms")
    if kind == "photo":
        face = _cat_head(200, 118, 1.05)
        corners = "".join(f'<path d="{p}" stroke="{ORANGE}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                          for p in ("M96 54v-24h24", "M304 54v-24h-24", "M96 186v24h24", "M304 186v24h-24"))
        body = (_bg("#FFE9DC", PEACH, "gp") + _blobs("#fff", .5)
                + f'<rect x="96" y="30" width="208" height="180" rx="26" fill="{LAV}" opacity=".9"/>' + face + corners
                + f'<g transform="translate(318 56)"><rect width="56" height="40" rx="12" fill="{BLUE}"/><circle cx="28" cy="20" r="11" fill="#fff"/><circle cx="28" cy="20" r="6" fill="{BLUE}"/>'
                  f'<rect x="38" y="-6" width="14" height="8" rx="3" fill="{BLUE}"/></g>'
                + _sparkle(70, 70, 1.3, ORANGE) + _sparkle(340, 168, 1.0, BLUE))
        return _svg("0 0 400 220", body, "pn-art-photo", "photo")
    if kind == "breath":
        sleep_head = (head or _dog_head)(112, 128, .78, True)
        wave = "M20 150q18 -22 36 0t36 0t36 0t36 0"
        body = (_bg(BLUE2, "#0E2A9E", "gb")
                + f'<circle cx="330" cy="30" r="80" fill="#fff" opacity=".07"/><circle cx="20" cy="210" r="70" fill="#fff" opacity=".06"/>'
                + f'<ellipse cx="210" cy="168" rx="120" ry="36" fill="{FUR}"/><ellipse cx="270" cy="150" rx="60" ry="28" fill="{FUR2}" opacity=".55"/>'
                + sleep_head
                + f'<path d="M318 152q38 -4 48 -34" stroke="{FUR}" stroke-width="14" fill="none" stroke-linecap="round"/>'
                + f'<path d="M20 206h360" stroke="#fff" stroke-opacity=".18" stroke-width="3"/>'
                + f'<g fill="#fff" font-family="Sora,Inter,sans-serif" font-weight="800"><text x="170" y="74" font-size="30" opacity=".95">z</text>'
                  f'<text x="196" y="52" font-size="24" opacity=".75">z</text><text x="216" y="34" font-size="18" opacity=".55">z</text></g>'
                + f'<g transform="translate(282 46)"><rect width="84" height="132" rx="16" fill="#101322"/><rect x="6" y="8" width="72" height="116" rx="11" fill="#1B2D8F"/>'
                  f'<circle cx="42" cy="46" r="20" fill="none" stroke="{ORANGE}" stroke-width="4" stroke-dasharray="78 50" stroke-linecap="round"/>'
                  f'<text x="42" y="53" text-anchor="middle" fill="#fff" font-family="Sora,Inter,sans-serif" font-weight="800" font-size="19">22</text>'
                  f'<path d="M12 98q8 -14 15 0t15 0t15 0t15 0" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" opacity=".9"/>'
                  f'<text x="42" y="116" text-anchor="middle" fill="#B9C4FF" font-family="Inter,sans-serif" font-size="8.5" font-weight="700">/min</text></g>'
                + f'<path d="{wave}" transform="translate(0 -58)" stroke="{ORANGE}" stroke-width="5" fill="none" stroke-linecap="round" opacity=".0"/>'
                + _sparkle(40, 50, 1.1, "#fff") + _sparkle(250, 18, .8, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-breath", "breathing scan")
    if kind == "longevity":
        body = (_bg("#FFE9DC", "#FFD2B8", "gl") + _blobs("#fff", .5)
                + f'<rect x="40" y="152" width="136" height="68" rx="16" fill="{BLUE}"/><rect x="224" y="130" width="136" height="90" rx="16" fill="{BLUE2}"/>'
                + _dog_head(108, 108, .82) + _cat_head(292, 86, .82)
                + f'<text x="108" y="196" text-anchor="middle" fill="#fff" font-family="Sora,Inter,sans-serif" font-weight="800" font-size="26">6 → 45</text>'
                  f'<text x="292" y="182" text-anchor="middle" fill="#fff" font-family="Sora,Inter,sans-serif" font-weight="800" font-size="26">3 → 28</text>'
                  f'<text x="108" y="210" text-anchor="middle" fill="#C9D0F5" font-family="Inter,sans-serif" font-weight="700" font-size="9" letter-spacing="1.2">HUMAN YEARS</text>'
                  f'<text x="292" y="200" text-anchor="middle" fill="#C9D0F5" font-family="Inter,sans-serif" font-weight="700" font-size="9" letter-spacing="1.2">HUMAN YEARS</text>'
                + _heart(200, 54, 1.0) + _sparkle(176, 34, .8, BLUE) + _sparkle(236, 78, .7, "#fff") + _sparkle(40, 40, 1.1, BLUE))
        return _svg("0 0 400 220", body, "pn-art-longevity", "longevity")
    if kind == "vitals":
        body = (_bg(LAV, LAV2, "gv") + _blobs()
                + f'<rect x="60" y="40" width="280" height="140" rx="26" fill="#fff"/>'
                + _heart(118, 108, 1.5)
                + f'<path d="M160 118h30l12 -34l22 66l16 -44l12 12h48" stroke="{BLUE}" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                + f'<g transform="translate(322 24)"><path d="M18 0c10 14 18 22 18 32a18 18 0 1 1 -36 0c0 -10 8 -18 18 -32z" fill="{ORANGE}"/></g>'
                + _sparkle(48, 190, 1.0, BLUE) + _sparkle(372, 190, .9, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-vitals", "vitals")
    if kind == "report":
        body = (_bg("#EEF1FD", LAV2, "gr") + _blobs()
                + f'<g transform="rotate(-6 200 110)"><rect x="120" y="24" width="160" height="186" rx="18" fill="#fff"/>'
                  f'<rect x="164" y="14" width="72" height="22" rx="9" fill="{BLUE}"/>'
                  + "".join(f'<rect x="144" y="{62 + i*26}" width="{112 - (i%2)*28}" height="9" rx="4.5" fill="{LAV2}"/>' for i in range(5))
                + f'<g transform="translate(236 168)"><circle r="24" fill="{ORANGE}"/>{_paw(0, 2, .8, "#fff")}</g></g>'
                + _sparkle(70, 50, 1.1, BLUE) + _sparkle(336, 70, .9, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-report", "report")
    if kind == "nurse":
        pet = (head or _dog_head)(142, 124, 1.2)
        body = (_bg(BLUE2, "#0E2A9E", "gn")
                + '<circle cx="340" cy="30" r="84" fill="#fff" opacity=".07"/><circle cx="24" cy="206" r="64" fill="#fff" opacity=".06"/>'
                + f'<path d="M70 216c8 -38 40 -50 72 -50s64 12 72 50z" fill="#fff"/>'
                + f'<path d="M104 168c-6 34 8 48 24 48M180 168c6 34 -8 48 -24 48" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/>'
                + f'<circle cx="142" cy="206" r="9" fill="{ORANGE}" stroke="{INK}" stroke-width="3"/>'
                + pet
                + f'<g transform="translate(236 34)"><rect width="140" height="86" rx="24" fill="#fff"/><path d="M34 86l-12 26l38 -26z" fill="#fff"/>'
                  f'<rect x="22" y="22" width="96" height="10" rx="5" fill="{LAV2}"/><rect x="22" y="42" width="70" height="10" rx="5" fill="{LAV2}"/>'
                  f'<rect x="22" y="62" width="40" height="10" rx="5" fill="{ORANGE}"/></g>'
                + f'<g transform="translate(300 150)"><circle r="30" fill="{ORANGE}"/><rect x="-5" y="-17" width="10" height="34" rx="3" fill="#fff"/><rect x="-17" y="-5" width="34" height="10" rx="3" fill="#fff"/></g>'
                + _sparkle(40, 44, 1.2, "#fff") + _sparkle(372, 130, .9, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-nurse", "AI vet nurse")
    if kind == "labs":
        tube = lambda x, c: (f'<g transform="translate({x} 40)"><rect width="34" height="120" rx="17" fill="#fff" stroke="{INK}" stroke-width="3"/>'
                             f'<rect x="3" y="58" width="28" height="59" rx="14" fill="{c}"/><rect x="-4" y="-6" width="42" height="14" rx="7" fill="{BLUE}"/></g>')
        body = (_bg(LAV, LAV2, "gla") + _blobs() + tube(100, ORANGE) + tube(150, BLUE2) + tube(200, "#7BD3A5")
                + f'<g transform="translate(262 46)"><rect width="104" height="130" rx="16" fill="#fff"/>'
                  f'<path d="M16 100l18 -22l16 12l22 -34" stroke="{BLUE}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                  f'<rect x="16" y="20" width="60" height="8" rx="4" fill="{LAV2}"/><rect x="16" y="36" width="40" height="8" rx="4" fill="{LAV2}"/></g>'
                + _sparkle(60, 188, 1.0, BLUE) + _sparkle(380, 36, .9, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-labs", "lab results")
    if kind == "diary":
        days = "".join(f'<rect x="{18 + (i%5)*34}" y="{62 + (i//5)*30}" width="26" height="22" rx="7" fill="{(ORANGE if i in (3, 8) else LAV)}"/>' for i in range(15))
        body = (_bg("#FFF1E8", PEACH, "gd") + _blobs("#fff", .5)
                + f'<g transform="translate(110 28)"><rect width="190" height="164" rx="22" fill="#fff"/><rect width="190" height="40" rx="22" fill="{BLUE}"/>'
                  f'<rect y="24" width="190" height="16" fill="{BLUE}"/>{days}'
                  f'<circle cx="40" cy="20" r="6" fill="#fff"/><circle cx="150" cy="20" r="6" fill="#fff"/></g>'
                + _paw(332, 160, 1.2, BLUE) + _sparkle(62, 54, 1.2, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-diary", "symptom diary")
    if kind == "vets":
        body = (_bg("#E3F0FF", "#BFD7FF", "gm") + _blobs()
                + f'<path d="M0 150q80 -50 160 -10t160 -40t80 20v100H0z" fill="#fff" opacity=".55"/>'
                + f'<path d="M-10 120l120 -50l110 40l190 -70" stroke="#fff" stroke-width="14" fill="none" stroke-linecap="round"/>'
                + f'<path d="M-10 120l120 -50l110 40l190 -70" stroke="{LAV2}" stroke-width="3" fill="none" stroke-dasharray="10 10"/>'
                + f'<g transform="translate(200 54)"><path d="M0 0c-34 0 -52 26 -52 52c0 36 52 80 52 80s52 -44 52 -80c0 -26 -18 -52 -52 -52z" fill="{ORANGE}"/>'
                  f'<circle cy="50" r="26" fill="#fff"/><rect x="-5" y="34" width="10" height="32" rx="3" fill="{ORANGE}"/><rect x="-16" y="45" width="32" height="10" rx="3" fill="{ORANGE}"/></g>'
                + f'<ellipse cx="200" cy="196" rx="44" ry="9" fill="{INK}" opacity=".15"/>' + _sparkle(70, 50, 1.1, BLUE) + _sparkle(350, 160, 1.0, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-vets", "find a vet")
    if kind == "shield":
        body = (_bg(LAV, LAV2, "gsh") + _blobs()
                + f'<path d="M200 28l92 34v62c0 40 -38 70 -92 90c-54 -20 -92 -50 -92 -90V62z" fill="{BLUE}"/>'
                + f'<path d="M200 46l74 28v50c0 30 -30 54 -74 72c-44 -18 -74 -42 -74 -72V74z" fill="{BLUE2}"/>'
                + _paw(200, 112, 1.9, "#fff") + _heart(262, 52, .9) + _sparkle(98, 50, 1.2, ORANGE) + _sparkle(318, 166, 1.0, BLUE))
        return _svg("0 0 400 220", body, "pn-art-shield", "insurance")
    if kind == "pets":
        body = (_bg("#FFE9DC", PEACH, "gpt") + _blobs("#fff", .5)
                + f'<rect x="36" y="120" width="104" height="100" rx="52" fill="{BLUE}"/><rect x="148" y="104" width="104" height="116" rx="52" fill="{BLUE2}"/><rect x="260" y="120" width="104" height="100" rx="52" fill="{ORANGE}"/>'
                + _dog_head(88, 104, .78) + _cat_head(200, 90, .78) + _bunny_head(312, 118, .66)
                + _heart(200, 28, .8) + _sparkle(40, 46, 1.2, BLUE) + _sparkle(364, 52, 1.0, ORANGE))
        return _svg("0 0 400 220", body, "pn-art-pets", "your pet")
    if kind == "measure":
        ticks = "".join(f'<path d="M{70 + i*20} 150v{14 if i%2 else 22}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>' for i in range(14))
        body = (_bg(LAV, LAV2, "gme") + _blobs()
                + f'<rect x="56" y="138" width="288" height="52" rx="14" fill="#fff"/>{ticks}'
                + f'<g transform="translate(200 76)"><rect x="-62" y="-14" width="124" height="70" rx="18" fill="{BLUE}"/><circle cy="20" r="24" fill="#fff"/>'
                  f'<path d="M0 20l10 -12" stroke="{ORANGE}" stroke-width="5" stroke-linecap="round"/><circle cy="20" r="4" fill="{INK}"/></g>'
                + _paw(332, 70, 1.2, ORANGE) + _sparkle(60, 56, 1.2, BLUE))
        return _svg("0 0 400 220", body, "pn-art-measure", "measurements")
    if kind == "meds":
        body = (_bg("#EAF8F1", "#BFE9D4", "gmd") + _blobs()
                + f'<g transform="translate(120 36)"><rect width="96" height="140" rx="20" fill="#fff" stroke="{INK}" stroke-width="3"/><rect x="-6" y="-12" width="108" height="34" rx="12" fill="{BLUE}"/>'
                  f'<rect x="16" y="52" width="64" height="52" rx="10" fill="{LAV}"/><rect x="42" y="58" width="12" height="40" rx="3" fill="{ORANGE}"/><rect x="28" y="72" width="40" height="12" rx="3" fill="{ORANGE}"/></g>'
                + f'<g transform="translate(262 120) rotate(-28)"><rect width="76" height="30" rx="15" fill="{ORANGE}"/><path d="M38 0h23a15 15 0 0 1 0 30H38z" fill="#fff"/></g>'
                + f'<circle cx="300" cy="64" r="16" fill="#fff"/><circle cx="268" cy="176" r="11" fill="{BLUE2}"/>' + _sparkle(64, 54, 1.2, ORANGE) + _sparkle(356, 170, 1.0, BLUE))
        return _svg("0 0 400 220", body, "pn-art-meds", "medications")
    if kind == "emergency":
        body = (_bg("#FFE3E3", "#FFC7C7", "ge") + _blobs()
                + f'<circle cx="200" cy="110" r="68" fill="#fff"/><rect x="188" y="66" width="24" height="88" rx="8" fill="#DC2626"/><rect x="156" y="98" width="88" height="24" rx="8" fill="#DC2626"/>')
        return _svg("0 0 400 220", body, "pn-art-emergency", "emergency")
    return _svg("0 0 400 220", _bg(LAV, LAV2, "gx"), "pn-art-blank")


def species_face(species: str, size: int = 64) -> str:
    """Round avatar with the species drawn in — used where a photo is not available."""
    fn = {"dog": _dog_head, "cat": _cat_head, "rabbit": _bunny_head}.get(species, _dog_head)
    sc = {"dog": .78, "cat": .78, "rabbit": .62}.get(species, .78)
    cy = {"rabbit": 78, "cat": 62}.get(species, 56)
    svg = (f'<svg viewBox="-60 -20 120 120" xmlns="http://www.w3.org/2000/svg" style="width:{size}px;height:{size}px;display:block">'
           f'<circle cx="0" cy="40" r="60" fill="{PEACH}"/>' + fn(0, cy - 10, sc) + '</svg>')
    return svg


# ── pillar icons (24 x 24, stroke style) ─────────────────────────────────────
_ICON = {
    "bcs": '<path d="M5 20h14M7 20l1.6-9h6.8L17 20M9 11a3 3 0 0 1 6 0"/>',
    "dental": '<path d="M7 4c-2.5 0-3.5 2.4-3 5c.4 2.2 1.4 3.6 1.8 6c.3 2 .8 5 2.2 5c1.6 0 1.3-3.4 2-5c.3-.7 1.2-.7 1.5 0c.7 1.6.4 5 2 5c1.4 0 1.9-3 2.2-5c.4-2.4 1.4-3.8 1.8-6c.5-2.6-.5-5-3-5c-1.6 0-2.2 1-5 1S8.6 4 7 4z"/>',
    "activity": '<circle cx="14.5" cy="4.5" r="2"/><path d="M6 20l3-6l3 2l2-5l-2.5-2L8 11M12 16l1 4M14 11l3 2l3-1"/>',
    "prevention": '<path d="M12 3l7 3v6c0 4.5-3 7.6-7 9c-4-1.4-7-4.5-7-9V6z"/><path d="M9 12l2 2l4-4"/>',
    "srr": '<path d="M12 4v8M12 12c-2 0-4 1-5 3c-1 2-2 4-.5 5c1.5 1 3.5-1 4.5-3.5M12 12c2 0 4 1 5 3c1 2 2 4 .5 5c-1.500 1-3.5-1-4.5-3.5"/>',
    "hr": '<path d="M12 20C5 15 3 11 3 8.200C3 5.800 4.800 4 7 4c2 0 3.500 1 5 3c1.500-2 3-3 5-3c2.200 0 4 1.800 4 4.200C21 11 19 15 12 20z"/>',
}


def pillar_icon(pid: str, color: str = BLUE) -> str:
    p = _ICON.get(pid, _ICON["prevention"])
    return (f'<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="{color}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">{p}</svg>')

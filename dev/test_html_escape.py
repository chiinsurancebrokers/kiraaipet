"""Guards the owner-typed values that reach unsafe_allow_html: they must be escaped."""
import re, sys
s = open("app.py", encoding="utf-8").read()
bad = []
for pat in (r'\{p\["name"\]\}', r'\{p\.get\("breed",""\)\}', r'\{p\.get\("age",""\)\}',
            r"\{email or '[^']*'\}"):
    for m in re.finditer(pat, s):
        bad.append((s.count("\n", 0, m.start()) + 1, m.group(0)))
if bad:
    print("unescaped owner text in HTML:", bad); sys.exit(1)
print("html escape guard: ok")

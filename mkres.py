"""Generate rsrc_windows_amd64.syso (COFF .rsrc with icon + manifest) and app.ico."""
import io, struct, sys
from PIL import Image, ImageDraw

def ball(size):
    S = size * 4
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = S * 0.04
    d.ellipse([pad, pad, S - pad, S - pad], fill=(28, 35, 45, 255))
    rw = S * 0.09
    d.ellipse([pad + rw * 0.5, pad + rw * 0.5, S - pad - rw * 0.5, S - pad - rw * 0.5], outline=(46, 204, 113, 255), width=int(rw))
    # simple globe: meridian + equator
    c = S / 2; r = S * 0.24; lw = max(1, int(S * 0.045))
    d.ellipse([c - r, c - r, c + r, c + r], outline=(235, 240, 245, 255), width=lw)
    d.ellipse([c - r * 0.45, c - r, c + r * 0.45, c + r], outline=(235, 240, 245, 255), width=lw)
    d.line([c - r, c, c + r, c], fill=(235, 240, 245, 255), width=lw)
    return im.resize((size, size), Image.LANCZOS)

sizes = [16, 24, 32, 48, 64, 256]
imgs = []
for s in sizes:
    b = io.BytesIO(); ball(s).save(b, "PNG"); imgs.append(b.getvalue())
ball(256).save(sys.argv[2], sizes=[(s, s) for s in sizes])

manifest = b'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="1.0.0.0" processorArchitecture="amd64" name="NetGateShow" type="win32"/>
  <dependency><dependentAssembly>
    <assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls" version="6.0.0.0" processorArchitecture="*" publicKeyToken="6595b64144ccf1df" language="*"/>
  </dependentAssembly></dependency>
  <application xmlns="urn:schemas-microsoft-com:asm.v3"><windowsSettings>
    <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
  </windowsSettings></application>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1"><application>
    <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
  </application></compatibility>
</assembly>
'''

grp = struct.pack("<HHH", 0, 1, len(sizes))
for i, (s, data) in enumerate(zip(sizes, imgs)):
    w = 0 if s >= 256 else s
    grp += struct.pack("<BBBBHHIH", w, w, 0, 0, 1, 32, len(data), i + 1)

# resources: type -> [(id, data)]
res = {3: [(i + 1, d) for i, d in enumerate(imgs)], 14: [(1, grp)], 24: [(1, manifest)]}
LANG = 0x0409

# Layout: root dir, type dirs, name dirs (lang level), data entries, data
def dir_size(n): return 16 + 8 * n
types = sorted(res)
off = dir_size(len(types))
type_dir_off = {}
for t in types:
    type_dir_off[t] = off; off += dir_size(len(res[t]))
lang_dir_off = {}
for t in types:
    for rid, _ in res[t]:
        lang_dir_off[(t, rid)] = off; off += dir_size(1)
entry_off = {}
for t in types:
    for rid, _ in res[t]:
        entry_off[(t, rid)] = off; off += 16
data_off = {}
for t in types:
    for rid, d in res[t]:
        off = (off + 7) & ~7
        data_off[(t, rid)] = off; off += len(d)
total = (off + 7) & ~7
buf = bytearray(total)
relocs = []

def put_dir(at, entries):
    struct.pack_into("<IIHHHH", buf, at, 0, 0, 0, 0, 0, len(entries))
    for i, (ident, target, is_dir) in enumerate(entries):
        struct.pack_into("<II", buf, at + 16 + 8 * i, ident, target | (0x80000000 if is_dir else 0))

put_dir(0, [(t, type_dir_off[t], True) for t in types])
for t in types:
    put_dir(type_dir_off[t], [(rid, lang_dir_off[(t, rid)], True) for rid, _ in res[t]])
    for rid, d in res[t]:
        put_dir(lang_dir_off[(t, rid)], [(LANG, entry_off[(t, rid)], False)])
        e = entry_off[(t, rid)]
        struct.pack_into("<IIII", buf, e, data_off[(t, rid)], len(d), 0, 0)
        relocs.append(e)
        buf[data_off[(t, rid)]:data_off[(t, rid)] + len(d)] = d

hdr_size = 20 + 40
raw_ptr = hdr_size
rel_ptr = raw_ptr + total
sym_ptr = rel_ptr + 10 * len(relocs)
out = bytearray()
out += struct.pack("<HHIIIHH", 0x8664, 1, 0, sym_ptr, 1, 0, 0)
out += struct.pack("<8sIIIIIIHHI", b".rsrc", 0, 0, total, raw_ptr, rel_ptr, 0, len(relocs), 0, 0x40000040)
out += buf
for r in relocs:
    out += struct.pack("<IIH", r, 0, 3)  # IMAGE_REL_AMD64_ADDR32NB vs symbol 0
out += struct.pack("<8sIhHBB", b".rsrc", 0, 1, 0, 3, 0)
out += struct.pack("<I", 4)
open(sys.argv[1], "wb").write(out)
print("ok", len(out))

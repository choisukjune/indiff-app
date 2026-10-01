#!/usr/bin/env python3
"""assets/shots/ 에 있는 그림을 index.html 의 figure[data-shot] 자리에 끼운다.

자리는 열 개가 비어 있고(figure:empty 는 접힌다) 지금 채워지는 것은 네 개다. 샷을 늘릴 때
고칠 곳이 한 군데여야 하므로, 이 스크립트는 **파일이 있는 것만** 채운다 — 그림을 떨어뜨리고
shot-alt.json 에 한 줄 더한 뒤 이 스크립트를 돌리면 끝이다.

width/height 를 박아 넣는다(CLS 0). 첫 화면 밖은 lazy, 히어로는 fetchpriority=high.
"""
import json, os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(HERE, "assets", "shots")
ALT = json.load(open(os.path.join(HERE, "tools", "shot-alt.json"), encoding="utf-8"))

TPL = """<picture>
  <source type="image/avif" srcset="assets/shots/{id}.avif 1x, assets/shots/{id}@2x.avif 2x">
  <source type="image/webp" srcset="assets/shots/{id}.webp 1x, assets/shots/{id}@2x.webp 2x">
  <img src="assets/shots/{id}.webp" width="{w}" height="{h}" alt="{alt}"{extra}>
</picture>"""


def main():
    html = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    done, skip = [], []
    for sid in sorted(set(re.findall(r'data-shot="([^"]+)"', html))):
        png = os.path.join(SHOTS, sid + ".webp")
        if not os.path.exists(png):
            skip.append(sid); continue
        if sid not in ALT:
            sys.exit("alt 가 없다: %s — tools/shot-alt.json 에 한 줄 더한다" % sid)
        w, h = Image.open(png).size
        hero = sid == "hero-full"
        pic = TPL.format(id=sid, w=w, h=h, alt=ALT[sid].replace('"', "&quot;"),
                         extra=' fetchpriority="high"' if hero else ' loading="lazy" decoding="async"')
        rx = re.compile(r'(<figure[^>]*data-shot="%s"[^>]*>)(.*?)(</figure>)' % re.escape(sid), re.S)
        if not rx.search(html):
            sys.exit("자리를 못 찾았다: %s" % sid)
        html = rx.sub(lambda m: m.group(1) + "\n" + pic + "\n" + m.group(3), html, count=1)
        done.append("%s %dx%d" % (sid, w, h))
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
    print("끼운 것: " + ", ".join(done))
    print("빈 자리(접힌다): " + ", ".join(skip))


if __name__ == "__main__":
    main()

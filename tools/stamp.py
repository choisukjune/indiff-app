#!/usr/bin/env python3
"""글꼴과 스타일시트 주소에 내용 해시를 박는다.

파일 이름을 그대로 둔 채 내용만 바꾸면 이미 본 브라우저는 옛것을 계속 쓴다
(GitHub Pages 가 max-age=600 을 준다). 그림은 wire-shots.py 가 이미 해시를 박고,
남아 있던 두 자리가 글꼴과 site.css 였다.

순서가 중요하다 — 글꼴 해시를 박으면 site.css 가 바뀌므로, CSS 해시는 **그 뒤에** 낸다.

    python3 tools/stamp.py
"""
import hashlib, io, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ver(rel):
    p = os.path.join(HERE, rel)
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:8]


css_path = os.path.join(HERE, "assets", "site.css")
css = io.open(css_path, encoding="utf-8").read()
fv = ver("assets/pretendard-subset.woff2")
css2 = re.sub(r"url\('pretendard-subset\.woff2(?:\?v=[0-9a-f]+)?'\)",
              "url('pretendard-subset.woff2?v=%s')" % fv, css)
if css2 == css and "pretendard-subset.woff2?v=" not in css:
    sys.exit("site.css 에서 글꼴 주소를 못 찾았다")
if css2 != css:
    io.open(css_path, "w", encoding="utf-8").write(css2)

html_path = os.path.join(HERE, "index.html")
h = io.open(html_path, encoding="utf-8").read()
cv = ver("assets/site.css")
h2 = re.sub(r'href="assets/site\.css(?:\?v=[0-9a-f]+)?"',
            'href="assets/site.css?v=%s"' % cv, h)
if h2 == h and "site.css?v=" not in h:
    sys.exit("index.html 에서 스타일시트 링크를 못 찾았다")
io.open(html_path, "w", encoding="utf-8").write(h2)

print("글꼴 ?v=%s · 스타일시트 ?v=%s" % (fv, cv))

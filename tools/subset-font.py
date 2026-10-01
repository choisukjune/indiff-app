#!/usr/bin/env python3
"""페이지가 실제로 쓰는 글자만 남긴 Pretendard 서브셋을 만든다.

통짜 Pretendard Variable 은 2.0MB 다 — 페이지 전체 예산(1.2MB)을 혼자 넘긴다.
이 페이지의 글자는 몇백 자뿐이라 그것만 남긴다. **카피를 고치면 이 스크립트를 다시 돌린다**
(안 돌리면 새로 쓴 글자가 시스템 글꼴로 떨어져 획이 섞인다).

    python3 tools/subset-font.py
"""
import html, io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.environ.get("PRETENDARD",
       os.path.expanduser("~/orca/workspaces/indiff/seahare/vendor/PretendardVariable.woff2"))
OUT  = os.path.join(HERE, "assets", "pretendard-subset.woff2")

def page_text():
    s = io.open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    s = re.sub(r"(?s)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return html.unescape(s)      # &ldquo; 는 “ 로 그려진다 — 실체로 바꿔야 빠뜨리지 않는다

# 페이지 글자 + 아스키 + 자주 쓰는 기호. 여유를 조금 둔다 — 숫자·한글 자모는 다 넣는다.
chars = set(page_text())
chars |= set(chr(c) for c in range(0x20, 0x7F))
chars |= set("0123456789%·—–…「」『』《》〈〉“”‘’→←↑↓✓×±≤≥°₩")
text = "".join(sorted(chars))

if not os.path.exists(SRC):
    sys.exit("원본 글꼴을 못 찾았다: " + SRC)

cmd = [sys.executable, "-m", "fontTools.subset", SRC,
       "--text=" + text, "--flavor=woff2", "--output-file=" + OUT,
       "--layout-features=kern,liga,calt", "--no-hinting", "--desubroutinize"]
subprocess.run(cmd, check=True)
print("%s — %.0f KB (원본 %.1f MB · 글자 %d자)"
      % (os.path.relpath(OUT, HERE), os.path.getsize(OUT)/1024,
         os.path.getsize(SRC)/1024/1024, len(text)))

# ── 구운 뒤 스스로 검사한다 ──
# 이 검사가 없어서 글자 70자가 시스템 글꼴로 떨어진 채 배포됐다. 한 줄 안에서 획이 섞이고
# 글자 크기가 들쭉날쭉해 보였는데, 그게 굵기 설정이 아니라 **다른 글꼴**이었다.
# 원본에 없는 글자(⌘ 같은 기호)는 어차피 못 넣으므로 검사에서 뺀다 — 막을 수 없는 것으로
# 실패시키면 검사를 끄게 된다.
from fontTools.ttLib import TTFont


def coverage(path):
    f = TTFont(path)
    out = set()
    for t in f["cmap"].tables:
        out |= set(t.cmap.keys())
    f.close()
    return out


src_cov, out_cov = coverage(SRC), coverage(OUT)
need = {c for c in page_text() if c.strip() and ord(c) > 31}
gone = sorted(c for c in need if ord(c) in src_cov and ord(c) not in out_cov)
skip = sorted(c for c in need if ord(c) not in src_cov)
if skip:
    print("원본 글꼴에 없는 글자 %d자 (시스템 글꼴로 그려진다): %s" % (len(skip), " ".join(skip)))
if gone:
    sys.exit("서브셋이 빠뜨린 글자 %d자: %s" % (len(gone), " ".join(gone)))
print("검사 통과 — 페이지가 쓰는 글자가 모두 들어 있다")

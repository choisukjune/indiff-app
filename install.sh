#!/bin/sh
# INDIFF 설치 — curl -fsSL https://choisukjune.github.io/indiff-app/install.sh | sh
#
# 왜 이 길이 있나: 브라우저로 받은 DMG 는 격리 표시가 붙어, 공증 없는 앱이 처음 열 때
# 「Apple 이 확인할 수 없습니다」에 막힌다. curl 로 받은 파일엔 그 표시가 안 붙는다 —
# 같은 DMG 를 같은 자리에 넣되, 경고 없이 바로 열린다.
#
# 하는 일: 최신 릴리스 DMG 받기 → 해시 대조 → 응용 프로그램 폴더에 넣기 → Claude Code 확인 → 열기.
# 시험용 손잡이: INDIFF_INSTALL_DIR(넣을 폴더) · INDIFF_NO_OPEN=1(다 넣고 열지 않기)
#                INDIFF_NO_PROMPT=1(Claude Code 설치를 묻지 않기)
set -eu

REL="https://github.com/choisukjune/indiff-releases/releases/latest/download"
DMG="INDIFF-mac-arm64.dmg"
DEST="${INDIFF_INSTALL_DIR:-/Applications}"

say() { printf '  %s\n' "$*"; }
die() { printf '  ✘ %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = "Darwin" ] || die "macOS 전용입니다."
[ "$(uname -m)" = "arm64" ] || die "Apple Silicon(M1 이후) 맥 전용입니다."
major=$(sw_vers -productVersion | cut -d. -f1)
[ "$major" -ge 12 ] || die "macOS 12 이상이 필요합니다 (지금 $(sw_vers -productVersion))."

# 쓸 수 없으면 내 계정의 응용 프로그램 폴더로 — sudo 를 묻지 않는다
if [ ! -w "$DEST" ]; then
  DEST="$HOME/Applications"
  mkdir -p "$DEST"
fi
APP="$DEST/INDIFF.app"

if pgrep -f "$APP/Contents/MacOS/INDIFF" >/dev/null 2>&1; then
  die "INDIFF 가 켜져 있습니다. 끄고(⌘Q) 다시 실행해 주세요."
fi

TMP=$(mktemp -d "${TMPDIR:-/tmp}/indiff-install.XXXXXX")
MNT=""
cleanup() {
  [ -n "$MNT" ] && hdiutil detach -quiet "$MNT" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT INT TERM

printf '\n  (indiff) 설치\n\n'
say "받는 중…"
curl -fL --progress-bar -o "$TMP/$DMG" "$REL/$DMG" || die "DMG 를 받지 못했습니다."
curl -fsSL -o "$TMP/$DMG.sha256" "$REL/$DMG.sha256" || die "해시 파일을 받지 못했습니다."

want=$(cut -d' ' -f1 < "$TMP/$DMG.sha256")
got=$(shasum -a 256 "$TMP/$DMG" | cut -d' ' -f1)
[ "$want" = "$got" ] || die "받은 파일의 해시가 맞지 않습니다. 다시 시도해 주세요."
say "해시 확인 ✓"

MNT=$(hdiutil attach -nobrowse -readonly -noautoopen "$TMP/$DMG" | awk -F'\t' '/\/Volumes\// {print $NF; exit}')
[ -n "$MNT" ] && [ -d "$MNT/INDIFF.app" ] || die "DMG 를 열지 못했습니다."

say "$DEST 에 넣는 중…"
rm -rf "$APP"
ditto "$MNT/INDIFF.app" "$APP"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true

ver=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Contents/Info.plist" 2>/dev/null || echo '')
say "설치했습니다 — INDIFF ${ver} · $APP"

# Claude Code — 없으면 알려 주고, 원할 때만 공식 설치기를 돌린다(묻지 않고 깔지 않는다).
# 로그인 셸로 찾는다: 앱이 찾는 방식과 같아야 「여기선 있다는데 앱은 모른다」가 안 생긴다.
CC_URL="https://claude.ai/install.sh"
cc=$(/bin/zsh -lic 'printf "__C=%s\n" "$(command -v claude)"' 2>/dev/null | sed -n 's/^__C=//p' | tail -n1 || true)
if [ -n "$cc" ]; then
  say "Claude Code 확인 ✓"
else
  printf '\n'
  say "Claude Code 가 없습니다. 없어도 문서 열기·고치기·찾기·노트·내보내기는 모두 됩니다."
  say "AI 기능( / 로 쓰기 · 질의 · 채팅 )을 쓰려면 Claude Code 가 필요합니다."
  ans=""
  # 파이프로 들어온 스크립트라 표준입력은 이 파일이다 — 답은 터미널에서 직접 받는다
  if [ "${INDIFF_NO_PROMPT:-}" != "1" ] && ( : < /dev/tty ) 2>/dev/null; then
    printf '  지금 설치할까요? 공식 설치기(%s)를 실행합니다 [y/N] ' "$CC_URL"
    read -r ans < /dev/tty || ans=""
  fi
  case "$ans" in
    y|Y|yes|YES)
      if curl -fsSL "$CC_URL" | bash; then
        say "Claude Code 를 설치했습니다. 앱 안 터미널에서 claude 를 한 번 실행해 로그인하세요."
      else
        say "Claude Code 를 설치하지 못했습니다. 나중에: curl -fsSL $CC_URL | bash"
      fi ;;
    *)
      say "나중에 설치하려면: curl -fsSL $CC_URL | bash"
      say "깔고 나면 앱을 다시 켤 필요 없이, 창으로 돌아올 때 켜집니다." ;;
  esac
  printf '\n'
fi

if [ "${INDIFF_NO_OPEN:-}" != "1" ]; then
  open "$APP"
  say "앱을 엽니다. 처음엔 볼 폴더를 묻습니다."
fi
printf '\n'

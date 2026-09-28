#!/usr/bin/env bash
# Приводит сырой клип танца в темп трека (117 BPM) и собирает рил с музыкой и титрами.
# Модель отдаёт ~60 движений/мин независимо от промпта, поэтому темп добираем ретаймингом.
# Использование: ./make_intempo.sh <raw.mp4> <тег> <секунды раскачки> <темп клипа>
set -euo pipefail

RAW="$1"; TAG="$2"; WINDUP="$3"; SRC_TEMPO="$4"
MUSIC_BPM=117.25
FONTS=/Users/pavelkuzauka/Cursor_Folders/Meta/meta/assets/fonts
OUT=out

FACTOR=$(python3 -c "print(f'{$MUSIC_BPM/$SRC_TEMPO:.4f}')")
RAW_DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$RAW")
BODY=$(python3 -c "print(f'{($RAW_DUR-$WINDUP)/$FACTOR:.3f}')")

ffmpeg -y -v error -ss "$WINDUP" -i "$RAW" -an \
  -filter_complex "[0:v]setpts=PTS/$FACTOR,fps=24[v]" -map "[v]" \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p "$OUT/_${TAG}_fast.mp4"

# Точка склейки петли — кадр, чья поза ближе всего к последней, чтобы стык не читался.
CUT=$(python3 - "$OUT/_${TAG}_fast.mp4" <<'PY'
import subprocess, sys
W, H, FPS = 64, 114, 24
p = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vf",
                    f"fps={FPS},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                   capture_output=True)
n = W * H
f = [p.stdout[i*n:(i+1)*n] for i in range(len(p.stdout)//n)]
last = f[-1]
best = min(((sum(abs(a-b) for a, b in zip(last, fr))/n, i/FPS)
            for i, fr in enumerate(f[:int(3*FPS)])), key=lambda t: t[0])
print(f"{best[1]:.3f}")
PY
)

ffmpeg -y -v error -i "$OUT/_${TAG}_fast.mp4" -ss "$CUT" -i "$OUT/_${TAG}_fast.mp4" \
  -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0[v]" -map "[v]" \
  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p "$OUT/_${TAG}_loop.mp4"

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/_${TAG}_loop.mp4")
DUR=$(python3 -c "print(f'{min(float(\"$DUR\"), 15.0):.3f}')")
OUTRO=$(python3 -c "print(f'{$DUR-0.70:.2f}')")
FADE=$(python3 -c "print(f'{$DUR-0.60:.2f}')")

python3 - "$OUT/captions_v22.ass" "$OUT/captions_${TAG}.ass" "$OUTRO" <<'PY'
import sys
src, dst, outro = sys.argv[1], sys.argv[2], float(sys.argv[3])
def ts(t):
    return f"{int(t//3600)}:{int(t//60)%60:02d}:{t%60:05.2f}"
out = []
for line in open(src):
    if line.startswith("Dialogue") and "ЖАЛОБ НЕТ" in line:
        parts = line.split(",")
        parts[1], parts[2] = ts(outro), ts(outro + 0.70)
        line = ",".join(parts)
    out.append(line)
open(dst, "w").writelines(out)
PY

ffmpeg -y -v error -i "$OUT/_${TAG}_loop.mp4" -ss 0 -t "$DUR" -i "$OUT/music_cheri_ref.wav" \
  -filter_complex "[0:v]subtitles=$OUT/captions_${TAG}.ass:fontsdir=$FONTS[v];[1:a]afade=t=in:st=0:d=0.15,afade=t=out:st=$FADE:d=0.6[a]" \
  -map "[v]" -map "[a]" -t "$DUR" \
  -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart \
  "$OUT/bacenko_reel_${TAG}_intempo.mp4"

rm -f "$OUT/_${TAG}_fast.mp4" "$OUT/_${TAG}_loop.mp4"
echo "$OUT/bacenko_reel_${TAG}_intempo.mp4  factor=${FACTOR}x  loop cut=${CUT}s  dur=${DUR}s"

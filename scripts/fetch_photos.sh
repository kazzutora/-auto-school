#!/usr/bin/env bash
# Скачивает фотографии из photos.txt. Запускать из корня проекта.
set -euo pipefail

LIST="${1:-scripts/photos.txt}"
DEST="${2:-static/src/img}"   # sources, not served; the crops go to static/img/
W=2400            # исходная ширина, дальше режется в optimize_photos.py

mkdir -p "$DEST"
: > "$DEST/CREDITS.txt"
echo "# Источник: Unsplash. Лицензия: https://unsplash.com/license" >> "$DEST/CREDITS.txt"
echo "# файл | страница фотографии" >> "$DEST/CREDITS.txt"

while IFS='|' read -r name id where ratio; do
  [[ -z "${name:-}" || "$name" == \#* ]] && continue
  url="https://images.unsplash.com/${id}?auto=format&fit=crop&w=${W}&q=85&fm=jpg"
  page="https://unsplash.com/photos/${id#photo-}"
  echo "→ $name  ($where)"
  curl -fsSL --retry 2 "$url" -o "$DEST/$name"
  echo "$name | $page" >> "$DEST/CREDITS.txt"
done < "$LIST"

echo
echo "Скачано в $DEST. Дальше: make optimize-photos"

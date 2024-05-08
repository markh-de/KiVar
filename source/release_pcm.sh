#!/bin/sh -e

if [ "$#" -lt 1 ]; then
    echo "Usage: $(basename "$0") <VERSION>" >&2
    exit 1
fi

VERSION=$1

ID='de_markh_kivar'
RELEASE_NAME='kivar'

RELEASE_DIR=$(dirname "$0")"/../release/v$VERSION/pcm"
SRC_DIR=$(dirname "$0")
SRC_PCM_DIR="$SRC_DIR/pcm"

PCM_DIR=$(mktemp -d)

mkdir -p "$PCM_DIR/plugins"

cp "$SRC_DIR/kivar_plugin.py" \
   "$PCM_DIR/plugins/__init__.py"

cp "$SRC_DIR/kivar_backend.py" \
   "$SRC_DIR/$ID-icon-light.png" \
   "$SRC_DIR/$ID-icon-dark.png" \
   "$PCM_DIR/plugins/"

mkdir -p "$PCM_DIR/resources"
cp "$SRC_PCM_DIR/icon.png" \
   "$PCM_DIR/resources/"

sed "s/<<VERSION>>/$VERSION/g" "$SRC_PCM_DIR/metadata.json.tpl" > "$PCM_DIR/metadata.json"

mkdir -p "$RELEASE_DIR/"
rm  -f "$RELEASE_DIR/${RELEASE_NAME}-v${VERSION}-pcm.zip"
OUT_FILE=$(readlink -f "$RELEASE_DIR/${RELEASE_NAME}-v${VERSION}-pcm.zip")
cd "$PCM_DIR"
zip -r "$OUT_FILE" .
cd - >/dev/null

rm -rf "$PCM_DIR"

#!/bin/sh -e

if [ "$#" -lt 1 ]; then
    echo "Usage: $(basename "$0") <VERSION>" >&2
    exit 1
fi

VERSION=$1

ID='de_markh_kivar'
RELEASE_NAME='kivar'

RELEASE_DIR="$(dirname "$0")/release"
SRC_PLUGIN_DIR="$(dirname "$0")/plugin"
SRC_PCM_DIR="$SRC_PLUGIN_DIR/pcm"

### PCM PACKAGE ###
PCM_DIR="$(mktemp -d)"

mkdir -p "$PCM_DIR/plugins"
cp "$SRC_PLUGIN_DIR/$ID-"*.png \
   "$PCM_DIR/plugins/"
cp "$SRC_PLUGIN_DIR/$ID.py" \
   "$PCM_DIR/plugins/__init__.py"

mkdir -p "$PCM_DIR/resources"
cp "$SRC_PCM_DIR/icon.png" \
   "$PCM_DIR/resources/"

sed "s/<<VERSION>>/$VERSION/g" "$SRC_PCM_DIR/metadata.json.tpl" > "$PCM_DIR/metadata.json"

cd "$PCM_DIR"
rm  -f "$RELEASE_DIR/${RELEASE_NAME}-v${VERSION}-pcm.zip"
zip -r "$RELEASE_DIR/${RELEASE_NAME}-v${VERSION}-pcm.zip" .
cd -

rm -rf "$PCM_DIR"

### ARCHIVE ###
ARCH_DIR="$(mktemp -d)"

cp "$SRC_PLUGIN_DIR/$ID-"*.png \
   "$SRC_PLUGIN_DIR/$ID.py" \
   "$ARCH_DIR/"

cd "$ARCH_DIR"
rm  -f "$RELEASE_DIR/${RELEASE_NAME}-v${VERSION}.zip"
zip -r "$RELEASE_DIR/${RELEASE_NAME}-v${VERSION}.zip" .
cd -

rm -rf "$ARCH_DIR"

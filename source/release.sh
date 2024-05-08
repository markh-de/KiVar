#!/bin/sh -e

release_pcm() {
    release_dir="$RELEASE_DIR"
    src_pcm_dir="$SRC_DIR/pcm"
    tmp_dir=$(mktemp -d)
    out_file="$release_dir/${RELEASE_NAME}-${VERSION}-pcm.zip"

    mkdir -p "$tmp_dir/plugins"

    cp "$SRC_DIR/kivar_plugin.py" \
       "$tmp_dir/plugins/__init__.py"

    cp "$SRC_DIR/kivar_backend.py" \
       "$SRC_DIR/$ID-icon-"*.png \
       "$tmp_dir/plugins/"

    mkdir -p "$tmp_dir/resources"
    cp "$src_pcm_dir/icon.png" \
       "$tmp_dir/resources/"

    sed "s/<<VERSION>>/$VERSION/g" "$src_pcm_dir/metadata.json.tpl" > "$tmp_dir/metadata.json"

    mkdir -p "$release_dir/"
    rm  -f "$out_file"
    cd "$tmp_dir"
    zip -r "$out_file" .
    cd - >/dev/null

    rm -rf "$tmp_dir"
}

release_pypi() {
    release_dir="$RELEASE_DIR"
    src_tmp_dir="$SRC_DIR/pypi"
    tmp_dir=$(mktemp -d)

    # TODO shorten README.md, only lines before:
    #      <!-- intro_end -->
    # is readme text used as description?

    sed "s/<<VERSION>>/$VERSION/g" "$src_tmp_dir/setup.py.tpl" > "$tmp_dir/setup.py"

    mkdir -p "$tmp_dir/$RELEASE_NAME/"

    cp "$src_tmp_dir/__init__.py" \
       "$SRC_DIR/kivar_cli.py" \
       "$SRC_DIR/kivar_backend.py" \
       "$tmp_dir/$RELEASE_NAME/"

    cp "$README_FILE" \
       "$tmp_dir/"

    mkdir -p "$release_dir/"

    cd "$tmp_dir/"
    python setup.py sdist
    cd - >/dev/null

    cp "$tmp_dir/dist/"* \
       "$release_dir"

    rm -rf "$tmp_dir"
}

release_zip() {
    release_dir="$RELEASE_DIR"
    tmp_dir=$(mktemp -d)
    out_file="$release_dir/${RELEASE_NAME}-${VERSION}-plugin.zip"

    cp "$SRC_DIR/$ID-"*.png \
       "$SRC_DIR/kivar_plugin.py" \
       "$SRC_DIR/kivar_backend.py" \
       "$tmp_dir/"

    rm -f "$out_file"

    cd "$tmp_dir"
    zip -r "$out_file" .
    cd - >/dev/null

    rm -rf "$tmp_dir"
}

# main

if [ "$#" -lt 1 ]; then
    echo "Usage: $(basename "$0") <VERSION>" >&2
    exit 1
fi

VERSION=$1
RELEASE_NAME='kivar'
ID='de_markh_kivar'
RELEASE_DIR=$(readlink -f "$(dirname "$0")")"/../release/v$VERSION"
README_FILE=$(readlink -f "$(dirname "$0")")"/../README.md"
SRC_DIR=$(readlink -f "$(dirname "$0")")

echo "--- PCM ---"
release_pcm
echo ''
echo "--- PyPI ---"
release_pypi
echo ''
echo "--- ZIP ---"
release_zip
echo ''
echo 'Release files created.'

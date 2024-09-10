#!/bin/sh -e

release_pcm() {
    out_base_name="${RELEASE_NAME}-${VERSION}-pcm.zip"
    meta_version="$VERSION"
    meta_status="testing"
    meta_kicad_version="8.0"
    meta_download_url="https://github.com/markh-de/KiVar/releases/download/v${VERSION}/${out_base_name}"

    release_dir="$RELEASE_DIR"
    src_pcm_dir="$SRC_DIR/pcm"
    tmp_dir=$(mktemp -d)
    out_file="$release_dir/${out_base_name}"

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

    rm  -f "$out_file"
    cd "$tmp_dir"
    zip -r "$out_file" .
    cd - >/dev/null

    rm -rf "$tmp_dir"

    echo ''
    echo '<<< PCM Package Info'
    cat <<EOF
{
    "version": "${meta_version}",
    "status": "${meta_status}",
    "kicad_version": "${meta_kicad_version}",
    "download_sha256": "$(sha256sum "$out_file" | cut -f1 -d' ')",
    "download_size": $(wc -c < "$out_file"),
    "download_url": "${meta_download_url}",
    "install_size": $(unzip -l "$out_file" | tail -n1 | xargs | cut -f1 -d' ')
},
EOF
    echo '>>>'
}

release_pypi() {
    release_dir="$RELEASE_DIR"
    src_tmp_dir="$SRC_DIR/pypi"
    tmp_dir=$(mktemp -d)

    sed "s/<<VERSION>>/$VERSION/g" "$src_tmp_dir/setup.py.tpl" > "$tmp_dir/setup.py"

    mkdir -p "$tmp_dir/$RELEASE_NAME/"

    cp "$src_tmp_dir/__init__.py" \
       "$SRC_DIR/kivar_cli.py" \
       "$SRC_DIR/kivar_backend.py" \
       "$tmp_dir/$RELEASE_NAME/"

    cp "$src_tmp_dir/README.md" \
       "$tmp_dir/"

    cd "$tmp_dir/"
    python3 ./setup.py sdist
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
SRC_DIR=$(readlink -f "$(dirname "$0")")

rm -rf "$RELEASE_DIR/"
mkdir -p "$RELEASE_DIR/"

echo "--- ZIP ---"
release_zip
echo ''

echo "--- PyPI ---"
release_pypi
echo ''

echo "--- PCM ---"
release_pcm
echo ''

echo 'Release files created.'

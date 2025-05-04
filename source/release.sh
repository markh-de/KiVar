#!/bin/sh -e

release_plugin_pcm() {
    out_base_name="${RELEASE_NAME}-${VERSION}-pcm.zip"
    meta_version="$VERSION"
    meta_status="stable"
    meta_kicad_version="8.0"
    meta_download_url="https://pcm.kivar.markh.de/${out_base_name}"

    release_dir="$RELEASE_DIR"
    src_pcm_dir="$SRC_DIR/pcm"
    tmp_dir=$(mktemp -d)
    out_file="$release_dir/${out_base_name}"

    mkdir -p "$tmp_dir/plugins"

    cp "$SRC_DIR/__init__.py" \
       "$SRC_DIR/kivar_engine.py" \
       "$SRC_DIR/kivar_forms.py" \
       "$SRC_DIR/kivar_gui.py" \
       "$SRC_DIR/kivar_gui_custom.py" \
       "$SRC_DIR/kivar_version.py" \
       "$SRC_DIR/kivar_icon_light.png" \
       "$SRC_DIR/kivar_icon_light_24.png" \
       "$SRC_DIR/kivar_icon_dark.png" \
       "$SRC_DIR/kivar_icon_dark_24.png" \
       "$tmp_dir/plugins/"

    mkdir -p "$tmp_dir/resources"
    cp "$src_pcm_dir/icon.png" \
       "$tmp_dir/resources/"

    sed "s/<<VERSION>>/$VERSION/g" "$src_pcm_dir/metadata-template.json" > "$tmp_dir/metadata.json"

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

release_cli_pypi() {
    release_dir="$RELEASE_DIR"
    pypi_meta_dir="$SRC_DIR/pypi"
    tmp_dir=$(mktemp -d)

    sed "s/<<VERSION>>/$VERSION/g" "$pypi_meta_dir/setup.py.tpl" > "$tmp_dir/setup.py"

    mkdir -p "$tmp_dir/$RELEASE_NAME/"

    cp "$pypi_meta_dir/__init__.py" \
       "$SRC_DIR/kivar_cli.py" \
       "$SRC_DIR/kivar_engine.py" \
       "$SRC_DIR/kivar_version.py" \
       "$tmp_dir/$RELEASE_NAME/"

    cp "$pypi_meta_dir/README.md" \
       "$pypi_meta_dir/pyproject.toml" \
       "$tmp_dir/"

    cd "$tmp_dir/"
    python3 ./setup.py sdist
    cd - >/dev/null

    cp "$tmp_dir/dist/"* \
       "$release_dir"

    rm -rf "$tmp_dir"
}

# main

SRC_DIR=$(readlink -f "$(dirname "$0")")
VERSION=$(python3 ${SRC_DIR}/kivar_version.py)
RELEASE_NAME='kivar'
ID='de_markh_kivar'
RELEASE_DIR=$(readlink -f "$(dirname "$0")")"/../release/v$VERSION"

echo "Creating KiVar release $VERSION:"
echo ''

rm -rf "$RELEASE_DIR/"
mkdir -p "$RELEASE_DIR/"

echo "--- PyPI ---"
release_cli_pypi
echo ''

echo "--- PCM ---"
release_plugin_pcm
echo ''

echo 'Release files created.'

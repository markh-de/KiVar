#!/bin/sh -e

if [ "$#" -lt 1 ]; then
    echo "Usage: $(basename "$0") <VERSION>" >&2
    exit 1
fi

VERSION=$1

RELEASE_NAME='kivar'

RELEASE_DIR=$(dirname "$0")"/../release/v$VERSION/pypi"
README_FILE=$(dirname "$0")"/../README.md"
SRC_DIR=$(dirname "$0")
SRC_PYPI_DIR="$SRC_DIR/pypi"

PYPI_DIR=$(mktemp -d)

# TODO shorten README.md, only lines before:
#      <!-- intro_end -->
# is readme text used as description?

sed "s/<<VERSION>>/$VERSION/g" "$SRC_PYPI_DIR/setup.py.tpl" > "$PYPI_DIR/setup.py"

mkdir -p "$PYPI_DIR/$RELEASE_NAME/"

cp "$SRC_PYPI_DIR/__init__.py" \
   "$SRC_DIR/kivar_cli.py" \
   "$SRC_DIR/kivar_backend.py" \
   "$PYPI_DIR/$RELEASE_NAME/"

cp "$README_FILE" \
   "$PYPI_DIR/"

mkdir -p "$RELEASE_DIR/"

cd "$PYPI_DIR/"
python setup.py sdist
cd - >/dev/null

cp "$PYPI_DIR/dist/"* \
   "$RELEASE_DIR"

rm -rf "$PYPI_DIR"

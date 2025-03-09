#! /usr/bin/env bash
uv venv rhizome
source rhizome/bin/activate
uv pip install .
cat > rhizome/rhizome <<'EOF'
#! /usr/bin/env bash
cd "`dirname $0`"
source bin/activate
python3 -m rhizome.main
EOF
chmod +x rhizome/rhizome
zip -r rhizome.linux.zip dist
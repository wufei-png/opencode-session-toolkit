#!/bin/bash
set -e

REPO="wufei-png/opencode-session-toolkit"
BRANCH="main"
SKILL_NAME="opencode-session-toolkit"
TARGET_DIR="${OPENCODE_TOOLKIT_DIR:-$HOME/.agents/skills/${SKILL_NAME}}"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}"
API_BASE="https://api.github.com/repos/${REPO}/contents"

# Language selection - support both interactive and piped modes
# Can be set via environment variable: LANG_CHOICE=2 curl ... | bash
if [ -n "$LANG_CHOICE" ]; then
    lang_choice="$LANG_CHOICE"
elif [ -t 0 ]; then
    # Interactive mode - stdin is a terminal
    echo "Select language / 选择语言:"
    echo "  1) English"
    echo "  2) 中文"
    echo ""
    read -p "Enter choice [1/2]: " lang_choice
else
    # Piped mode - default to English, show how to select Chinese
    echo "Select language / 选择语言:"
    echo "  1) English"
    echo "  2) 中文"
    echo ""
    echo "Non-interactive mode detected. Defaulting to English."
    echo "For Chinese, use: LANG_CHOICE=2 bash -c \"\$(curl -fsSL ...)\""
    echo ""
    lang_choice="1"
fi

case "$lang_choice" in
    2|中文|cn|CN)
        SOURCE_DIR="opencode-session-toolkit-cn"
        echo ""
        echo "已选择中文版本"
        ;;
    *)
        SOURCE_DIR="opencode-session-toolkit"
        echo ""
        echo "Selected English version"
        ;;
esac

download_file() {
    local src_file="$1"
    local dest_file="$2"
    local dir="${TARGET_DIR}/$(dirname "$dest_file")"
    mkdir -p "${dir}"
    
    local url="${RAW_BASE}/${SOURCE_DIR}/${src_file}"
    local target="${TARGET_DIR}/${dest_file}"
    
    echo "  Downloading ${src_file}..."
    if curl -fsSL "${url}" -o "${target}"; then
        echo "    ✓ ${dest_file}"
    else
        echo "    ✗ Failed to download ${src_file}"
        return 1
    fi
}

download_directory() {
    local dir_path="$1"
    echo "  Fetching directory listing: ${dir_path}..."
    
    local files
    files=$(curl -fsSL "${API_BASE}/${SOURCE_DIR}/${dir_path}?ref=${BRANCH}" | grep '"name"' | sed 's/.*"name": "\([^"]*\)".*/\1/')
    
    if [ -z "$files" ]; then
        echo "    ✗ Failed to list ${dir_path}"
        return 1
    fi
    
    for file in $files; do
        download_file "${dir_path}/${file}" "${dir_path}/${file}" || return 1
    done
}

echo ""
echo "Installing opencode-session-toolkit to ${TARGET_DIR}..."
echo ""

mkdir -p "${TARGET_DIR}"

# Download SKILL.md
download_file "SKILL.md" "SKILL.md" || exit 1

# Download directories dynamically
download_directory "references" || exit 1
download_directory "scripts" || exit 1
download_directory "agents" || exit 1

# Make scripts executable
chmod +x "${TARGET_DIR}/scripts/"* 2>/dev/null || true

# Create symlinks for common clients
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
CURSOR_SKILLS_DIR="$HOME/.cursor/skills"

mkdir -p "${CLAUDE_SKILLS_DIR}" "${CURSOR_SKILLS_DIR}"
ln -sfn "${TARGET_DIR}" "${CLAUDE_SKILLS_DIR}/${SKILL_NAME}"
ln -sfn "${TARGET_DIR}" "${CURSOR_SKILLS_DIR}/${SKILL_NAME}"

echo ""
echo "✓ Installation complete!"
echo "  Location: ${TARGET_DIR}"
echo "  Symlinks:"
echo "    ${CLAUDE_SKILLS_DIR}/${SKILL_NAME} -> ${TARGET_DIR}"
echo "    ${CURSOR_SKILLS_DIR}/${SKILL_NAME} -> ${TARGET_DIR}"
echo ""
echo "To use with OpenCode, the skill is ready at:"
echo "  ${TARGET_DIR}/SKILL.md"

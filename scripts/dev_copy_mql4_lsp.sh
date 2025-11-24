#!/bin/bash
# Script simple de desarrollo para copiar MQL4 LSP a Serena
# Usage: ./scripts/dev_copy_mql4_lsp.sh

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SOURCE_DIR="./src/bin/Release/net10.0/publish/linux-x64"
SOURCE_FILE="$SOURCE_DIR/mql4-lsp-server"
DEST_DIR="$HOME/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp"
DEST_FILE="$DEST_DIR/mql4-lsp-server"

echo "======================================"
echo "  Copiar MQL4 LSP a Serena"
echo "======================================"
echo ""

# Verificar archivo fuente
if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${YELLOW}[WARN]${NC} Archivo fuente no encontrado: $SOURCE_FILE"
    echo "Asegúrate de haber compilado el proyecto para linux-x64"
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Archivo fuente: $SOURCE_FILE"
ls -lh "$SOURCE_FILE"

# Crear directorio destino
echo -e "${GREEN}[INFO]${NC} Creando directorio destino..."
mkdir -p "$DEST_DIR"

# Copiar archivo
echo -e "${GREEN}[INFO]${NC} Copiando archivo..."
cp "$SOURCE_FILE" "$DEST_FILE"
chmod +x "$DEST_FILE"

# Verificar versión
echo ""
echo -e "${GREEN}[INFO]${NC} Verificando versión instalada..."
echo -e "${GREEN}[INFO]${NC} Ejecutando $DEST_FILE --version"
echo "---"
"$DEST_FILE" --version
echo "---"

echo ""
echo -e "${GREEN}[INFO]${NC} ¡Copiado exitosamente!"
echo -e "${GREEN}[INFO]${NC} Destino: $DEST_FILE"
ls -lh "$DEST_FILE"
echo ""

# Iron Editor

[![PyPI - Version](https://img.shields.io/pypi/v/iron-editor.svg)](https://pypi.org/project/iron-editor)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/iron-editor.svg)](https://pypi.org/project/iron-editor)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A terminal-based code editor built with [Textual](https://textual.textualize.io/). Designed for educational environments where students edit code directly in the terminal.

---

## Features

- Syntax highlighting for Python, JavaScript, HTML, CSS, Java, C, C++, JSON and Markdown
- Multi-tab editing
- Integrated file explorer (sidebar)
- Integrated terminal panel
- File integrity verification via HMAC signature
- Log panel for debugging
- Dracula theme

---

## Installation

```bash
pip install iron-editor
```

**Requirements:** Python 3.9+

---

## Usage

```bash
# Open editor in current directory
ironedit

# Open editor in a specific directory
ironedit /path/to/project
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `N` | Create new file |
| `Shift+N` | Create new folder |
| `Ctrl+S` | Save current file |
| `Ctrl+W` | Close current tab |
| `Ctrl+T` | Toggle terminal panel |
| `Ctrl+L` | Toggle log panel |
| `Ctrl+R` | Run current file (in terminal) |
| `Q` | Quit |

---

## File Signing

Iron Editor signs every saved file with an HMAC signature. Files created or modified outside of Iron Editor will be blocked when opened. This is intentional for classroom use — it ensures students work within the editor.

---

---

## Para alumnos / For Students (Español)

### Instalación

```bash
pip install iron-editor
```

### Cómo usarlo

Abre una terminal y escribe:

```bash
ironedit
```

Esto abrirá el editor en la carpeta actual. También puedes indicar una carpeta específica:

```bash
ironedit C:\Users\TuNombre\mis-proyectos
```

### Interfaz

```
┌─────────────────────────────────────────────────────┐
│  IronEdit                              🕐 12:00      │
├──────────┬──────────────────────────┬────────────────┤
│          │  archivo.py  ×           │                │
│  📁 src  │──────────────────────────│   Log          │
│  📄 main │  1  def main():          │                │
│  📄 util │  2      print("Hola")    │                │
│          │  3                       │                │
│          ├──────────────────────────┤                │
│          │  Terminal                │                │
├──────────┴──────────────────────────┴────────────────┤
│  N Nueva  Shift+N Carpeta  Ctrl+S Guardar  Q Salir   │
└─────────────────────────────────────────────────────┘
```

- **Panel izquierdo:** explorador de archivos. Haz clic en un archivo para abrirlo.
- **Centro:** editor de código con pestañas. Puedes tener varios archivos abiertos.
- **Panel inferior (`Ctrl+T`):** terminal integrada para ejecutar tu código.
- **Panel derecho (`Ctrl+L`):** log de eventos del editor.

### Atajos principales

| Tecla | Acción |
|-------|--------|
| `N` | Crear archivo nuevo |
| `Shift+N` | Crear carpeta nueva |
| `Ctrl+S` | Guardar archivo actual |
| `Ctrl+W` | Cerrar pestaña actual |
| `Ctrl+T` | Mostrar/ocultar terminal |
| `Ctrl+L` | Mostrar/ocultar log |
| `Ctrl+R` | Ejecutar archivo actual |
| `Q` | Salir del editor |

### Nota sobre los archivos

Iron Editor firma los archivos que guarda. Si intentas abrir un archivo que **no fue creado o guardado con Iron Editor**, el editor lo bloqueará. Esto es para garantizar que trabajes siempre dentro del entorno del editor.

---

## Changelog

### v0.0.3
- Terminal: resize panel with `Ctrl+Up` / `Ctrl+Down`
- Terminal: added `min-height` to prevent collapsing too small
- File explorer: `F5` refreshes the directory tree
- pyproject.toml: corrected author email and GitHub URLs

### v0.0.2
- Integrated terminal panel with command history and `cd` support
- `Ctrl+T` toggle for terminal, `Ctrl+R` to run current file
- Log panel toggle (`Ctrl+L`) and last-log in status bar

### v0.0.1
- Initial release: syntax highlighting, multi-tab editor, file explorer, HMAC file signing

---

## License

`iron-editor` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

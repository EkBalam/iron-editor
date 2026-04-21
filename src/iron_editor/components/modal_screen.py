"""Modales de la aplicación (crear archivo, crear carpeta)."""

import pathlib
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, RichLog, Static

from iron_editor.components.directory import Directory
from iron_editor.components.ironedit import IronEdit
from iron_editor.components.signer import sign_content, load_secret_key


class CreateFileModal(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close create file")]

    def compose(self) -> ComposeResult:
        yield Static("Crear archivo", id="create_title")
        yield Input(placeholder="ruta/archivo.py o solo archivo.py", id="new_filename")
        yield Horizontal(Button("Create", id="create_confirm"), Button("Cancel", id="create_cancel"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "create_cancel":
            self.app.pop_screen()
            return
        if btn_id == "create_confirm":
            input_widget = self.query_one("#new_filename", Input)
            name = input_widget.value.strip()
            log = self.app.query_one(RichLog)
            if not name:
                log.write("No filename provided")
                return
            try:
                p = pathlib.Path(name)
                if not p.parent.exists():
                    p.parent.mkdir(parents=True, exist_ok=True)
                if not p.exists():
                    ext = p.suffix.lower()
                    secret_key = load_secret_key()
                    initial_content = sign_content("", p.name, ext, secret_key)
                    p.write_text(initial_content, encoding="utf-8")
                    log.write(f"Created file: {p}")
                else:
                    log.write(f"File already exists: {p}")
                try:
                    editor = self.app.query_one(IronEdit)
                    editor.open_file(str(p))
                except Exception:
                    pass
                try:
                    tree = self.app.query_one(Directory)
                    tree.reload()
                except Exception as e:
                    log.write(f"Error recargando árbol: {e}")
                self.app.pop_screen()
            except Exception as e:
                log.write(f"Error creating file: {e}")


class CreateFolderModal(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close create folder")]

    def compose(self) -> ComposeResult:
        yield Static("Crear carpeta", id="create_title")
        yield Input(placeholder="ruta/carpeta o solo carpeta", id="new_foldername")
        yield Button("Create", id="create_confirm")
        yield Button("Cancel", id="create_cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "create_cancel":
            self.app.pop_screen()
            return
        if btn_id == "create_confirm":
            input_widget = self.query_one("#new_foldername", Input)
            name = input_widget.value.strip()
            log = self.app.query_one(RichLog)
            if not name:
                log.write("No folder name provided")
                return
            try:
                p = pathlib.Path(name)
                if not p.exists():
                    p.mkdir(parents=True, exist_ok=True)
                    log.write(f"Created folder: {p}")
                else:
                    log.write(f"Folder already exists: {p}")
                try:
                    tree = self.app.query_one(Directory)
                    tree.reload()
                except Exception:
                    pass
                self.app.pop_screen()
            except Exception as e:
                log.write(f"Error creating folder: {e}")

    def action_dismiss(self) -> None:
        self.app.pop_screen()

import argparse
import hashlib
import os
import pathlib

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, RichLog, Static, TabbedContent, TabPane

from iron_editor.components.directory import Directory
from iron_editor.components.ironedit import IronEdit
from iron_editor.components.modal_screen import (
    CreateFileModal,
    CreateFolderModal,
    DeleteConfirmModal,
    RenameModal,
)
from iron_editor.components.terminal import TerminalWidget


class TextAreaExample(App):
    CSS = """
    DirectoryTree {
        width: auto;
        height: 100%;
        border-right: heavy $secondary;
        padding: 1;
    }
    #editor-area {
        height: 1fr;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        height: 1fr;
        padding: 0;
    }
    IronEdit {
        height: 1fr;
    }
    TerminalWidget {
        height: 12;
        display: none;
    }
    TerminalWidget.visible {
        display: block;
    }
    #log {
        width: 40;
        border-left: heavy $secondary;
        display: none;
    }
    #log.visible {
        display: block;
    }
    #log-status {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="n", action="create_file", description="Create new file", key_display="N"),
        Binding(key="shift+n", action="create_folder", description="Create new folder", key_display="Shift+N"),
        Binding(key="ctrl+w", action="close_tab", description="Close tab", key_display="Ctrl+W"),
        Binding(key="ctrl+t", action="toggle_terminal", description="Terminal", key_display="Ctrl+T"),
        Binding(key="ctrl+l", action="toggle_log", description="Log", key_display="Ctrl+L"),
    ]

    def __init__(self, path="."):
        super().__init__()
        self.path = path

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield Directory(self.path)
            with Vertical(id="editor-area"):
                yield TabbedContent(id="editor-tabs")
                yield TerminalWidget(id="terminal")
            yield RichLog(id="log")
        yield Static("", id="log-status")
        yield Footer(show_command_palette=True)

    def on_mount(self) -> None:
        self.title = "IronEdit"

    def log_msg(self, text: str) -> None:
        self.query_one("#log", RichLog).write(text)
        self.query_one("#log-status", Static).update(text)

    # ── Tab helpers ────────────────────────────────────────────────────────────

    def _get_tab_id(self, path_str: str) -> str:
        return "tab-" + hashlib.md5(path_str.encode()).hexdigest()[:8]

    def open_file_in_tab(self, path: pathlib.Path) -> None:
        path = path.resolve()
        tabs = self.query_one("#editor-tabs", TabbedContent)
        tab_id = self._get_tab_id(str(path))

        # Si ya está abierto, activar ese tab
        existing_pane_ids = [pane.id for pane in tabs.query(TabPane)]
        if tab_id in existing_pane_ids:
            tabs.active = tab_id
            try:
                pane = tabs.get_pane(tab_id)
                pane.query_one(IronEdit).focus()
            except Exception:
                pass
            return

        editor = IronEdit.code_editor()
        pane = TabPane(path.name, editor, id=tab_id)
        tabs.add_pane(pane)
        self.call_after_refresh(self._finish_open, tab_id, path)

    def _finish_open(self, tab_id: str, path: pathlib.Path) -> None:
        tabs = self.query_one("#editor-tabs", TabbedContent)
        tabs.active = tab_id
        try:
            pane = tabs.get_pane(tab_id)
            editor = pane.query_one(IronEdit)
            editor.open_file(str(path))
            editor.focus()
        except Exception as e:
            self.log_msg(f"Error abriendo {path}: {e}")

    def _update_tab_after_rename(self, old_path_str: str, new_path: pathlib.Path) -> None:
        tabs = self.query_one("#editor-tabs", TabbedContent)
        old_tab_id = self._get_tab_id(old_path_str)
        existing_pane_ids = [pane.id for pane in tabs.query(TabPane)]
        if old_tab_id in existing_pane_ids:
            tabs.remove_pane(old_tab_id)
            self.open_file_in_tab(new_path)

    def _close_tab_for_path(self, path_str: str) -> None:
        tabs = self.query_one("#editor-tabs", TabbedContent)
        tab_id = self._get_tab_id(path_str)
        existing_pane_ids = [pane.id for pane in tabs.query(TabPane)]
        if tab_id in existing_pane_ids:
            tabs.remove_pane(tab_id)

    # ── Event handlers ─────────────────────────────────────────────────────────

    def on_iron_edit_log_requested(self, event: IronEdit.LogRequested) -> None:
        self.log_msg(event.text)

    def on_directory_file_open_requested(self, event: Directory.FileOpenRequested) -> None:
        self.open_file_in_tab(event.path)

    def on_iron_edit_title_changed(self, event: IronEdit.TitleChanged) -> None:
        tabs = self.query_one("#editor-tabs", TabbedContent)
        for pane in tabs.query(TabPane):
            try:
                editor = pane.query_one(IronEdit)
                if editor is event.editor:
                    tab = tabs.get_tab(pane.id)
                    path = pathlib.Path(editor.current_file) if editor.current_file else None
                    base_name = path.name if path else "sin título"
                    tab.label = f"{base_name} *" if event.has_unsaved else base_name
                    break
            except Exception:
                continue

    def on_directory_rename_requested(self, event: Directory.RenameRequested) -> None:
        path = event.path
        old_path_str = str(path.resolve())

        def handle_rename(new_name: str | None) -> None:
            if not new_name:
                return
            try:
                new_path = path.parent / new_name
                path.rename(new_path)
                self.log_msg(f"Renombrado: {path.name} → {new_name}")
                self.query_one(Directory).reload()
                self._update_tab_after_rename(old_path_str, new_path)
            except Exception as e:
                self.log_msg(f"Error al renombrar: {e}")

        self.push_screen(RenameModal(path), handle_rename)

    def on_directory_delete_requested(self, event: Directory.DeleteRequested) -> None:
        path = event.path
        path_str = str(path.resolve())

        def handle_delete(confirmed: bool) -> None:
            if not confirmed:
                return
            try:
                path.unlink()
                self.log_msg(f"Eliminado: {path.name}")
                self.query_one(Directory).reload()
                self._close_tab_for_path(path_str)
            except Exception as e:
                self.log_msg(f"Error al eliminar: {e}")

        self.push_screen(DeleteConfirmModal(path), handle_delete)

    # ── Actions ────────────────────────────────────────────────────────────────

    def action_create_file(self) -> None:
        self.push_screen(CreateFileModal())

    def action_create_folder(self) -> None:
        self.push_screen(CreateFolderModal())

    def action_close_tab(self) -> None:
        tabs = self.query_one("#editor-tabs", TabbedContent)
        if tabs.tab_count <= 1:
            self.log_msg("No se puede cerrar el único tab")
            return
        active_id = tabs.active
        if active_id:
            tabs.remove_pane(active_id)

    def action_toggle_log(self) -> None:
        log = self.query_one("#log", RichLog)
        if log.has_class("visible"):
            log.remove_class("visible")
        else:
            log.add_class("visible")

    def action_toggle_terminal(self) -> None:
        terminal = self.query_one("#terminal", TerminalWidget)
        if terminal.has_class("visible"):
            terminal.remove_class("visible")
            try:
                tabs = self.query_one("#editor-tabs", TabbedContent)
                pane = tabs.get_pane(tabs.active)
                pane.query_one(IronEdit).focus()
            except Exception:
                pass
        else:
            terminal.add_class("visible")
            terminal.focus()


def main():
    parser = argparse.ArgumentParser(description="IronEdit Text Editor")
    parser.add_argument("path", nargs="?", default=os.getcwd(), help="Path to the directory to open")
    args = parser.parse_args()
    app = TextAreaExample(path=args.path)
    app.run()


if __name__ == "__main__":
    main()

import pathlib
from textual.binding import Binding
from textual.message import Message
from textual.widgets import DirectoryTree, RichLog


class Directory(DirectoryTree):

    class FileOpenRequested(Message):
        def __init__(self, path: pathlib.Path) -> None:
            super().__init__()
            self.path = path

    class RenameRequested(Message):
        def __init__(self, path: pathlib.Path) -> None:
            super().__init__()
            self.path = path

    class DeleteRequested(Message):
        def __init__(self, path: pathlib.Path) -> None:
            super().__init__()
            self.path = path

    BINDINGS = [
        Binding("f5", "refresh_tree", "Refrescar", show=True),
        Binding("f2", "rename", "Renombrar", show=True),
        Binding("r", "rename", "Renombrar", show=False),
        Binding("delete", "delete_file", "Eliminar", show=True),
        Binding("d", "delete_file", "Eliminar", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = pathlib.Path.cwd()
        self._selected_path: pathlib.Path | None = None

    def on_mount(self) -> None:
        self.path = pathlib.Path.cwd()
        self.root_directory = self.path
        self.rich_log = self.app.query_one(RichLog)
        self.reload()

    def _on_directory_tree_file_selected(self, event) -> None:
        self._selected_path = event.path
        self.rich_log.write(f"File selected: {event.path}")
        self.post_message(self.FileOpenRequested(event.path))

    def on_tree_node_highlighted(self, event) -> None:
        if event.node.data is not None:
            path = event.node.data.path
            if path.is_file():
                self._selected_path = path
            else:
                self._selected_path = None

    def action_refresh_tree(self) -> None:
        self.reload()

    def action_rename(self) -> None:
        if self._selected_path and self._selected_path.is_file():
            self.post_message(self.RenameRequested(self._selected_path))

    def action_delete_file(self) -> None:
        if self._selected_path and self._selected_path.is_file():
            self.post_message(self.DeleteRequested(self._selected_path))

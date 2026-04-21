
from textual.widgets import DirectoryTree, RichLog
from textual.binding import Binding
from iron_editor.components.ironedit import IronEdit
import pathlib

class Directory(DirectoryTree):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = pathlib.Path.cwd()
        

    def on_mount(self) -> None:
        self.path = pathlib.Path.cwd()
        self.root_directory = self.path
        self.rich_log = self.app.query_one(RichLog)
        self.reload()
    
    # def _on_key(self, event):
    #     self.rich_log = self.app.query_one(RichLog)
    #     self.rich_log.write(f"Key pressed in Directory: {event.key}")
    #     return super()._on_key(event)
    
    def _on_directory_tree_file_selected (self, event):
        self.rich_log.write(f"File selected: {event.path}")
        if event.path.is_file():
            self.parent.app.query_one(IronEdit).open_file(str(event.path))        
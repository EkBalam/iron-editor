from textual.app import App, ComposeResult
from textual.widgets import RichLog, Header, Footer
from textual.binding import Binding
from textual.containers import Horizontal
from iron_editor.components.ironedit import IronEdit
from iron_editor.components.directory import Directory
from iron_editor.components.modal_screen import CreateFileModal, CreateFolderModal
import argparse
import os


TEXT = """\
def hello(name):
    print("hello" + name)

def goodbye(name):
    print("goodbye" + name)

name = input()
"""

class TextAreaExample(App):
    CSS = """
    DirectoryTree {
        width: auto;
        height: 100%;
        border-right: heavy $secondary;
        padding: 1;
    }
    """
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
        Binding(key="n", action="create_file", description="Create new file", key_display="N"),
        Binding(key="shift+n", action="create_folder", description="Create new folder", key_display="Shift+N"),        
    ]

    def __init__(self, path="."):
        super().__init__()
        self.path = path

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            yield Directory(self.path)
            yield IronEdit.code_editor()
            yield RichLog(id="log")
        yield Footer(show_command_palette=True)

    def on_mount(self) -> None:
        self.title = "IronEdit"
        editor = self.query_one(IronEdit)
        editor.focus()

    def action_create_file(self) -> None:
        self.push_screen(CreateFileModal())
    
    def action_create_folder(self) -> None:
        self.push_screen(CreateFolderModal())
    

def main():
    parser = argparse.ArgumentParser(description="IronEdit Text Editor")
    parser.add_argument("path", nargs="?", default=os.getcwd(), help="Path to the directory to open")
    args = parser.parse_args()
    app = TextAreaExample(path=args.path)
    app.run()


if __name__ == "__main__":
    main()
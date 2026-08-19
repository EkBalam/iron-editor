import dataclasses
from textual.binding import Binding
from textual.message import Message
from textual.widgets import TextArea
import random
import pathlib
from iron_editor.components.signer import sign_content, strip_and_verify, load_identity


class IronEdit(TextArea):

    class TitleChanged(Message):
        def __init__(self, editor: "IronEdit", has_unsaved: bool) -> None:
            super().__init__()
            self.editor = editor
            self.has_unsaved = has_unsaved

    class LogRequested(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    BINDINGS = [
        Binding(key="shift+n", action="none", show=False),
        Binding(key="ctrl+s", action="save", description="Save current file", key_display="Ctrl+S", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = ""
        self.language = "python"
        self.theme = "dracula"
        self.show_line_numbers = True
        self.current_file = None
        self._saved_text = ""

    def _has_unsaved_changes(self) -> bool:
        return self.current_file is not None and self.text != self._saved_text

    def _update_save_binding_visibility(self) -> None:
        show_save = self._has_unsaved_changes()
        key = "ctrl+s"
        if key in self._bindings.key_to_bindings:
            new_list = [
                dataclasses.replace(b, show=show_save and bool(b.description))
                for b in self._bindings.key_to_bindings[key]
            ]
            self._bindings.key_to_bindings[key] = new_list
            self.refresh_bindings()
        self.post_message(self.TitleChanged(self, show_save))

    def on_text_area_changed(self) -> None:
        self._update_save_binding_visibility()

    def _on_paste(self, event):
        text = event.text
        lines = text.splitlines()
        random.shuffle(lines)
        shuffled = []
        for line in lines:
            words = line.split(" ")
            random.shuffle(words)
            scrambled_words = []
            for word in words:
                chars = list(word)
                random.shuffle(chars)
                scrambled_words.append("".join(chars))
            shuffled.append(" ".join(scrambled_words))
        event.text = "\n".join(shuffled)
        return super()._on_paste(event)

    def _log(self, text: str) -> None:
        self.post_message(self.LogRequested(text))

    def open_file(self, path: str) -> None:
        self._log(f"Attempting to open file: {path}")
        try:
            p = pathlib.Path(path)
            if p.is_file():
                raw_content = p.read_text(encoding="utf-8")
                ext = p.suffix.lower()
                _, secret_key = load_identity()
                clean_content, has_sig, is_valid, signer_id = strip_and_verify(
                    raw_content, p.name, ext, secret_key
                )
                if not has_sig:
                    self.app.notify(
                        "Este archivo no tiene firma de IronEdit y no puede abrirse.",
                        title="Bloqueado: Sin firma",
                        severity="error",
                        timeout=6,
                    )
                    self._log(f"Bloqueado (sin firma): {path}")
                    return
                if not is_valid:
                    self.app.notify(
                        "La firma del archivo es inválida. Pudo haber sido modificado externamente.",
                        title="Bloqueado: Firma inválida",
                        severity="error",
                        timeout=6,
                    )
                    self._log(f"Bloqueado (firma inválida): {path}")
                    return
                self.text = clean_content
                self.current_file = str(p)
                self._saved_text = self.text
                self.language = self.__get_language_from_extension(p.suffix)
                self._log(f"Abierto: {path} | Lenguaje: {self.language} | Firmado por: {signer_id or 'default'}")
                self._update_save_binding_visibility()
        except Exception as e:
            self._log(f"Error opening file: {e}")

    def action_save(self) -> None:
        self.save_file()

    def save_file(self) -> None:
        if self.current_file:
            try:
                p = pathlib.Path(self.current_file)
                ext = p.suffix.lower()
                student_id, secret_key = load_identity()
                signed_text = sign_content(self.text, p.name, ext, secret_key, student_id)
                p.write_text(signed_text, encoding="utf-8")
                self._saved_text = self.text
                self._update_save_binding_visibility()
                self._log(f"Guardado: {self.current_file}")
            except Exception as e:
                self._log(f"Error saving file: {e}")
        else:
            self._log("No hay archivo para guardar")

    def __get_language_from_extension(self, ext: str) -> str:
        if not ext:
            return "markdown"
        ext = ext.lower()
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".html": "html",
            ".css": "css",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".json": "json",
            ".md": "markdown",
        }
        return extension_map.get(ext, "markdown")

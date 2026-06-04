"""Terminal widget — ejecución interactiva de comandos."""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import RichLog, Static


class TerminalWidget(Vertical):
    DEFAULT_CSS = """
    TerminalWidget {
        height: 12;
        min-height: 4;
        border-top: heavy $secondary;
        padding: 0 1;
    }
    TerminalWidget #terminal_output {
        height: 1fr;
    }
    TerminalWidget #terminal_input_line {
        height: 1;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("ctrl+r", "run_current_file", "Run file", show=True),
        Binding("ctrl+c", "stop_process", "Stop", show=True),
        Binding("ctrl+l", "clear", "Clear", show=True),
        Binding("ctrl+up", "grow", "Más alto", show=True),
        Binding("ctrl+down", "shrink", "Más bajo", show=True),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_dir = os.getcwd()
        self.process: subprocess.Popen | None = None
        self.output_thread: threading.Thread | None = None
        self.input_buffer = ""
        self._history: list[str] = []
        self._history_pos = -1

    def compose(self) -> ComposeResult:
        yield RichLog(id="terminal_output", markup=True)
        yield Static(self._prompt(), id="terminal_input_line")

    def on_mount(self) -> None:
        self.focus()

    def _prompt(self) -> str:
        short = Path(self.current_dir).name or self.current_dir
        return f"[bold cyan]{short}$[/bold cyan] {self.input_buffer}"

    def _update_prompt(self) -> None:
        self.query_one("#terminal_input_line", Static).update(self._prompt())

    def on_key(self, event: events.Key) -> None:
        key = event.key
        character = event.character

        # Consume el evento — evita que bindings del App se activen.
        # Excepción: ctrl+t lo dejamos burbujear para que el App pueda cerrar el terminal.
        if key not in ("ctrl+t", "ctrl+up", "ctrl+down"):
            event.stop()

        # Proceso corriendo — siempre permitir escribir
        if self.process and self.process.poll() is None:
            if key == "ctrl+c":
                self.action_stop_process()
            elif key == "enter":
                self._send_to_process(self.input_buffer)
            elif key == "backspace":
                self.input_buffer = self.input_buffer[:-1]
                self._update_prompt()
            elif character and character.isprintable():
                self.input_buffer += character
                self._update_prompt()
            return

        # Sin proceso corriendo: modo comando
        if key == "enter":
            cmd = self.input_buffer.strip()
            if cmd:
                self._history.append(cmd)
                self._history_pos = -1
                log = self.query_one("#terminal_output", RichLog)
                log.write(f"[bold cyan]{Path(self.current_dir).name}$[/bold cyan] {cmd}")
                self.input_buffer = ""
                self._update_prompt()
                self._dispatch(cmd)
            event.prevent_default()

        elif key == "backspace":
            self.input_buffer = self.input_buffer[:-1]
            self._update_prompt()
            event.prevent_default()

        elif key == "up":
            if self._history:
                self._history_pos = min(self._history_pos + 1, len(self._history) - 1)
                self.input_buffer = self._history[-(self._history_pos + 1)]
                self._update_prompt()
            event.prevent_default()

        elif key == "down":
            if self._history_pos > 0:
                self._history_pos -= 1
                self.input_buffer = self._history[-(self._history_pos + 1)]
            else:
                self._history_pos = -1
                self.input_buffer = ""
            self._update_prompt()
            event.prevent_default()

        elif character and character.isprintable():
            self.input_buffer += character
            self._update_prompt()
            event.prevent_default()

    def _dispatch(self, cmd: str) -> None:
        """Maneja builtins o delega al sistema."""
        parts = cmd.split()
        if not parts:
            return

        if parts[0] == "cd":
            self._builtin_cd(parts[1] if len(parts) > 1 else str(Path.home()))
        elif parts[0] == "clear" or parts[0] == "cls":
            self.action_clear()
        else:
            self._run_external(cmd)

    def _builtin_cd(self, target: str) -> None:
        log = self.query_one("#terminal_output", RichLog)
        try:
            new_path = Path(self.current_dir) / target if not Path(target).is_absolute() else Path(target)
            new_path = new_path.resolve()
            if new_path.is_dir():
                self.current_dir = str(new_path)
                self._update_prompt()
            else:
                log.write(f"[red]cd: no existe: {target}[/red]")
        except Exception as e:
            log.write(f"[red]cd: {e}[/red]")

    def _run_external(self, command: str) -> None:
        log = self.query_one("#terminal_output", RichLog)
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=self.current_dir,
                env=env,
            )
            self.input_buffer = ""
            self.output_thread = threading.Thread(
                target=self._read_output, daemon=True
            )
            self.output_thread.start()
        except Exception as e:
            log.write(f"[red]✗ {e}[/red]")
            self.process = None

    def _send_to_process(self, text: str) -> None:
        log = self.query_one("#terminal_output", RichLog)
        try:
            self.process.stdin.write(text + "\n")
            self.process.stdin.flush()
            log.write(f"[bold green]{text}[/bold green]")
            self.input_buffer = ""
            self._update_prompt()
        except Exception as e:
            log.write(f"[red]Error enviando input: {e}[/red]")

    def _read_output(self) -> None:
        """Lee stdout del proceso en un hilo separado."""
        if not self.process:
            return
        log = self.query_one("#terminal_output", RichLog)
        try:
            buffer = ""
            chars_no_newline = 0
            while self.process.poll() is None:
                try:
                    ch = self.process.stdout.read(1)
                    if not ch:
                        break
                    buffer += ch
                    chars_no_newline += 1
                    if ch == "\n":
                        self.app.call_from_thread(log.write, buffer.rstrip("\r\n"))
                        buffer = ""
                        chars_no_newline = 0
                    elif buffer.endswith(": ") or chars_no_newline > 80:
                        self.app.call_from_thread(log.write, buffer)
                        buffer = ""
                        chars_no_newline = 0

                except Exception:
                    time.sleep(0.01)

            try:
                remaining = self.process.stdout.read()
                if remaining:
                    buffer += remaining
            except Exception:
                pass

            if buffer:
                for line in buffer.split("\n"):
                    if line:
                        self.app.call_from_thread(log.write, line)

            code = self.process.returncode
            if code == 0:
                self.app.call_from_thread(log.write, "[green]✓ Listo[/green]")
            else:
                self.app.call_from_thread(log.write, f"[yellow]Exit: {code}[/yellow]")
        except Exception as e:
            self.app.call_from_thread(log.write, f"[red]Error: {e}[/red]")
        finally:
            self.process = None
            self.app.call_from_thread(self._update_prompt)

    def action_run_current_file(self) -> None:
        """Corre el archivo del tab activo si es .py."""
        log = self.query_one("#terminal_output", RichLog)
        try:
            from iron_editor.components.ironedit import IronEdit
            from textual.widgets import TabbedContent, TabPane
            tabs = self.app.query_one("#editor-tabs", TabbedContent)
            pane = tabs.get_pane(tabs.active)
            editor = pane.query_one(IronEdit)
            if editor.current_file:
                fp = Path(editor.current_file)
                if fp.suffix == ".py":
                    cmd = f"{sys.executable} \"{fp}\""
                    log.write(f"[bold cyan]{Path(self.current_dir).name}$[/bold cyan] {cmd}")
                    self._run_external(cmd)
                else:
                    log.write("[yellow]Solo archivos .py[/yellow]")
            else:
                log.write("[yellow]No hay archivo abierto[/yellow]")
        except Exception as e:
            log.write(f"[red]✗ {e}[/red]")

    def action_stop_process(self) -> None:
        """Termina el proceso corriendo."""
        if self.process and self.process.poll() is None:
            log = self.query_one("#terminal_output", RichLog)
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
                log.write("[yellow]✓ Proceso terminado[/yellow]")
            except subprocess.TimeoutExpired:
                self.process.kill()
                log.write("[yellow]✓ Proceso eliminado[/yellow]")
            except Exception as e:
                log.write(f"[red]{e}[/red]")
        self.process = None

    def action_clear(self) -> None:
        self.query_one("#terminal_output", RichLog).clear()

    def action_grow(self) -> None:
        self.styles.height = max(4, (self.size.height or 12) + 2)

    def action_shrink(self) -> None:
        self.styles.height = max(4, (self.size.height or 12) - 2)

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Mount
from textual.widgets import Footer, Header, Pretty, SelectionList, Button
from textual.widgets.selection_list import Selection


class PlaylistSelector(App[None]):
    CSS_PATH = "selection_list_selected.tcss"

    def compose(self) -> ComposeResult:
        with Header():
            yield Button("Start", id="start", variant="success")

        with Horizontal():
            yield SelectionList[str](

                Selection("Falken's Maze", "secret_back_door", True),
                Selection("Black Jack", "black_jack"),
                Selection("Gin Rummy", "gin_rummy"),
                Selection("Hearts", "hearts"),
                Selection("Bridge", "bridge"),
                Selection("Checkers", "checkers"),
                Selection("Chess", "a_nice_game_of_chess", True),
                Selection("Poker", "poker"),
                Selection("Fighter Combat", "fighter_combat", True),
                id='playlist_selectlist'
            )
            yield Pretty([])
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one('#playlist_selectlist').select_all()

    def on_mount(self) -> None:
        self.query_one(SelectionList).border_title = "Shall we play some games?"
        self.query_one(Pretty).border_title = "Selected games"

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    def update_selected_view(self) -> None:
        self.query_one(Pretty).update(self.query_one(SelectionList).selected)


if __name__ == "__main__":
    PlaylistSelector().run()
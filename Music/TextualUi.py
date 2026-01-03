from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Mount
from textual.widgets import Footer, Header, Pretty, SelectionList, Button
from textual.widgets.selection_list import Selection


class PlaylistSelector(App[None]):
    CSS_PATH = "selection_list_selected.tcss"

    def __init__(self, playlists):
        super().__init__()
        self.playlists = playlists

    def compose(self) -> ComposeResult:
        with Header():
            yield Button("Start", id="start", variant="success")

        with Horizontal():
            yield SelectionList[str](

                *[Selection(playlist_name,playlist_id) for playlist_name,playlist_id in self.playlists],

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
    test_list =     [("Falken's Maze", 'a'),
                    ("Black Jack", 'g'),
                    ("Gin Rummy",'5'),
                    ("Hearts", 'z'),
                    ("Bridge", 'R')]

    PlaylistSelector(test_list).run()
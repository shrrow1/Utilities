import logging

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.events import Mount
from textual.widgets import Footer, Header, Pretty, SelectionList, Button, Label
from textual.widgets.selection_list import Selection


class PlaylistSelector(App[None]):
    CSS_PATH = "selection_list_selected.tcss"

    def __init__(self, playlists):
        super().__init__()
        self.playlists = playlists
        self.from_playlists=[]
        self.to_playlist=None

    def compose(self) -> ComposeResult:
        yield Header()

        # with Horizontal():
        yield SelectionList[str](

            *[Selection(playlist_name,playlist_id) for playlist_name,playlist_id in self.playlists],

            id='from_playlist'
        )
        yield SelectionList[str](

            *[Selection(playlist_name,playlist_id) for playlist_name,playlist_id in self.playlists],

            id='to_playlist'
        )
        # yield Pretty([])
        yield Button("Do Merge", id="do_merge", variant="success")
        self.message_box = Label()
        yield self.message_box
        yield Footer()


    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.query_one('#from_playlist').select_all()

    def on_mount(self) -> None:
        self.query_one('#from_playlist').border_title = "Source Playlist"
        self.query_one('#to_playlist').border_title = "Target Playlist"
        # self.query_one(Pretty).border_title = "Selected games"

    # @on(Mount)
    # @on(SelectionList.SelectedChanged)
    # def update_selected_view(self) -> None:
    #     self.query_one(Pretty).update(self.query_one(SelectionList).selected)

    @on(SelectionList.SelectedChanged, '#from_playlist')
    def check_selected(self):
        self.from_playlists = []
        sel_playlists = self.query_one('#from_playlist').selected
        if len(sel_playlists) > 2:
            self.message_box.update('Cant have more thatn 2')
        elif len(sel_playlists) == 0:
            self.message_box.update('Must choose 1 or 2')
        else:
            self.from_playlists = sel_playlists
            self.message_box.update()




if __name__ == "__main__":
    test_list =     [("Falken's Maze", 'a'),
                    ("Black Jack", 'g'),
                    ("Gin Rummy",'5'),
                    ("Hearts", 'z'),
                    ("Bridge", 'R')]

    PlaylistSelector(test_list).run()
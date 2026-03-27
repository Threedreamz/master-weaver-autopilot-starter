
from libs.pywinauto.controller import controller
class task:
    con = None
    def __init__(self, name: str, progress: int):
        self.con = controller()

    def choose_profile(self, profile: str):
        print(f"[TASK] Profil wählen: {profile}")
        self.con.profileChooser(profile)
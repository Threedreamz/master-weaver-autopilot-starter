from pywinauto import Application

from libs.pywinauto.process import winWerth_Process

class TreeViewInspector:




    def __init__(self, dlg):
        self.dlg = dlg


    def get_all_treeviews(self):
        """Findet alle TreeView-Elemente im Dialog."""
        return self.dlg.children(control_type="Tree")


    def get_tree_items(self, treeview):
        """Listet alle Items eines TreeView-Elements rekursiv auf."""
        items = []
        try:
            root_items = treeview.children(control_type="TreeItem")
            for root in root_items:
                items.append(root)
                items += self._get_child_items(root)
        except Exception as e:
            print(f"[Fehler] TreeView konnte nicht gelesen werden: {e}")
        return items

    def _get_child_items(self, parent_item):
        """Rekursive Hilfsfunktion für Unterknoten."""
        items = []
        try:
            children = parent_item.children(control_type="TreeItem")
            for child in children:
                items.append(child)
                items += self._get_child_items(child)
        except Exception:
            pass
        return items

    def inspect_all(self):
        """Findet alle TreeViews, deren AutomationId und Name/Text und Items."""
        all_treeviews = self.get_all_treeviews()
        if not all_treeviews:
            print("Keine TreeViews im Dialog gefunden.")
            return

        for t_idx, tv in enumerate(all_treeviews):
            tv_info = tv.element_info
            print("=" * 60)
            print(f"[TreeView {t_idx}]")
            print(f"  AutomationId : {tv_info.automation_id}")
            print(f"  Name/Text    : {tv_info.name}")

            items = self.get_tree_items(tv)
            if not items:
                print("  (Keine Items gefunden)")
                continue

            for i, item in enumerate(items):
                info = item.element_info
                print(f"    [{i}]  AutomationId: {info.automation_id or '-'}")
                print(f"         Name/Text  : {info.name or '-'}")

        print("=" * 60)


# Beispielnutzung:
if __name__ == "__main__":
    # Beispiel (du hast dein dlg schon)
    # app = Application(backend="uia").connect(title_re=".*WinWerth.*")
    # dlg = app.window(title_re=".*WinWerth.*")
    wp = winWerth_Process()
    wp.connect()
    inspector = TreeViewInspector(wp.dlg)
    inspector.inspect_all()

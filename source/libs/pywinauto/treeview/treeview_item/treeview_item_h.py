from pywinauto.controls.uia_controls import TreeViewWrapper

class treeview_item_h:
    def click_tree_item(self, dlg, item_text: str = "ENDFIL"):
        """
        Findet im übergebenen Dialog `dlg` ein TreeView-Control und klickt das Item mit dem Text `item_text` an.
        Führt einen echten linken Mausklick aus.
        """
        try:
            # TreeView suchen (UIA-Backend)
            tree = dlg.child_window(control_type="Tree", found_index=0).wrapper_object()

            if not isinstance(tree, TreeViewWrapper):
                print("[x] Kein TreeView-Element gefunden.")
                return False

            # Item suchen
            item = tree.get_item([item_text])
            if not item:
                print(f"[x] Item '{item_text}' nicht gefunden.")
                return False

            # Auswählen und anklicken
            item.select()
            item.click_input()
            print(f"[OK] '{item_text}' wurde angeklickt.")
            return True

        except Exception as e:
            print(f"[x] Fehler beim Klicken auf '{item_text}': {e}")
            return False

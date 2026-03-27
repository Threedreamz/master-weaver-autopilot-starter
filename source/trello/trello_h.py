from trello.trello_config import trello_config
import requests
import json
from typing import Optional, Any
import sys

class trello_h:
    """
    Minimalistische Trello Helper Klasse.
    Alle API Calls laufen über _request().
    """

    def __init__(self):
        self.config = trello_config()
        self.api_key = self.config.get_api_key()
        self.api_token = self.config.get_token()
        self.base_url = "https://api.trello.com/1"
        self.lists = {
            "queue": "690c8cd55903bd7892d2f7a2",
            "auftrag": "690c8f6ae371f8239995c4a8",
            "fertig": "690d42e9f65eb01f947852f0",
            "defect": "690d42ec4e43c528ca339353"
        }

    # -------------------------------------------------
    # INTERNES HILFSTOOL
    # -------------------------------------------------
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Any]:
        url = f"{self.base_url}{endpoint}"
        params = kwargs.get("params", {})
        params.update({"key": self.api_key, "token": self.api_token})
        kwargs["params"] = params

        try:
            resp = requests.request(method, url, **kwargs)
            resp.raise_for_status()
            if resp.text:
                return resp.json()
            return None
        except Exception as e:
            print(f"[TRELLO] Fehler bei {method.upper()} {endpoint}: {e}")
            return None

    # -------------------------------------------------
    # GENERISCHE LISTEN-/KARTEN-HILFEN
    # -------------------------------------------------
    def _get_list_cards(self, list_id: str):
        return self._request("GET", f"/lists/{list_id}/cards")

    def _move_card(self, card_id: str, list_id: str):
        return self._request("PUT", f"/cards/{card_id}", params={"idList": list_id})

    def _make_comment(self, card_id: str, text: str):
        return self._request("POST", f"/cards/{card_id}/actions/comments", params={"text": text})

    def _upload_attachment(self, card_id: str, file_path: str):
        with open(file_path, "rb") as f:
            return self._request("POST", f"/cards/{card_id}/attachments", files={"file": f})

    # -------------------------------------------------
    # KOMMENTAR FUNKTIONEN
    # -------------------------------------------------
    def getComments(self, card_id: str):
        """
        Gibt alle Kommentare einer Karte zurück.
        """
        comments = self._request("GET", f"/cards/{card_id}/actions", params={"filter": "commentCard"})
        return comments if comments else []

    def getCommentX(self, card_id: str) -> bool:
        """
        Prüft, ob bereits ein Kommentar mit 'X' existiert.
        """
        comments = self.getComments(card_id)
        for c in comments:
            text = c.get("data", {}).get("text", "")
            if text.strip().upper() == "X":
                return True
        return False

    def countComments(self, card_id: str) -> bool:
        """
        Prüft, ob bereits ein Kommentar mit 'X' existiert.
        """
        comments = self.getComments(card_id)
        return len(comments)


    def markXComment(self, card_id: str):
        """
        Markiert Karte mit 'X', aber nur einmalig.
        """
        if self.getCommentX(card_id):
            print(f"⚠️ Karte {card_id} hat bereits ein X-Kommentar. Kein weiteres hinzugefügt.")
            return None
        return self._make_comment(card_id, "X")

    # -------------------------------------------------
    # AUFTRAGSLOGIK
    # -------------------------------------------------
    def queueGetNext(self):
        cards = self._get_list_cards(self.lists["queue"])
        return cards[0] if cards else None

    def getAuftrag(self):
        cards = self._get_list_cards(self.lists["auftrag"])
        if not cards:
            return None

        card = cards[0]
        return {
            "id": card.get("id"),
            "name": card.get("name"),
            "desc": card.get("desc")
        }


    def getSize(self):
        auftr = self.getAuftrag()
        json_dump = json.loads(auftr['desc'])
        return json_dump['size']

    def getStatus(self):
        auftr = self.getAuftrag()
        json_dump = json.loads(auftr['desc'])
        return json_dump['status']
    
    def getAuftragsId(self):
        auftr = self.getAuftrag()
        json_dump = json.loads(auftr['desc'])
        return json_dump['id']
    

    def addQueue_(self, id: str, auftragId: str, size: str):

        data = {
            "idList": self.lists["queue"],
            "name": f"{auftragId} | {id} | {size}",
            "desc": json.dumps({"id": id, "auftragId": auftragId, "size": size, "status": "ready to start"}),
        }
        return self._request("POST", "/cards", params=data)

    def moveToAuftrag(self, card_id: str):
        if not self.getAuftrag() == None:
            print("there exists a 'Auftrag' already..")
            return None
        return self._move_card(card_id, self.lists["auftrag"])

    def moveToFertig(self, card_id: str):
        return self._move_card(card_id, self.lists["fertig"])

    def moveToDefect(self, card_id: str):
        return self._move_card(card_id, self.lists["defect"])

    def UploadSTL(self, card_id: str, stlPath: str):
        return self._upload_attachment(card_id, stlPath)

    def makeComment(self, card_id: str, comment: str):
        return self._make_comment(card_id, comment)

    # -------------------------------------------------
    # OPTIONAL
    # -------------------------------------------------
    def get_first_card_from_list(self, list_id: str):
        cards = self._get_list_cards(list_id)
        if not cards:
            print(f"⚠️ Keine Karten in Liste {list_id}.")
            return None
        first = cards[0]
        print(f"🟩 Erste Karte: {first['name']} (ID: {first['id']})")
        return first

    def getLastComment(self, card_id: str) -> Optional[str]:
        """
        Gibt den Text des neuesten Kommentars einer Karte zurück (oder None, falls keine vorhanden sind).
        """
        comments = self.getComments(card_id)
        return comments[0].get("data", {}).get("text", "") if comments else None

    def get_latest_comment(self, card_id: str) -> Optional[str]:
        """
        Gibt den neuesten Kommentar (Text) einer Karte zurück.
        """
        actions = self._request(
            "GET",
            f"/cards/{card_id}/actions",
            params={"filter": "commentCard"}
        )

        if not actions:
            return None

        # Kommentare sind chronologisch, letzter = neuester
        latest_comment = actions[0] if isinstance(actions, list) and len(actions) > 0 else None
        return latest_comment["data"]["text"] if latest_comment else None

import os


class trello_config:
    def __init__(self):
        self.api_key = os.environ.get("TRELLO_API_KEY", "")
        self.list_id = os.environ.get("TRELLO_LIST_ID", "")  # Queue_Liste
        self.token = os.environ.get("TRELLO_TOKEN", "")
        self.url = "https://api.trello.com/1/cards"


    def get_api_key(self):
        return self.api_key
        
    def get_token(self):
        return self.token
    def get_list_id(self):
        return self.list_id
    def get_url(self):
        return self.url

    
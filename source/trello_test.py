from trello.trello import trello
import json
tr = trello()


print(json.loads(tr.getAuftrag()['desc'])['size'])
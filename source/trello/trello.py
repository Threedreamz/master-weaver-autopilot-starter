from .trello_h import trello_h

class trello:


#
# webui -> erstelle queue item
#           -> move to auftrag
#               -> comment X
#               -> comment start
#               -> comment setup -> profile
#               -> upload STL
#           -> move to fertig
#       
# webui <- get Status
#       <- is auftrag
#       <- get Id / Size / AuftragsId
##

    #
    #   -- get current auftrag
    #   -- get current queue
    #   -- add queue
    #   -- moveAuftrag
    #   
    ##
    #
    #   self.getQueue_Item()
    #   self.getCurrentComment(queue_item['id']))
    #   self.getAuftrag()

    def test(self):

        queue_item = self.getQueue_Item()
        print("Marked with X?: ", self.isMarkedX())
        print(self.th.getCommentX(queue_item['id']))
        auftrag = self.getAuftrag()
        print(auftrag)
        #print(self.th.get_latest_comment(auftrag["id"]))
       
     #   markedAuftrag = self.markAuftrag(card["id"])
     #   print(self.getCurrentComment(cardid=card["id"]))
     #   move = self.moveToAuftrag(card["id"])

    def getQueue_Item(self):
        list_id = "690c8cd55903bd7892d2f7a2"  # Queue_ Liste
        card = self.th.get_first_card_from_list(list_id)
        if card:
            print("➡️ Karte:", card["name"])
            print("🔗 URL:", card["url"])
        return card
    
    def getAuftragStatus(self):
        auftrag = self.th.getAuftrag()
        return self.th.get_latest_comment(auftrag["id"])


    def __init__(self):
        self.th = trello_h()


    def getLastComment(self, card_id):
        return self.th.getLastComment(card_id)

    def getAuftrag(self):
        return self.th.getAuftrag()

    def getProfile(self):
        return self.th.getSize()

    def markAuftrag( self, cardId):
        self.th.markXComment(cardId)

    def markQueue( self, cardId):
        self.th.markXComment(cardId)


    def addQueue_(self, id, auftragId, size):
        self.th.addQueue_(id, auftragId, size)
        item = self.getQueue_()
        self.markAuftrag(item['id'])
        return self.getQueue_()
    def getQueue_(self):
        return self.getQueue_Item()
    def isMarkedX(self):
        queue_item = self.getQueue_Item()
        return (self.th.getCommentX(queue_item['id']))

    def isOnlyMarkedX(self, auftrag):
        print(self.th.countComments(auftrag["id"]))
        if self.th.countComments(auftrag["id"]) > 1:
            return False
        else:
            return True
        


    def makeComment(self, card_id, comments):
        return self.th.makeComment(card_id,comments)

    def setState(self, state):
        auftrag_id = self.getAuftrag()['id']
        return self.th.makeComment(auftrag_id, state)

    def uploadSTL(self, cardId, stlPath):
        self.th.UploadSTL(cardId, stlPath)   

    def moveToFertig(self, cardId):
        self.th.moveToFertig(cardId)
    
    def moveToAuftrag(self, auftragId):
        self.th.moveToAuftrag(auftragId)
    
    def moveToDefect(self, auftragId):
        return self.th.moveToDefect(auftragId)
    
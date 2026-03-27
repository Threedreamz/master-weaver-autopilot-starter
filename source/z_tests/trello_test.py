from trello.trello_class import trello_class

tc = trello_class()


auftr = tc.getAuftrag()
tc.checkDefect()
tc.prepAuftrag(auftr)





tc.prozessStepSet(1)
tc.prozessStepSet(2)
tc.prozessStepSet(3)

#tr.makeComment(auftrag["id"], " sd ")





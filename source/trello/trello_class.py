from .trello import trello

from time import sleep

class trello_class:


    #simulate flow
    def __init__(self):
        self.tr = trello()
    #add Queue
    #tr.addQueue_("bsdv3waaw", "3dz-000032", "l")

        #
    #   leeren auftrag checken, coment statt stl
    #
    #
    def addQueue(self):
        return self.tr.addQueue_("11", "22", "m")
    def addAuftrag(self, id, auftragid, size):
        queue = self.tr.getQueue_Item()
        auftrag = self.tr.getAuftrag()
        if queue:
            #return none for choosing between continuing
            self.tr.moveToDefect(queue['id'])
        if auftrag:
            self.tr.moveToDefect(auftrag['id'])
        
        item = self.tr.addQueue_(id, auftragid, size)
        print(item['id'])
        self.tr.moveToAuftrag(item['id'])
        return self.tr.getAuftrag()
    
    #
    def getAuftrag(self):
        return self.tr.getAuftrag()
    def getQueue(self):
        return self.tr.getQueue_Item()
    # solange nicht auftrag zu ende...
    def checkDefect(self):
        auftrag = self.tr.getAuftrag()
        if auftrag == None:
            return None
        if not self.tr.isOnlyMarkedX(auftrag):
            print(self.tr.moveToDefect(auftrag["id"]))
        sleep(2)
    #
    #
    def moveToDefect(self, auftrags_id):
        return self.tr.moveToDefect(auftrags_id)  
    def prepAuftrag(self,auftrag):
        #setzte auftrag falls keiner existiert
        if auftrag == None:
            
            queue_i = self.tr.getQueue_Item()
            
            if queue_i == None:
                raise Exception("queue empty")
            
            if not self.tr.isMarkedX():
                self.tr.markQueue(queue_i["id"])

            self.tr.moveToAuftrag(queue_i["id"])

        

    def getprozessStep(self):
        self.tr.getAuftragStatus()

    #for the server
    def prozessStepSet(self, step):
        auftrag_current = self.tr.getAuftrag()
        if auftrag_current == None:
            print("auftrag is empty")
            return
        auftrag_id = auftrag_current["id"]
        current_status = self.tr.getLastComment(auftrag_id)

        # Alle möglichen Befehle in Reihenfolge
        befehle = [
            "start_flow",
            "start_rec",
            "chooseProfile",   # Sonderfall
            "setup",
            "getBoxValues",
            "createBox",
            "startScan",
            "waitForScanDone",
            "exportScan",
            "done"
        ]

        # Ungültigen Step abfangen
        if step < 1 or step > len(befehle):
            print(f"[!] Ungültiger Step: {step}")
            return

        befehl = befehle[step - 1]  # Step 1-basiert → Listenindex 0-basiert

        # === Schutzmechanismus ===
        if step > 1:  # Es gibt einen Vorgänger
            vorgaenger = befehle[step - 2]
            if not (current_status == vorgaenger):
                print(f"[!] Schutz: aktueller Status '{current_status}' != Vorgänger '{vorgaenger}' → moveToDefect()")
                self.tr.moveToDefect(auftrag_id)
                return

        # === Normale Logic ===
        match befehl:
            case "chooseProfile":
                profile_name = (auftrag_current["name"].split("|"))[2]
                self.tr.makeComment(auftrag_id, f"{befehl}:{profile_name}")
                print(f"{befehl} ({profile_name}) {step}")
            case _:
                self.tr.makeComment(auftrag_id, befehl)
        print(f"{befehl} {step}")





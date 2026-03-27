from libs.pseudo_pipe.pseudi_pipe_h import pseudi_pipe_h


class pywin_pipe:

    #   
    #   Wrapper für pseudi_pipe_h
    #   
    #   principle:
    #      1. 

    def __init__(self): 
        self.psh = pseudi_pipe_h()
    
    
<<<<<<< HEAD
    def choose_profile(self, dlg,  profile_name):
        return self.psh.choose_profile(dlg, profile_name)
=======
    def choose_profile(self, profile_name):
        return self.psh.selectProfile(profile_name)
>>>>>>> 52f48f067ab5d14a5c96e6843131751f06aad838
    
    def setup(self):
        return self.psh.setup()
    
    def getBoxValues(self):
        return self.psh.getValueBox()
    
    def createBox(self, box_values):
        return self.psh.createBox(box_values)
    
    def startScan(self):
        return self.psh.startScan()
    
    def waitForScanDone(self):
        return self.psh.waitForScanToComplete()
    
<<<<<<< HEAD
    def prepareExport(self):
        pass
        #return self.psh.prepareExport()

    def exportScan(self):
        return self.psh.saveSTL("testfile")
=======
    def exportScan(self, name):
        return self.psh.saveSTL(name)
>>>>>>> 52f48f067ab5d14a5c96e6843131751f06aad838
    
    
    def saveSTL(self, filename="testfile"):
        return self.psh.saveSTL(filename)


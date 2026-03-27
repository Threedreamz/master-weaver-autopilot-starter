from libs.pywinauto.punkte_Menu.punkte_Menu_e import punkte_Menu_

from libs.pywinauto.punkte_Menu.punkteMenu_h import punkteMenu_h

from libs.pywinauto.button.button import ButtonPresser


class punkte_Menu:

    pk_e = punkte_Menu_()
    pk_h = punkteMenu_h()
    btnP = ButtonPresser()
    


    #
    #   PROBLEM FOUND
    #       trying to check lable availability
    #       checkMenuCT: True
    #       trying to check lable availability
    #       checkMenuHand: True
    #
    #
    ##

    
    def selectMenuById(self, auto_id, dlg):
        self.btnP.press_by_automation_id(auto_id, dlg)

    def selectMenuByIndex(self, index, dlg):
        self.btnP.press_by_index(index, dlg)

    
    def checkMenuMessfleck(self, dlg_desc):
        print("trying to check lable availability")
        return self.pk_h.isButtonAvailableText(text=self.pk_e.tab_MessFleck["detection"]["text"],dlg_desc=dlg_desc)
    
    def checkMenuCT(self, dlg_desc):
        print("trying to check lable availability")
        return self.pk_h.isButtonAvailableText(text=self.pk_e.tab_CT["detection"]["text"],dlg_desc=dlg_desc)
    
    def checkMenuHand(self, dlg_desc):
        print("trying to check lable availability")
        return not self.pk_h.isButtonAvailableId(id_=self.pk_e.tab_Hand["detection"]["id"],dlg_desc=dlg_desc)

    def checkMenuRechnen(self, dlg_desc):
        print("trying to check lable availability")
        return self.pk_h.isButtonAvailableId(id_=self.pk_e.tab_Rechnen["detection"]["id"],dlg_desc=dlg_desc)
   



    def detectMenu(self, dlg):
        dlg_desc = dlg.descendants(control_type="Button")
        if self.checkMenuMessfleck(dlg_desc):
            return "Messfleck"
        elif self.checkMenuCT(dlg_desc): 
            return "CT"
        elif self.checkMenuHand(dlg_desc):
            return "Hand"
        elif self.checkMenuRechnen(dlg_desc):
            return "Rechnen"
        else:
            return None
        
    def clickTabByName(self, tabName):
        
        if tabName == "Messfleck":
            self.clickTab(self.pk_e.tab_MessFleck["button_Messfleck"]["text"])
        elif tabName == "CT":
            self.clickTab(self.pk_e.tab_CT_Sensor_Unique_Exists["text"])
        elif tabName == "Hand":
            self.clickTab(self.pk_e.tab_Handeingabe_Unique_NotExists["id"])
        elif tabName == "Rechnen":
            self.clickTab(self.pk_e.tab_Rechnen_Unique_Exists["id"])

        else:
            print(f"Error : cant find tab by name {tabName}")


    def clickTab(self, tabName, dlg):
        current_Tab = self.detectMenu(dlg)
        if not (current_Tab == None) and current_Tab == tabName:
            print(f"Already selected the tab : {tabName}")
            return True
        index = self.btnIndexByTab(tabName, current_Tab)
        
        print(f"Current Tab : {current_Tab}\nTarget Tab: {tabName}\nIndex : {index}")
        
        return self.btnP.press_by_index(index, dlg)



    

    def btnIndexByTab(self, tabName, current_Tab):
        result_index = 0
        if tabName == "Messfleck":
            result_index = 77
        if tabName == "CT":
            result_index = 78
        if tabName == "Hand":
            result_index = 79
        if tabName == "Rechnen":
            result_index = 80
        if current_Tab == "Rechnen":
            result_index += 2
        return result_index
    


    
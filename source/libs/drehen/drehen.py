from libs.pywinauto.button.button import ButtonPresser
from libs.pywinauto.process import winWerth_Process

from libs.pywinauto.textbox.textBox import TextBox_method

#Methods
from libs.pywinauto.textbox.textBox import TextBox_method
from libs.pywinauto.tabcontrol.tabcontrol import tabcontrol
from libs.pywinauto.tabcontrol.tabcontrol_e import tabcontrol_e





from libs.pywinauto.button.buttons_e import buttons
from libs.pywinauto.label.label_e import label_e


from time import sleep
class drehen:
#   Process
    winWerth = winWerth_Process()
    #winWerth.init()

#   Elements
    tab_element = tabcontrol_e()
    label_element = label_e()
    button_element = buttons()


#   Element Handlers/Functions
    btn_press = ButtonPresser()
 
    tbm = TextBox_method()


#   pywinauto classen
    tabcontrol = tabcontrol()
##

  
    drehen_tab = tab_element.drehen_tab
 



    def drehen(self, value=360):
        timeout = 60
        time_count = 0
        self.winWerth.connect()

        self.btn_press.press(self.winWerth.dlg,automation_id=self.drehen_tab["id"])

        if self.tabcontrol.checkTabDrehen_byLabel(A_Label_Drehen=self.label_element.A_Label_Drehen, dlg_=self.winWerth.dlg):
            print("checked tab Drehen")
            
            if float(self.tbm.getA_State_Value(dlg=self.winWerth.dlg)) >0.002:
                self.tbm.setAValue(0, self.winWerth.dlg)
                self.btn_press.press(self.winWerth.dlg, automation_id=self.button_element._tab_start["id"])
                while self.tbm.getA_State_Value(dlg=self.winWerth.dlg) != '':
                    sleep(1)
                    time_count += 1
                    if timeout == time_count:
                         print(f"TIMEOUT : couldnt set A to value 0 (reset) within {timeout} seconds")
            
            if self.tbm.setAValue(value, self.winWerth.dlg):
                if self.btn_press.press(self.winWerth.dlg, automation_id=self.button_element._tab_start["id"]):
                    
                    while self.tbm.getA_State_Value(dlg=self.winWerth.dlg) == '':
                        sleep(1)
                        time_count += 1
                        if timeout == time_count:
                            print(f"TIMEOUT : couldnt set A to value 360 (reset) within {timeout} seconds")
                    if float(self.tbm.getA_State_Value(dlg=self.winWerth.dlg)) >= float(value):
                        print("SUCCESS!")
                    #check if value is already 360 #entweder über second_textboxA oder über Tab_Positionsanzeige->A_label
                    return True
        else:
            print(f"Error: could'nt set the value to the textbox with id {self.label_element.A_Label_Drehen} ")
            return False
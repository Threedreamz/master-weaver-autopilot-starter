#
#
#
from app.runner import run_app
#
#    76 messfleckensensor
#    77 ct - profile btn, 
#    78 hände
#    79 rechnen
#
#
#   Rechnen TAB -
#       Wichtige buttons ::
#           [113] AutomationID: '1000' | Text: 'Messen'
#       
#       Detection Buttons ::
#           automationid [111] AutomationID: '32806' | Text: 'Kreispunkt'
#
#   Handeingabe TAB-
#       Detection Buttons ::
#           
#       Detection Inverse ::
#           . no button with automation_id "UpButton" [93] AutomationID: 'UpButton' | Text: 'Bildlauf nach links'
#
#   CT-Sensor
#       Detection Buttons ::
#           [77] AutomationID: '' | Text: 'CT-Sensor'
#
#   Flecksensor
#       Detection Buttons ::
#           [76] AutomationID: '' | Text: 'Messflecksensor'
#
##
#
#   Tab detection ->
#
#
#
import sys

import threading

from PySide6.QtWidgets import QApplication

from gui.ui.main_window import MainWindow


from libs.pywinauto.process import winWerth_Process 
from pywinauto import findwindows, Application
import re

#from libs.pseudo_pipe.pywin_pipe  import pywin_pipe

#from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu

#from libs.pywinauto.profile.profile import profile

from time import sleep
from network_lib.server.server import Server

def main():
 #   srv = Server()
  #  srv_thread = threading.Thread(target=srv.start_server, daemon=True)
  #  srv_thread.start()


    # Blockiere Main-Thread, damit das Programm läuft
  #  try:
     #   while True:
     #       sleep(1)
   # except KeyboardInterrupt:
   #     print("Beendet durch Benutzer.")
    #    srv.stop_server()
   
   # getTxtBox(dlg=dlg)
 #   pk = punkte_Menu()
    
  #  winWerth = winWerth_Process()
  #  winWerth.init()
    
  #  pr = profile()


#selectListBoxItemByText
   # ff =  pr.find_ct_sensor(winWerth.dlg)
  #  print(ff)
  #  if ff == None:
   #     print("Cant find CT Sensor profile window")
  #  else:
    #    print("found CT Sensor window")
    #    window = pr.getCTSensorDlg(winWerth.dlg)
        
      #  pr.closeWindow(window, winWerth.dlg)
        
        #er = pr.selectListBoxItemByText(window, "Size_110_L")
        
        #print(f"rsultat: {er}")
        
        #print(pr.showButtons(window))
 #   print(f"THE DETECTION SAIYS : {pk.detectMenu(dlg=winWerth.dlg)}")




    # # Beispielaufrufe
    # e1 = pk.checkMenuMessfleck(winWerth.dlg)
    # print("checkMenuMessfleckr:", e1)

    # e2 = pk.checkMenuCT(winWerth.dlg)
    # print("checkMenuCT:", e2)

    # e3 = pk.checkMenuHand(winWerth.dlg)
    # print("checkMenuHand:", e3)

    # e4 = pk.checkMenuRechnen(winWerth.dlg)
    # print("checkMenuRechnen:", e4)


   # pipe = pywin_pipe()
    
    # while True:
    #     eing = input("Wähle inde von x: ")
        
    #     if "exit" in (eing):
    #         return
      #  pipe.pressButton(int(eing))

    # while True:
    #     eing_min = input("Wähle inde von x: ")
    #     eing_max = input("Bis :")
    #     for i in range(int(eing_max)):
    #         start = i+int(eing_min)
    #         if "exit" in eing_min or "exit" in eing_max:
    #             return
    #         pipe.pressButton(int(start))
    #         sleep(2)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    main()
    
    #run_app()
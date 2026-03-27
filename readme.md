------ ReamMe.md for Autopilot v1.0 ------
       ----------------------------


#
#
##
#       Idee : ERROR CORRECTION -> Ampere ScrollBar / Voltage ScrollBar als "progressbar" betrachten, somit voll variabel [siehe error_section/error_correction.py]
##
#
#
#
#
#
#
#
#
Version : 1.0
Author  : Jonas Weber (zet0)                 ,-.
Datum   : 11.09.2025                        /°v°\
Name    : Autopilot                        (/   \)
Company : IES Inovative Erodier Systeme     _| |_

-------------------------------------------


Programm zur automatisierung von der winWerth software für CT-Scanner

Idee : Das vollständige automatisieren des visierens, scannens und nachbereiten der STL dateien


Geräte Notwendig: Raspberry Pi 5.0, USB-Cam, Ipdad/Tablet, Service-Machine
----FUTURE TO DO
EMAIL NOTIFICATION : wenn aufwärmzeit vorbei ist.
                   - remote aufwärmen
----
----CURRENT TO DO
COMPLETE SCAN RUN
COMPLETE AFTER SCAN
        -> rechnen
        -> voxel select✅
        -> rechnen
        -> export✅
        -> checkiffileexists✅&size🚨
        -
        -> Design
                -> textbox -> server [groupbox]
                -> 
                -> 
--- Installation Guide ---

####
Für die Service-Maschine : 
Python : v3.13
####
Requirements : 
                1.
                        pip install numpy
                2.
                        pip install opencv-python
                3.
                        pip install mss
                4. 
                        pip install pyautogui
                5.
                        pip install pynput
                6.
                        pip install pywinauto

GUI Requirements :
                1.      
                        pip install PySide6
                2.      
                        pip install PySide6 BlurWindow
                3.      
                        pip install PyQt6
                4.      
                        pip install python -m pip install BlurWindow
                5.      
                        pip install PyQt6-Frameless-Window

                
####
Für Camera-System : 
Python : v3.13
Raspberry Pi 5.0
####
Requirements : 
                1.
                        pip install numpy







#    76 messfleckensensor
#    77 index -Y profile btn, 
#    78 hände
#    79 rechnen
#
#
#   Rechnen TAB -
#       Detection Buttons ::
#           [rechnen_Tab.txt] AutomationID=32807  (key='id:32807')
#               [112] AutomationID: '32807' | Text: '1. Ergebnis'
#           
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

class punkte_Menu_:
    #76 bis 81

    tab_MessFleck = {
        "detection" : {
        "id" : '',
        "text" : "Messflecksensor"
        },
        "button_Messfleck": {
            "id" : '',
            "text" : "Messflecksensor",
            "index" : 76
        },
        "button_CT": {
            "id" : '',
            "text" : "",
            "index" : 77
        },
        "button_Hand": {
            "id" : '',
            "text" : "",
            "index" : 78
        },
        "button_Rechnen": {
            "id" : '',
            "text" : "",
            "index" : 81
        }   
    }


    tab_CT = {
        "detection" : {
            "id" : '',
            "text" : "CT-Sensor"
        },
        "button_Messfleck": {
            "id" : '',
            "text" : "",
            "index" : 76
        },
        "button_CT": {
            "id" : '',
            "text" : "CT-Sensor",
            "index" : 77
        },
        "button_Hand": {
            "id" : '',
            "text" : "",
            "index" : 78
        },
        "button_Rechnen": {
            "id" : '',
            "text" : "",
            "index" : 81
        }   
    }
    tab_Hand = {
        "detection" : {
            "id" : "UpButton",
            "text": "Bildlauf nach links"
        },
        "button_Messfleck": {
            "id" : '',
            "text" : "",
            "index" : 78
        },
        "button_CT": {
            "id" : '',
            "text" : "",
            "index" : 79
        },
        "button_Hand": {
            "id" : '',
            "text" : "",
            "index" : 80
        },
        "button_Rechnen": {
            "id" : '',
            "text" : "",
            "index" : 81
        }   
    }

    tab_Rechnen = {
        "detection": {
            "id" : "32807",
            "text": "1. Ergebnis"
        },
        "button_Messfleck": {
            "id" : '',
            "text" : "Messflecksensor",
            "index" : 76
        },
        "button_CT": {
            "id" : '',
            "text" : "CT-Sensor",
            "index" : 77
        },
        "button_Hand": {
            "id" : '',
            "text" : "",
            "index" : 78
        },
        "button_Rechnen": {
            "id" : '',
            "text" : "",
            "index" : 79
        }
    }

    
 
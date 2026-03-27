

###
#       This file is a part of the pywinauto library and contains various configuration settings and utilities for pywinauto library
#
#
#
###



class PyWinConfig:


    #Program Scan Settings
    EFFICIENT_ROTATION = True
    """Set to True to enable efficient rotation -> using 360 degree and 0 degree instead of 360 degree only"""

    SCHNELLES_LIVE_BILD = True
    """Set to True to enable schnelles life bild """


    #Imageing Profiles
    USING_IMAGING = 0
    """
    0 = blur[low]
    1 = blur[medium]
    2 = blur[high]
    3 = no blur
    """

    ANTI_DONUT = True
    """Set to True to enable anti donut -> detects holes and "fills" them"""





    #Debug Settings
import win32gui
import win32con
import win32ui
import win32api
import time
import numpy as np


'''
Coordinates:
    daily:
        truhla = 240, 638
            collect truhla = 303, 576
        begin battle = 230, 704
            confirm = 225, 624
                2nd begin = 231, 777
                end = 147, 358
        fast rewards = 399, 700
            collect = 297, 538
            end = 189, 689
        friends = 410, 341
            send&receive =  387, 683
        mail = 409, 271
            collect all = 346, 625
            end = 217, 793
        dark forest = 140, 770
            
        
        
            
    
    push:
        next stage = 220, 708

'''
class Routine:
    daily = 1
    labyrinth = 2
    campaign_push = 3


class Bot:

    def click(self, x, y, window_name=None, window_hWnd=None):
        if window_name != 0:
            hWnd = win32gui.FindWindow(None, window_name)
        else:
            hWnd = window_hWnd
        lParam = win32api.MAKELONG(x, y)

        win32gui.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.PostMessage(hWnd, win32con.WM_LBUTTONUP, 0, lParam)

    def post_key(self, key, window_name=None, window_hWnd=None):
        if window_name != 0:
            hWnd = win32gui.FindWindow(None, window_name)
        else:
            hWnd = window_hWnd

        win32api.PostMessage(hWnd, win32con.WM_KEYDOWN, key, lParam_global)
        win32api.PostMessage(hWnd, win32con.WM_KEYUP, key, lParam_global)


    def Daily (self):
        return(None)


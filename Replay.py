import numpy as np
import cv2 as cv
import pyautogui
import time
from PIL import ImageGrab
import win32gui
import win32con
import win32ui
import win32api
import pywinauto
from pynput.mouse import Button, Controller
from Recorder import Recorder
import json
import os
import sys
from windowcapture import WindowCapture


class Replay:

    file_name = None
    file_path = None
    hWnd = None
    window_name = None
    data = []
    meta = []
    wincap = None

    repeatCount = 1
    scanCode = 16
    extended = 0
    context = 0
    previousState = 0
    transition = 0
    lParam_key = repeatCount | (scanCode << 16) | (extended << 24) | (context << 29) | (previousState << 30) | (
                transition << 31)

    def replay_begin(self, routine_f_n, routine_f_p, client_window_name=None, client_hwnd=0):

        self.file_name = routine_f_n
        self.file_path = routine_f_p


        if client_window_name == 0 and client_hwnd == 0:
            print('No client window name or handle.')
            return
        self.window_name = client_window_name
        self.hWnd = client_hwnd
        self.wincap = WindowCapture(self.window_name, self.hWnd)

        with open(self.file_path, 'r') as jsonfile:
            # parse the json
            file = json.load(jsonfile)
            self.data = file['events']
            self.meta = file['meta']

    def replay_action(self, action):
        if action['type'] == 'keyDown':
            key = self.convertKey(action['button'])
            #pyautogui.keyDown(key)
            print("keyDown on {}".format(key))
        elif action['type'] == 'keyUp':
            key = self.convertKey(action['button'])
            pyautogui.keyUp(key)
            print("keyUp on {}".format(key))
        elif action['type'] == 'click':
            self.click(action['pos'][0], action['pos'][1])
            print("click on {}".format(action['pos']))
        elif action['type'] == 'search image':
            self.image_search()
        elif action['type'] == 'click image':
            self.image_click()

    def image_search(self, image_number, image_paths, image_names, click_image_name, click_image_path):
        while True:
            time.sleep(1)
            screen_grab = self.wincap.get_screenshot()

            for needle_name, needle_path in zip(image_names, image_paths):

                cwd = os.getcwd()
                if not needle_path == cwd:
                    try:
                        os.chdir(needle_path)
                    except:
                        print("Something wrong with needle path ({}). specified directory. Exception- ".format(needle_path), sys.exc_info())
                        os.chdir(cwd)
                        print("Restored the directory. Current directory is-", os.getcwd())
                        continue

                needle_img = cv.imread(needle_name, cv.IMREAD_UNCHANGED)

                result = cv.matchTemplate(screen_grab, needle_img, cv.TM_CCOEFF_NORMED)
                threshold = 0.95
                locations = np.where(result >= threshold)
                if locations:
                    self.image_click(click_image_path, click_image_name)
                    print('Image {} found.'.format(needle_name))
                    break
            else:
                continue
            break

    def image_click(self, image_path, image_name):

        screen_grab = self.wincap.get_screenshot()

        cwd = os.getcwd()
        try:
            os.chdir(image_path)
            print("Inserting inside-", os.getcwd())
        except:
            print("Something wrong with needle path ({}). specified directory. Exception- ".format(image_path), sys.exc_info())
            os.chdir(cwd)
            print("Restored the directory. Current directory is-", os.getcwd())

        needle_img = cv.imread(image_name, cv.IMREAD_UNCHANGED)
        result = cv.matchTemplate(screen_grab, needle_img, cv.TM_CCOEFF_NORMED)
        threshold = 0.95
        locations = np.where(result >= threshold)
        if locations:
            needle_w = needle_img.shape[1]
            needle_h = needle_img.shape[0]
            needle_center = (locations[0][0] + (needle_w/2), locations[0][1] + (needle_h/2))
            self.click(needle_center[0], needle_center[1])
        else:
            print('No such image on screen. Image:{0}/{1}'.format(image_path, image_name))

    def click(self, x, y):
        if self.window_name != 0:
            hWnd = win32gui.FindWindow(None, self.window_name)
        else:
            hWnd = self.window_hWnd
        lParam = win32api.MAKELONG(x, y)

        win32gui.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32gui.PostMessage(hWnd, win32con.WM_LBUTTONUP, 0, lParam)

    def key_down(self, key):

        win32api.PostMessage(self.hWnd, win32con.WM_KEYDOWN, key, self.lParam_key)

    def key_up(self, key):

        win32api.PostMessage(self.hWnd, win32con.WM_KEYUP, key, self.lParam_key)

    def replayActions(self):

        for index, action in enumerate(self.data):
            action_start_time = time()

            #if action['button'] == 'Key.esc':
            #    break

            # perform the action
            if action['type'] == 'keyDown':
                key = self.convertKey(action['button'])
                pyautogui.keyDown(key)
                print("keyDown on {}".format(key))
            elif action['type'] == 'keyUp':
                key = self.convertKey(action['button'])
                pyautogui.keyUp(key)
                print("keyUp on {}".format(key))
            elif action['type'] == 'click':
                pyautogui.click(action['pos'][0], action['pos'][1], duration=0.25)
                print("click on {}".format(action['pos']))

            # then sleep until next action should occur
            try:
                next_action = self.data[index + 1]
            except IndexError:
                # this was the last action in the list
                break
            elapsed_time = next_action['time'] - action['time']
            # if elapsed_time is negative, that means our actions are not ordered correctly. throw an error
            if elapsed_time < 0:
                raise Exception('Unexpected action ordering.')

            # adjust elapsed_time to account for our code taking time to run
            elapsed_time -= (time() - action_start_time)
            if elapsed_time < 0:
                elapsed_time = 0
            print('sleeping for {}'.format(elapsed_time))
            time.sleep(elapsed_time)

    def convertKey(self, button):
        WINAPI_SPECIAL_CASE_MAP = {
            'alt_l': 'altleft',
            'alt_r': 'altright',
            'alt_gr': 'altright',
            'caps_lock': 'capslock',
            'ctrl_l': 'ctrlleft',
            'ctrl_r': 'ctrlright',
            'page_down': 'pagedown',
            'page_up': 'pageup',
            'shift_l': 'shiftleft',
            'shift_r': 'shiftright',
            'num_lock': 'numlock',
            'print_screen': 'printscreen',
            'scroll_lock': 'scrolllock',
        }

        # example: 'Key.F9' should return 'F9', 'w' should return as 'w'
        cleaned_key = button.replace('Key.', '')

        if cleaned_key in WINAPI_SPECIAL_CASE_MAP:
            return WINAPI_SPECIAL_CASE_MAP[cleaned_key]

        return cleaned_key

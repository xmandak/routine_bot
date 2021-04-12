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

        if client_window_name == 0 and client_hwnd:
            self.hWnd = client_hwnd
            self.window_name = win32gui.GetWindowText(client_hwnd)
        elif client_hwnd:
            self.window_name = client_window_name
            self.hWnd = win32gui.FindWindow(None, client_window_name)
        elif client_window_name == 0 and client_hwnd == 0:
            print('No client window name or handle.')
            return
        print(self.hWnd)
        print(self.window_name)
        self.wincap = WindowCapture(self.hWnd)

        with open(self.file_path, 'r') as jsonfile:
            # parse the json
            file = json.load(jsonfile)
            self.data = file['events']
            self.meta = file['meta']

        jsonfile.close()


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


    def image_search(self, image_number, image_paths, image_names):
        search_time = time.time()
        original_cwd = os.getcwd()
        while True:
            time.sleep(1)
            screen_grab = self.wincap.get_screenshot()
            gray_value = 0.07 * screen_grab[:, :, 2] + 0.72 * screen_grab[:, :, 1] + 0.21 * screen_grab[:, :, 0]
            gray_screen = gray_value.astype(np.uint8)
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

                print(needle_name, needle_path)

                needle_img = cv.imread(needle_name, cv.IMREAD_GRAYSCALE)

                result = cv.matchTemplate(gray_screen, needle_img, cv.TM_CCOEFF_NORMED)
                threshold = 0.95
                locations = np.where(result >= threshold)
                locations = list(zip(*locations[::-1]))
                if locations:
                    self.image_click_chain(needle_img, locations)
                    print('Image {} found.'.format(needle_name))
                    break
            else:
                continue
            break

        if not os.getcwd() == original_cwd:
            try:
                os.chdir(original_cwd)
            except:
                print("Can't change back to original directory.")

        search_time = time.time() - search_time
        print("Search took {} second".format(search_time))
    def image_click_chain(self, needle_img, locations):
        if locations:
            print(locations)
            needle_w = needle_img.shape[1]
            needle_h = needle_img.shape[0]
            needle_center = (int(locations[0][0] + (needle_w/2)), int(locations[0][1] + (needle_h/2)))
            print(needle_center)
            self.click(needle_center[0], needle_center[1])
            time.sleep(1)
        else:
            print('No such image on screen.')


    def image_click_solo(self, image_path, image_name):

        screen_grab = self.wincap.get_screenshot()

        cwd = os.getcwd()
        if not cwd == image_path:
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
            print(needle_center)
            self.click(needle_center[0], needle_center[1])
        else:
            print('No such image on screen. Image:{0}/{1}'.format(image_path, image_name))

        if not os.getcwd() == cwd:
            try:
                os.chdir(cwd)
            except:
                print("Can't change back to original directory.")


    def click(self, x, y):
        if self.window_name != 0:
            hWnd = win32gui.FindWindow(None, self.window_name)
        else:
            hWnd = self.hWnd
        lParam = win32api.MAKELONG(x, y)

        win32gui.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)

    def key_down(self, key):

        win32api.PostMessage(self.hWnd, win32con.WM_KEYDOWN, key, 0)


    def key_up(self, key):

        win32api.PostMessage(self.hWnd, win32con.WM_KEYUP, key, 0)

    '''
    def key_action(self, key, duration):
        if duration > 0.25:
            elapsed_time = 0
            print("Presing key: {0} for : {1} seconds".format(chr(int(key,16)), duration))
            while elapsed_time < duration:
                self.key_down(key)
                elapsed_time += 0.1
                time.sleep(0.1)
        else:
            self.key_down(key)
        self.key_up(key)
    '''
    def replay_actions(self):

        for index, action in enumerate(self.data):
            action_start_time = time.time()

            # get duration for action
            try:
                next_action = self.data[index + 1]
                action_duration = next_action['time'] - action['time']
            except IndexError:
                # this was the last action in the list
                action_duration = 0
                pass
            except KeyError:
                # its image search or click
                action_duration = 0
            # if elapsed_time is negative, that means our actions are not ordered correctly. throw an error
            if action_duration < 0:
                raise Exception('Unexpected action ordering.')

            #if action['button'] == 'Key.esc':
            #    break

            # perform the action


            if action['type'] == 'push key':
                key = self.convertKey(action['button'])
                print('Key down on {} key.'.format(key))
                self.key_down(key)
                print("keyDown on {}".format(key))
            elif action['type'] == 'release key':
                key = self.convertKey(action['button'])
                print('Key down on {} key.'.format(key))
                self.key_up(key)
                print("keyUp on {}".format(key))
            elif action['type'] == 'click':
                self.click(action['pos'][0], action['pos'][1], )
                print("click on {}".format(action['pos']))
            elif action['type'] == 'search image':
                self.image_search(action['number of images'], action['paths'], action['names'])
            elif action['type'] == 'image_click':
                self.image_click_solo(action['path'], action['name'])


            # adjust elapsed_time to account for our code taking time to run
            action_duration -= (time.time() - action_start_time)
            if action_duration < 0:
                action_duration = 0
            time.sleep(action_duration)
            print('Sleeping for {} seconds'.format(action_duration))

    def convertKey(self, button):
        WINAPI_SPECIAL_CASE_MAP = {
        }
        # example: 'Key.F9' should return 'F9', 'w' should return as 'w'
        cleaned_key = button.replace('Key.', '')

        hex_char = hex(ord(cleaned_key.upper()))
        cleaned_key = int(hex_char, 16)

        # if cleaned_key in WINAPI_SPECIAL_CASE_MAP:
        #     pass

        return cleaned_key

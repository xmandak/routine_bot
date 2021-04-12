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
from  Replay import Replay
import json
import os
from windowcapture import WindowCapture
from datetime import datetime
MAIN_HWND = 0

repeatCount = 1
scanCode = 16
extended = 0
context = 0
previousState = 0
transition = 0

lParam_global = repeatCount | (scanCode << 16) | (extended << 24) | (context << 29) | (previousState << 30) | (transition << 31)


OUTPUT_FILENAME = 'RecorderTestClass2'
INPUT_FILENAME = 'RecorderTestClass2.json'


def capture_window(window_name):
    w = 1600
    h = 900

    hwnd = win32gui.FindWindow(None, window_name)

    # get the window image data
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0, 0), (w, h), dcObj, (0, 0), win32con.SRCCOPY)

    # convert the raw data into a format opencv can read
    # dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
    signedIntsArray = dataBitMap.GetBitmapBits(True)
    img = np.fromstring(signedIntsArray, dtype='uint8')
    img.shape = (h, w, 4)

    # free resources
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())

    # drop the alpha channel, or cv.matchTemplate() will throw an error like:
    #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type()
    #   && _img.dims() <= 2 in function 'cv::matchTemplate'
    img = img[..., :3]

    # make image C_CONTIGUOUS to avoid errors that look like:
    #   File ... in draw_rectangles
    #   TypeError: an integer is required (got type tuple)
    # see the discussion here:
    # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
    img = np.ascontiguousarray(img)

    return img



def list_window_names():
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            print(hwnd, win32gui.GetWindowText(hwnd))
            #list_child_names(win32gui.GetWindowText(hwnd))
    win32gui.EnumWindows(winEnumHandler, None)


def list_child_names(main_app):

    def is_win_ok(hwnd, starttext):
        s = win32gui.GetWindowText(hwnd)
        if s.startswith(starttext):
            print(s)
            global MAIN_HWND
            MAIN_HWND = hwnd
            return None
        return 1

    def find_main_window(starttxt):
        global MAIN_HWND
        win32gui.EnumChildWindows(0, is_win_ok, starttxt)
        return MAIN_HWND

    def callback(hwnd, lparam):
        s = win32gui.GetWindowText(hwnd)
        if len(s) > 3:
            print("winfun, child_hwnd: %d   txt: %s" % (hwnd, s))
        return 1

    hwnd = win32gui.FindWindow(None, main_app)
    print(hex(hwnd))
    if hwnd < 1:
        hwnd = find_main_window(main_app)
    print(hex(hwnd))
    if hwnd:
        win32gui.EnumChildWindows(hwnd, callback, None)


def click(x, y, window_name=None, window_hWnd=None):
    if window_name != 0:
        hWnd = win32gui.FindWindow(None, window_name)
    else:
        hWnd = window_hWnd
    lParam = win32api.MAKELONG(x, y)

    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONUP, 0, lParam)

def click_child(x, y, parent_name, child_name):
    parent_hWnd = win32gui.FindWindow(None, parent_name)
    hWnd = win32gui.FindWindowEx(parent_hWnd, None, None, child_name)
    lParam = win32api.MAKELONG(x, y)

    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    time.sleep(0.2)
    win32gui.PostMessage(hWnd, win32con.WM_LBUTTONUP, 0, lParam)
    print('Clicked on child {0}, from parent {1}, on coordinates {2}'.format(child_name, parent_name, (x,y)))


def post_key(key, window_name=None, window_hWnd=None):
    hex_char = hex(ord(key.upper()))
    key = int(hex_char, 16)
    if window_name != 0:
        hWnd = win32gui.FindWindow(None, window_name)
    else:
        hWnd = window_hWnd

    win32api.PostMessage(hWnd, win32con.WM_KEYDOWN, key, 0)
    time.sleep(0.1)
    #win32api.PostMessage(hWnd, win32con.WM_CHAR, int(key)+32, 0)
    win32api.PostMessage(hWnd, win32con.WM_KEYUP, key, 0)

def key_down(key, window_name=None, window_hWnd=None):
    if window_name != 0:
        hWnd = win32gui.FindWindow(None, window_name)
    else:
        hWnd = window_hWnd
    win32api.PostMessage(hWnd, win32con.WM_KEYDOWN, key, 0)

def key_up(key, window_name=None, window_hWnd=None):
    if window_name != 0:
        hWnd = win32gui.FindWindow(None, window_name)
    else:
        hWnd = window_hWnd
    win32api.PostMessage(hWnd, win32con.WM_KEYUP, key, 0)


def call_recorder():
    t = 5
    print('Recorder starts in:')
    while t:
        print(t)
        time.sleep(1)
        t -= 1

    recorder = Recorder()
    print("Recording duration: {} seconds".format(recorder.elapsed_time()))
    print(json.dumps(recorder.input_events))

    # write the output to a file
    script_dir = os.path.dirname(__file__)
    filepath = os.path.join(
        script_dir,
        'routines',
        '{}.json'.format(OUTPUT_FILENAME)
    )
    with open(filepath, 'w') as outfile:
        json.dump(recorder.input_events, outfile, indent=4)

def main():

    # recorder = Recorder('RecorderFinalTestimgsearch', 0, 4719774)
    player = Replay()
    player.replay_begin(
        'RecorderFinalTest3', "C:\\ostatne\\skola\\python\\bots\\rsbot\\routines\\RecorderFinalTestimgsearch.json", 0, 2032708)

    t = 5
    while t:
        print(t)
        time.sleep(1)
        t -= 1
    print(player.meta)
    player.replay_actions()
    # recorder.buttons_recording_begin()
    # recorder.image_search(1, [os.getcwd()], ['NeedleTest1.PNG'])
    # recorder.buttons_recording_begin()
    # recorder.make_json()
    # print('Recording done.')
    print('Replaying done.')
    '''
    loop_time = time()
    while True:

        screenshot = capture_screen()

        cv.imshow('compture vision', screenshot)

        print('FPS {}'.format(1/(time() - loop_time)))
        loop_time = time()

        #gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        # Display the resulting frame
        #cv.imshow('frame', gray)
        if cv.waitKey(1) == ord('q'):
            break
    # When everything done, release the capture
    cv.destroyAllWindows()
    '''
    #list_window_names()

    #list_child_names('test2 - Malování')

    #click(303, 784, 0, int('13053C', 16))

    #post_key(0x51, 0, int('13053C', 16))

    #click_child(110, 82, 'test2 - Malování', 'UIRibbonWorkPane')

    '''
    parent_hWnd = win32gui.FindWindow(None, 'test2 - Malování')
    hWnd = 262968
    print(hex(hWnd))
    child_win_text = win32gui.GetWindowText(hWnd)
    print(child_win_text)
    hWnd_parent = win32gui.GetParent(hWnd)
    print(hex(hWnd_parent))
    if hWnd_parent == parent_hWnd:
        print('parent handles are equal')
    parent_win_text = win32gui.GetWindowText(hWnd_parent)
    print(parent_win_text)
    if parent_win_text == 'test2 - Malování':
        print('parent windows texts are equal')
    
    
    rect = win32gui.GetWindowRect(hWnd)
    
    print(rect)
    '''

    #print(int('4704D6',16),'decimal jagex')

    '''
    loc = win32api.GetCursorPos()
    print(loc)
    loc = win32gui.ScreenToClient(win32gui.FindWindow(None, 'Kalkulačka'), loc)
    # runescape ore coords (893, 337)uu
    print(loc)
    '''
    #print(bin(lParam_global), '=> lParam for key strokes')
    #print('done')

    '''
        file_name = 'RecorderFinalTest2.json'

    script_dir = os.path.dirname(__file__)
    filepath = os.path.join(
        script_dir,
        'routines',
        file_name
    )
    with open(filepath, 'r') as jsonfile:
        # parse the json
        file = json.load(jsonfile)
    file2 = file['meta']
    print(file2[0][0]) 
    '''

if __name__ == "__main__":
    main()
    # key = 'a'
    # hex_char = hex(ord(key.upper()))
    # print(int(0x51))
    # key = hex(ord(key.upper()))
    # print(key)
    #
    # hex_str = "0x41"
    # hex_int = int(hex_char, 16)
    # print(hex(hex_int))
    # t = 5
    # while t:
    #     print(t)
    #     time.sleep(1)
    #     t -= 1
    # post_key('a', 0, 328716)
    # wincap = WindowCapture(2032708)
    # needle_img = cv.imread('NeedleTest2.PNG', cv.IMREAD_GRAYSCALE)
    # haystack = cv.imread('ScreenGrab1.PNG', cv.IMREAD_GRAYSCALE)
    # screen_grab = wincap.get_screenshot()
    #
    # grayValue = 0.07 * screen_grab[:, :, 2] + 0.72 * screen_grab[:, :, 1] + 0.21 * screen_grab[:, :, 0]
    # gray_screen = grayValue.astype(np.uint8)
    #
    # cv.imwrite('ScreenGrab1.PNG', screen_grab)
    # result = cv.matchTemplate(gray_screen, needle_img, cv.TM_CCOEFF_NORMED)
    # locations = np.where(result >= 0.95)
    # locations = list(zip(*locations[::-1]))
    # print(locations)
#     (601.0, 459.0)
















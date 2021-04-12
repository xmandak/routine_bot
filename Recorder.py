from pynput import mouse, keyboard
import time
import cv2 as cv
import os
import json
from datetime import datetime


class Recorder:

    start_time = None
    unreleased_keys = []
    mouse_listener = None
    keyboard_listener = None
    meta_data = []
    input_events = []
    recorder_flag = False
    routine_name = None

    def __init__(self, bot_name, window_name=None, window_hwnd = None):
        script_dir = os.getcwd()
        filepath = os.path.join(
            script_dir,
            'routines',
            '{}.json'.format(bot_name)
        )

        self.routine_name = bot_name
        self.meta_data = {
                'routine name': bot_name,
                'file path': filepath,
                'window name': window_name,
                'window hwnd': window_hwnd,
                'date of creation': datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        }

    def buttons_recording_begin(self):
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.start()
        self.mouse_listener.wait()

        with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release) as listener:
            self.start_time = time.time()
            self.keyboard_listener = listener
            self.keyboard_listener.join()

        self.recorder_flag = True

    def __buttons_recording_end(self):
        self.recorder_flag = False
        self.mouse_listener.stop()
        raise keyboard.Listener.StopException

    def on_press(self, key):
        if key in self.unreleased_keys:
            return
        else:
            self.unreleased_keys.append(key)

        try:
            self.record_event('push key', self.elapsed_time(), key.char)
        except AttributeError:
            self.record_event('push key', self.elapsed_time(), key)

    def on_release(self, key):

        try:
            self.unreleased_keys.remove(key)
        except ValueError:
            print('ERROR: {} not in unreleased_keys'.format(key))

        try:
            self.record_event('release key', self.elapsed_time(), key.char)
        except AttributeError:
            self.record_event('release key', self.elapsed_time(), key)

        if key == keyboard.Key.esc:
            self.__buttons_recording_end()

    def on_click(self, x, y, button, pressed):
        if not pressed:
            self.record_event('click', self.elapsed_time(), button, (x, y))

    def elapsed_time(self):
        return time.time() - self.start_time

    def image_search(self, needle_count, needle_paths=[], needle_names=[]):
        self.record_event('search image', 0, 0, 0, needle_count, needle_paths, needle_names)

    def click_image(self, needle_path, needle_name):
        self.record_event('click image', 0, 0, 0, 0, needle_path, needle_name)

    def make_json(self):
        out_json = {}
        out_json['meta'] = self.meta_data
        out_json['events'] = self.input_events
        #out_json.append(self.meta_data)
        #out_json.append({'data': self.input_events})
        script_dir = os.getcwd()
        filepath = os.path.join(
            script_dir,
            'routines',
            '{}.json'.format(self.routine_name)
        )
        with open(filepath, 'w') as out_file:
            json.dump(out_json, out_file, indent=4)
        out_file.close()

    def record_event(self, event_type, event_time=None, button=None, pos=None, numOfImg=None, image_paths=None, image_names = None):

        if str(button) == "Key.esc":
            return

        if event_type == 'release key' or event_type == 'push key':
            self.input_events.append({
                'time': event_time,
                'type': event_type,
                'button': str(button),
            })
        elif event_type == 'click':
            self.input_events.append({
                'time': event_time,
                'type': event_type,
                'button': str(button),
                'pos': pos
            })
        elif event_type == 'search image':
            self.input_events.append({
                'type': event_type,
                'number of images': numOfImg,
                'paths': image_paths,
                'names': image_names,
            })
        elif event_type == 'click image':
            self.input_events.append({
                'type': event_type,
                'path': image_paths,
                'name': image_names,
            })

        if event_type == 'click':
            print('{} on {} pos {} at {}'.format(event_type, button, pos, event_time))
        elif event_type == 'release key':
            print('{} on {} at {}'.format(event_type, button, event_time))
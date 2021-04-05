from pynput import mouse, keyboard
import time
import json
import os


OUTPUT_FILENAME = 'RecorderTest1'
# declare mouse_listener globally so that keyboard on_release can stop it
mouse_listener = None
# declare our start_time globally so that the callback functions can reference it
start_time = None
# keep track of unreleased keys to prevent over-reporting press events
unreleased_keys = []
# storing all input events
input_events = []

class EventType():
    KEYDOWN = 'keyDown'
    KEYUP = 'keyUp'
    CLICK = 'click'


def main():
    runListeners()
    print("Recording duration: {} seconds".format(elapsed_time()))
    global input_events
    print(json.dumps(input_events))

    # write the output to a file
    script_dir = os.path.dirname(__file__)
    filepath = os.path.join(
        script_dir,
        'routines',
        '{}.json'.format(OUTPUT_FILENAME)
    )
    with open(filepath, 'w') as outfile:
        json.dump(input_events, outfile, indent=4)


def elapsed_time():
    global start_time
    return time.time() - start_time


def record_event(event_type, event_time, button, pos=None):

    if str(button) == "Key.esc":
        return

    global input_events
    input_events.append({
        'time': event_time,
        'type': event_type,
        'button': str(button),
        'pos': pos
    })

    if event_type == EventType.CLICK:
        print('{} on {} pos {} at {}'.format(event_type, button, pos, event_time))
    else:
        print('{} on {} at {}'.format(event_type, button, event_time))


def on_press(key):

    global unreleased_keys
    if key in unreleased_keys:
        return
    else:
        unreleased_keys.append(key)

    try:
        record_event(EventType.KEYDOWN, elapsed_time(), key.char)
    except AttributeError:
        record_event(EventType.KEYDOWN, elapsed_time(), key)


def on_release(key):

    global unreleased_keys
    try:
        unreleased_keys.remove(key)
    except ValueError:
        print('ERROR: {} not in unreleased_keys'.format(key))

    try:
        record_event(EventType.KEYUP, elapsed_time(), key.char)
    except AttributeError:
        record_event(EventType.KEYUP, elapsed_time(), key)

    if key == keyboard.Key.esc:

        global mouse_listener
        mouse_listener.stop()

        raise keyboard.Listener.StopException


def on_click(x, y, button, pressed):

    if not pressed:
        record_event(EventType.CLICK, elapsed_time(), button, (x, y))


def runListeners():

    global mouse_listener
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()
    mouse_listener.wait()

    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        global start_time
        start_time = time.time()
        listener.join()


if __name__ == "__main__":
    main()
import time
import digitalio
import board
import adafruit_matrixkeypad



def keypad_setup():
    # Membrane 3x4 matrix keypad on Raspberry Pi -
    # https://www.adafruit.com/product/419
    cols = [digitalio.DigitalInOut(x) for x in (board.D18, board.D23, board.D24)]
    rows = [digitalio.DigitalInOut(x) for x in (board.D4, board.D17, board.D27, board.D22)]

    # 3x4 matrix keypad on Raspberry Pi -
    # rows and columns are mixed up for https://www.adafruit.com/product/3845
    # cols = [digitalio.DigitalInOut(x) for x in (board.D13, board.D5, board.D26)]
    # rows = [digitalio.DigitalInOut(x) for x in (board.D6, board.D21, board.D20, board.D19)]

    keys = ((1, 2, 3),
            (4, 5, 6),
            (7, 8, 9),
            ('*', 0, '#'))

    keypad = adafruit_matrixkeypad.Matrix_Keypad(rows, cols, keys)
    return keypad


    
def keypad_verify(code, keypad):
    code_as_list = list(code)
    #create empty buffer for entered code
    entered_code = list()
    code_active = False # flag for signaling when input seq ready 


    while True:
        keys = keypad.pressed_keys
        if len(keys) != 1: continue #eliminate multi press
        if keys == ['*']: #input is reset and now look for code
            entered_code = list()
            code_active = True 
        elif code_active:
                entered_code += keys #add key to code
                if len(code_as_list) == len(entered_code): #submit code for verification
                    code_active = False
                    print("code", entered_code)
                    return entered_code == [int(i) for i in code_as_list] #verify list
        else:
            continue
 
        print("code", entered_code)
        time.sleep(0.2)

    # while True:
    #     keys = keypad.pressed_keys
    #     if keys:
    #         print("Pressed: ", keys)
    #     time.sleep(0.1)

# k = keypad_setup()
# keypad_verify('1234', k)


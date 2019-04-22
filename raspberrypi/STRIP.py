# Simple test for NeoPixels on Raspberry Pi
import time
import board
import neopixel


def setup_strip():
    # Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
    # NeoPixels must be connected to D10, D12, D18 or D21 to work.
    pixel_pin = board.D21

    # The number of NeoPixels
    num_pixels = 60

    # The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
    # For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
    ORDER = neopixel.GRB

    pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.2, auto_write=False,
                               pixel_order=ORDER)

    return pixels

def wheel(pos,ORDER):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, g, b) if ORDER == neopixel.RGB or ORDER == neopixel.GRB else (r, g, b, 0)


def rainbow_cycle(wait, ORDER):
    for j in range(255):
        for i in range(60):
            pixel_index = (i * 256 // 60) + j
            pixels[i] = wheel(pixel_index & 255, ORDER)
        pixels.show()
        time.sleep(wait)


def unlock_success(pixels):
    print("eek3")
    for i in range(60):
        pixels[i] = (0, 125, 0)
        pixels.show()
        time.sleep(.01)
    print("eek4")

    for i in range(60):
        pixels[60-i-1] = (0, 50, 0)
        pixels.show()
        time.sleep(.01)
    print("eek5")

def unlock_fail(pixels):
    #pulse three on fail
    print("eek6")

    for eek in range(3):

        print("eek7")

        for i in range(60):
            print("eek8")

            pixels.fill((225-i, 0, 0))
            pixels.show()
            time.sleep(.0005)
        time.sleep(.5)

def idle(pixels):
    print("eek9")
    while True:
        for i in range(60):
            pixels[i] = (125, 125, 125)
            pixels.show()
            time.sleep(.01)

        for i in range(60):
            pixels[60-i-1] = (50, 50, 50)
            pixels.show()
            time.sleep(.01)


# time.sleep(1)

# pixels.fill((0, 0, 0))
# pixels.show()
# pixels.fill((0, 255, 0))
# while True:

#     for i in range(60):
#         pixels[i] = (0, 255, 0)
#         pixels.show()
#         time.sleep(1)

    # for i in range(num_pixels):
    #     pixels[num_pixels-i-1] = (255, 255, 255)
    #     pixels.show()
    #     time.sleep(.1)


# while True:
#     # Comment this line out if you have RGBW/GRBW NeoPixels
#     pixels.fill((255, 0, 0))
#     # Uncomment this line if you have RGBW/GRBW NeoPixels
#     # pixels.fill((255, 0, 0, 0))
#     pixels.show()
#     time.sleep(.5)

#     # Comment this line out if you have RGBW/GRBW NeoPixels
#     pixels.fill((0, 255, 0))
#     # Uncomment this line if you have RGBW/GRBW NeoPixels
#     # pixels.fill((0, 255, 0, 0))
#     pixels.show()
#     time.sleep(.5)

#     # Comment this line out if you have RGBW/GRBW NeoPixels
#     pixels.fill((0, 0, 255))
#     # Uncomment this line if you have RGBW/GRBW NeoPixels
#     # pixels.fill((0, 0, 255, 0))
#     pixels.show()
#     time.sleep(.5)

    # rainbow_cycle(0.001, ORDER)    # rainbow cycle with 1ms delay per step



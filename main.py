#!/usr/bin/python
import gtk
import random
import time
import cv2
import sys
import pyautogui

import numpy as np

from PIL import Image
from algorithm import Algorithm


TMP_FILE = '/tmp/screenshot.png'


class WebSudoku(object):

    def __init__(self, verbose):
        self._verbose = verbose
        self._values, self._centroids = self._grab_board()
        self._algo = Algorithm(self, self._values)

    def solve(self):
        self._algo.solve()
        if self._verbose:
            return

        for row in range(9):
            for col in range(9):
                if (row, col) in self._algo.board_default:
                    continue
                y, x = self._centroids[(row, col)]
                pyautogui.moveTo(x, y)
                pyautogui.click()
                pyautogui.press(str(self._algo.value(row, col)))

    def fill_cell(self, row, col, default=False):
        if not self._verbose and not default:
            return

        if random.random() < 0.2 and not default:
            #time.sleep(5)
            pass

        y, x = self._centroids[(row, col)]
        pyautogui.moveTo(x, y)
        pyautogui.click()

        value = self._algo.value(row, col)
        pyautogui.press('backspace')
        pyautogui.press('delete')
        pyautogui.press(str(value))

    def _grab_board(self):
        time.sleep(3)

        samples = np.float32(np.loadtxt('vectors.data'))
        responses = np.float32(np.loadtxt('samples.data'))

        model = cv2.KNearest()
        model.train(samples, responses)

        window = gtk.gdk.get_default_root_window()
        x, y, width, height, _ = window.get_geometry()
        ss = gtk.gdk.Pixbuf.get_from_drawable(gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width, height),
                                              gtk.gdk.get_default_root_window(),
                                              gtk.gdk.colormap_get_system(),
                                              0, 0, x, y, width, height)
        ss.save(TMP_FILE, 'png')

        raw = cv2.imread(TMP_FILE)
        gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        threshold = cv2.adaptiveThreshold(gray, 255, 1, 1, 11, 15)
        cache = threshold.copy()
        contours, _ = cv2.findContours(threshold,
                                       cv2.RETR_LIST,
                                       cv2.CHAIN_APPROX_SIMPLE)

        squares = []
        for c in contours:
            c = cv2.approxPolyDP(c, 4, True)
            if len(c) != 4:
                continue
            if not cv2.isContourConvex(c):
                continue
            squares.append(c)

        board_size = max(cv2.contourArea(s) for s in squares)
        board = [s for s in squares if cv2.contourArea(s) == board_size][0]

        min_x = min(s[0][0] for s in board)
        max_x = max(s[0][0] for s in board)
        min_y = min(s[0][1] for s in board)
        max_y = max(s[0][1] for s in board)

        step_x = (max_x - min_x) / 9.0
        step_y = (max_y - min_y) / 9.0

        values = {}
        centroids = {}
        for y in range(9):
            values[y] = {}
            for x in range(9):
                local_min_y = min_y + (y * step_y) + 5
                local_max_y = min_y + ((y+1) * step_y) - 5
                local_min_x = min_x + (x * step_x) + 5
                local_max_x = min_x + ((x+1) * step_x) - 5

                roi = cache[
                    local_min_y:local_max_y,
                    local_min_x:local_max_x]

                centroids[(y, x)] = (
                    int((local_min_y + local_max_y) / 2.0),
                    int((local_min_x + local_max_x) / 2.0))

                cache = cache.copy()
                roi_cache = roi.copy()

                contours, _ = cv2.findContours(roi,
                                               cv2.RETR_LIST,
                                               cv2.CHAIN_APPROX_SIMPLE)

                if not contours:
                    values[y][x] = (0, 0)
                    continue

                item = max(contours, key=lambda c: cv2.contourArea(c))
                _x, _y, _w, _h = cv2.boundingRect(item)

                digit = roi_cache[_y:_y+_h, _x:_x+_w]
                small_digit = cv2.resize(digit, (10, 10))
                vector = small_digit.reshape((1, 100)).astype(np.float32)
                _, results, _, err = model.find_nearest(vector, k=1)

                value = int(results.ravel()[0])
                values[y][x] = (value, err[0][0])

        errs = [values[y][x][1] for y in range(9) for x in range(9)]
        err_threshold = np.percentile(errs, 90)

        # "TODO": relearn 1 :(
        for y in range(9):
            for x in range(9):
                val, err = values[y][x]
                if err > err_threshold and val == 7:
                    values[y][x] = 1
                else:
                    values[y][x] = val

        return values, centroids


if __name__ == '__main__':
    # :^)
    sys.setrecursionlimit(1000000000)
    verbose = True if len(sys.argv) > 1 else False

    ws = WebSudoku(verbose)
    ws.solve()

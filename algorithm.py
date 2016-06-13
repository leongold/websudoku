

class Algorithm(object):

    def __init__(self, parent, board):
        self._parent = parent
        self._board = board
        self._board_default = [(y, x) for y in range(9) for x in range(9) if
                               board[y][x] > 0]
    @property
    def board_default(self):
        return self._board_default

    def value(self, row, col):
        return self._board[row][col]

    def solve(self):
        self._initial_solve()
        self._solve(0, 0)

    def _solve(self, row, col, regressing=False):
        if row == 8 and col == 8:
            if (row, col) in self._board_default:
                return True

            candidate = self._candidates(row, col)[0]
            self._board[row][col] = candidate
            self._parent.fill_cell(row, col)
            return True

        if (row, col) in self._board_default:
            return self._regress(row, col) if regressing else \
                   self._advance(row, col)

        if self._board[row][col] > 0:
            cache = self._board[row][col]
            self._board[row][col] = 0
            self._parent.fill_cell(row, col)
            candidates = [candidate for candidate in self._candidates(row, col)
                          if candidate > cache]

            if not candidates:
                return self._regress(row, col)
            else:
                candidate = min(candidates)
                self._board[row][col] = candidate
                self._parent.fill_cell(row, col)
                return self._advance(row, col)
        else:
            candidates = self._candidates(row, col)
            if not candidates:
                return self._regress(row, col)

            candidate = min(candidates)
            self._board[row][col] = candidate
            self._parent.fill_cell(row, col)
            return self._advance(row, col)

    def _initial_solve(self):
        while True:
            solved_cells = False

            for row in xrange(9):
                for col in xrange(9):
                    if (row, col) in self._board_default:
                        continue
                    candidates = self._candidates(row, col)
                    if len(candidates) == 1:
                        self._board_default.append((row, col))
                        self._board[row][col] = candidates[0]
                        self._parent.fill_cell(row, col, default=True)
                        solved_cells = True

            if not solved_cells:
                break

    def _regress(self, row, col):
        if col == 0:
            col = 8
            row -= 1
        else:
            col -= 1

        return self._solve(row, col, regressing=True)

    def _advance(self, row, col):
        if col == 8:
            col = 0
            row += 1
        else:
            col += 1

        return self._solve(row, col)

    def _row(self, row):
        return self._board[row].values()

    def _col(self, col):
        return [self._board[row][col] for row in xrange(9)]

    def _block(self, row, col):
        def block_index(index):
            if index in (0, 3, 6):
                return index
            if index < 3:
                return 0
            if 3 < index < 6:
                return 3
            return 6

        row, col = block_index(row), block_index(col)

        return [self._board[row+y][col+x] for y in range(3) for x in range(3)]

    def _candidates(self, row, col):
        row_values = self._row(row)
        col_values = self._col(col)
        block_values = self._block(row, col)

        res = range(1, 10)
        return list(set(res) - set(col_values) -
                    set(row_values) - set(block_values))

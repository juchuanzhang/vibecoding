import os
import time
from concurrent.futures import ProcessPoolExecutor

KING = 0
ADVISOR = 1
BISHOP = 2
KNIGHT = 3
ROOK = 4
CANNON = 5
PAWN = 6
RED = 0
BLACK = 1

INFINITY_SCORE = 99999

RED_COLS = ["九", "八", "七", "六", "五", "四", "三", "二", "一"]
BLACK_COLS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
RED_NUMS = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
BLACK_NUMS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
BASE_VALUES = [10000, 120, 120, 270, 600, 450, 30]
CANNON_ENDGAME_VALUE = 240
PAST_RIVER_PAWN_VALUE = 70
MID_PAWN_VALUE = 50
PIECE_SORT_VALUES = {KING: 10000, ROOK: 600, CANNON: 450, KNIGHT: 270, ADVISOR: 120, BISHOP: 120, PAWN: 30}

ZOBRIST_SEED = 1070372
_zobrist_pieces = None
_zobrist_side = None

def _init_zobrist():
    global _zobrist_pieces, _zobrist_side
    seed = ZOBRIST_SEED
    _zobrist_pieces = {}
    for y in range(10):
        for x in range(9):
            for pt in range(7):
                for s in range(2):
                    seed = (seed * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
                    _zobrist_pieces[(y, x, pt, s)] = seed
    seed = (seed * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
    _zobrist_side = seed

_init_zobrist()

POS_TABLES = [
    [[0]*9]*7 + [[0,0,0,-8,-16,-8,0,0,0],[0,0,0,-8,-12,-8,0,0,0],[0,0,0,2,8,2,0,0,0]],
    [[0]*9]*8 + [[0,0,0,20,0,20,0,0,0],[0,0,0,0,20,0,0,0,0]],
    [[0]*9]*5 + [[0,0,0,0,20,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,20,0,0,0,20,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]],
    [[4,8,16,12,12,12,16,8,4],[4,10,28,16,8,16,28,10,4],[12,14,16,20,18,20,16,14,12],[8,24,18,24,20,24,18,24,8],[6,16,14,18,16,18,14,16,6],[4,12,16,14,12,14,16,12,4],[2,6,8,6,10,6,8,6,2],[4,2,8,0,8,0,8,2,4],[0,2,4,4,-2,4,4,2,0],[0,-4,0,0,0,0,0,-4,0]],
    [[14,14,12,18,16,18,12,14,14],[16,20,18,24,26,24,18,20,16],[12,12,12,18,18,18,12,12,12],[12,18,16,22,22,22,16,18,12],[12,14,12,18,18,18,12,14,12],[12,16,14,20,20,20,14,16,12],[6,10,8,14,14,14,8,10,6],[4,8,6,14,12,14,6,8,4],[8,4,8,16,8,16,8,4,8],[-2,10,6,14,12,14,6,10,-2]],
    [[6,4,0,-10,-12,-10,0,4,6],[2,2,0,-4,-14,-4,0,2,2],[2,2,0,-10,-8,-10,0,2,2],[0,0,-2,4,10,4,-2,0,0],[0,0,0,2,8,2,0,0,0],[-2,0,4,2,6,2,4,0,-2],[0,0,0,2,8,2,0,0,0],[4,0,8,6,10,6,8,0,4],[0,2,4,6,6,6,4,2,0],[0,0,-2,0,4,0,-2,0,0]],
    [[0,3,6,9,12,9,6,3,0],[18,36,56,80,120,80,56,36,18],[14,26,42,60,80,60,42,26,14],[10,20,30,34,40,34,30,20,10],[6,12,18,18,20,18,18,12,6],[2,0,8,0,8,0,8,0,2],[0,0,-2,0,4,0,-2,0,0],[0]*9,[0]*9,[0]*9],
]

KNIGHT_TARGETS = [(2,1,1,0),(2,-1,1,0),(-2,1,-1,0),(-2,-1,-1,0),(1,2,0,1),(1,-2,0,-1),(-1,2,0,1),(-1,-2,0,-1)]
KING_DIRS = [(0,1),(0,-1),(1,0),(-1,0)]
ADVISOR_DIRS = [(1,1),(1,-1),(-1,1),(-1,-1)]
BISHOP_DIRS = [(2,2),(2,-2),(-2,2),(-2,-2)]
LINE_PIECES = frozenset({KING, ROOK, CANNON, PAWN})

INITIAL_PIECES = [
    (ROOK,RED,0,9),(KNIGHT,RED,1,9),(BISHOP,RED,2,9),(ADVISOR,RED,3,9),(KING,RED,4,9),(ADVISOR,RED,5,9),(BISHOP,RED,6,9),(KNIGHT,RED,7,9),(ROOK,RED,8,9),
    (CANNON,RED,1,7),(CANNON,RED,7,7),(PAWN,RED,0,6),(PAWN,RED,2,6),(PAWN,RED,4,6),(PAWN,RED,6,6),(PAWN,RED,8,6),
    (ROOK,BLACK,0,0),(KNIGHT,BLACK,1,0),(BISHOP,BLACK,2,0),(ADVISOR,BLACK,3,0),(KING,BLACK,4,0),(ADVISOR,BLACK,5,0),(BISHOP,BLACK,6,0),(KNIGHT,BLACK,7,0),(ROOK,BLACK,8,0),
    (CANNON,BLACK,1,2),(CANNON,BLACK,7,2),(PAWN,BLACK,0,3),(PAWN,BLACK,2,3),(PAWN,BLACK,4,3),(PAWN,BLACK,6,3),(PAWN,BLACK,8,3),
]

FEN_PIECE_MAP = {'K':(KING,RED),'A':(ADVISOR,RED),'B':(BISHOP,RED),'N':(KNIGHT,RED),'R':(ROOK,RED),'C':(CANNON,RED),'P':(PAWN,RED),'k':(KING,BLACK),'a':(ADVISOR,BLACK),'b':(BISHOP,BLACK),'n':(KNIGHT,BLACK),'r':(ROOK,BLACK),'c':(CANNON,BLACK),'p':(PAWN,BLACK)}

def _mirror_y(y, side):
    return y if side == RED else 9 - y

def _piece_value(pt, side, x, y, total_pieces=32):
    base = BASE_VALUES[pt]
    if pt == CANNON:
        base = CANNON_ENDGAME_VALUE + (BASE_VALUES[CANNON] - CANNON_ENDGAME_VALUE) * min(total_pieces / 32, 1)
    pos_val = POS_TABLES[pt][_mirror_y(y, side)][x]
    if pt == PAWN:
        past_river = (y <= 4) if side == RED else (y >= 5)
        pawn_base = PAST_RIVER_PAWN_VALUE if past_river else base
        mid_bonus = MID_PAWN_VALUE if (x == 4 and past_river) else 0
        return pawn_base + pos_val + mid_bonus
    return base + pos_val

def _evaluate(cells, side, rkx, rky, bkx, bky):
    red_score = 0; black_score = 0; red_count = 0; black_count = 0; total_pieces = 0
    for y in range(10):
        for x in range(9):
            c = cells[y * 9 + x]
            if c is None: continue
            total_pieces += 1
            val = _piece_value(c[0], c[1], x, y, total_pieces)
            if c[1] == RED: red_score += val; red_count += 1
            else: black_score += val; black_count += 1
    score = red_score - black_score
    kx_r, ky_r = rkx, rky; kx_b, ky_b = bkx, bky
    opp = BLACK if RED == RED else RED
    for yy in range(10):
        for xx in range(9):
            oc = cells[yy * 9 + xx]
            if oc is None or oc[1] != BLACK: continue
            dist = abs(kx_r - xx) + abs(ky_r - yy)
            if oc[0] == ROOK and (xx == kx_r or yy == ky_r): score -= 40 - dist * 5
            elif oc[0] == CANNON and (xx == kx_r or yy == ky_r): score -= 20 - dist * 3
            elif oc[0] == KNIGHT and dist <= 5: score -= 15 - dist * 2
    for yy in range(10):
        for xx in range(9):
            oc = cells[yy * 9 + xx]
            if oc is None or oc[1] != RED: continue
            dist = abs(kx_b - xx) + abs(ky_b - yy)
            if oc[0] == ROOK and (xx == kx_b or yy == ky_b): score += 40 - dist * 5
            elif oc[0] == CANNON and (xx == kx_b or yy == ky_b): score += 20 - dist * 3
            elif oc[0] == KNIGHT and dist <= 5: score += 15 - dist * 2
    score += (3 - abs(kx_r - 4) - abs(ky_r - 8)) * 5
    score -= (3 - abs(kx_b - 4) - abs(ky_b - 1)) * 5
    if red_count <= 3 or black_count <= 3: return score * 2
    return score

def _path_clear(cells, fx, fy, tx, ty):
    dx = tx - fx; dy = ty - fy
    steps = max(abs(dx), abs(dy))
    if steps == 0: return False
    sx = (1 if dx > 0 else -1 if dx < 0 else 0)
    sy = (1 if dy > 0 else -1 if dy < 0 else 0)
    for i in range(1, steps):
        if cells[(fy + sy * i) * 9 + (fx + sx * i)] is not None: return False
    return True

def _count_between(cells, fx, fy, tx, ty):
    dx = tx - fx; dy = ty - fy
    steps = max(abs(dx), abs(dy))
    sx = (1 if dx > 0 else -1 if dx < 0 else 0)
    sy = (1 if dy > 0 else -1 if dy < 0 else 0)
    count = 0
    for i in range(1, steps):
        if cells[(fy + sy * i) * 9 + (fx + sx * i)] is not None: count += 1
    return count

def _is_in_check(cells, side, kx, ky, rkx, rky, bkx, bky):
    opp = 1 - side
    for yy in range(10):
        for xx in range(9):
            oc = cells[yy * 9 + xx]
            if oc is None or oc[1] != opp: continue
            pt = oc[0]; dx = kx - xx; dy = ky - yy; adx = abs(dx); ady = abs(dy)
            if pt == ROOK:
                if (xx == kx or yy == ky) and _path_clear(cells, xx, yy, kx, ky): return True
            elif pt == CANNON:
                if (xx == kx or yy == ky) and _count_between(cells, xx, yy, kx, ky) == 1: return True
            elif pt == KNIGHT:
                if (adx == 1 and ady == 2) or (adx == 2 and ady == 1):
                    bx = xx + dx // 2 if adx == 2 else xx
                    by = yy if adx == 2 else yy + dy // 2
                    if cells[by * 9 + bx] is None: return True
            elif pt == PAWN:
                fwd = -1 if oc[1] == RED else 1
                pr = yy <= 4 if oc[1] == RED else yy >= 5
                if pr:
                    if (dy == fwd and adx == 0) or (dy == 0 and adx == 1): return True
                elif dy == fwd and adx == 0: return True
    if rkx == bkx:
        mn = min(rky, bky); mx = max(rky, bky)
        for cy in range(mn + 1, mx):
            if cells[cy * 9 + rkx] is not None: return False
        return True
    return False

def _gen_piece_moves(cells, piece, fx, fy):
    pt = piece[0]; side = piece[1]; moves = []
    if pt == KING:
        for dx, dy in KING_DIRS:
            nx, ny = fx + dx, fy + dy
            if 3 <= nx <= 5 and ((7 <= ny <= 9) if side == RED else (0 <= ny <= 2)): moves.append((nx, ny))
    elif pt == ADVISOR:
        for dx, dy in ADVISOR_DIRS:
            nx, ny = fx + dx, fy + dy
            if 3 <= nx <= 5 and ((7 <= ny <= 9) if side == RED else (0 <= ny <= 2)): moves.append((nx, ny))
    elif pt == BISHOP:
        for dx, dy in BISHOP_DIRS:
            nx, ny = fx + dx, fy + dy
            if nx < 0 or nx >= 9 or ny < 0 or ny >= 10: continue
            own = ny >= 5 if side == RED else ny <= 4
            if not own: continue
            ex, ey = fx + dx // 2, fy + dy // 2
            if cells[ey * 9 + ex] is not None: continue
            moves.append((nx, ny))
    elif pt == KNIGHT:
        for dx, dy, bdx, bdy in KNIGHT_TARGETS:
            nx, ny = fx + dx, fy + dy
            if nx < 0 or nx >= 9 or ny < 0 or ny >= 10: continue
            if cells[(fy + bdy) * 9 + (fx + bdx)] is not None: continue
            moves.append((nx, ny))
    elif pt == ROOK:
        for dx, dy in KING_DIRS:
            nx, ny = fx + dx, fy + dy
            while 0 <= nx < 9 and 0 <= ny < 10:
                tc = cells[ny * 9 + nx]
                if tc is not None:
                    if tc[1] != side: moves.append((nx, ny))
                    break
                moves.append((nx, ny)); nx += dx; ny += dy
    elif pt == CANNON:
        for dx, dy in KING_DIRS:
            nx, ny = fx + dx, fy + dy; jumped = False
            while 0 <= nx < 9 and 0 <= ny < 10:
                tc = cells[ny * 9 + nx]
                if tc is not None:
                    if not jumped: jumped = True
                    else:
                        if tc[1] != side: moves.append((nx, ny))
                        break
                elif not jumped: moves.append((nx, ny))
                nx += dx; ny += dy
    elif pt == PAWN:
        fwd = -1 if side == RED else 1
        ny = fy + fwd
        if 0 <= ny < 10: moves.append((fx, ny))
        pr = fy <= 4 if side == RED else fy >= 5
        if pr:
            for nx in [fx - 1, fx + 1]:
                if 0 <= nx < 9: moves.append((nx, fy))
    return moves

def gen_moves(cells, side, rkx, rky, bkx, bky):
    result = []
    for y in range(10):
        for x in range(9):
            piece = cells[y * 9 + x]
            if piece is None or piece[1] != side: continue
            for tx, ty in _gen_piece_moves(cells, piece, x, y):
                target = cells[ty * 9 + tx]
                if target is not None and target[1] == side: continue
                cells[y * 9 + x] = None; cells[ty * 9 + tx] = piece
                nrkx, nrky, nbkx, nbky = rkx, rky, bkx, bky
                if piece[0] == KING:
                    if piece[1] == RED: nrkx, nrky = tx, ty
                    else: nbkx, nbky = tx, ty
                if target is not None and target[0] == KING:
                    if target[1] == RED: nrkx, nrky = tx, ty
                    else: nbkx, nbky = tx, ty
                legal = not _is_in_check(cells, side, nrkx if side == RED else nbkx, nrky if side == RED else nbky, nrkx, nrky, nbkx, nbky)
                cells[y * 9 + x] = piece; cells[ty * 9 + tx] = target
                if legal: result.append((x, y, tx, ty))
    return result

def describe_move(cells, fx, fy, tx, ty):
    piece = cells[fy * 9 + fx]
    if piece is None: return f"({fx},{fy})->({tx},{ty})"
    pt, side = piece
    red_names = {KING:"帅",ADVISOR:"仕",BISHOP:"相",KNIGHT:"马",ROOK:"车",CANNON:"炮",PAWN:"兵"}
    black_names = {KING:"将",ADVISOR:"士",BISHOP:"象",KNIGHT:"马",ROOK:"车",CANNON:"炮",PAWN:"卒"}
    name = red_names[pt] if side == RED else black_names[pt]
    cols = RED_COLS if side == RED else BLACK_COLS
    nums = RED_NUMS if side == RED else BLACK_NUMS
    from_col = cols[fx]
    dx = tx - fx; dy = ty - fy
    if dx == 0: action = ("进" if dy < 0 else "退") if side == RED else ("进" if dy > 0 else "退")
    elif dy == 0: action = "平"
    else: action = ("进" if dy < 0 else "退") if side == RED else ("进" if dy > 0 else "退")
    if dx == 0 and pt in LINE_PIECES: dest = nums[abs(dy) - 1]
    else: dest = cols[tx]
    return f"{name}{from_col}{action}{dest}"

def _sort_moves(cells, moves):
    return sorted(moves, key=lambda m: -PIECE_SORT_VALUES.get(cells[m[3]*9+m[2]][0] if cells[m[3]*9+m[2]] else PAWN, 0))

class FastBoard:
    __slots__ = ('cells', 'side', 'rkx', 'rky', 'bkx', 'bky', 'hash', 'undo_stack')

    def __init__(self):
        self.cells = [None] * 90
        self.side = RED; self.rkx = 4; self.rky = 9; self.bkx = 4; self.bky = 0
        self.hash = 0; self.undo_stack = []
        for pt, sd, x, y in INITIAL_PIECES:
            self.cells[y * 9 + x] = (pt, sd)
        self.hash = self._compute_hash()

    def _compute_hash(self):
        h = 0
        for y in range(10):
            for x in range(9):
                c = self.cells[y * 9 + x]
                if c is not None: h ^= _zobrist_pieces[(y, x, c[0], c[1])]
        if self.side == BLACK: h ^= _zobrist_side
        return h

    def make_move(self, fx, fy, tx, ty):
        fi = fy * 9 + fx; ti = ty * 9 + tx
        piece = self.cells[fi]; captured = self.cells[ti]
        prev_hash = self.hash; prev_rkx = self.rkx; prev_rky = self.rky; prev_bkx = self.bkx; prev_bky = self.bky
        self.undo_stack.append((fx, fy, tx, ty, piece, captured, prev_hash, prev_rkx, prev_rky, prev_bkx, prev_bky))
        self.hash ^= _zobrist_pieces[(fy, fx, piece[0], piece[1])]
        if captured is not None: self.hash ^= _zobrist_pieces[(ty, tx, captured[0], captured[1])]
        self.hash ^= _zobrist_pieces[(ty, tx, piece[0], piece[1])]
        self.hash ^= _zobrist_side
        self.cells[fi] = None; self.cells[ti] = piece
        if piece[0] == KING:
            if piece[1] == RED: self.rkx = tx; self.rky = ty
            else: self.bkx = tx; self.bky = ty
        if captured is not None and captured[0] == KING:
            if captured[1] == RED: self.rkx = tx; self.rky = ty
            else: self.bkx = tx; self.bky = ty
        self.side = 1 - self.side

    def undo_move(self):
        if not self.undo_stack: return False
        fx, fy, tx, ty, piece, captured, prev_hash, prev_rkx, prev_rky, prev_bkx, prev_bky = self.undo_stack.pop()
        self.cells[fy * 9 + fx] = piece; self.cells[ty * 9 + tx] = captured
        self.rkx = prev_rkx; self.rky = prev_rky; self.bkx = prev_bkx; self.bky = prev_bky
        self.hash = prev_hash; self.side = 1 - self.side
        return True

    def from_fen(self, fen):
        parts = fen.split()
        if len(parts) < 2: return False
        self.cells = [None] * 90; self.rkx = 4; self.rky = 9; self.bkx = 4; self.bky = 0
        self.side = RED; self.undo_stack = []
        rows = parts[0].split('/')
        if len(rows) != 10: return False
        for y, row in enumerate(rows):
            x = 0
            for ch in row:
                if ch.isdigit(): x += int(ch)
                elif ch in FEN_PIECE_MAP:
                    pt, sd = FEN_PIECE_MAP[ch]
                    if x < 9:
                        self.cells[y * 9 + x] = (pt, sd)
                        if pt == KING:
                            if sd == RED: self.rkx = x; self.rky = y
                            else: self.bkx = x; self.bky = y
                    x += 1
        self.side = RED if parts[1] == 'w' else BLACK
        self.hash = self._compute_hash()
        return True

    def to_fen(self):
        fen = ""
        for y in range(10):
            empty = 0
            for x in range(9):
                c = self.cells[y * 9 + x]
                if c is not None:
                    if empty: fen += str(empty); empty = 0
                    fen_chars = {(KING,RED):'K',(ADVISOR,RED):'A',(BISHOP,RED):'B',(KNIGHT,RED):'N',(ROOK,RED):'R',(CANNON,RED):'C',(PAWN,RED):'P',(KING,BLACK):'k',(ADVISOR,BLACK):'a',(BISHOP,BLACK):'b',(KNIGHT,BLACK):'n',(ROOK,BLACK):'r',(CANNON,BLACK):'c',(PAWN,BLACK):'p'}
                    fen += fen_chars[c]
                else: empty += 1
            if empty: fen += str(empty)
            if y < 9: fen += '/'
        fen += ' ' + ('w' if self.side == RED else 'b') + ' - 0 1'
        return fen

    def clone(self):
        b = FastBoard.__new__(FastBoard)
        b.cells = self.cells[:]; b.side = self.side
        b.rkx = self.rkx; b.rky = self.rky; b.bkx = self.bkx; b.bky = self.bky
        b.hash = self.hash; b.undo_stack = []
        return b

class FastEngine:
    NULL_MOVE_DEPTH = 3
    LMR_MIN_DEPTH = 3
    LMR_MIN_MOVES = 4

    def __init__(self, thread_count=None):
        self.thread_count = thread_count or int(os.environ.get('XIANGQI_THREADS', os.cpu_count() or 4))
        self.tt = {}; self.killers = [[None, None] for _ in range(64)]
        self.nodes = 0; self.ht = [[0]*9 for _ in range(10)]
        self._pool = None

    def _get_pool(self):
        if self._pool is None and self.thread_count > 1:
            self._pool = ProcessPoolExecutor(max_workers=self.thread_count)
        return self._pool

    def clear(self):
        self.tt.clear(); self.killers = [[None, None] for _ in range(64)]; self.ht = [[0]*9 for _ in range(10)]

    def analyze(self, board, depth):
        self.nodes = 0; start = time.time()
        moves = gen_moves(board.cells, board.side, board.rkx, board.rky, board.bkx, board.bky)
        if not moves:
            kx = board.rkx if board.side == RED else board.bkx
            ky = board.rky if board.side == RED else board.bky
            score = -INFINITY_SCORE if _is_in_check(board.cells, board.side, kx, ky, board.rkx, board.rky, board.bkx, board.bky) else 0
            return {'best': None, 'score': score, 'candidates': [], 'path': [], 'nodes': 0, 'depth': depth, 'time': 0}
        best = None
        for d in range(1, depth + 1):
            best = self._search_depth(board, d)
        elapsed = int((time.time() - start) * 1000)
        best['time'] = elapsed; best['depth'] = depth
        return best

    def _search_depth(self, board, depth):
        self.nodes = 0
        moves = gen_moves(board.cells, board.side, board.rkx, board.rky, board.bkx, board.bky)
        if not moves:
            kx = board.rkx if board.side == RED else board.bkx
            ky = board.rky if board.side == RED else board.bky
            score = -INFINITY_SCORE if _is_in_check(board.cells, board.side, kx, ky, board.rkx, board.rky, board.bkx, board.bky) else 0
            return {'best': None, 'score': score, 'candidates': [], 'path': [], 'nodes': self.nodes, 'depth': depth, 'time': 0}
        self._order_root(board, moves)
        maximizing = board.side == RED
        pool = self._get_pool()
        if pool is not None and len(moves) > 1 and depth >= 3:
            return self._search_depth_mt(board, moves, depth, maximizing, pool)
        best_score = -INFINITY_SCORE if maximizing else INFINITY_SCORE
        best_move = moves[0]; candidates = []
        sb = board.clone()
        for i, (fx, fy, tx, ty) in enumerate(moves):
            sb.make_move(fx, fy, tx, ty)
            reduction = 0
            if depth >= self.LMR_MIN_DEPTH and i >= self.LMR_MIN_MOVES and sb.cells[ty * 9 + tx] is None:
                reduction = 1 + (i >= 8)
            s_depth = depth - 1 - reduction
            score = self._alpha_beta(sb, s_depth, -INFINITY_SCORE, INFINITY_SCORE, not maximizing, 0)
            if reduction > 0 and ((maximizing and score > best_score) or (not maximizing and score < best_score)):
                score = self._alpha_beta(sb, depth - 1, -INFINITY_SCORE, INFINITY_SCORE, not maximizing, 0)
            sb.undo_move()
            candidates.append(((fx, fy, tx, ty), score))
            if maximizing and score > best_score: best_score = score; best_move = (fx, fy, tx, ty)
            elif not maximizing and score < best_score: best_score = score; best_move = (fx, fy, tx, ty)
        if maximizing: candidates.sort(key=lambda c: -c[1])
        else: candidates.sort(key=lambda c: c[1])
        candidates = candidates[:3]
        path = self._get_path(board, best_move, depth)
        return {'best': best_move, 'score': best_score, 'candidates': candidates, 'path': path, 'nodes': self.nodes, 'depth': depth, 'time': 0}

    def _search_depth_mt(self, board, moves, depth, maximizing, pool):
        fen = board.to_fen()
        tt_hint = {}
        e = self.tt.get(board.hash)
        if e and e[2]:
            tt_hint[board.hash] = e
        futures = {}
        for move in moves:
            fx, fy, tx, ty = move
            futures[move] = pool.submit(_worker_root_search, fen, fx, fy, tx, ty, depth - 1, maximizing, tt_hint)
        best_score = -INFINITY_SCORE if maximizing else INFINITY_SCORE
        best_move = moves[0]; candidates = []
        total_nodes = 0
        for move, future in futures.items():
            result = future.result()
            score = result['score']; total_nodes += result['nodes']
            candidates.append((move, score))
            if maximizing and score > best_score: best_score = score; best_move = move
            elif not maximizing and score < best_score: best_score = score; best_move = move
        self.nodes = total_nodes
        if maximizing: candidates.sort(key=lambda c: -c[1])
        else: candidates.sort(key=lambda c: c[1])
        candidates = candidates[:3]
        path = self._get_path(board, best_move, depth)
        return {'best': best_move, 'score': best_score, 'candidates': candidates, 'path': path, 'nodes': total_nodes, 'depth': depth, 'time': 0}

    def _order_root(self, board, moves):
        moves.sort(key=lambda m: -PIECE_SORT_VALUES.get(board.cells[m[3]*9+m[2]][0] if board.cells[m[3]*9+m[2]] else PAWN, 0))
        e = self.tt.get(board.hash)
        if e and e[2]:
            for i, m in enumerate(moves):
                if m == e[2]: moves.insert(0, moves.pop(i)); break

    def _alpha_beta(self, board, depth, alpha, beta, maximizing, ply):
        self.nodes += 1
        e = self.tt.get(board.hash)
        if e and e[0] >= depth:
            ed, es, em, ef = e
            if ef == 0: return es
            elif ef == 1:
                if es >= beta: return es
                if es > alpha: alpha = es
            elif ef == 2:
                if es <= alpha: return es
                if es < beta: beta = es
        if depth <= 0:
            return _evaluate(board.cells, board.side, board.rkx, board.rky, board.bkx, board.bky)
        in_check = _is_in_check(board.cells, board.side,
                                 board.rkx if board.side == RED else board.bkx,
                                 board.rky if board.side == RED else board.bky,
                                 board.rkx, board.rky, board.bkx, board.bky)
        if not in_check and depth >= self.NULL_MOVE_DEPTH and ply > 0:
            board.side = 1 - board.side; board.hash ^= _zobrist_side
            nm_score = self._alpha_beta(board, depth - 2, alpha, beta, not maximizing, ply + 1)
            board.side = 1 - board.side; board.hash ^= _zobrist_side
            if maximizing and nm_score >= beta: return beta
            elif not maximizing and nm_score <= alpha: return alpha
        moves = gen_moves(board.cells, board.side, board.rkx, board.rky, board.bkx, board.bky)
        if not moves:
            if in_check:
                return -INFINITY_SCORE + ply if maximizing else INFINITY_SCORE - ply
            return 0
        self._order_moves(board, moves, ply)
        orig_alpha = alpha; best_score = -INFINITY_SCORE if maximizing else INFINITY_SCORE; best_move = moves[0]
        for i, (fx, fy, tx, ty) in enumerate(moves):
            is_cap = board.cells[ty * 9 + tx] is not None
            board.make_move(fx, fy, tx, ty)
            reduction = 0
            if depth >= self.LMR_MIN_DEPTH and i >= self.LMR_MIN_MOVES and not is_cap and not in_check:
                reduction = 1 + (i >= 8)
            s_depth = depth - 1 - reduction
            score = self._alpha_beta(board, s_depth, alpha, beta, not maximizing, ply + 1)
            if reduction > 0 and ((maximizing and score > alpha) or (not maximizing and score < beta)):
                score = self._alpha_beta(board, depth - 1, alpha, beta, not maximizing, ply + 1)
            board.undo_move()
            if maximizing:
                if score > best_score: best_score = score; best_move = (fx, fy, tx, ty)
                if score > alpha: alpha = score
                if alpha >= beta:
                    if not is_cap and ply < 64: self.killers[ply][1] = self.killers[ply][0]; self.killers[ply][0] = (fx, fy, tx, ty)
                    self.ht[fy][fx] += depth * depth; break
            else:
                if score < best_score: best_score = score; best_move = (fx, fy, tx, ty)
                if score < beta: beta = score
                if beta <= alpha:
                    if not is_cap and ply < 64: self.killers[ply][1] = self.killers[ply][0]; self.killers[ply][0] = (fx, fy, tx, ty)
                    self.ht[fy][fx] += depth * depth; break
        flag = 0
        if best_score <= orig_alpha: flag = 2
        elif best_score >= beta: flag = 1
        self.tt[board.hash] = (depth, best_score, best_move, flag)
        return best_score

    def _order_moves(self, board, moves, ply):
        def ms(m):
            s = 0; fx, fy, tx, ty = m
            e = self.tt.get(board.hash)
            if e and e[2] == m: s += 10000
            target = board.cells[ty * 9 + tx]
            if target is not None: s += PIECE_SORT_VALUES[target[0]] * 10 - PIECE_SORT_VALUES.get(board.cells[fy*9+fx][0], 0)
            if ply < 64:
                for k in range(2):
                    if self.killers[ply][k] == m: s += 9000 - k * 100
            s += self.ht[fy][fx]; return s
        moves.sort(key=lambda m: -ms(m))

    def _get_path(self, board, first_move, depth):
        path = [first_move]; sb = board.clone()
        sb.make_move(first_move[0], first_move[1], first_move[2], first_move[3])
        for _ in range(1, depth):
            e = self.tt.get(sb.hash)
            if e and e[2]:
                legal = gen_moves(sb.cells, sb.side, sb.rkx, sb.rky, sb.bkx, sb.bky)
                if e[2] in legal:
                    path.append(e[2]); sb.make_move(e[2][0], e[2][1], e[2][2], e[2][3]); continue
            break
        return path


def _worker_root_search(fen, fx, fy, tx, ty, depth, maximizing, tt_hint):
    board = FastBoard()
    board.from_fen(fen)
    board.make_move(fx, fy, tx, ty)
    engine = FastEngine(thread_count=1)
    engine.tt = tt_hint.copy()
    score = engine._alpha_beta(board, depth, -INFINITY_SCORE, INFINITY_SCORE, not maximizing, 0)
    return {'score': score, 'nodes': engine.nodes}
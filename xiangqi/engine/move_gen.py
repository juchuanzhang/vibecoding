from .types import Piece, PieceType, Side, Position, Move
from .board import Board


def generate_legal_moves(board: Board) -> list[Move]:
    return _generate_legal_moves_fast(board)


def _generate_legal_moves_fast(board: Board) -> list[Move]:
    side = board.side_to_move
    result = []
    for y in range(10):
        for x in range(9):
            idx = y * 9 + x
            piece = board.cells[idx]
            if piece is not None and piece.side == side:
                from_pos = Position(x, y)
                candidates = _generate_raw_moves(board, piece, from_pos)
                for to_pos in candidates:
                    mv = Move(from_pos, to_pos)
                    target = board.cells[to_pos.y * 9 + to_pos.x]
                    if target is not None and target.side == side:
                        continue
                    board.make_move_internal(mv)
                    legal = not _is_in_check_after_move(board, side)
                    board.undo_move_internal()
                    if legal:
                        result.append(mv)
    return result


def _is_in_check_after_move(board: Board, side: Side) -> bool:
    king_pos = board.red_king_pos if side == Side.Red else board.black_king_pos
    opponent = side.opponent()

    for oy in range(10):
        for ox in range(9):
            idx = oy * 9 + ox
            piece = board.cells[idx]
            if piece is not None and piece.side == opponent:
                from_pos = Position(ox, oy)
                if _can_attack_fast(board, piece, from_pos, king_pos):
                    return True

    red_king = board.red_king_pos
    black_king = board.black_king_pos
    if red_king.x == black_king.x:
        min_y = min(red_king.y, black_king.y)
        max_y = max(red_king.y, black_king.y)
        for cy in range(min_y + 1, max_y):
            if board.cells[cy * 9 + red_king.x] is not None:
                return False
        return True

    return False


def _can_attack_fast(board: Board, piece: Piece, from_pos: Position, king_pos: Position) -> bool:
    pt = piece.piece_type
    dx = king_pos.x - from_pos.x
    dy = king_pos.y - from_pos.y
    adx = abs(dx)
    ady = abs(dy)

    if pt == PieceType.Rook:
        if from_pos.x != king_pos.x and from_pos.y != king_pos.y:
            return False
        return _is_path_clear_fast(board, from_pos, king_pos)

    elif pt == PieceType.Cannon:
        if from_pos.x != king_pos.x and from_pos.y != king_pos.y:
            return False
        return _count_between_fast(board, from_pos, king_pos) == 1

    elif pt == PieceType.Knight:
        if not ((adx == 1 and ady == 2) or (adx == 2 and ady == 1)):
            return False
        if adx == 2:
            block_x = from_pos.x + dx // 2
            block_y = from_pos.y
        else:
            block_x = from_pos.x
            block_y = from_pos.y + dy // 2
        return board.cells[block_y * 9 + block_x] is None

    elif pt == PieceType.Pawn:
        forward = -1 if piece.side == Side.Red else 1
        past_river = from_pos.is_past_river(piece.side)
        if past_river:
            return (dy == forward and adx == 0) or (dy == 0 and adx == 1)
        else:
            return dy == forward and adx == 0

    elif pt == PieceType.King:
        if from_pos.x != king_pos.x:
            return False
        return _is_path_clear_fast(board, from_pos, king_pos)

    elif pt == PieceType.Advisor:
        return adx == 1 and ady == 1

    elif pt == PieceType.Bishop:
        if adx != 2 or ady != 2:
            return False
        eye_x = from_pos.x + dx // 2
        eye_y = from_pos.y + dy // 2
        return board.cells[eye_y * 9 + eye_x] is None

    return False


def _is_path_clear_fast(board: Board, from_pos: Position, to_pos: Position) -> bool:
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return False
    step_x = dx // steps
    step_y = dy // steps

    for i in range(1, steps):
        idx = (from_pos.y + step_y * i) * 9 + (from_pos.x + step_x * i)
        if board.cells[idx] is not None:
            return False
    return True


def _count_between_fast(board: Board, from_pos: Position, to_pos: Position) -> int:
    dx = to_pos.x - from_pos.x
    dy = to_pos.y - from_pos.y
    steps = max(abs(dx), abs(dy))
    step_x = dx // steps
    step_y = dy // steps

    count = 0
    for i in range(1, steps):
        idx = (from_pos.y + step_y * i) * 9 + (from_pos.x + step_x * i)
        if board.cells[idx] is not None:
            count += 1
    return count


def _generate_raw_moves(board: Board, piece: Piece, from_pos: Position) -> list[Position]:
    generators = {
        PieceType.King: _gen_king,
        PieceType.Advisor: _gen_advisor,
        PieceType.Bishop: _gen_bishop,
        PieceType.Knight: _gen_knight,
        PieceType.Rook: _gen_rook,
        PieceType.Cannon: _gen_cannon,
        PieceType.Pawn: _gen_pawn,
    }
    gen = generators[piece.piece_type]
    if piece.piece_type in (PieceType.Bishop, PieceType.Knight, PieceType.Rook, PieceType.Cannon):
        return gen(board, piece, from_pos)
    return gen(piece, from_pos)


def _gen_king(piece: Piece, from_pos: Position) -> list[Position]:
    moves = []
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx = from_pos.x + dx
        ny = from_pos.y + dy
        to_pos = Position(nx, ny)
        if 0 <= nx < 9 and 0 <= ny < 10 and to_pos.in_palace(piece.side):
            moves.append(to_pos)
    return moves


def _gen_advisor(piece: Piece, from_pos: Position) -> list[Position]:
    moves = []
    for dx, dy in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nx = from_pos.x + dx
        ny = from_pos.y + dy
        to_pos = Position(nx, ny)
        if 0 <= nx < 9 and 0 <= ny < 10 and to_pos.in_palace(piece.side):
            moves.append(to_pos)
    return moves


def _gen_bishop(board: Board, piece: Piece, from_pos: Position) -> list[Position]:
    moves = []
    for dx, dy in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
        nx = from_pos.x + dx
        ny = from_pos.y + dy
        if nx < 0 or nx >= 9 or ny < 0 or ny >= 10:
            continue
        to_pos = Position(nx, ny)
        if not to_pos.in_own_territory(piece.side):
            continue
        eye_x = from_pos.x + dx // 2
        eye_y = from_pos.y + dy // 2
        if board.cells[eye_y * 9 + eye_x] is not None:
            continue
        moves.append(to_pos)
    return moves


def _gen_knight(board: Board, piece: Piece, from_pos: Position) -> list[Position]:
    moves = []
    for dx, dy, bdx, bdy in [(2,1,1,0),(2,-1,1,0),(-2,1,-1,0),(-2,-1,-1,0),(1,2,0,1),(1,-2,0,-1),(-1,2,0,1),(-1,-2,0,-1)]:
        nx = from_pos.x + dx
        ny = from_pos.y + dy
        if nx < 0 or nx >= 9 or ny < 0 or ny >= 10:
            continue
        bx = from_pos.x + bdx
        by = from_pos.y + bdy
        if board.cells[by * 9 + bx] is not None:
            continue
        moves.append(Position(nx, ny))
    return moves


def _gen_rook(board: Board, piece: Piece, from_pos: Position) -> list[Position]:
    moves = []
    my_side = board.side_to_move
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx = from_pos.x + dx
        ny = from_pos.y + dy
        while 0 <= nx < 9 and 0 <= ny < 10:
            p = board.cells[ny * 9 + nx]
            if p is not None:
                if p.side != my_side:
                    moves.append(Position(nx, ny))
                break
            moves.append(Position(nx, ny))
            nx += dx
            ny += dy
    return moves


def _gen_cannon(board: Board, piece: Piece, from_pos: Position) -> list[Position]:
    moves = []
    my_side = board.side_to_move
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx = from_pos.x + dx
        ny = from_pos.y + dy
        jumped = False
        while 0 <= nx < 9 and 0 <= ny < 10:
            p = board.cells[ny * 9 + nx]
            if p is not None:
                if not jumped:
                    jumped = True
                else:
                    if p.side != my_side:
                        moves.append(Position(nx, ny))
                    break
            else:
                if not jumped:
                    moves.append(Position(nx, ny))
            nx += dx
            ny += dy
    return moves


def _gen_pawn(piece: Piece, from_pos: Position) -> list[Position]:
    moves = []
    forward = -1 if piece.side == Side.Red else 1
    fy = from_pos.y + forward
    if 0 <= fy < 10:
        moves.append(Position(from_pos.x, fy))

    past_river = from_pos.is_past_river(piece.side)
    if past_river:
        lx = from_pos.x - 1
        rx = from_pos.x + 1
        if lx >= 0:
            moves.append(Position(lx, from_pos.y))
        if rx < 9:
            moves.append(Position(rx, from_pos.y))
    return moves


PIECE_SORT_VALUES = {
    PieceType.King: 10000,
    PieceType.Rook: 600,
    PieceType.Cannon: 285,
    PieceType.Knight: 270,
    PieceType.Advisor: 120,
    PieceType.Bishop: 120,
    PieceType.Pawn: 30,
}


def sort_moves(board: Board, moves: list[Move]) -> list[Move]:
    return sorted(moves, key=lambda m: -PIECE_SORT_VALUES.get(
        board.cells[m.to_pos.y * 9 + m.to_pos.x].piece_type if board.cells[m.to_pos.y * 9 + m.to_pos.x] else PieceType.Pawn, 0))
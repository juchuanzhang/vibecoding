from .types import Piece, PieceType, Side, Position, Move
from .board import Board
from typing import Optional


def is_legal_move(board: Board, from_pos: Position, to_pos: Position) -> bool:
    if not from_pos.is_valid() or not to_pos.is_valid():
        return False
    if from_pos == to_pos:
        return False

    piece = board.piece_at(from_pos)
    if piece is None or piece.side != board.side_to_move:
        return False

    target = board.piece_at(to_pos)
    if target is not None and target.side == piece.side:
        return False

    if not _is_piece_move_valid(board, piece, from_pos, to_pos):
        return False

    board.make_move_internal(Move(from_pos, to_pos))
    in_check = _is_in_check_fast(board, piece.side)
    board.undo_move_internal()

    return not in_check


def _is_piece_move_valid(board: Board, piece: Piece, from_pos: Position, to_pos: Position) -> bool:
    pt = piece.piece_type.value
    side = piece.side

    if pt == 0:  # King
        if side == Side.Red:
            if to_pos.x < 3 or to_pos.x > 5 or to_pos.y < 7 or to_pos.y > 9:
                return False
        else:
            if to_pos.x < 3 or to_pos.x > 5 or to_pos.y < 0 or to_pos.y > 2:
                return False
        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)
        return dx + dy == 1

    elif pt == 1:  # Advisor
        if side == Side.Red:
            if to_pos.x < 3 or to_pos.x > 5 or to_pos.y < 7 or to_pos.y > 9:
                return False
        else:
            if to_pos.x < 3 or to_pos.x > 5 or to_pos.y < 0 or to_pos.y > 2:
                return False
        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)
        return dx == 1 and dy == 1

    elif pt == 2:  # Bishop
        if side == Side.Red:
            if to_pos.y < 5:
                return False
        else:
            if to_pos.y > 4:
                return False
        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)
        if dx != 2 or dy != 2:
            return False
        eye_x = from_pos.x + (to_pos.x - from_pos.x) // 2
        eye_y = from_pos.y + (to_pos.y - from_pos.y) // 2
        return board.cells[eye_y * 9 + eye_x] is None

    elif pt == 3:  # Knight
        dx = to_pos.x - from_pos.x
        dy = to_pos.y - from_pos.y
        adx = abs(dx)
        ady = abs(dy)
        if not ((adx == 1 and ady == 2) or (adx == 2 and ady == 1)):
            return False
        if adx == 2:
            block_idx = from_pos.y * 9 + (from_pos.x + dx // 2)
        else:
            block_idx = (from_pos.y + dy // 2) * 9 + from_pos.x
        return board.cells[block_idx] is None

    elif pt == 4:  # Rook
        if from_pos.x != to_pos.x and from_pos.y != to_pos.y:
            return False
        return _is_path_clear_fast(board, from_pos, to_pos)

    elif pt == 5:  # Cannon
        if from_pos.x != to_pos.x and from_pos.y != to_pos.y:
            return False
        target = board.cells[to_pos.y * 9 + to_pos.x]
        if target is not None:
            return _count_between_fast(board, from_pos, to_pos) == 1
        else:
            return _is_path_clear_fast(board, from_pos, to_pos)

    elif pt == 6:  # Pawn
        dx = abs(to_pos.x - from_pos.x)
        dy = to_pos.y - from_pos.y
        forward = -1 if side == Side.Red else 1
        if side == Side.Red:
            past_river = from_pos.y <= 4
        else:
            past_river = from_pos.y >= 5
        if past_river:
            return (dy == forward and dx == 0) or (dy == 0 and dx == 1)
        else:
            return dy == forward and dx == 0

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


def is_in_check(board: Board, side: Side) -> bool:
    return _is_in_check_fast(board, side)


def _is_in_check_fast(board: Board, side: Side) -> bool:
    if side == Side.Red:
        king_x, king_y = board.red_king_pos.x, board.red_king_pos.y
    else:
        king_x, king_y = board.black_king_pos.x, board.black_king_pos.y

    opponent = Side.Black if side == Side.Red else Side.Red
    king_idx = king_y * 9 + king_x

    # Check flying generals
    if board.red_king_pos.x == board.black_king_pos.x:
        ry = board.red_king_pos.y
        by = board.black_king_pos.y
        min_y = min(ry, by)
        max_y = max(ry, by)
        clear = True
        for y in range(min_y + 1, max_y):
            if board.cells[y * 9 + board.red_king_pos.x] is not None:
                clear = False
                break
        if clear:
            return True

    # Check all opponent pieces for attacks on king
    for y in range(10):
        for x in range(9):
            idx = y * 9 + x
            piece = board.cells[idx]
            if piece is None or piece.side != opponent:
                continue

            pt = piece.piece_type.value

            if pt == 4:  # Rook - same row or column, path clear
                if x == king_x or y == king_y:
                    if _is_path_clear_fast(board, Position(x, y), Position(king_x, king_y)):
                        return True

            elif pt == 5:  # Cannon - same row or column, exactly 1 between
                if x == king_x or y == king_y:
                    if _count_between_fast(board, Position(x, y), Position(king_x, king_y)) == 1:
                        return True

            elif pt == 3:  # Knight
                dx = abs(king_x - x)
                dy = abs(king_y - y)
                if (dx == 1 and dy == 2) or (dx == 2 and dy == 1):
                    if dx == 2:
                        block_idx = y * 9 + (x + (king_x - x) // 2)
                    else:
                        block_idx = (y + (king_y - y) // 2) * 9 + x
                    if board.cells[block_idx] is None:
                        return True

            elif pt == 6:  # Pawn
                dx = abs(king_x - x)
                dy = king_y - y
                forward = -1 if piece.side == Side.Red else 1
                if piece.side == Side.Red:
                    past_river = y <= 4
                else:
                    past_river = y >= 5
                if past_river:
                    if (dy == forward and dx == 0) or (dy == 0 and dx == 1):
                        return True
                else:
                    if dy == forward and dx == 0:
                        return True

    return False
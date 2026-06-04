from .types import Piece, PieceType, Side, Position
from .board import Board

PIECE_BASE_VALUES = {
    PieceType.King: 10000,
    PieceType.Advisor: 120,
    PieceType.Bishop: 120,
    PieceType.Knight: 270,
    PieceType.Rook: 600,
    PieceType.Cannon: 285,
    PieceType.Pawn: 30,
}
PAST_RIVER_PAWN_VALUE = 70
MID_PAWN_VALUE = 50

RED_KNIGHT_POS = [
    [  4,   8,  16,  12,  12,  12,  16,   8,   4],
    [  4,  10,  28,  16,   8,  16,  28,  10,   4],
    [ 12,  14,  16,  20,  18,  20,  16,  14,  12],
    [  8,  24,  18,  24,  20,  24,  18,  24,   8],
    [  6,  16,  14,  18,  16,  18,  14,  16,   6],
    [  4,  12,  16,  14,  12,  14,  16,  12,   4],
    [  2,   6,   8,   6,  10,   6,   8,   6,   2],
    [  4,   2,   8,   0,   8,   0,   8,   2,   4],
    [  0,   2,   4,   4,  -2,   4,   4,   2,   0],
    [  0,  -4,   0,   0,   0,   0,   0,  -4,   0],
]

RED_ROOK_POS = [
    [ 14,  14,  12,  18,  16,  18,  12,  14,  14],
    [ 16,  20,  18,  24,  26,  24,  18,  20,  16],
    [ 12,  12,  12,  18,  18,  18,  12,  12,  12],
    [ 12,  18,  16,  22,  22,  22,  16,  18,  12],
    [ 12,  14,  12,  18,  18,  18,  12,  14,  12],
    [ 12,  16,  14,  20,  20,  20,  14,  16,  12],
    [  6,  10,   8,  14,  14,  14,   8,  10,   6],
    [  4,   8,   6,  14,  12,  14,   6,   8,   4],
    [  8,   4,   8,  16,   8,  16,   8,   4,   8],
    [ -2,  10,   6,  14,  12,  14,   6,  10,  -2],
]

RED_CANNON_POS = [
    [  6,   4,   0, -10, -12, -10,   0,   4,   6],
    [  2,   2,   0,  -4, -14,  -4,   0,   2,   2],
    [  2,   2,   0, -10,  -8, -10,   0,   2,   2],
    [  0,   0,  -2,   4,  10,   4,  -2,   0,   0],
    [  0,   0,   0,   2,   8,   2,   0,   0,   0],
    [ -2,   0,   4,   2,   6,   2,   4,   0,  -2],
    [  0,   0,   0,   2,   8,   2,   0,   0,   0],
    [  4,   0,   8,   6,  10,   6,   8,   0,   4],
    [  0,   2,   4,   6,   6,   6,   4,   2,   0],
    [  0,   0,  -2,   0,   4,   0,  -2,   0,   0],
]

RED_PAWN_POS = [
    [  0,   3,   6,   9,  12,   9,   6,   3,   0],
    [ 18,  36,  56,  80, 120,  80,  56,  36,  18],
    [ 14,  26,  42,  60,  80,  60,  42,  26,  14],
    [ 10,  20,  30,  34,  40,  34,  30,  20,  10],
    [  6,  12,  18,  18,  20,  18,  18,  12,   6],
    [  2,   0,   8,   0,   8,   0,   8,   0,   2],
    [  0,   0,  -2,   0,   4,   0,  -2,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
]

RED_ADVISOR_POS = [
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,  20,   0,  20,   0,   0,   0],
    [  0,   0,   0,   0,  20,   0,   0,   0,   0],
]

RED_BISHOP_POS = [
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,  20,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,  20,   0,   0,   0,  20,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
]

RED_KING_POS_TABLE = [
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,  -8, -16,  -8,   0,   0,   0],
    [  0,   0,   0,  -8, -12,  -8,   0,   0,   0],
    [  0,   0,   0,   2,   8,   2,   0,   0,   0],
]

POS_TABLES = {
    PieceType.King: RED_KING_POS_TABLE,
    PieceType.Advisor: RED_ADVISOR_POS,
    PieceType.Bishop: RED_BISHOP_POS,
    PieceType.Knight: RED_KNIGHT_POS,
    PieceType.Rook: RED_ROOK_POS,
    PieceType.Cannon: RED_CANNON_POS,
    PieceType.Pawn: RED_PAWN_POS,
}


def _mirror_y(y: int, side: Side) -> int:
    return y if side == Side.Red else 9 - y


def _piece_value(piece: Piece, pos: Position) -> int:
    base = PIECE_BASE_VALUES[piece.piece_type]
    table = POS_TABLES[piece.piece_type]
    pos_val = table[_mirror_y(pos.y, piece.side)][pos.x]

    if piece.piece_type == PieceType.Pawn:
        past_river = pos.is_past_river(piece.side)
        mid_line = pos.x == 4 and past_river
        pawn_base = PAST_RIVER_PAWN_VALUE if past_river else base
        mid_bonus = MID_PAWN_VALUE if mid_line else 0
        return pawn_base + pos_val + mid_bonus
    else:
        return base + pos_val


def evaluate(board: Board) -> int:
    red_score = 0
    black_score = 0
    red_pieces_count = 0
    black_pieces_count = 0

    for y in range(10):
        for x in range(9):
            piece = board.cells[y * 9 + x]
            if piece is not None:
                val = _piece_value(piece, Position(x, y))
                if piece.side == Side.Red:
                    red_score += val
                    red_pieces_count += 1
                else:
                    black_score += val
                    black_pieces_count += 1

    total = red_score - black_score

    king_safety_red = _evaluate_king_safety(board, Side.Red, board.red_king_pos)
    king_safety_black = _evaluate_king_safety(board, Side.Black, board.black_king_pos)
    total += king_safety_red - king_safety_black

    if red_pieces_count <= 3 or black_pieces_count <= 3:
        return total * 2

    return total


def _evaluate_king_safety(board: Board, side: Side, king_pos: Position) -> int:
    score = 0
    opponent = side.opponent()

    for pos in board.all_pieces(opponent):
        piece = board.piece_at(pos)
        if piece is None:
            continue
        dist_x = abs(king_pos.x - pos.x)
        dist_y = abs(king_pos.y - pos.y)
        dist = dist_x + dist_y

        if piece.piece_type == PieceType.Rook:
            if pos.x == king_pos.x or pos.y == king_pos.y:
                score -= 40 - dist * 5
        elif piece.piece_type == PieceType.Cannon:
            if pos.x == king_pos.x or pos.y == king_pos.y:
                score -= 20 - dist * 3
        elif piece.piece_type == PieceType.Knight:
            if dist <= 5:
                score -= 15 - dist * 2

    palace_center_y = 8 if side == Side.Red else 1
    palace_center = Position(4, palace_center_y)
    dist_from_center = abs(king_pos.x - palace_center.x) + abs(king_pos.y - palace_center.y)
    score += (3 - dist_from_center) * 5

    return score
from .types import Piece, PieceType, Side, Position, Move


RED_COLS = ["九", "八", "七", "六", "五", "四", "三", "二", "一"]
BLACK_COLS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
RED_NUMS = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
BLACK_NUMS = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]


def describe_move(board, from_x: int, from_y: int, to_x: int, to_y: int) -> str:
    from_pos = Position(from_x, from_y)
    to_pos = Position(to_x, to_y)
    piece = board.piece_at(from_pos)
    if piece is None:
        return f"({from_x},{from_y})→({to_x},{to_y})"

    name = piece.display_name()

    from_col = RED_COLS[from_x] if piece.side == Side.Red else BLACK_COLS[from_x]

    dx = to_x - from_x
    dy = to_y - from_y

    is_line_piece = piece.piece_type in (PieceType.Rook, PieceType.Cannon, PieceType.Pawn, PieceType.King)

    if dx == 0:
        if piece.side == Side.Red:
            action = "进" if dy < 0 else "退"
        else:
            action = "进" if dy > 0 else "退"
    elif dy == 0:
        action = "平"
    else:
        if piece.side == Side.Red:
            action = "进" if dy < 0 else "退"
        else:
            action = "进" if dy > 0 else "退"

    if dx == 0 and is_line_piece:
        steps = abs(dy)
        dest = RED_NUMS[steps - 1] if piece.side == Side.Red else BLACK_NUMS[steps - 1]
    else:
        dest = RED_COLS[to_x] if piece.side == Side.Red else BLACK_COLS[to_x]

    return f"{name}{from_col}{action}{dest}"
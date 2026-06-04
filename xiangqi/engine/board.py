from .types import Piece, PieceType, Side, Position, Move
from typing import Optional


ZOBRIST_SEED = 1070372
ZOBRIST_PIECES = None
ZOBRIST_SIDE = None


def _init_zobrist():
    global ZOBRIST_PIECES, ZOBRIST_SIDE
    seed = ZOBRIST_SEED
    piece_types = list(PieceType)
    sides = list(Side)
    ZOBRIST_PIECES = {}
    for y in range(10):
        for x in range(9):
            for pt in piece_types:
                for s in sides:
                    seed = (seed * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
                    ZOBRIST_PIECES[(y, x, pt, s)] = seed
    seed = (seed * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
    ZOBRIST_SIDE = seed


_init_zobrist()


class _MoveUndoInfo:
    __slots__ = ('mv', 'captured', 'prev_hash', 'prev_red_king_pos', 'prev_black_king_pos')

    def __init__(self, mv, captured, prev_hash, prev_red_king_pos, prev_black_king_pos):
        self.mv = mv
        self.captured = captured
        self.prev_hash = prev_hash
        self.prev_red_king_pos = prev_red_king_pos
        self.prev_black_king_pos = prev_black_king_pos


class Board:
    __slots__ = ('cells', 'red_king_pos', 'black_king_pos', 'side_to_move', 'zobrist_hash', 'move_history')

    def __init__(self):
        self.cells: list[Optional[Piece]] = [None] * 90
        self.red_king_pos = Position(4, 9)
        self.black_king_pos = Position(4, 0)
        self.side_to_move = Side.Red
        self.zobrist_hash = 0
        self.move_history: list[_MoveUndoInfo] = []
        self._setup_initial_position()
        self.zobrist_hash = self._compute_hash()

    def _setup_initial_position(self):
        self._set_piece(Position(0, 9), Piece(PieceType.Rook, Side.Red))
        self._set_piece(Position(1, 9), Piece(PieceType.Knight, Side.Red))
        self._set_piece(Position(2, 9), Piece(PieceType.Bishop, Side.Red))
        self._set_piece(Position(3, 9), Piece(PieceType.Advisor, Side.Red))
        self._set_piece(Position(4, 9), Piece(PieceType.King, Side.Red))
        self._set_piece(Position(5, 9), Piece(PieceType.Advisor, Side.Red))
        self._set_piece(Position(6, 9), Piece(PieceType.Bishop, Side.Red))
        self._set_piece(Position(7, 9), Piece(PieceType.Knight, Side.Red))
        self._set_piece(Position(8, 9), Piece(PieceType.Rook, Side.Red))
        self._set_piece(Position(1, 7), Piece(PieceType.Cannon, Side.Red))
        self._set_piece(Position(7, 7), Piece(PieceType.Cannon, Side.Red))
        for x in [0, 2, 4, 6, 8]:
            self._set_piece(Position(x, 6), Piece(PieceType.Pawn, Side.Red))

        self._set_piece(Position(0, 0), Piece(PieceType.Rook, Side.Black))
        self._set_piece(Position(1, 0), Piece(PieceType.Knight, Side.Black))
        self._set_piece(Position(2, 0), Piece(PieceType.Bishop, Side.Black))
        self._set_piece(Position(3, 0), Piece(PieceType.Advisor, Side.Black))
        self._set_piece(Position(4, 0), Piece(PieceType.King, Side.Black))
        self._set_piece(Position(5, 0), Piece(PieceType.Advisor, Side.Black))
        self._set_piece(Position(6, 0), Piece(PieceType.Bishop, Side.Black))
        self._set_piece(Position(7, 0), Piece(PieceType.Knight, Side.Black))
        self._set_piece(Position(8, 0), Piece(PieceType.Rook, Side.Black))
        self._set_piece(Position(1, 2), Piece(PieceType.Cannon, Side.Black))
        self._set_piece(Position(7, 2), Piece(PieceType.Cannon, Side.Black))
        for x in [0, 2, 4, 6, 8]:
            self._set_piece(Position(x, 3), Piece(PieceType.Pawn, Side.Black))

        self.red_king_pos = Position(4, 9)
        self.black_king_pos = Position(4, 0)

    def _compute_hash(self) -> int:
        hash_val = 0
        for y in range(10):
            for x in range(9):
                piece = self.cells[y * 9 + x]
                if piece is not None:
                    hash_val ^= ZOBRIST_PIECES[(y, x, piece.piece_type, piece.side)]
        if self.side_to_move == Side.Black:
            hash_val ^= ZOBRIST_SIDE
        return hash_val

    def _set_piece(self, pos: Position, piece: Piece):
        self.cells[pos.index()] = piece

    def _clear_piece(self, pos: Position):
        self.cells[pos.index()] = None

    def piece_at(self, pos: Position) -> Optional[Piece]:
        if pos.is_valid():
            return self.cells[pos.index()]
        return None

    def all_pieces(self, side: Side) -> list[Position]:
        positions = []
        for y in range(10):
            for x in range(9):
                idx = y * 9 + x
                piece = self.cells[idx]
                if piece is not None and piece.side == side:
                    positions.append(Position(x, y))
        return positions

    def make_move_internal(self, move: Move) -> Optional[Piece]:
        captured = self.piece_at(move.to_pos)
        piece = self.piece_at(move.from_pos)

        prev_hash = self.zobrist_hash
        prev_red_king = self.red_king_pos
        prev_black_king = self.black_king_pos

        self.zobrist_hash ^= ZOBRIST_PIECES[(move.from_pos.y, move.from_pos.x, piece.piece_type, piece.side)]
        if captured is not None:
            self.zobrist_hash ^= ZOBRIST_PIECES[(move.to_pos.y, move.to_pos.x, captured.piece_type, captured.side)]
        self.zobrist_hash ^= ZOBRIST_PIECES[(move.to_pos.y, move.to_pos.x, piece.piece_type, piece.side)]
        self.zobrist_hash ^= ZOBRIST_SIDE

        self._clear_piece(move.from_pos)
        self._set_piece(move.to_pos, piece)

        if piece.piece_type == PieceType.King:
            if piece.side == Side.Red:
                self.red_king_pos = move.to_pos
            else:
                self.black_king_pos = move.to_pos

        if captured is not None and captured.piece_type == PieceType.King:
            if captured.side == Side.Red:
                self.red_king_pos = move.to_pos
            else:
                self.black_king_pos = move.to_pos

        self.side_to_move = self.side_to_move.opponent()

        self.move_history.append(_MoveUndoInfo(
            mv=move, captured=captured, prev_hash=prev_hash,
            prev_red_king_pos=prev_red_king, prev_black_king_pos=prev_black_king
        ))

        return captured

    def undo_move_internal(self) -> bool:
        if not self.move_history:
            return False
        undo = self.move_history.pop()

        piece = self.piece_at(undo.mv.to_pos)

        self._clear_piece(undo.mv.to_pos)
        self._set_piece(undo.mv.from_pos, piece)

        if undo.captured is not None:
            self._set_piece(undo.mv.to_pos, undo.captured)

        self.red_king_pos = undo.prev_red_king_pos
        self.black_king_pos = undo.prev_black_king_pos

        self.zobrist_hash = undo.prev_hash
        self.side_to_move = self.side_to_move.opponent()

        return True

    def clone_for_search(self) -> 'Board':
        b = Board.__new__(Board)
        b.cells = self.cells.copy()
        b.red_king_pos = self.red_king_pos
        b.black_king_pos = self.black_king_pos
        b.side_to_move = self.side_to_move
        b.zobrist_hash = self.zobrist_hash
        b.move_history = []
        return b

    @staticmethod
    def from_fen(fen: str) -> Optional['Board']:
        parts = fen.split()
        if len(parts) < 2:
            return None

        b = Board.__new__(Board)
        b.cells = [None] * 90
        b.red_king_pos = Position(4, 9)
        b.black_king_pos = Position(4, 0)
        b.side_to_move = Side.Red
        b.zobrist_hash = 0
        b.move_history = []

        rows = parts[0].split('/')
        if len(rows) != 10:
            return None

        for y, row in enumerate(rows):
            x = 0
            for ch in row:
                if ch.isdigit():
                    x += int(ch)
                else:
                    piece = Piece.from_fen_char(ch)
                    if piece is None:
                        return None
                    if x < 9:
                        pos = Position(x, y)
                        b._set_piece(pos, piece)
                        if piece.piece_type == PieceType.King:
                            if piece.side == Side.Red:
                                b.red_king_pos = pos
                            else:
                                b.black_king_pos = pos
                    x += 1

        b.side_to_move = Side.Red if parts[1] == 'w' else Side.Black
        b.zobrist_hash = b._compute_hash()
        return b

    def to_fen(self) -> str:
        fen = ""
        for y in range(10):
            empty_count = 0
            for x in range(9):
                piece = self.cells[y * 9 + x]
                if piece is not None:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    fen += piece.fen_char()
                else:
                    empty_count += 1
            if empty_count > 0:
                fen += str(empty_count)
            if y < 9:
                fen += '/'
        fen += ' '
        fen += 'w' if self.side_to_move == Side.Red else 'b'
        fen += ' - 0 1'
        return fen

    def move_history_len(self) -> int:
        return len(self.move_history)

    def get_last_move(self) -> Optional[Move]:
        if self.move_history:
            return self.move_history[-1].mv
        return None
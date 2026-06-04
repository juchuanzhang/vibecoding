from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class PieceType(Enum):
    King = 0
    Advisor = 1
    Bishop = 2
    Knight = 3
    Rook = 4
    Cannon = 5
    Pawn = 6


class Side(Enum):
    Red = 0
    Black = 1

    def opponent(self):
        return Side.Black if self == Side.Red else Side.Red


@dataclass
class Piece:
    piece_type: PieceType
    side: Side

    def display_name(self) -> str:
        red_names = {
            PieceType.King: "帅",
            PieceType.Advisor: "仕",
            PieceType.Bishop: "相",
            PieceType.Knight: "马",
            PieceType.Rook: "车",
            PieceType.Cannon: "炮",
            PieceType.Pawn: "兵",
        }
        black_names = {
            PieceType.King: "将",
            PieceType.Advisor: "士",
            PieceType.Bishop: "象",
            PieceType.Knight: "马",
            PieceType.Rook: "车",
            PieceType.Cannon: "炮",
            PieceType.Pawn: "卒",
        }
        names = red_names if self.side == Side.Red else black_names
        return names[self.piece_type]

    def base_value(self) -> int:
        values = {
            PieceType.King: 10000,
            PieceType.Advisor: 120,
            PieceType.Bishop: 120,
            PieceType.Knight: 270,
            PieceType.Rook: 600,
            PieceType.Cannon: 285,
            PieceType.Pawn: 30,
        }
        return values[self.piece_type]

    def fen_char(self) -> str:
        red_chars = {
            PieceType.King: 'K',
            PieceType.Advisor: 'A',
            PieceType.Bishop: 'B',
            PieceType.Knight: 'N',
            PieceType.Rook: 'R',
            PieceType.Cannon: 'C',
            PieceType.Pawn: 'P',
        }
        black_chars = {
            PieceType.King: 'k',
            PieceType.Advisor: 'a',
            PieceType.Bishop: 'b',
            PieceType.Knight: 'n',
            PieceType.Rook: 'r',
            PieceType.Cannon: 'c',
            PieceType.Pawn: 'p',
        }
        chars = red_chars if self.side == Side.Red else black_chars
        return chars[self.piece_type]

    @staticmethod
    def from_fen_char(ch: str) -> Optional['Piece']:
        red_map = {'K': PieceType.King, 'A': PieceType.Advisor, 'B': PieceType.Bishop,
                    'N': PieceType.Knight, 'R': PieceType.Rook, 'C': PieceType.Cannon, 'P': PieceType.Pawn}
        black_map = {'k': PieceType.King, 'a': PieceType.Advisor, 'b': PieceType.Bishop,
                      'n': PieceType.Knight, 'r': PieceType.Rook, 'c': PieceType.Cannon, 'p': PieceType.Pawn}
        if ch in red_map:
            return Piece(red_map[ch], Side.Red)
        if ch in black_map:
            return Piece(black_map[ch], Side.Black)
        return None


class Position:
    __slots__ = ('x', 'y')

    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return self.x * 10 + self.y

    def index(self) -> int:
        return self.y * 9 + self.x

    def is_valid(self) -> bool:
        return 0 <= self.x < 9 and 0 <= self.y < 10

    def in_palace(self, side: Side) -> bool:
        if side == Side.Red:
            return 3 <= self.x <= 5 and 7 <= self.y <= 9
        else:
            return 3 <= self.x <= 5 and 0 <= self.y <= 2

    def in_own_territory(self, side: Side) -> bool:
        if side == Side.Red:
            return self.y >= 5
        else:
            return self.y <= 4

    def is_past_river(self, side: Side) -> bool:
        if side == Side.Red:
            return self.y <= 4
        else:
            return self.y >= 5


class Move:
    __slots__ = ('from_pos', 'to_pos')
    from_pos: Position
    to_pos: Position

    def __init__(self, from_pos: Position, to_pos: Position):
        self.from_pos = from_pos
        self.to_pos = to_pos

    def __eq__(self, other):
        if other is None:
            return False
        return self.from_pos == other.from_pos and self.to_pos == other.to_pos

    def __hash__(self):
        return hash((self.from_pos, self.to_pos))


@dataclass
class MoveRecord:
    piece: Piece
    from_pos: Position
    to_pos: Position
    captured: Optional[Piece]
    description: str
    move_number: int
    side: Side


@dataclass
class AnalysisResult:
    best_move: Optional[Move]
    score: int
    candidates: list
    search_path: list
    nodes_searched: int
    time_ms: int
    depth: int


@dataclass
class CandidateMove:
    move: Move
    score: int


class GameStatus(Enum):
    Playing = 0
    RedWin = 1
    BlackWin = 2
    Draw = 3
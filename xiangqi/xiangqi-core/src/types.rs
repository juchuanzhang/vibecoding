#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PieceType {
    King,
    Advisor,
    Bishop,
    Knight,
    Rook,
    Cannon,
    Pawn,
}

#[repr(u8)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Side {
    Red,
    Black,
}

impl Side {
    pub fn opponent(&self) -> Side {
        match self {
            Side::Red => Side::Black,
            Side::Black => Side::Red,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Piece {
    pub piece_type: PieceType,
    pub side: Side,
}

impl Piece {
    pub fn new(piece_type: PieceType, side: Side) -> Self {
        Piece { piece_type, side }
    }

    pub fn display_name(&self) -> &str {
        match self.side {
            Side::Red => match self.piece_type {
                PieceType::King => "帅",
                PieceType::Advisor => "仕",
                PieceType::Bishop => "相",
                PieceType::Knight => "马",
                PieceType::Rook => "车",
                PieceType::Cannon => "炮",
                PieceType::Pawn => "兵",
            },
            Side::Black => match self.piece_type {
                PieceType::King => "将",
                PieceType::Advisor => "士",
                PieceType::Bishop => "象",
                PieceType::Knight => "马",
                PieceType::Rook => "车",
                PieceType::Cannon => "炮",
                PieceType::Pawn => "卒",
            },
        }
    }

    pub fn base_value(&self) -> i32 {
        match self.piece_type {
            PieceType::King => 10000,
            PieceType::Advisor => 200,
            PieceType::Bishop => 200,
            PieceType::Knight => 400,
            PieceType::Rook => 900,
            PieceType::Cannon => 450,
            PieceType::Pawn => 100,
        }
    }

    pub fn pawn_value_past_river() -> i32 {
        200
    }

    pub fn fen_char(&self) -> char {
        match self.side {
            Side::Red => match self.piece_type {
                PieceType::King => 'K',
                PieceType::Advisor => 'A',
                PieceType::Bishop => 'B',
                PieceType::Knight => 'N',
                PieceType::Rook => 'R',
                PieceType::Cannon => 'C',
                PieceType::Pawn => 'P',
            },
            Side::Black => match self.piece_type {
                PieceType::King => 'k',
                PieceType::Advisor => 'a',
                PieceType::Bishop => 'b',
                PieceType::Knight => 'n',
                PieceType::Rook => 'r',
                PieceType::Cannon => 'c',
                PieceType::Pawn => 'p',
            },
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Position {
    pub x: u8,
    pub y: u8,
}

impl Position {
    pub fn new(x: u8, y: u8) -> Self {
        Position { x, y }
    }

    pub fn index(&self) -> usize {
        (self.y as usize) * 9 + (self.x as usize)
    }

    pub fn is_valid(&self) -> bool {
        self.x < 9 && self.y < 10
    }

    pub fn in_palace(&self, side: Side) -> bool {
        match side {
            Side::Red => self.x >= 3 && self.x <= 5 && self.y >= 7 && self.y <= 9,
            Side::Black => self.x >= 3 && self.x <= 5 && self.y <= 2,
        }
    }

    pub fn in_own_territory(&self, side: Side) -> bool {
        match side {
            Side::Red => self.y >= 5,
            Side::Black => self.y <= 4,
        }
    }

    pub fn is_past_river(&self, side: Side) -> bool {
        match side {
            Side::Red => self.y <= 4,
            Side::Black => self.y >= 5,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Move {
    pub from: Position,
    pub to: Position,
}

impl Move {
    pub fn new(from: Position, to: Position) -> Self {
        Move { from, to }
    }
}

pub struct MoveRecord {
    pub piece: Piece,
    pub from: Position,
    pub to: Position,
    pub captured: Option<Piece>,
    pub description: String,
    pub move_number: u32,
    pub side: Side,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GameStatus {
    Playing,
    RedWin,
    BlackWin,
    Draw,
}
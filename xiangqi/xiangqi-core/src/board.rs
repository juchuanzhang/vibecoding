use crate::types::*;

pub struct Board {
    cells: [Option<Piece>; 90],
    red_king_pos: Position,
    black_king_pos: Position,
    side_to_move: Side,
    zobrist_hash: u64,
    move_history: Vec<MoveUndoInfo>,
}

struct MoveUndoInfo {
    mv: Move,
    captured: Option<Piece>,
    prev_hash: u64,
    prev_red_king_pos: Position,
    prev_black_king_pos: Position,
}

static ZOBRIST_PIECES: [[[[u64; 2]; 7]; 9]; 10] = {
    let mut table = [[[[0u64; 2]; 7]; 9]; 10];
    let mut seed = 1070372u64;
    let mut i = 0;
    while i < 10 {
        let mut j = 0;
        while j < 9 {
            let mut k = 0;
            while k < 7 {
                let mut l = 0;
                while l < 2 {
                    seed = (seed.wrapping_mul(6364136223846793005)).wrapping_add(1442695040888963407);
                    table[i][j][k][l] = seed;
                    l += 1;
                }
                k += 1;
            }
            j += 1;
        }
        i += 1;
    }
    table
};

static ZOBRIST_SIDE: u64 = {
    let mut seed = 1070372u64;
    seed = (seed.wrapping_mul(6364136223846793005)).wrapping_add(1442695040888963407);
    seed = (seed.wrapping_mul(6364136223846793005)).wrapping_add(1442695040888963407);
    seed
};

fn piece_type_index(pt: PieceType) -> usize {
    match pt {
        PieceType::King => 0,
        PieceType::Advisor => 1,
        PieceType::Bishop => 2,
        PieceType::Knight => 3,
        PieceType::Rook => 4,
        PieceType::Cannon => 5,
        PieceType::Pawn => 6,
    }
}

fn side_index(s: Side) -> usize {
    match s {
        Side::Red => 0,
        Side::Black => 1,
    }
}

impl Board {
    pub fn new() -> Self {
        let mut board = Board {
            cells: [None; 90],
            red_king_pos: Position::new(4, 9),
            black_king_pos: Position::new(4, 0),
            side_to_move: Side::Red,
            zobrist_hash: 0,
            move_history: Vec::new(),
        };
        board.setup_initial_position();
        board.zobrist_hash = board.compute_hash();
        board
    }

    fn setup_initial_position(&mut self) {
        self.set_piece(Position::new(0, 9), Piece::new(PieceType::Rook, Side::Red));
        self.set_piece(Position::new(1, 9), Piece::new(PieceType::Knight, Side::Red));
        self.set_piece(Position::new(2, 9), Piece::new(PieceType::Bishop, Side::Red));
        self.set_piece(Position::new(3, 9), Piece::new(PieceType::Advisor, Side::Red));
        self.set_piece(Position::new(4, 9), Piece::new(PieceType::King, Side::Red));
        self.set_piece(Position::new(5, 9), Piece::new(PieceType::Advisor, Side::Red));
        self.set_piece(Position::new(6, 9), Piece::new(PieceType::Bishop, Side::Red));
        self.set_piece(Position::new(7, 9), Piece::new(PieceType::Knight, Side::Red));
        self.set_piece(Position::new(8, 9), Piece::new(PieceType::Rook, Side::Red));

        self.set_piece(Position::new(1, 7), Piece::new(PieceType::Cannon, Side::Red));
        self.set_piece(Position::new(7, 7), Piece::new(PieceType::Cannon, Side::Red));

        for x in [0, 2, 4, 6, 8] {
            self.set_piece(Position::new(x, 6), Piece::new(PieceType::Pawn, Side::Red));
        }

        self.set_piece(Position::new(0, 0), Piece::new(PieceType::Rook, Side::Black));
        self.set_piece(Position::new(1, 0), Piece::new(PieceType::Knight, Side::Black));
        self.set_piece(Position::new(2, 0), Piece::new(PieceType::Bishop, Side::Black));
        self.set_piece(Position::new(3, 0), Piece::new(PieceType::Advisor, Side::Black));
        self.set_piece(Position::new(4, 0), Piece::new(PieceType::King, Side::Black));
        self.set_piece(Position::new(5, 0), Piece::new(PieceType::Advisor, Side::Black));
        self.set_piece(Position::new(6, 0), Piece::new(PieceType::Bishop, Side::Black));
        self.set_piece(Position::new(7, 0), Piece::new(PieceType::Knight, Side::Black));
        self.set_piece(Position::new(8, 0), Piece::new(PieceType::Rook, Side::Black));

        self.set_piece(Position::new(1, 2), Piece::new(PieceType::Cannon, Side::Black));
        self.set_piece(Position::new(7, 2), Piece::new(PieceType::Cannon, Side::Black));

        for x in [0, 2, 4, 6, 8] {
            self.set_piece(Position::new(x, 3), Piece::new(PieceType::Pawn, Side::Black));
        }

        self.red_king_pos = Position::new(4, 9);
        self.black_king_pos = Position::new(4, 0);
    }

    fn compute_hash(&self) -> u64 {
        let mut hash = 0;
        for y in 0..10 {
            for x in 0..9 {
                if let Some(piece) = self.cells[y * 9 + x] {
                    hash ^= ZOBRIST_PIECES[y][x][piece_type_index(piece.piece_type)][side_index(piece.side)];
                }
            }
        }
        if self.side_to_move == Side::Black {
            hash ^= ZOBRIST_SIDE;
        }
        hash
    }

    fn set_piece(&mut self, pos: Position, piece: Piece) {
        self.cells[pos.index()] = Some(piece);
    }

    fn clear_piece(&mut self, pos: Position) {
        self.cells[pos.index()] = None;
    }

    pub fn piece_at(&self, pos: Position) -> Option<Piece> {
        if pos.is_valid() {
            self.cells[pos.index()]
        } else {
            None
        }
    }

    pub fn side_to_move(&self) -> Side {
        self.side_to_move
    }

    pub fn zobrist_hash(&self) -> u64 {
        self.zobrist_hash
    }

    pub fn red_king_pos(&self) -> Position {
        self.red_king_pos
    }

    pub fn black_king_pos(&self) -> Position {
        self.black_king_pos
    }

    pub fn all_pieces(&self, side: Side) -> Vec<Position> {
        let mut positions = Vec::new();
        for y in 0..10 {
            for x in 0..9 {
                let idx = y * 9 + x;
                if let Some(piece) = self.cells[idx] {
                    if piece.side == side {
                        positions.push(Position::new(x as u8, y as u8));
                    }
                }
            }
        }
        positions
    }

    pub fn make_move_internal(&mut self, move_: Move) -> Option<Piece> {
        let captured = self.piece_at(move_.to);
        let piece = self.piece_at(move_.from).unwrap();

        let prev_hash = self.zobrist_hash;
        let prev_red_king = self.red_king_pos;
        let prev_black_king = self.black_king_pos;

        self.zobrist_hash ^= ZOBRIST_PIECES[move_.from.y as usize][move_.from.x as usize][piece_type_index(piece.piece_type)][side_index(piece.side)];
        if let Some(cap) = captured {
            self.zobrist_hash ^= ZOBRIST_PIECES[move_.to.y as usize][move_.to.x as usize][piece_type_index(cap.piece_type)][side_index(cap.side)];
        }
        self.zobrist_hash ^= ZOBRIST_PIECES[move_.to.y as usize][move_.to.x as usize][piece_type_index(piece.piece_type)][side_index(piece.side)];
        self.zobrist_hash ^= ZOBRIST_SIDE;

        self.clear_piece(move_.from);
        self.set_piece(move_.to, piece);

        if piece.piece_type == PieceType::King {
            match piece.side {
                Side::Red => self.red_king_pos = move_.to,
                Side::Black => self.black_king_pos = move_.to,
            }
        }

        if let Some(cap) = captured {
            if cap.piece_type == PieceType::King {
                match cap.side {
                    Side::Red => self.red_king_pos = move_.to,
                    Side::Black => self.black_king_pos = move_.to,
                }
            }
        }

        self.side_to_move = self.side_to_move.opponent();

        self.move_history.push(MoveUndoInfo {
            mv: move_,
            captured,
            prev_hash,
            prev_red_king_pos: prev_red_king,
            prev_black_king_pos: prev_black_king,
        });

        captured
    }

    pub fn undo_move_internal(&mut self) -> bool {
        if self.move_history.is_empty() {
            return false;
        }
        let undo = self.move_history.pop().unwrap();

        let piece = self.piece_at(undo.mv.to).unwrap();

        self.clear_piece(undo.mv.to);
        self.set_piece(undo.mv.from, piece);

        if let Some(cap) = undo.captured {
            self.set_piece(undo.mv.to, cap);
        }

        if piece.piece_type == PieceType::King {
            match piece.side {
                Side::Red => self.red_king_pos = undo.prev_red_king_pos,
                Side::Black => self.black_king_pos = undo.prev_black_king_pos,
            }
        }

        self.red_king_pos = undo.prev_red_king_pos;
        self.black_king_pos = undo.prev_black_king_pos;

        self.zobrist_hash = undo.prev_hash;
        self.side_to_move = self.side_to_move.opponent();

        true
    }

    pub fn move_history_len(&self) -> usize {
        self.move_history.len()
    }

    pub fn get_last_move(&self) -> Option<Move> {
        self.move_history.last().map(|undo| undo.mv)
    }

    pub fn clone_for_search(&self) -> Board {
        Board {
            cells: self.cells,
            red_king_pos: self.red_king_pos,
            black_king_pos: self.black_king_pos,
            side_to_move: self.side_to_move,
            zobrist_hash: self.zobrist_hash,
            move_history: Vec::new(),
        }
    }

    pub fn from_fen(fen: &str) -> Option<Self> {
        let parts: Vec<&str> = fen.split_whitespace().collect();
        if parts.len() < 2 {
            return None;
        }

        let mut board = Board {
            cells: [None; 90],
            red_king_pos: Position::new(4, 9),
            black_king_pos: Position::new(4, 0),
            side_to_move: Side::Red,
            zobrist_hash: 0,
            move_history: Vec::new(),
        };

        let rows: Vec<&str> = parts[0].split('/').collect();
        if rows.len() != 10 {
            return None;
        }

        for (y, row) in rows.iter().enumerate() {
            let mut x = 0;
            for ch in row.chars() {
                if ch.is_digit(10) {
                    x += ch.to_digit(10).unwrap() as usize;
                } else {
                    let piece = Board::piece_from_fen_char(ch)?;
                    if x < 9 {
                        board.set_piece(Position::new(x as u8, y as u8), piece);
                        if piece.piece_type == PieceType::King {
                            match piece.side {
                                Side::Red => board.red_king_pos = Position::new(x as u8, y as u8),
                                Side::Black => board.black_king_pos = Position::new(x as u8, y as u8),
                            }
                        }
                    }
                    x += 1;
                }
            }
        }

        board.side_to_move = match parts[1] {
            "w" => Side::Red,
            "b" => Side::Black,
            _ => Side::Red,
        };

        board.zobrist_hash = board.compute_hash();
        Some(board)
    }

    pub fn to_fen(&self) -> String {
        let mut fen = String::new();
        for y in 0..10 {
            let mut empty_count = 0;
            for x in 0..9 {
                if let Some(piece) = self.cells[y * 9 + x] {
                    if empty_count > 0 {
                        fen.push_str(&empty_count.to_string());
                        empty_count = 0;
                    }
                    fen.push(piece.fen_char());
                } else {
                    empty_count += 1;
                }
            }
            if empty_count > 0 {
                fen.push_str(&empty_count.to_string());
            }
            if y < 9 {
                fen.push('/');
            }
        }
        fen.push(' ');
        fen.push(match self.side_to_move {
            Side::Red => 'w',
            Side::Black => 'b',
        });
        fen.push_str(" - 0 1");
        fen
    }

    fn piece_from_fen_char(ch: char) -> Option<Piece> {
        match ch {
            'K' => Some(Piece::new(PieceType::King, Side::Red)),
            'A' => Some(Piece::new(PieceType::Advisor, Side::Red)),
            'B' => Some(Piece::new(PieceType::Bishop, Side::Red)),
            'N' => Some(Piece::new(PieceType::Knight, Side::Red)),
            'R' => Some(Piece::new(PieceType::Rook, Side::Red)),
            'C' => Some(Piece::new(PieceType::Cannon, Side::Red)),
            'P' => Some(Piece::new(PieceType::Pawn, Side::Red)),
            'k' => Some(Piece::new(PieceType::King, Side::Black)),
            'a' => Some(Piece::new(PieceType::Advisor, Side::Black)),
            'b' => Some(Piece::new(PieceType::Bishop, Side::Black)),
            'n' => Some(Piece::new(PieceType::Knight, Side::Black)),
            'r' => Some(Piece::new(PieceType::Rook, Side::Black)),
            'c' => Some(Piece::new(PieceType::Cannon, Side::Black)),
            'p' => Some(Piece::new(PieceType::Pawn, Side::Black)),
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initial_position() {
        let board = Board::new();
        assert_eq!(board.piece_at(Position::new(4, 9)), Some(Piece::new(PieceType::King, Side::Red)));
        assert_eq!(board.piece_at(Position::new(4, 0)), Some(Piece::new(PieceType::King, Side::Black)));
        assert_eq!(board.piece_at(Position::new(0, 0)), Some(Piece::new(PieceType::Rook, Side::Black)));
        assert_eq!(board.piece_at(Position::new(8, 9)), Some(Piece::new(PieceType::Rook, Side::Red)));
        assert_eq!(board.side_to_move(), Side::Red);
    }

    #[test]
    fn test_fen_roundtrip() {
        let board = Board::new();
        let fen = board.to_fen();
        let board2 = Board::from_fen(&fen).unwrap();
        let fen2 = board2.to_fen();
        assert_eq!(fen, fen2);
    }

    #[test]
    fn test_make_undo_move() {
        let mut board = Board::new();
        let m = Move::new(Position::new(1, 7), Position::new(4, 7));
        let captured = board.make_move_internal(m);
        assert_eq!(captured, None);
        assert_eq!(board.piece_at(Position::new(4, 7)), Some(Piece::new(PieceType::Cannon, Side::Red)));
        assert_eq!(board.piece_at(Position::new(1, 7)), None);
        assert_eq!(board.side_to_move(), Side::Black);

        board.undo_move_internal();
        assert_eq!(board.piece_at(Position::new(1, 7)), Some(Piece::new(PieceType::Cannon, Side::Red)));
        assert_eq!(board.piece_at(Position::new(4, 7)), None);
    }

    #[test]
    fn test_zobrist_consistency() {
        let board = Board::new();
        let hash1 = board.compute_hash();
        let hash2 = board.zobrist_hash();
        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_zobrist_incremental() {
        let mut board = Board::new();
        let initial_hash = board.zobrist_hash();
        let m = Move::new(Position::new(1, 7), Position::new(4, 7));
        board.make_move_internal(m);
        let after_hash = board.zobrist_hash();
        assert_ne!(initial_hash, after_hash);

        board.undo_move_internal();
        assert_eq!(board.zobrist_hash(), initial_hash);
    }
}
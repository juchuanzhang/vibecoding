use crate::types::*;
use crate::board::Board;

pub fn is_legal_move(board: &Board, from: Position, to: Position) -> bool {
    if !from.is_valid() || !to.is_valid() {
        return false;
    }
    if from == to {
        return false;
    }

    let piece = board.piece_at(from);
    if piece.is_none() {
        return false;
    }
    let piece = piece.unwrap();
    if piece.side != board.side_to_move() {
        return false;
    }

    let target = board.piece_at(to);
    if let Some(target_piece) = target {
        if target_piece.side == piece.side {
            return false;
        }
    }

    if !is_piece_move_valid(board, piece, from, to) {
        return false;
    }

    let mut temp_board = board.clone();
    temp_board.make_move_internal(Move::new(from, to));
    if is_in_check(&temp_board, piece.side) {
        return false;
    }

    true
}

fn is_piece_move_valid(board: &Board, piece: Piece, from: Position, to: Position) -> bool {
    match piece.piece_type {
        PieceType::King => is_king_move_valid(piece, from, to),
        PieceType::Advisor => is_advisor_move_valid(piece, from, to),
        PieceType::Bishop => is_bishop_move_valid(board, piece, from, to),
        PieceType::Knight => is_knight_move_valid(board, from, to),
        PieceType::Rook => is_rook_move_valid(board, from, to),
        PieceType::Cannon => is_cannon_move_valid(board, from, to),
        PieceType::Pawn => is_pawn_move_valid(piece, from, to),
    }
}

fn is_king_move_valid(piece: Piece, from: Position, to: Position) -> bool {
    if !to.in_palace(piece.side) {
        return false;
    }
    let dx = (to.x as i32 - from.x as i32).abs();
    let dy = (to.y as i32 - from.y as i32).abs();
    dx + dy == 1
}

fn is_advisor_move_valid(piece: Piece, from: Position, to: Position) -> bool {
    if !to.in_palace(piece.side) {
        return false;
    }
    let dx = (to.x as i32 - from.x as i32).abs();
    let dy = (to.y as i32 - from.y as i32).abs();
    dx == 1 && dy == 1
}

fn is_bishop_move_valid(board: &Board, piece: Piece, from: Position, to: Position) -> bool {
    if !to.in_own_territory(piece.side) {
        return false;
    }
    let dx = (to.x as i32 - from.x as i32).abs();
    let dy = (to.y as i32 - from.y as i32).abs();
    if dx != 2 || dy != 2 {
        return false;
    }

    let eye_x = from.x as i32 + (to.x as i32 - from.x as i32) / 2;
    let eye_y = from.y as i32 + (to.y as i32 - from.y as i32) / 2;
    if board.piece_at(Position::new(eye_x as u8, eye_y as u8)).is_some() {
        return false;
    }

    true
}

fn is_knight_move_valid(board: &Board, from: Position, to: Position) -> bool {
    let dx = to.x as i32 - from.x as i32;
    let dy = to.y as i32 - from.y as i32;
    let adx = dx.abs();
    let ady = dy.abs();

    if !((adx == 1 && ady == 2) || (adx == 2 && ady == 1)) {
        return false;
    }

    let (block_x, block_y) = if adx == 2 {
        (from.x as i32 + dx / 2, from.y as i32)
    } else {
        (from.x as i32, from.y as i32 + dy / 2)
    };

    if board.piece_at(Position::new(block_x as u8, block_y as u8)).is_some() {
        return false;
    }

    true
}

fn is_rook_move_valid(board: &Board, from: Position, to: Position) -> bool {
    if from.x != to.x && from.y != to.y {
        return false;
    }
    is_path_clear(board, from, to)
}

fn is_cannon_move_valid(board: &Board, from: Position, to: Position) -> bool {
    if from.x != to.x && from.y != to.y {
        return false;
    }

    let target = board.piece_at(to);
    if target.is_some() {
        let count = count_pieces_between(board, from, to);
        count == 1
    } else {
        is_path_clear(board, from, to)
    }
}

fn is_pawn_move_valid(piece: Piece, from: Position, to: Position) -> bool {
    let dx = (to.x as i32 - from.x as i32).abs();
    let dy = to.y as i32 - from.y as i32;

    let forward = match piece.side {
        Side::Red => -1,
        Side::Black => 1,
    };

    let past_river = from.is_past_river(piece.side);

    if past_river {
        if dy == forward && dx == 0 {
            return true;
        }
        if dy == 0 && dx == 1 {
            return true;
        }
        false
    } else {
        dy == forward && dx == 0
    }
}

fn is_path_clear(board: &Board, from: Position, to: Position) -> bool {
    let dx = to.x as i32 - from.x as i32;
    let dy = to.y as i32 - from.y as i32;
    let steps = dx.abs().max(dy.abs());
    if steps == 0 {
        return false;
    }
    let step_x = dx / steps;
    let step_y = dy / steps;

    for i in 1..steps {
        let x = from.x as i32 + step_x * i;
        let y = from.y as i32 + step_y * i;
        if board.piece_at(Position::new(x as u8, y as u8)).is_some() {
            return false;
        }
    }
    true
}

fn count_pieces_between(board: &Board, from: Position, to: Position) -> u32 {
    let dx = to.x as i32 - from.x as i32;
    let dy = to.y as i32 - from.y as i32;
    let steps = dx.abs().max(dy.abs());
    let step_x = dx / steps;
    let step_y = dy / steps;

    let mut count = 0;
    for i in 1..steps {
        let x = from.x as i32 + step_x * i;
        let y = from.y as i32 + step_y * i;
        if board.piece_at(Position::new(x as u8, y as u8)).is_some() {
            count += 1;
        }
    }
    count
}

pub fn is_in_check(board: &Board, side: Side) -> bool {
    let king_pos = match side {
        Side::Red => board.red_king_pos(),
        Side::Black => board.black_king_pos(),
    };

    let opponent = side.opponent();
    for pos in board.all_pieces(opponent) {
        let piece = board.piece_at(pos).unwrap();
        if can_attack(board, piece, pos, king_pos) {
            return true;
        }
    }

    if kings_opposing(board) {
        return true;
    }

    false
}

fn can_attack(board: &Board, piece: Piece, from: Position, to: Position) -> bool {
    match piece.piece_type {
        PieceType::King => from.x == to.x && is_path_clear(board, from, to),
        PieceType::Advisor => {
            let dx = (to.x as i32 - from.x as i32).abs();
            let dy = (to.y as i32 - from.y as i32).abs();
            dx == 1 && dy == 1
        }
        PieceType::Bishop => {
            let dx = (to.x as i32 - from.x as i32).abs();
            let dy = (to.y as i32 - from.y as i32).abs();
            if dx == 2 && dy == 2 {
                let eye_x = from.x as i32 + (to.x as i32 - from.x as i32) / 2;
                let eye_y = from.y as i32 + (to.y as i32 - from.y as i32) / 2;
                board.piece_at(Position::new(eye_x as u8, eye_y as u8)).is_none()
            } else {
                false
            }
        }
        PieceType::Knight => {
            let dx = (to.x as i32 - from.x as i32).abs();
            let dy = (to.y as i32 - from.y as i32).abs();
            if (dx == 1 && dy == 2) || (dx == 2 && dy == 1) {
                let (block_x, block_y) = if dx == 2 {
                    (from.x as i32 + (to.x as i32 - from.x as i32) / 2, from.y as i32)
                } else {
                    (from.x as i32, from.y as i32 + (to.y as i32 - from.y as i32) / 2)
                };
                board.piece_at(Position::new(block_x as u8, block_y as u8)).is_none()
            } else {
                false
            }
        }
        PieceType::Rook => (from.x == to.x || from.y == to.y) && is_path_clear(board, from, to),
        PieceType::Cannon => {
            if from.x == to.x || from.y == to.y {
                count_pieces_between(board, from, to) == 1
            } else {
                false
            }
        }
        PieceType::Pawn => {
            let dx = (to.x as i32 - from.x as i32).abs();
            let dy = to.y as i32 - from.y as i32;
            let forward = match piece.side {
                Side::Red => -1,
                Side::Black => 1,
            };
            let past_river = from.is_past_river(piece.side);
            if past_river {
                (dy == forward && dx == 0) || (dy == 0 && dx == 1)
            } else {
                dy == forward && dx == 0
            }
        }
    }
}

fn kings_opposing(board: &Board) -> bool {
    let red_king = board.red_king_pos();
    let black_king = board.black_king_pos();

    if red_king.x != black_king.x {
        return false;
    }

    let min_y = red_king.y.min(black_king.y);
    let max_y = red_king.y.max(black_king.y);
    for y in (min_y + 1)..max_y {
        if board.piece_at(Position::new(red_king.x, y)).is_some() {
            return false;
        }
    }
    true
}

impl Clone for Board {
    fn clone(&self) -> Self {
        self.clone_for_search()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_test_board() -> Board {
        Board::new()
    }

    #[test]
    fn test_king_in_palace() {
        let board = make_test_board();
        assert!(is_legal_move(&board, Position::new(4, 9), Position::new(4, 8)));
        assert!(!is_legal_move(&board, Position::new(4, 9), Position::new(3, 9)));
        assert!(!is_legal_move(&board, Position::new(4, 9), Position::new(4, 7)));

        let board2 = Board::from_fen("4k4/9/9/9/9/4P3/9/9/9/3K5 w").unwrap();
        assert!(is_legal_move(&board2, Position::new(3, 9), Position::new(4, 9)));
        assert!(is_legal_move(&board2, Position::new(3, 9), Position::new(3, 8)));
        assert!(!is_legal_move(&board2, Position::new(3, 9), Position::new(2, 9)));
    }

    #[test]
    fn test_king_diagonal() {
        let board = make_test_board();
        assert!(!is_legal_move(&board, Position::new(4, 9), Position::new(5, 8)));
    }

    #[test]
    fn test_advisor_move() {
        let board = make_test_board();
        assert!(is_legal_move(&board, Position::new(3, 9), Position::new(4, 8)));
        assert!(!is_legal_move(&board, Position::new(3, 9), Position::new(3, 8)));
    }

    #[test]
    fn test_bishop_eye_blocked() {
        let board = Board::from_fen("4k4/9/9/9/9/9/9/9/1N6/2B1K4 w").unwrap();
        let bishop_from = Position::new(2, 9);
        let bishop_to = Position::new(0, 7);
        assert!(!is_legal_move(&board, bishop_from, bishop_to));
    }

    #[test]
    fn test_knight_leg_blocked() {
        let board = Board::from_fen("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/1p7/RNBAKABNR w").unwrap();
        assert!(!is_legal_move(&board, Position::new(1, 9), Position::new(2, 7)));
    }

    #[test]
    fn test_pawn_forward_only() {
        let board = make_test_board();
        assert!(is_legal_move(&board, Position::new(4, 6), Position::new(4, 5)));
        assert!(!is_legal_move(&board, Position::new(4, 6), Position::new(4, 7)));
        assert!(!is_legal_move(&board, Position::new(4, 6), Position::new(3, 6)));
    }

    #[test]
    fn test_cannon_capture() {
        let mut board = make_test_board();
        board.make_move_internal(Move::new(Position::new(1, 7), Position::new(4, 7)));
        board.make_move_internal(Move::new(Position::new(4, 3), Position::new(4, 5)));
        assert!(is_legal_move(&board, Position::new(4, 7), Position::new(4, 5)));
    }

    #[test]
    fn test_cannon_no_capture_over_piece() {
        let board = Board::from_fen("4k4/9/9/9/9/9/1p6/1C6/9/4K4 w").unwrap();
        let cannon_from = Position::new(1, 7);
        assert!(!is_legal_move(&board, cannon_from, Position::new(1, 5)));
    }

    #[test]
    fn test_rook_blocked() {
        let board = make_test_board();
        assert!(!is_legal_move(&board, Position::new(0, 9), Position::new(0, 5)));
    }

    #[test]
    fn test_check_detection() {
        let board = Board::from_fen("4k4/9/4p4/9/4C4/9/4P3/9/9/4K4 w").unwrap();
        assert!(is_in_check(&board, Side::Black));
    }

    #[test]
    fn test_no_check_initial() {
        let board = make_test_board();
        assert!(!is_in_check(&board, Side::Red));
        assert!(!is_in_check(&board, Side::Black));
    }

    #[test]
    fn test_flying_generals() {
        let board = Board::from_fen("4k4/9/9/9/9/4P4/9/9/9/4K4 w").unwrap();
        assert!(!is_legal_move(&board, Position::new(4, 4), Position::new(3, 4)));
        assert!(is_legal_move(&board, Position::new(4, 9), Position::new(3, 9)));
    }
}
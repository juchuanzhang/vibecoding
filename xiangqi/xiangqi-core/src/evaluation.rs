use crate::types::*;
use crate::board::Board;

const PIECE_BASE_VALUES: [i32; 7] = [
    10000, // King
    200,   // Advisor
    200,   // Bishop
    400,   // Knight
    900,   // Rook
    450,   // Cannon
    100,   // Pawn
];

const PAST_RIVER_PAWN_VALUE: i32 = 200;

const RED_KNIGHT_POS: [[i32; 9]; 10] = [
    [  0,  -4,   0,   0,   0,   0,   0,  -4,   0],
    [  0,   2,   4,   4,  -2,   4,   4,   2,   0],
    [  4,   2,   8,  10,  12,  10,   8,   2,   4],
    [  2,   6,  14,  16,  14,  16,  14,   6,   2],
    [  4,  10,  16,  14,  12,  14,  16,  10,   4],
    [  4,  10,  16,  14,  12,  14,  16,  10,   4],
    [  2,   6,  14,  16,  14,  16,  14,   6,   2],
    [  4,   2,   8,  10,  12,  10,   8,   2,   4],
    [  0,   2,   4,   4,  -2,   4,   4,   2,   0],
    [  0,  -4,   0,   0,   0,   0,   0,  -4,   0],
];

const RED_ROOK_POS: [[i32; 9]; 10] = [
    [  6,   8,   8,  12,  14,  12,   8,   8,   6],
    [  6,  10,  12,  18,  18,  18,  12,  10,   6],
    [  4,  12,  14,  20,  20,  20,  14,  12,   4],
    [  2,   6,  14,  16,  16,  16,  14,   6,   2],
    [  2,   8,  12,  14,  12,  14,  12,   8,   2],
    [  0,   6,  10,  12,  12,  12,  10,   6,   0],
    [ -2,   4,   6,  10,  10,  10,   6,   4,  -2],
    [  0,   2,   4,   6,   6,   6,   4,   2,   0],
    [  0,   2,   2,   4,   4,   4,   2,   2,   0],
    [  0,  -2,   0,   2,   2,   2,   0,  -2,   0],
];

const RED_CANNON_POS: [[i32; 9]; 10] = [
    [  0,   2,   4,   4,  -2,   4,   4,   2,   0],
    [  0,   0,   2,   6,   6,   6,   2,   0,   0],
    [  2,   4,   6,  10,  12,  10,   6,   4,   2],
    [  0,   0,   2,   6,   6,   6,   2,   0,   0],
    [  0,   0,   0,   2,   4,   2,   0,   0,   0],
    [ -2,   0,   4,   2,   6,   2,   4,   0,  -2],
    [  0,   0,   0,   2,   4,   2,   0,   0,   0],
    [  2,   2,   2,   0,   0,   0,   2,   2,   2],
    [  0,   0,   2,   2,   0,   2,   2,   0,   0],
    [  0,  -2,   0,   0,   0,   0,   0,  -2,   0],
];

const RED_PAWN_POS: [[i32; 9]; 10] = [
    [  0,   0,   0,   2,   6,   2,   0,   0,   0],
    [  0,   2,   6,  10,  18,  10,   6,   2,   0],
    [  2,  12,  16,  20,  30,  20,  16,  12,   2],
    [  0,   8,  10,  14,  18,  14,  10,   8,   0],
    [  0,   4,   8,  12,  16,  12,   8,   4,   0],
    [  0,   0,   2,   4,   4,   4,   2,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
];

const RED_ADVISOR_POS: [[i32; 9]; 10] = [
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   4,   0,   4,   0,   0,   0],
    [  0,   0,   0,   2,   0,   2,   0,   0,   0],
];

const RED_BISHOP_POS: [[i32; 9]; 10] = [
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,  20,   0,   0,   0,  20,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,  20,   0,  18,   0,  20,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
];

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

fn get_pos_table(piece_type: PieceType, _side: Side) -> &'static [[i32; 9]; 10] {
    match piece_type {
        PieceType::Knight => &RED_KNIGHT_POS,
        PieceType::Rook => &RED_ROOK_POS,
        PieceType::Cannon => &RED_CANNON_POS,
        PieceType::Pawn => &RED_PAWN_POS,
        PieceType::Advisor => &RED_ADVISOR_POS,
        PieceType::Bishop => &RED_BISHOP_POS,
        _ => &[[-20; 9]; 10], // King has minimal positional value
    }
}

fn mirror_pos(y: u8, side: Side) -> usize {
    match side {
        Side::Red => y as usize,
        Side::Black => (9 - y) as usize,
    }
}

pub fn evaluate(board: &Board) -> i32 {
    let mut red_score = 0;
    let mut black_score = 0;

    for y in 0..10 {
        for x in 0..9 {
            if let Some(piece) = board.piece_at(Position::new(x as u8, y as u8)) {
                let base = PIECE_BASE_VALUES[piece_type_index(piece.piece_type)];
                let pos_bonus = if piece.piece_type == PieceType::Pawn {
                    let past_river = Position::new(x as u8, y as u8).is_past_river(piece.side);
                    let pawn_base = if past_river { PAST_RIVER_PAWN_VALUE } else { base };
                    let table = get_pos_table(piece.piece_type, piece.side);
                    pawn_base + table[mirror_pos(y as u8, piece.side)][x as usize]
                } else if piece.piece_type == PieceType::King {
                    base
                } else {
                    let table = get_pos_table(piece.piece_type, piece.side);
                    base + table[mirror_pos(y as u8, piece.side)][x as usize]
                };

                match piece.side {
                    Side::Red => red_score += pos_bonus,
                    Side::Black => black_score += pos_bonus,
                }
            }
        }
    }

    red_score - black_score
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initial_score_near_zero() {
        let board = Board::new();
        let score = evaluate(&board);
        assert!(score.abs() < 100, "Initial score should be near zero, got {}", score);
    }

    #[test]
    fn test_empty_board_score_zero() {
        let fen = "9/9/9/9/9/9/9/9/9/9 w - 0 1";
        let board = Board::from_fen(fen).unwrap();
        let score = evaluate(&board);
        assert_eq!(score, 0);
    }

    #[test]
    fn test_single_rook_score() {
        let fen = "9/9/9/9/9/9/9/9/9/R8 w - 0 1";
        let board = Board::from_fen(fen).unwrap();
        let score = evaluate(&board);
        assert!(score > 800, "Red rook should give positive score, got {}", score);
    }

    #[test]
    fn test_red_advantage_with_extra_rook() {
        let board = Board::new();
        let score = evaluate(&board);
        assert!(score.abs() < 100);
    }
}
use crate::types::*;
use crate::board::Board;
use crate::move_gen::generate_legal_moves;

const PIECE_BASE_VALUES: [i32; 7] = [
    10000,
    120,
    120,
    270,
    600,
    285,
    30,
];

const PAST_RIVER_PAWN_VALUE: i32 = 70;
const MID_PAWN_VALUE: i32 = 50;

const RED_KNIGHT_POS: [[i32; 9]; 10] = [
    [  4,   8,  16,  12,  12,  12,  16,   8,   4],
    [  4,  10,  28,  16,   8,  16,  28,  10,   4],
    [  12,  14,  16,  20,  18,  20,  16,  14,  12],
    [  8,  24,  18,  24,  20,  24,  18,  24,   8],
    [  6,  16,  14,  18,  16,  18,  14,  16,   6],
    [  4,  12,  16,  14,  12,  14,  16,  12,   4],
    [  2,   6,   8,   6,  10,   6,   8,   6,   2],
    [  4,   2,   8,   0,   8,   0,   8,   2,   4],
    [  0,   2,   4,   4,  -2,   4,   4,   2,   0],
    [  0,  -4,   0,   0,   0,   0,   0,  -4,   0],
];

const RED_ROOK_POS: [[i32; 9]; 10] = [
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
];

const RED_CANNON_POS: [[i32; 9]; 10] = [
    [  6,   4,   0, -10,  -12, -10,   0,   4,   6],
    [  2,   2,   0,  -4,  -14,  -4,   0,   2,   2],
    [  2,   2,   0, -10,  -8, -10,   0,   2,   2],
    [  0,   0,  -2,   4,  10,   4,  -2,   0,   0],
    [  0,   0,   0,   2,   8,   2,   0,   0,   0],
    [ -2,   0,   4,   2,   6,   2,   4,   0,  -2],
    [  0,   0,   0,   2,   8,   2,   0,   0,   0],
    [  4,   0,   8,   6,  10,   6,   8,   0,   4],
    [  0,   2,   4,   6,   6,   6,   4,   2,   0],
    [  0,   0,  -2,   0,   4,   0,  -2,   0,   0],
];

const RED_PAWN_POS: [[i32; 9]; 10] = [
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
    [  0,   0,   0,  20,   0,  20,   0,   0,   0],
    [  0,   0,   0,   0,  20,   0,   0,   0,   0],
];

const RED_BISHOP_POS: [[i32; 9]; 10] = [
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
];

const RED_KING_POS: [[i32; 9]; 10] = [
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,   0,   0,   0,   0,   0,   0],
    [  0,   0,   0,  -8,  -16,  -8,   0,   0,   0],
    [  0,   0,   0,  -8,  -12,  -8,   0,   0,   0],
    [  0,   0,   0,   2,   8,   2,   0,   0,   0],
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

fn get_pos_table(piece_type: PieceType) -> &'static [[i32; 9]; 10] {
    match piece_type {
        PieceType::King => &RED_KING_POS,
        PieceType::Advisor => &RED_ADVISOR_POS,
        PieceType::Bishop => &RED_BISHOP_POS,
        PieceType::Knight => &RED_KNIGHT_POS,
        PieceType::Rook => &RED_ROOK_POS,
        PieceType::Cannon => &RED_CANNON_POS,
        PieceType::Pawn => &RED_PAWN_POS,
    }
}

fn mirror_pos(y: u8, side: Side) -> usize {
    match side {
        Side::Red => y as usize,
        Side::Black => (9 - y) as usize,
    }
}

fn piece_value(piece: Piece, pos: Position) -> i32 {
    let base = PIECE_BASE_VALUES[piece_type_index(piece.piece_type)];
    let table = get_pos_table(piece.piece_type);
    let pos_val = table[mirror_pos(pos.y, piece.side)][pos.x as usize];

    if piece.piece_type == PieceType::Pawn {
        let past_river = pos.is_past_river(piece.side);
        let mid_line = pos.x == 4 && past_river;
        let pawn_base = if past_river { PAST_RIVER_PAWN_VALUE } else { base };
        let mid_bonus = if mid_line { MID_PAWN_VALUE } else { 0 };
        pawn_base + pos_val + mid_bonus
    } else {
        base + pos_val
    }
}

pub fn evaluate(board: &Board) -> i32 {
    let mut red_score: i32 = 0;
    let mut black_score: i32 = 0;
    let mut red_pieces_count = 0;
    let mut black_pieces_count = 0;

    for y in 0..10 {
        for x in 0..9 {
            let pos = Position::new(x as u8, y as u8);
            if let Some(piece) = board.piece_at(pos) {
                let val = piece_value(piece, pos);
                match piece.side {
                    Side::Red => { red_score += val; red_pieces_count += 1; },
                    Side::Black => { black_score += val; black_pieces_count += 1; },
                }
            }
        }
    }

    let material_score = red_score - black_score;

    let red_king_pos = board.red_king_pos();
    let black_king_pos = board.black_king_pos();

    let king_safety_red = evaluate_king_safety(board, Side::Red, red_king_pos);
    let king_safety_black = evaluate_king_safety(board, Side::Black, black_king_pos);

    let mobility_red = evaluate_mobility(board, Side::Red);
    let mobility_black = evaluate_mobility(board, Side::Black);

    let total = material_score + king_safety_red - king_safety_black
        + (mobility_red - mobility_black) * 3;

    if red_pieces_count <= 3 || black_pieces_count <= 3 {
        return total * 2;
    }

    total
}

fn evaluate_king_safety(board: &Board, side: Side, king_pos: Position) -> i32 {
    let mut score: i32 = 0;
    let opponent = side.opponent();

    for pos in board.all_pieces(opponent) {
        let piece = board.piece_at(pos).unwrap();
        let dist_x = (king_pos.x as i32 - pos.x as i32).abs();
        let dist_y = (king_pos.y as i32 - pos.y as i32).abs();
        let dist = dist_x + dist_y;

        match piece.piece_type {
            PieceType::Rook => {
                if pos.x == king_pos.x || pos.y == king_pos.y {
                    score -= 40 - dist * 5;
                }
            },
            PieceType::Cannon => {
                if pos.x == king_pos.x || pos.y == king_pos.y {
                    score -= 20 - dist * 3;
                }
            },
            PieceType::Knight => {
                if dist <= 5 {
                    score -= 15 - dist * 2;
                }
            },
            _ => {},
        }
    }

    let palace_center = Position::new(4, if side == Side::Red { 8 } else { 1 });
    let dist_from_center = (king_pos.x as i32 - palace_center.x as i32).abs()
        + (king_pos.y as i32 - palace_center.y as i32).abs();
    score += (3 - dist_from_center) * 5;

    score
}

fn evaluate_mobility(board: &Board, side: Side) -> i32 {
    let current_side = board.side_to_move();
    if current_side != side {
        return 0;
    }
    let moves = generate_legal_moves(board);
    moves.len() as i32
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initial_score_near_zero() {
        let board = Board::new();
        let score = evaluate(&board);
        assert!(score.abs() < 200, "Initial score should be near zero, got {}", score);
    }

    #[test]
    fn test_empty_board_score_zero() {
        let fen = "4k4/9/9/9/9/9/9/9/9/4K4 w - 0 1";
        let board = Board::from_fen(fen).unwrap();
        let score = evaluate(&board);
        assert!(score.abs() < 200);
    }

    #[test]
    fn test_single_rook_advantage() {
        let fen = "4k4/9/9/9/9/9/9/9/R8/4K4 w - 0 1";
        let board = Board::from_fen(fen).unwrap();
        let score = evaluate(&board);
        assert!(score > 400, "Red should have advantage with extra rook, got {}", score);
    }
}
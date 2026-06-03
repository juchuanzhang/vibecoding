use crate::types::*;
use crate::board::Board;
use crate::rules::is_legal_move;

pub fn generate_legal_moves(board: &Board) -> Vec<Move> {
    let side = board.side_to_move();
    let mut moves = Vec::new();

    for pos in board.all_pieces(side) {
        let piece_moves = generate_piece_moves(board, pos);
        moves.extend(piece_moves);
    }

    moves
}

pub fn generate_piece_moves(board: &Board, from: Position) -> Vec<Move> {
    let piece = board.piece_at(from);
    if piece.is_none() || piece.unwrap().side != board.side_to_move() {
        return Vec::new();
    }

    let piece = piece.unwrap();
    let candidates = generate_raw_moves(board, piece, from);

    candidates
        .into_iter()
        .filter(|to| is_legal_move(board, from, *to))
        .map(|to| Move::new(from, to))
        .collect()
}

fn generate_raw_moves(board: &Board, piece: Piece, from: Position) -> Vec<Position> {
    match piece.piece_type {
        PieceType::King => generate_king_moves(piece, from),
        PieceType::Advisor => generate_advisor_moves(piece, from),
        PieceType::Bishop => generate_bishop_moves(board, piece, from),
        PieceType::Knight => generate_knight_moves(board, from),
        PieceType::Rook => generate_rook_moves(board, from),
        PieceType::Cannon => generate_cannon_moves(board, from),
        PieceType::Pawn => generate_pawn_moves(piece, from),
    }
}

fn generate_king_moves(piece: Piece, from: Position) -> Vec<Position> {
    let mut moves = Vec::new();
    let dirs: [(i32, i32); 4] = [(0, 1), (0, -1), (1, 0), (-1, 0)];

    for (dx, dy) in dirs {
        let nx = from.x as i32 + dx;
        let ny = from.y as i32 + dy;
        let to = Position::new(nx as u8, ny as u8);
        if to.is_valid() && to.in_palace(piece.side) {
            moves.push(to);
        }
    }
    moves
}

fn generate_advisor_moves(piece: Piece, from: Position) -> Vec<Position> {
    let mut moves = Vec::new();
    let dirs: [(i32, i32); 4] = [(1, 1), (1, -1), (-1, 1), (-1, -1)];

    for (dx, dy) in dirs {
        let nx = from.x as i32 + dx;
        let ny = from.y as i32 + dy;
        let to = Position::new(nx as u8, ny as u8);
        if to.is_valid() && to.in_palace(piece.side) {
            moves.push(to);
        }
    }
    moves
}

fn generate_bishop_moves(board: &Board, piece: Piece, from: Position) -> Vec<Position> {
    let mut moves = Vec::new();
    let dirs: [(i32, i32); 4] = [(2, 2), (2, -2), (-2, 2), (-2, -2)];

    for (dx, dy) in dirs {
        let nx = from.x as i32 + dx;
        let ny = from.y as i32 + dy;
        let to = Position::new(nx as u8, ny as u8);
        if !to.is_valid() || !to.in_own_territory(piece.side) {
            continue;
        }
        let eye_x = from.x as i32 + dx / 2;
        let eye_y = from.y as i32 + dy / 2;
        if board.piece_at(Position::new(eye_x as u8, eye_y as u8)).is_some() {
            continue;
        }
        moves.push(to);
    }
    moves
}

fn generate_knight_moves(board: &Board, from: Position) -> Vec<Position> {
    let mut moves = Vec::new();
    let knight_targets: [(i32, i32, i32, i32); 8] = [
        (2, 1, 1, 0),
        (2, -1, 1, 0),
        (-2, 1, -1, 0),
        (-2, -1, -1, 0),
        (1, 2, 0, 1),
        (1, -2, 0, -1),
        (-1, 2, 0, 1),
        (-1, -2, 0, -1),
    ];

    for (dx, dy, block_dx, block_dy) in knight_targets {
        let nx = from.x as i32 + dx;
        let ny = from.y as i32 + dy;
        let to = Position::new(nx as u8, ny as u8);
        if !to.is_valid() {
            continue;
        }
        let bx = from.x as i32 + block_dx;
        let by = from.y as i32 + block_dy;
        if board.piece_at(Position::new(bx as u8, by as u8)).is_some() {
            continue;
        }
        moves.push(to);
    }
    moves
}

fn generate_rook_moves(board: &Board, from: Position) -> Vec<Position> {
    let mut moves = Vec::new();
    let dirs: [(i32, i32); 4] = [(0, 1), (0, -1), (1, 0), (-1, 0)];

    for (dx, dy) in dirs {
        let mut nx = from.x as i32 + dx;
        let mut ny = from.y as i32 + dy;
        while nx >= 0 && nx < 9 && ny >= 0 && ny < 10 {
            let to = Position::new(nx as u8, ny as u8);
            if let Some(p) = board.piece_at(to) {
                if p.side != board.side_to_move() {
                    moves.push(to);
                }
                break;
            }
            moves.push(to);
            nx += dx;
            ny += dy;
        }
    }
    moves
}

fn generate_cannon_moves(board: &Board, from: Position) -> Vec<Position> {
    let mut moves = Vec::new();
    let dirs: [(i32, i32); 4] = [(0, 1), (0, -1), (1, 0), (-1, 0)];
    let my_side = board.side_to_move();

    for (dx, dy) in dirs {
        let mut nx = from.x as i32 + dx;
        let mut ny = from.y as i32 + dy;
        let mut jumped = false;

        while nx >= 0 && nx < 9 && ny >= 0 && ny < 10 {
            let to = Position::new(nx as u8, ny as u8);
            if let Some(p) = board.piece_at(to) {
                if !jumped {
                    jumped = true;
                } else {
                    if p.side != my_side {
                        moves.push(to);
                    }
                    break;
                }
            } else {
                if !jumped {
                    moves.push(to);
                }
            }
            nx += dx;
            ny += dy;
        }
    }
    moves
}

fn generate_pawn_moves(piece: Piece, from: Position) -> Vec<Position> {
    let mut moves = Vec::new();
    let forward = match piece.side {
        Side::Red => -1,
        Side::Black => 1,
    };

    let fy = from.y as i32 + forward;
    if fy >= 0 && fy < 10 {
        moves.push(Position::new(from.x, fy as u8));
    }

    let past_river = from.is_past_river(piece.side);
    if past_river {
        let lx = from.x as i32 - 1;
        let rx = from.x as i32 + 1;
        if lx >= 0 {
            moves.push(Position::new(lx as u8, from.y));
        }
        if rx < 9 {
            moves.push(Position::new(rx as u8, from.y));
        }
    }

    moves
}

pub fn sort_moves(board: &Board, moves: &mut Vec<Move>) {
    let piece_values = |pt: PieceType| -> i32 {
        match pt {
            PieceType::King => 10000,
            PieceType::Rook => 900,
            PieceType::Cannon => 450,
            PieceType::Knight => 400,
            PieceType::Advisor => 200,
            PieceType::Bishop => 200,
            PieceType::Pawn => 100,
        }
    };

    moves.sort_by(|a, b| {
        let a_cap = board.piece_at(a.to).map(|p| piece_values(p.piece_type)).unwrap_or(0);
        let b_cap = board.piece_at(b.to).map(|p| piece_values(p.piece_type)).unwrap_or(0);
        b_cap.cmp(&a_cap)
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_initial_red_moves() {
        let board = Board::new();
        let moves = generate_legal_moves(&board);
        assert!(moves.len() > 0);
        assert!(moves.len() <= 50);
    }

    #[test]
    fn test_empty_pos_moves() {
        let board = Board::new();
        let moves = generate_piece_moves(&board, Position::new(0, 5));
        assert!(moves.is_empty());
    }

    #[test]
    fn test_opponent_piece_moves() {
        let board = Board::new();
        let moves = generate_piece_moves(&board, Position::new(0, 0));
        assert!(moves.is_empty());
    }

    #[test]
    fn test_move_sort_captures_first() {
        let mut board = Board::new();
        board.make_move_internal(Move::new(Position::new(1, 7), Position::new(4, 7)));
        board.make_move_internal(Move::new(Position::new(4, 3), Position::new(4, 5)));
        let mut moves = generate_legal_moves(&board);
        sort_moves(&board, &mut moves);
        let first_captures = moves.iter().take_while(|m| board.piece_at(m.to).is_some()).count();
        assert!(first_captures > 0 || moves.iter().all(|m| board.piece_at(m.to).is_none()));
    }
}
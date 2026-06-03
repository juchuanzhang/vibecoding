use crate::types::*;
use crate::board::Board;
use crate::move_gen::{generate_legal_moves, sort_moves};
use crate::rules::is_in_check;
use crate::evaluation::evaluate;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct TableEntry {
    depth: u8,
    score: i32,
    best_move: Option<Move>,
    flag: EntryFlag,
}

#[derive(Debug, Clone, Copy, PartialEq)]
enum EntryFlag {
    Exact,
    LowerBound,
    UpperBound,
}

const INFINITY: i32 = 99999;
const MAX_DEPTH: u8 = 10;

pub struct Engine {
    transposition_table: HashMap<u64, TableEntry>,
    killer_moves: [[Option<Move>; 2]; 64],
    nodes_searched: u32,
    history_table: [[i32; 9]; 10],
}

impl Engine {
    pub fn new() -> Self {
        Engine {
            transposition_table: HashMap::new(),
            killer_moves: [[None; 2]; 64],
            nodes_searched: 0,
            history_table: [[0; 9]; 10],
        }
    }

    pub fn clear_table(&mut self) {
        self.transposition_table.clear();
        self.killer_moves = [[None; 2]; 64];
        self.history_table = [[0; 9]; 10];
    }

    pub fn analyze(&mut self, board: &Board, depth: u8) -> AnalysisResult {
        self.nodes_searched = 0;

        let moves = generate_legal_moves(board);
        if moves.is_empty() {
            return AnalysisResult {
                best_move: None,
                score: if is_in_check(board, board.side_to_move()) { -INFINITY } else { 0 },
                candidates: Vec::new(),
                search_path: Vec::new(),
                nodes_searched: 0,
                time_ms: 0,
            };
        }

        let mut best_result: Option<AnalysisResult> = None;

        for d in 1..=depth {
            let result = self.search_at_depth(board, d);
            best_result = Some(result);
        }

        best_result.unwrap()
    }

    fn search_at_depth(&mut self, board: &Board, depth: u8) -> AnalysisResult {
        let mut moves = generate_legal_moves(board);
        if moves.is_empty() {
            return AnalysisResult {
                best_move: None,
                score: if is_in_check(board, board.side_to_move()) { -INFINITY } else { 0 },
                candidates: Vec::new(),
                search_path: Vec::new(),
                nodes_searched: self.nodes_searched,
                time_ms: 0,
            };
        }

        self.order_root_moves(board, &mut moves);

        let maximizing = board.side_to_move() == Side::Red;
        let mut best_score = if maximizing { -INFINITY } else { INFINITY };
        let mut best_move = moves[0];
        let mut candidates: Vec<CandidateMove> = Vec::new();

        let mut search_board = board.clone_for_search();

        for mv in moves {
            search_board.make_move_internal(mv);
            let score = self.alpha_beta(&mut search_board, depth - 1, -INFINITY, INFINITY, !maximizing, 0);
            search_board.undo_move_internal();

            candidates.push(CandidateMove { mv, score });

            if maximizing {
                if score > best_score {
                    best_score = score;
                    best_move = mv;
                }
            } else {
                if score < best_score {
                    best_score = score;
                    best_move = mv;
                }
            }
        }

        if maximizing {
            candidates.sort_by(|a, b| b.score.cmp(&a.score));
        } else {
            candidates.sort_by(|a, b| a.score.cmp(&b.score));
        }
        candidates.truncate(3);

        let search_path = self.get_search_path(board, best_move, depth);

        AnalysisResult {
            best_move: Some(best_move),
            score: best_score,
            candidates,
            search_path,
            nodes_searched: self.nodes_searched,
            time_ms: 0,
        }
    }

    fn order_root_moves(&mut self, board: &Board, moves: &mut Vec<Move>) {
        sort_moves(board, moves);

        let hash = board.zobrist_hash();
        if let Some(entry) = self.transposition_table.get(&hash) {
            if let Some(tt_move) = entry.best_move {
                if let Some(idx) = moves.iter().position(|m| *m == tt_move) {
                    let tt_mv = moves.remove(idx);
                    moves.insert(0, tt_mv);
                }
            }
        }

        let ply = 0;
        for i in 1..moves.len() {
            for k in 0..2 {
                if let Some(killer) = self.killer_moves[ply][k] {
                    if moves[i] == killer && i > k {
                        let km = moves.remove(i);
                        moves.insert(k + 1, km);
                        break;
                    }
                }
            }
        }
    }

    fn alpha_beta(&mut self, board: &mut Board, depth: u8, mut alpha: i32, mut beta: i32, maximizing: bool, ply: usize) -> i32 {
        self.nodes_searched += 1;

        let hash = board.zobrist_hash();
        if let Some(entry) = self.transposition_table.get(&hash) {
            if entry.depth >= depth {
                match entry.flag {
                    EntryFlag::Exact => return entry.score,
                    EntryFlag::LowerBound => {
                        if entry.score >= beta { return entry.score; }
                        if entry.score > alpha { alpha = entry.score; }
                    }
                    EntryFlag::UpperBound => {
                        if entry.score <= alpha { return entry.score; }
                        if entry.score < beta { beta = entry.score; }
                    }
                }
            }
        }

        if depth == 0 {
            return self.quiescence(board, alpha, beta, maximizing, ply, 6);
        }

        let mut moves = generate_legal_moves(board);
        if moves.is_empty() {
            if is_in_check(board, board.side_to_move()) {
                return if maximizing { -INFINITY + ply as i32 } else { INFINITY - ply as i32 };
            }
            return 0;
        }

        self.order_moves(board, &mut moves, ply);

        let original_alpha = alpha;
        let mut best_score = if maximizing { -INFINITY } else { INFINITY };
        let mut best_move_in_node = moves[0];

        for mv in moves.iter() {
            let is_capture = board.piece_at(mv.to).is_some();
            board.make_move_internal(*mv);
            let score = self.alpha_beta(board, depth - 1, alpha, beta, !maximizing, ply + 1);
            board.undo_move_internal();

            if maximizing {
                if score > best_score {
                    best_score = score;
                    best_move_in_node = *mv;
                }
                if score > alpha { alpha = score; }
                if alpha >= beta {
                    if !is_capture && ply < 64 {
                        self.killer_moves[ply][1] = self.killer_moves[ply][0];
                        self.killer_moves[ply][0] = Some(*mv);
                    }
                    self.history_table[mv.from.y as usize][mv.from.x as usize] += depth as i32 * depth as i32;
                    break;
                }
            } else {
                if score < best_score {
                    best_score = score;
                    best_move_in_node = *mv;
                }
                if score < beta { beta = score; }
                if beta <= alpha {
                    if !is_capture && ply < 64 {
                        self.killer_moves[ply][1] = self.killer_moves[ply][0];
                        self.killer_moves[ply][0] = Some(*mv);
                    }
                    self.history_table[mv.from.y as usize][mv.from.x as usize] += depth as i32 * depth as i32;
                    break;
                }
            }
        }

        let flag = if best_score <= original_alpha {
            EntryFlag::UpperBound
        } else if best_score >= beta {
            EntryFlag::LowerBound
        } else {
            EntryFlag::Exact
        };

        self.transposition_table.insert(hash, TableEntry {
            depth,
            score: best_score,
            best_move: Some(best_move_in_node),
            flag,
        });

        best_score
    }

    fn quiescence(&mut self, board: &mut Board, mut alpha: i32, mut beta: i32, maximizing: bool, ply: usize, max_depth: u8) -> i32 {
        self.nodes_searched += 1;

        let stand_pat = evaluate(board);

        if maximizing {
            if stand_pat >= beta { return beta; }
            if stand_pat > alpha { alpha = stand_pat; }
        } else {
            if stand_pat <= alpha { return alpha; }
            if stand_pat < beta { beta = stand_pat; }
        }

        if max_depth == 0 { return stand_pat; }

        let moves = generate_legal_moves(board);
        let capture_moves: Vec<Move> = moves.iter().filter(|m| board.piece_at(m.to).is_some()).copied().collect();

        if capture_moves.is_empty() && !is_in_check(board, board.side_to_move()) {
            return stand_pat;
        }

        let search_moves = if capture_moves.is_empty() { moves } else { capture_moves };
        let mut sorted_moves = search_moves;
        sort_moves(board, &mut sorted_moves);

        let mut best_score = stand_pat;

        for mv in sorted_moves {
            board.make_move_internal(mv);
            let score = self.quiescence(board, alpha, beta, !maximizing, ply + 1, max_depth - 1);
            board.undo_move_internal();

            if maximizing {
                if score > best_score { best_score = score; }
                if score > alpha { alpha = score; }
                if alpha >= beta { return beta; }
            } else {
                if score < best_score { best_score = score; }
                if score < beta { beta = score; }
                if beta <= alpha { return alpha; }
            }
        }

        best_score
    }

    fn order_moves(&self, board: &Board, moves: &mut [Move], ply: usize) {
        let piece_values = |pt: PieceType| -> i32 {
            match pt {
                PieceType::King => 10000,
                PieceType::Rook => 600,
                PieceType::Cannon => 285,
                PieceType::Knight => 270,
                PieceType::Advisor => 120,
                PieceType::Bishop => 120,
                PieceType::Pawn => 30,
            }
        };

        moves.sort_by(|a, b| {
            let a_score = self.move_score(board, a, ply, piece_values);
            let b_score = self.move_score(board, b, ply, piece_values);
            b_score.cmp(&a_score)
        });
    }

    fn move_score(&self, board: &Board, mv: &Move, ply: usize, piece_values: fn(PieceType) -> i32) -> i32 {
        let mut score = 0;

        let hash = board.zobrist_hash();
        if let Some(entry) = self.transposition_table.get(&hash) {
            if entry.best_move == Some(*mv) {
                score += 10000;
            }
        }

        if let Some(target) = board.piece_at(mv.to) {
            let attacker = board.piece_at(mv.from).unwrap();
            score += piece_values(target.piece_type) * 10 - piece_values(attacker.piece_type);
        }

        if ply < 64 {
            for k in 0..2 {
                if self.killer_moves[ply][k] == Some(*mv) {
                    score += 9000 - k as i32 * 100;
                }
            }
        }

        score += self.history_table[mv.from.y as usize][mv.from.x as usize];

        score
    }

    fn get_search_path(&self, board: &Board, first_move: Move, depth: u8) -> Vec<Move> {
        let mut path = vec![first_move];
        let mut search_board = board.clone_for_search();
        search_board.make_move_internal(first_move);

        for _ in 1..depth {
            let hash = search_board.zobrist_hash();
            if let Some(entry) = self.transposition_table.get(&hash) {
                if let Some(mv) = entry.best_move {
                    let legal_moves = generate_legal_moves(&search_board);
                    if legal_moves.contains(&mv) {
                        path.push(mv);
                        search_board.make_move_internal(mv);
                        continue;
                    }
                }
            }
            break;
        }

        path
    }

    pub fn nodes_searched(&self) -> u32 {
        self.nodes_searched
    }
}

pub struct AnalysisResult {
    pub best_move: Option<Move>,
    pub score: i32,
    pub candidates: Vec<CandidateMove>,
    pub search_path: Vec<Move>,
    pub nodes_searched: u32,
    pub time_ms: u64,
}

pub struct CandidateMove {
    pub mv: Move,
    pub score: i32,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_search_depth_1() {
        let board = Board::new();
        let mut engine = Engine::new();
        let result = engine.analyze(&board, 1);
        assert!(result.best_move.is_some());
    }

    #[test]
    fn test_search_depth_3() {
        let board = Board::new();
        let mut engine = Engine::new();
        let result = engine.analyze(&board, 3);
        assert!(result.best_move.is_some());
    }

    #[test]
    fn test_search_check_response() {
        let fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/4C4/9/P1P1P1P1P/1C5C1/9/RNBAKABNR b - 0 1";
        let board = Board::from_fen(fen).unwrap();
        let mut engine = Engine::new();
        let result = engine.analyze(&board, 3);
        assert!(result.best_move.is_some());
    }

    #[test]
    fn test_candidates_count() {
        let board = Board::new();
        let mut engine = Engine::new();
        let result = engine.analyze(&board, 2);
        assert!(result.candidates.len() >= 1);
    }
}
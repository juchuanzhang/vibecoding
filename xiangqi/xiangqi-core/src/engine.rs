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
const MAX_SEARCH_TIME_MS: u64 = 30000;

pub struct Engine {
    transposition_table: HashMap<u64, TableEntry>,
    nodes_searched: u32,
    search_start_time: u64,
    max_time_ms: u64,
    should_stop: bool,
}

impl Engine {
    pub fn new() -> Self {
        Engine {
            transposition_table: HashMap::new(),
            nodes_searched: 0,
            search_start_time: 0,
            max_time_ms: MAX_SEARCH_TIME_MS,
            should_stop: false,
        }
    }

    pub fn clear_table(&mut self) {
        self.transposition_table.clear();
    }

    pub fn analyze(&mut self, board: &Board, depth: u8) -> AnalysisResult {
        self.nodes_searched = 0;
        self.should_stop = false;

        let mut moves = generate_legal_moves(board);
        if moves.is_empty() {
            return AnalysisResult {
                best_move: None,
                score: if is_in_check(board, board.side_to_move()) {
                    -INFINITY
                } else {
                    0
                },
                candidates: Vec::new(),
                search_path: Vec::new(),
                nodes_searched: 0,
                time_ms: 0,
            };
        }
        sort_moves(board, &mut moves);

        let maximizing = board.side_to_move() == Side::Red;
        let mut best_score = if maximizing { -INFINITY } else { INFINITY };
        let mut best_move = moves[0];
        let mut candidates: Vec<CandidateMove> = Vec::new();

        let mut search_board = board.clone_for_search();

        for mv in moves {
            search_board.make_move_internal(mv);
            let score = self.alpha_beta(&mut search_board, depth - 1, -INFINITY, INFINITY, !maximizing);
            search_board.undo_move_internal();

            if self.should_stop {
                break;
            }

            candidates.push(CandidateMove {
                mv,
                score,
            });

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

    fn alpha_beta(&mut self, board: &mut Board, depth: u8, mut alpha: i32, mut beta: i32, maximizing: bool) -> i32 {
        self.nodes_searched += 1;

        let hash = board.zobrist_hash();
        if let Some(entry) = self.transposition_table.get(&hash) {
            if entry.depth >= depth {
                match entry.flag {
                    EntryFlag::Exact => return entry.score,
                    EntryFlag::LowerBound => {
                        if entry.score >= beta {
                            return entry.score;
                        }
                    }
                    EntryFlag::UpperBound => {
                        if entry.score <= alpha {
                            return entry.score;
                        }
                    }
                }
            }
        }

        if depth == 0 {
            return evaluate(board);
        }

        let mut moves = generate_legal_moves(board);
        if moves.is_empty() {
            if is_in_check(board, board.side_to_move()) {
                return if maximizing { -INFINITY + (MAX_DEPTH - depth) as i32 } else { INFINITY - (MAX_DEPTH - depth) as i32 };
            }
            return 0;
        }

        sort_moves(board, &mut moves);

        let original_alpha = alpha;
        let original_beta = beta;
        let mut best_score = if maximizing { -INFINITY } else { INFINITY };
        let mut best_move_in_node = moves[0];

        if maximizing {
            for mv in moves {
                board.make_move_internal(mv);
                let score = self.alpha_beta(board, depth - 1, alpha, beta, false);
                board.undo_move_internal();

                if score > best_score {
                    best_score = score;
                    best_move_in_node = mv;
                }
                if score > alpha {
                    alpha = score;
                }
                if alpha >= beta {
                    break;
                }
            }
        } else {
            for mv in moves {
                board.make_move_internal(mv);
                let score = self.alpha_beta(board, depth - 1, alpha, beta, true);
                board.undo_move_internal();

                if score < best_score {
                    best_score = score;
                    best_move_in_node = mv;
                }
                if score < beta {
                    beta = score;
                }
                if beta <= alpha {
                    break;
                }
            }
        }

        let flag = if best_score <= original_alpha {
            EntryFlag::UpperBound
        } else if best_score >= original_beta {
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

const MAX_DEPTH: u8 = 10;

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
        assert!(result.nodes_searched > 0);
    }

    #[test]
    fn test_search_depth_3() {
        let board = Board::new();
        let mut engine = Engine::new();
        let result = engine.analyze(&board, 3);
        assert!(result.best_move.is_some());
        assert!(result.nodes_searched > 0);
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
    fn test_transposition_table() {
        let board = Board::new();
        let mut engine = Engine::new();
        let result1 = engine.analyze(&board, 3);
        let nodes1 = result1.nodes_searched;
        let result2 = engine.analyze(&board, 3);
        let nodes2 = result2.nodes_searched;
        assert!(nodes2 <= nodes1, "Second search should be faster due to TT");
    }

    #[test]
    fn test_candidates_count() {
        let board = Board::new();
        let mut engine = Engine::new();
        let result = engine.analyze(&board, 2);
        assert!(result.candidates.len() >= 1);
        assert!(result.candidates.len() <= 3);
    }
}
use crate::types::*;
use crate::board::Board;
use crate::move_gen::generate_legal_moves;
use crate::rules::{is_legal_move, is_in_check};
use crate::engine::Engine;
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub struct XiangQiEngine {
    board: Board,
    engine: Engine,
}

#[wasm_bindgen]
pub struct JsPosition {
    x: u8,
    y: u8,
}

#[wasm_bindgen]
impl JsPosition {
    #[wasm_bindgen(constructor)]
    pub fn new(x: u8, y: u8) -> Self {
        JsPosition { x, y }
    }

    pub fn get_x(&self) -> u8 {
        self.x
    }

    pub fn get_y(&self) -> u8 {
        self.y
    }
}

#[wasm_bindgen]
pub struct JsPieceInfo {
    piece_type: String,
    side: String,
    name: String,
    x: u8,
    y: u8,
}

#[wasm_bindgen]
impl JsPieceInfo {
    pub fn get_piece_type(&self) -> String {
        self.piece_type.clone()
    }

    pub fn get_side(&self) -> String {
        self.side.clone()
    }

    pub fn get_name(&self) -> String {
        self.name.clone()
    }

    pub fn get_x(&self) -> u8 {
        self.x
    }

    pub fn get_y(&self) -> u8 {
        self.y
    }
}

#[wasm_bindgen]
pub struct JsAnalysisResult {
    best_move_from_x: u8,
    best_move_from_y: u8,
    best_move_to_x: u8,
    best_move_to_y: u8,
    score: i32,
    candidates: Vec<JsCandidateMove>,
    search_path_from_x: Vec<u8>,
    search_path_from_y: Vec<u8>,
    search_path_to_x: Vec<u8>,
    search_path_to_y: Vec<u8>,
    nodes_searched: u32,
}

#[wasm_bindgen]
impl JsAnalysisResult {
    pub fn get_best_move_from_x(&self) -> u8 {
        self.best_move_from_x
    }

    pub fn get_best_move_from_y(&self) -> u8 {
        self.best_move_from_y
    }

    pub fn get_best_move_to_x(&self) -> u8 {
        self.best_move_to_x
    }

    pub fn get_best_move_to_y(&self) -> u8 {
        self.best_move_to_y
    }

    pub fn get_score(&self) -> i32 {
        self.score
    }

    pub fn get_nodes_searched(&self) -> u32 {
        self.nodes_searched
    }

    pub fn get_candidates(&self) -> Vec<JsCandidateMove> {
        self.candidates.clone()
    }

    pub fn get_search_path_from_x(&self) -> Vec<u8> {
        self.search_path_from_x.clone()
    }

    pub fn get_search_path_from_y(&self) -> Vec<u8> {
        self.search_path_from_y.clone()
    }

    pub fn get_search_path_to_x(&self) -> Vec<u8> {
        self.search_path_to_x.clone()
    }

    pub fn get_search_path_to_y(&self) -> Vec<u8> {
        self.search_path_to_y.clone()
    }
}

#[derive(Clone)]
#[wasm_bindgen]
pub struct JsCandidateMove {
    from_x: u8,
    from_y: u8,
    to_x: u8,
    to_y: u8,
    score: i32,
}

#[wasm_bindgen]
impl JsCandidateMove {
    pub fn get_from_x(&self) -> u8 {
        self.from_x
    }

    pub fn get_from_y(&self) -> u8 {
        self.from_y
    }

    pub fn get_to_x(&self) -> u8 {
        self.to_x
    }

    pub fn get_to_y(&self) -> u8 {
        self.to_y
    }

    pub fn get_score(&self) -> i32 {
        self.score
    }
}

#[wasm_bindgen]
pub struct JsBoardState {
    pieces_json: String,
    side_to_move: String,
    last_move_json: String,
    is_in_check: bool,
    game_over: String,
}

#[wasm_bindgen]
impl JsBoardState {
    pub fn get_pieces_json(&self) -> String {
        self.pieces_json.clone()
    }

    pub fn get_side_to_move(&self) -> String {
        self.side_to_move.clone()
    }

    pub fn get_last_move_json(&self) -> String {
        self.last_move_json.clone()
    }

    pub fn get_is_in_check(&self) -> bool {
        self.is_in_check
    }

    pub fn get_game_over(&self) -> String {
        self.game_over.clone()
    }
}

#[wasm_bindgen]
impl XiangQiEngine {
    #[wasm_bindgen(constructor)]
    pub fn new() -> XiangQiEngine {
        XiangQiEngine {
            board: Board::new(),
            engine: Engine::new(),
        }
    }

    pub fn from_fen(fen: &str) -> Result<XiangQiEngine, JsValue> {
        let board = Board::from_fen(fen);
        match board {
            Some(b) => Ok(XiangQiEngine {
                board: b,
                engine: Engine::new(),
            }),
            None => Err(JsValue::from_str("Invalid FEN string")),
        }
    }

    pub fn to_fen(&self) -> String {
        self.board.to_fen()
    }

    pub fn evaluate(&self) -> i32 {
        crate::evaluation::evaluate(&self.board)
    }

    pub fn make_move(&mut self, from_x: u8, from_y: u8, to_x: u8, to_y: u8) -> bool {
        let from = Position::new(from_x, from_y);
        let to = Position::new(to_x, to_y);
        if is_legal_move(&self.board, from, to) {
            self.board.make_move_internal(Move::new(from, to));
            true
        } else {
            false
        }
    }

    pub fn undo_move(&mut self) -> bool {
        self.board.undo_move_internal()
    }

    pub fn get_legal_moves_at(&self, x: u8, y: u8) -> Vec<JsPosition> {
        let pos = Position::new(x, y);
        let piece = self.board.piece_at(pos);
        if piece.is_none() || piece.unwrap().side != self.board.side_to_move() {
            return Vec::new();
        }

        let moves = generate_legal_moves(&self.board);
        moves
            .into_iter()
            .filter(|m| m.from == pos)
            .map(|m| JsPosition::new(m.to.x, m.to.y))
            .collect()
    }

    pub fn analyze(&mut self, depth: u8) -> JsAnalysisResult {
        let result = self.engine.analyze(&self.board, depth);
        let (bf_x, bf_y, bt_x, bt_y) = match result.best_move {
            Some(mv) => (mv.from.x, mv.from.y, mv.to.x, mv.to.y),
            None => (0, 0, 0, 0),
        };

        let candidates: Vec<JsCandidateMove> = result.candidates.iter().map(|c| {
            JsCandidateMove {
                from_x: c.mv.from.x,
                from_y: c.mv.from.y,
                to_x: c.mv.to.x,
                to_y: c.mv.to.y,
                score: c.score,
            }
        }).collect();

        let (sp_from_x, sp_from_y, sp_to_x, sp_to_y) = (
            result.search_path.iter().map(|m| m.from.x).collect(),
            result.search_path.iter().map(|m| m.from.y).collect(),
            result.search_path.iter().map(|m| m.to.x).collect(),
            result.search_path.iter().map(|m| m.to.y).collect(),
        );

        JsAnalysisResult {
            best_move_from_x: bf_x,
            best_move_from_y: bf_y,
            best_move_to_x: bt_x,
            best_move_to_y: bt_y,
            score: result.score,
            candidates,
            search_path_from_x: sp_from_x,
            search_path_from_y: sp_from_y,
            search_path_to_x: sp_to_x,
            search_path_to_y: sp_to_y,
            nodes_searched: result.nodes_searched,
        }
    }

    pub fn is_in_check(&self) -> bool {
        is_in_check(&self.board, self.board.side_to_move())
    }

    pub fn is_game_over(&self) -> String {
        let moves = generate_legal_moves(&self.board);
        if moves.is_empty() {
            if is_in_check(&self.board, self.board.side_to_move()) {
                match self.board.side_to_move() {
                    Side::Red => "black_win".to_string(),
                    Side::Black => "red_win".to_string(),
                }
            } else {
                "draw".to_string()
            }
        } else {
            "playing".to_string()
        }
    }

    pub fn get_board_state(&self) -> JsBoardState {
        let mut pieces = Vec::new();
        for y in 0..10 {
            for x in 0..9 {
                if let Some(piece) = self.board.piece_at(Position::new(x as u8, y as u8)) {
                    pieces.push(serde_json::json!({
                        "piece_type": format!("{:?}", piece.piece_type),
                        "side": if piece.side == Side::Red { "red" } else { "black" },
                        "name": piece.display_name(),
                        "x": x,
                        "y": y,
                    }));
                }
            }
        }
        let pieces_json = serde_json::to_string(&pieces).unwrap_or_else(|_| "[]".to_string());

        let last_move_json = if self.board.move_history_len() > 0 {
            let hist = self.board.get_last_move();
            match hist {
                Some(mv) => serde_json::json!({
                    "from_x": mv.from.x,
                    "from_y": mv.from.y,
                    "to_x": mv.to.x,
                    "to_y": mv.to.y,
                }).to_string(),
                None => "null".to_string(),
            }
        } else {
            "null".to_string()
        };

        JsBoardState {
            pieces_json,
            side_to_move: if self.board.side_to_move() == Side::Red { "red".to_string() } else { "black".to_string() },
            last_move_json,
            is_in_check: is_in_check(&self.board, self.board.side_to_move()),
            game_over: self.is_game_over(),
        }
    }

    pub fn reset(&mut self) {
        self.board = Board::new();
        self.engine.clear_table();
    }

    pub fn import_fen(&mut self, fen: &str) -> bool {
        let new_board = Board::from_fen(fen);
        match new_board {
            Some(b) => {
                self.board = b;
                self.engine.clear_table();
                true
            },
            None => false,
        }
    }
}
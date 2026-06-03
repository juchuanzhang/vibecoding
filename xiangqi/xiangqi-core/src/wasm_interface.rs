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

    pub fn describe_move(&self, from_x: u8, from_y: u8, to_x: u8, to_y: u8) -> String {
        let from = Position::new(from_x, from_y);
        let _to = Position::new(to_x, to_y);
        let piece = self.board.piece_at(from);
        if piece.is_none() {
            return format!("({},{})→({},{})", from_x, from_y, to_x, to_y);
        }
        let piece = piece.unwrap();
        let name = piece.display_name();

        let red_cols = ["九", "八", "七", "六", "五", "四", "三", "二", "一"];
        let black_cols = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];
        let red_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九"];
        let black_nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];

        let from_col = match piece.side {
            Side::Red => red_cols[from_x as usize],
            Side::Black => black_cols[from_x as usize],
        };

        let dx = to_x as i32 - from_x as i32;
        let dy = to_y as i32 - from_y as i32;

        let is_line_piece = piece.piece_type == PieceType::Rook
            || piece.piece_type == PieceType::Cannon
            || piece.piece_type == PieceType::Pawn
            || piece.piece_type == PieceType::King;

        let action = if dx == 0 {
            match piece.side {
                Side::Red => if dy < 0 { "进" } else { "退" },
                Side::Black => if dy > 0 { "进" } else { "退" },
            }
        } else if dy == 0 {
            "平"
        } else {
            match piece.side {
                Side::Red => if dy < 0 { "进" } else { "退" },
                Side::Black => if dy > 0 { "进" } else { "退" },
            }
        };

        let dest = if dx == 0 && is_line_piece {
            let steps = dy.abs() as u8;
            match piece.side {
                Side::Red => red_nums[(steps - 1) as usize],
                Side::Black => black_nums[(steps - 1) as usize],
            }
        } else {
            match piece.side {
                Side::Red => red_cols[to_x as usize],
                Side::Black => black_cols[to_x as usize],
            }
        };

        format!("{}{}{}{}", name, from_col, action, dest)
    }
}

#[cfg(test)]
mod opening_tests {
    use super::*;

    struct MoveStep {
        from: (u8, u8),
        to: (u8, u8),
        expected_desc: &'static str,
    }

    fn play_opening(steps: &[MoveStep]) -> XiangQiEngine {
        let mut engine = XiangQiEngine::new();
        for step in steps {
            let desc = engine.describe_move(step.from.0, step.from.1, step.to.0, step.to.1);
            assert_eq!(desc, step.expected_desc,
                "Move ({},{})→({},{}) description: expected '{}', got '{}'",
                step.from.0, step.from.1, step.to.0, step.to.1,
                step.expected_desc, desc);
            let ok = engine.make_move(step.from.0, step.from.1, step.to.0, step.to.1);
            assert!(ok, "Move ({},{})→({},{}) should be legal",
                step.from.0, step.from.1, step.to.0, step.to.1);
        }
        engine
    }

    #[test]
    fn test_central_cannon_vs_screen_horse() {
        let steps = [
            MoveStep { from: (7, 7), to: (4, 7), expected_desc: "炮二平五" },
            MoveStep { from: (7, 0), to: (6, 2), expected_desc: "马8进7" },
            MoveStep { from: (7, 9), to: (6, 7), expected_desc: "马二进三" },
            MoveStep { from: (8, 0), to: (7, 0), expected_desc: "车9平8" },
            MoveStep { from: (8, 9), to: (7, 9), expected_desc: "车一平二" },
            MoveStep { from: (1, 0), to: (2, 2), expected_desc: "马2进3" },
        ];
        let engine = play_opening(&steps);
        let fen = engine.to_fen();
        assert!(fen.starts_with("r1bakabr1"), "Black back row: {}", fen);
        assert!(fen.contains("RNBAKABR1"), "Red back row: {}", fen);
        assert!(!engine.is_in_check(), "No check after opening");
        assert_eq!(engine.is_game_over(), "playing");
    }

    #[test]
    fn test_same_side_cannon_opening() {
        let steps = [
            MoveStep { from: (7, 7), to: (4, 7), expected_desc: "炮二平五" },
            MoveStep { from: (7, 2), to: (4, 2), expected_desc: "炮8平5" },
        ];
        let engine = play_opening(&steps);
        let fen = engine.to_fen();
        assert!(fen.contains("1c2c4"), "Black cannon row: {}", fen);
        assert!(fen.contains("1C2C4"), "Red cannon row: {}", fen);
    }

    #[test]
    fn test_pawn_advance_opening() {
        let steps = [
            MoveStep { from: (2, 6), to: (2, 5), expected_desc: "兵七进一" },
        ];
        let engine = play_opening(&steps);
        let fen = engine.to_fen();
        assert!(fen.contains("2P6"), "Pawn advanced to row 5: {}", fen);
        assert!(fen.contains("P3P1P1P"), "Row 6 has gap: {}", fen);
    }

    #[test]
    fn test_knight_retreat() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(7, 7, 4, 7);
        engine.make_move(7, 0, 6, 2);
        engine.make_move(7, 9, 6, 7);
        let desc = engine.describe_move(6, 2, 7, 0);
        assert_eq!(desc, "马7退8", "Black knight retreat: got '{}'", desc);
        let ok = engine.make_move(6, 2, 7, 0);
        assert!(ok, "Knight retreat should be legal");
    }

    #[test]
    fn test_cannon_horizontal_back() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(7, 7, 4, 7);
        engine.make_move(7, 0, 6, 2);
        let desc = engine.describe_move(4, 7, 7, 7);
        assert_eq!(desc, "炮五平二", "Cannon horizontal back: got '{}'", desc);
        let ok = engine.make_move(4, 7, 7, 7);
        assert!(ok, "Cannon horizontal should be legal");
    }

    #[test]
    fn test_cannon_vertical_retreat() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(7, 7, 4, 7);
        engine.make_move(7, 0, 6, 2);
        engine.make_move(1, 7, 4, 7);
        let desc = engine.describe_move(4, 7, 4, 8);
        assert_eq!(desc, "炮五退一", "Red cannon retreat 1 step: got '{}'", desc);
    }

#[test]
    fn test_advisor_move() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(2, 6, 2, 5);
        engine.make_move(2, 3, 2, 4);
        let desc = engine.describe_move(3, 9, 4, 8);
        assert_eq!(desc, "仕六进五", "Red advisor move: got '{}'", desc);
        let ok = engine.make_move(3, 9, 4, 8);
        assert!(ok, "Advisor move should be legal");
    }

    #[test]
    fn test_bishop_move() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(4, 6, 4, 5);
        engine.make_move(4, 3, 4, 4);
        engine.make_move(3, 9, 4, 8);
        engine.make_move(0, 3, 0, 4);
        let desc = engine.describe_move(6, 9, 4, 7);
        assert_eq!(desc, "相三进五", "Red bishop move: got '{}'", desc);
        let ok = engine.make_move(6, 9, 4, 7);
        assert!(ok, "Bishop move should be legal");
    }

    #[test]
    fn test_king_move() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(4, 6, 4, 5);
        engine.make_move(4, 3, 4, 4);
        let desc = engine.describe_move(4, 9, 4, 8);
        assert_eq!(desc, "帅五进一", "Red king move: got '{}'", desc);
        let ok = engine.make_move(4, 9, 4, 8);
        assert!(ok, "King move should be legal");
    }

    #[test]
    fn test_red_pawn_forward_steps_count() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(4, 6, 4, 5);
        engine.make_move(7, 2, 4, 2);
        let desc = engine.describe_move(4, 5, 4, 4);
        assert_eq!(desc, "兵五进一", "Red pawn 1 step forward: got '{}'", desc);
        engine.make_move(4, 5, 4, 4);
        engine.make_move(7, 0, 6, 2);
        let desc2 = engine.describe_move(4, 4, 4, 3);
        assert_eq!(desc2, "兵五进一", "Red pawn another step: got '{}'", desc2);
    }

    #[test]
    fn test_black_pawn_forward() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(2, 6, 2, 5);
        let desc = engine.describe_move(2, 3, 2, 4);
        assert_eq!(desc, "卒3进1", "Black pawn forward: got '{}'", desc);
    }

    #[test]
    fn test_cannon_forward() {
        let engine = XiangQiEngine::new();
        let desc = engine.describe_move(1, 7, 1, 6);
        assert_eq!(desc, "炮八进一", "Red cannon 1 step forward: got '{}'", desc);
    }

    #[test]
    fn test_rook_forward() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(7, 7, 4, 7);
        engine.make_move(7, 0, 6, 2);
        engine.make_move(7, 9, 6, 7);
        engine.make_move(8, 0, 7, 0);
        engine.make_move(8, 9, 7, 9);
        engine.make_move(1, 0, 2, 2);
        let desc = engine.describe_move(7, 9, 7, 7);
        assert_eq!(desc, "车二进二", "Red rook forward: got '{}'", desc);
    }

    #[test]
    fn test_rook_retreat() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(7, 7, 4, 7);
        engine.make_move(7, 0, 6, 2);
        engine.make_move(7, 9, 6, 7);
        engine.make_move(8, 0, 7, 0);
        engine.make_move(8, 9, 7, 9);
        engine.make_move(1, 0, 2, 2);
        engine.make_move(7, 9, 7, 7);
        engine.make_move(7, 0, 7, 2);
        let desc = engine.describe_move(7, 7, 7, 9);
        assert_eq!(desc, "车二退二", "Red rook retreat: got '{}'", desc);
    }

    #[test]
    fn test_opening_sequence_undo() {
        let mut engine = XiangQiEngine::new();
        let initial_fen = engine.to_fen();

        engine.make_move(7, 7, 4, 7);
        engine.make_move(7, 0, 6, 2);
        engine.make_move(7, 9, 6, 7);

        engine.undo_move();
        engine.undo_move();
        engine.undo_move();

        assert_eq!(engine.to_fen(), initial_fen, "Undo should restore initial position");
    }

#[test]
    fn test_flying_general_rule() {
        let fen = "4k4/4R4/9/9/9/9/9/9/9/4K4 w - 0 1";
        let mut engine = XiangQiEngine::from_fen(fen).unwrap();
        let ok = engine.make_move(4, 1, 0, 1);
        assert!(!ok, "Rook can't leave column - would create flying general");
        let ok2 = engine.make_move(4, 1, 4, 5);
        assert!(ok2, "Rook can stay on column between kings");
    }

    #[test]
    fn test_knight_blocked_by_own_piece() {
        let mut engine = XiangQiEngine::new();
        let ok = engine.make_move(1, 9, 3, 8);
        assert!(!ok, "Knight blocked by Bishop at (2,9)");
    }

    #[test]
    fn test_knight_can_move_when_not_blocked() {
        let mut engine = XiangQiEngine::new();
        let ok = engine.make_move(1, 9, 0, 7);
        assert!(ok, "Knight at (1,9) can move to (0,7) - (1,8) is empty");
    }

    #[test]
    fn test_black_advisor_move() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(4, 6, 4, 5);
        let desc = engine.describe_move(3, 0, 4, 1);
        assert_eq!(desc, "士4进5", "Black advisor move: got '{}'", desc);
        let ok = engine.make_move(3, 0, 4, 1);
        assert!(ok, "Black advisor should be able to move");
    }

    #[test]
    fn test_black_king_move() {
        let mut engine = XiangQiEngine::new();
        engine.make_move(4, 6, 4, 5);
        engine.make_move(4, 0, 4, 1);
        let desc = engine.describe_move(4, 1, 4, 0);
        assert_eq!(desc, "将5退1", "Black king retreat: got '{}'", desc);
    }

    #[test]
    fn test_pawn_sideways_after_river() {
        let fen = "3k5/9/9/9/4P4/9/9/9/9/4K4 w - 0 1";
        let mut engine = XiangQiEngine::from_fen(fen).unwrap();
        let desc = engine.describe_move(4, 4, 3, 4);
        assert_eq!(desc, "兵五平六", "Red pawn sideways after river: got '{}'", desc);
        let ok = engine.make_move(4, 4, 3, 4);
        assert!(ok, "Pawn can move sideways past river");
    }

    #[test]
    fn test_pawn_cannot_sideways_before_river() {
        let mut engine = XiangQiEngine::new();
        let ok = engine.make_move(4, 6, 3, 6);
        assert!(!ok, "Pawn can't move sideways before crossing river");
    }
}
export class Game {
    constructor() {
        this.engine = null;
        this.selectedPos = null;
        this.moveHistory = [];
        this.analysisDepth = 4;
        this.isAnalyzing = false;
        this.currentAnalysis = null;
        this.wasmModule = null;
    }

    async initEngine() {
        try {
            const wasmModule = await import('../pkg/xiangqi_core.js');
            await wasmModule.default();
            this.wasmModule = wasmModule;
            this.engine = new wasmModule.XiangQiEngine();
        } catch (e) {
            console.error('WASM init error:', e);
            throw new Error('Engine load failed. Please use HTTP server. Error: ' + e.message);
        }
    }

    reset() {
        this.engine = new this.wasmModule.XiangQiEngine();
        this.selectedPos = null;
        this.moveHistory = [];
        this.currentAnalysis = null;
    }

    makeMove(from, to) {
        if (!this.engine) return false;
        const desc = this.engine.describe_move(from.x, from.y, to.x, to.y);
        const result = this.engine.make_move(from.x, from.y, to.x, to.y);
        if (result) {
            this.moveHistory.push({ from, to, description: desc });
            this.selectedPos = null;
            this.currentAnalysis = null;
        }
        return result;
    }

    undoMove() {
        if (!this.engine || this.moveHistory.length === 0) return false;
        const result = this.engine.undo_move();
        if (result) {
            this.moveHistory.pop();
            this.selectedPos = null;
            this.currentAnalysis = null;
        }
        return result;
    }

    getLegalTargets(pos) {
        if (!this.engine) return [];
        const targets = this.engine.get_legal_moves_at(pos.x, pos.y);
        const result = [];
        for (let i = 0; i < targets.length; i++) {
            result.push({ x: targets[i].get_x(), y: targets[i].get_y() });
            targets[i].free();
        }
        return result;
    }

    getBoardState() {
        if (!this.engine) return null;
        const state = this.engine.get_board_state();
        const piecesJson = state.get_pieces_json();
        const pieces = JSON.parse(piecesJson);

        const sideToMove = state.get_side_to_move();
        const isInCheck = state.get_is_in_check();
        const gameOver = state.get_game_over();

        let lastMove = null;
        const lastMoveJson = state.get_last_move_json();
        if (lastMoveJson && lastMoveJson !== 'null') {
            const lm = JSON.parse(lastMoveJson);
            lastMove = { from: { x: lm.from_x, y: lm.from_y }, to: { x: lm.to_x, y: lm.to_y } };
        }

        state.free();
        return {
            pieces,
            sideToMove,
            isInCheck,
            gameOver,
            lastMove
        };
    }

    getScore() {
        if (!this.engine) return 0;
        return this.engine.evaluate();
    }

    analyze(depth) {
        if (!this.engine || this.isAnalyzing) return null;
        this.isAnalyzing = true;
        try {
            const result = this.engine.analyze(depth);

            let bestMove = null;
            if (result.get_best_move_from_x() !== 0 || result.get_best_move_from_y() !== 0) {
                bestMove = {
                    from: { x: result.get_best_move_from_x(), y: result.get_best_move_from_y() },
                    to: { x: result.get_best_move_to_x(), y: result.get_best_move_to_y() }
                };
            }

            const candidates = [];
            const cands = result.get_candidates();
            for (let i = 0; i < cands.length; i++) {
                const cDesc = this.engine.describe_move(cands[i].get_from_x(), cands[i].get_from_y(), cands[i].get_to_x(), cands[i].get_to_y());
                candidates.push({
                    from: { x: cands[i].get_from_x(), y: cands[i].get_from_y() },
                    to: { x: cands[i].get_to_x(), y: cands[i].get_to_y() },
                    score: cands[i].get_score(),
                    description: cDesc
                });
                cands[i].free();
            }

            const spFromX = result.get_search_path_from_x();
            const spFromY = result.get_search_path_from_y();
            const spToX = result.get_search_path_to_x();
            const spToY = result.get_search_path_to_y();
            const searchPath = [];
            for (let i = 0; i < spFromX.length; i++) {
                searchPath.push({
                    from: { x: spFromX[i], y: spFromY[i] },
                    to: { x: spToX[i], y: spToY[i] }
                });
            }

            this.currentAnalysis = {
                bestMove,
                score: result.get_score(),
                candidates,
                searchPath,
                nodesSearched: result.get_nodes_searched()
            };

            result.free();
            return this.currentAnalysis;
        } finally {
            this.isAnalyzing = false;
        }
    }

    importFEN(fen) {
        if (!this.engine) return false;
        const result = this.engine.import_fen(fen);
        if (result) {
            this.moveHistory = [];
            this.selectedPos = null;
            this.currentAnalysis = null;
        }
        return result;
    }

    exportFEN() {
        if (!this.engine) return '';
        return this.engine.to_fen();
    }

    isGameOver() {
        if (!this.engine) return 'playing';
        return this.engine.is_game_over();
    }

    isInCheck() {
        if (!this.engine) return false;
        return this.engine.is_in_check();
    }

    describeMove(fromX, fromY, toX, toY) {
        if (!this.engine) return `(${fromX},${fromY})→(${toX},${toY})`;
        return this.engine.describe_move(fromX, fromY, toX, toY);
    }
}

    async initEngine() {
        try {
            const wasmModule = await import('../pkg/xiangqi_core.js');
            await wasmModule.default();
            this.wasmModule = wasmModule;
            this.engine = new wasmModule.XiangQiEngine();
        } catch (e) {
            console.error('WASM init error:', e);
            throw new Error('Engine load failed. Please use HTTP server. Error: ' + e.message);
        }
    }

    reset() {
        this.engine = new this.wasmModule.XiangQiEngine();
        this.selectedPos = null;
        this.moveHistory = [];
        this.currentAnalysis = null;
    }

    makeMove(from, to) {
        if (!this.engine) return false;
        const desc = this.engine.describe_move(from.x, from.y, to.x, to.y);
        const result = this.engine.make_move(from.x, from.y, to.x, to.y);
        if (result) {
            this.moveHistory.push({ from, to, description: desc });
            this.selectedPos = null;
            this.currentAnalysis = null;
        }
        return result;
    }

    undoMove() {
        if (!this.engine || this.moveHistory.length === 0) return false;
        const result = this.engine.undo_move();
        if (result) {
            this.moveHistory.pop();
            this.selectedPos = null;
            this.currentAnalysis = null;
        }
        return result;
    }

    getLegalTargets(pos) {
        if (!this.engine) return [];
        const targets = this.engine.get_legal_moves_at(pos.x, pos.y);
        const result = [];
        for (let i = 0; i < targets.length; i++) {
            result.push({ x: targets[i].get_x(), y: targets[i].get_y() });
            targets[i].free();
        }
        return result;
    }

    getBoardState() {
        if (!this.engine) return null;
        const state = this.engine.get_board_state();
        const piecesJson = state.get_pieces_json();
        const pieces = JSON.parse(piecesJson);

        const sideToMove = state.get_side_to_move();
        const isInCheck = state.get_is_in_check();
        const gameOver = state.get_game_over();

        let lastMove = null;
        const lastMoveJson = state.get_last_move_json();
        if (lastMoveJson && lastMoveJson !== 'null') {
            const lm = JSON.parse(lastMoveJson);
            lastMove = { from: { x: lm.from_x, y: lm.from_y }, to: { x: lm.to_x, y: lm.to_y } };
        }

        state.free();
        return {
            pieces,
            sideToMove,
            isInCheck,
            gameOver,
            lastMove
        };
    }

    getScore() {
        if (!this.engine) return 0;
        return this.engine.evaluate();
    }

    analyze(depth) {
        if (!this.engine || this.isAnalyzing) return null;
        this.isAnalyzing = true;
        try {
            const result = this.engine.analyze(depth);

            let bestMove = null;
            if (result.get_best_move_from_x() !== 0 || result.get_best_move_from_y() !== 0) {
                bestMove = {
                    from: { x: result.get_best_move_from_x(), y: result.get_best_move_from_y() },
                    to: { x: result.get_best_move_to_x(), y: result.get_best_move_to_y() }
                };
            }

            const candidates = [];
            const cands = result.get_candidates();
            for (let i = 0; i < cands.length; i++) {
                const cDesc = this.engine.describe_move(cands[i].get_from_x(), cands[i].get_from_y(), cands[i].get_to_x(), cands[i].get_to_y());
                candidates.push({
                    from: { x: cands[i].get_from_x(), y: cands[i].get_from_y() },
                    to: { x: cands[i].get_to_x(), y: cands[i].get_to_y() },
                    score: cands[i].get_score(),
                    description: cDesc
                });
                cands[i].free();
            }

            const spFromX = result.get_search_path_from_x();
            const spFromY = result.get_search_path_from_y();
            const spToX = result.get_search_path_to_x();
            const spToY = result.get_search_path_to_y();
            const searchPath = [];
            for (let i = 0; i < spFromX.length; i++) {
                searchPath.push({
                    from: { x: spFromX[i], y: spFromY[i] },
                    to: { x: spToX[i], y: spToY[i] }
                });
            }

            this.currentAnalysis = {
                bestMove,
                score: result.get_score(),
                candidates,
                searchPath,
                nodesSearched: result.get_nodes_searched()
            };

            result.free();
            return this.currentAnalysis;
        } finally {
            this.isAnalyzing = false;
        }
    }

    importFEN(fen) {
        if (!this.engine) return false;
        const result = this.engine.import_fen(fen);
        if (result) {
            this.moveHistory = [];
            this.selectedPos = null;
            this.currentAnalysis = null;
        }
        return result;
    }

    exportFEN() {
        if (!this.engine) return '';
        return this.engine.to_fen();
    }

    isGameOver() {
        if (!this.engine) return 'playing';
        return this.engine.is_game_over();
    }

    isInCheck() {
        if (!this.engine) return false;
        return this.engine.is_in_check();
    }

    describeMove(fromX, fromY, toX, toY) {
        if (!this.engine) return `(${fromX},${fromY})→(${toX},${toY})`;
        return this.engine.describe_move(fromX, fromY, toX, toY);
    }
}
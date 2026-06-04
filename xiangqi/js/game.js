export class Game {
    constructor() {
        this.ws = null;
        this.boardState = null;
        this.selectedPos = null;
        this.moveHistory = [];
        this.analysisDepth = 4;
        this.isAnalyzing = false;
        this.currentAnalysis = null;
        this.connected = false;
        this.onUpdate = null;
        this.onAnalysisProgress = null;
        this.onAnalysisComplete = null;
        this.onError = null;
    }

    async connect() {
        return new Promise((resolve, reject) => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.host;
            const wsUrl = protocol + '//' + host + '/ws';

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                this.connected = true;
                resolve();
            };

            this.ws.onerror = (e) => {
                reject(new Error('WebSocket connection failed'));
            };

            this.ws.onclose = () => {
                this.connected = false;
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
        });
    }

    handleMessage(msg) {
        switch (msg.type) {
            case 'board_state':
                this.boardState = {
                    pieces: msg.pieces,
                    sideToMove: msg.side,
                    isInCheck: msg.in_check,
                    gameOver: msg.game_status,
                    lastMove: msg.last_move ? {
                        from: { x: msg.last_move.from[0], y: msg.last_move.from[1] },
                        to: { x: msg.last_move.to[0], y: msg.last_move.to[1] },
                    } : null,
                    fen: msg.fen,
                };
                this.moveHistory = msg.move_history || [];
                if (this.onUpdate) this.onUpdate();
                break;

            case 'move_result':
                this.moveHistory = msg.move_history || [];
                this.currentAnalysis = null;
                break;

            case 'undo_result':
                this.moveHistory = msg.move_history || [];
                this.currentAnalysis = null;
                break;

            case 'new_game_result':
                this.moveHistory = [];
                this.currentAnalysis = null;
                break;

            case 'import_result':
                this.moveHistory = [];
                this.currentAnalysis = null;
                break;

            case 'analysis_progress':
                if (msg.best_move) {
                    this.currentAnalysis = {
                        bestMove: {
                            from: { x: msg.best_move.from[0], y: msg.best_move.from[1] },
                            to: { x: msg.best_move.to[0], y: msg.best_move.to[1] }
                        },
                        score: msg.score,
                        candidates: [],
                        searchPath: [],
                        nodesSearched: 0,
                        depth: msg.depth,
                        description: msg.best_move_description,
                    };
                }
                if (this.onAnalysisProgress) this.onAnalysisProgress(msg);
                break;

            case 'analysis_complete':
                this.isAnalyzing = false;
                this.currentAnalysis = {
                    bestMove: msg.best_move ? {
                        from: { x: msg.best_move.from[0], y: msg.best_move.from[1] },
                        to: { x: msg.best_move.to[0], y: msg.best_move.to[1] }
                    } : null,
                    score: msg.score,
                    candidates: (msg.candidates || []).map(c => ({
                        from: { x: c.from[0], y: c.from[1] },
                        to: { x: c.to[0], y: c.to[1] },
                        score: c.score,
                        description: c.description
                    })),
                    searchPath: (msg.search_path || []).map(m => ({
                        from: { x: m.from[0], y: m.from[1] },
                        to: { x: m.to[0], y: m.to[1] }
                    })),
                    nodesSearched: msg.nodes,
                    depth: msg.depth,
                    description: msg.best_move ? msg.best_move.description : '',
                };
                if (this.onAnalysisComplete) this.onAnalysisComplete(msg);
                break;

            case 'error':
                this.isAnalyzing = false;
                if (this.onError) this.onError(msg.message);
                break;
        }
    }

    send(data) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(data));
        }
    }

    makeMove(from, to) {
        this.send({ type: 'move', from: [from.x, from.y], to: [to.x, to.y] });
        this.selectedPos = null;
        return true;
    }

    undoMove() {
        this.send({ type: 'undo' });
        this.selectedPos = null;
        return true;
    }

    newGame() {
        this.send({ type: 'new_game' });
        this.selectedPos = null;
        this.currentAnalysis = null;
    }

    requestAnalysis(depth) {
        if (this.isAnalyzing) return;
        this.isAnalyzing = true;
        this.send({ type: 'analyze', depth: depth });
    }

    importFEN(fen) {
        this.send({ type: 'import_fen', fen: fen });
        this.selectedPos = null;
        this.currentAnalysis = null;
        return true;
    }

    exportFEN() {
        if (this.boardState) return this.boardState.fen;
        return '';
    }

    getBoardState() {
        return this.boardState;
    }

    isGameOver() {
        if (!this.boardState) return 'playing';
        return this.boardState.gameOver;
    }

    isInCheck() {
        if (!this.boardState) return false;
        return this.boardState.isInCheck;
    }

    getScore() {
        if (this.currentAnalysis) return this.currentAnalysis.score;
        return 0;
    }

    describeMove(fromX, fromY, toX, toY) {
        if (this.currentAnalysis && this.currentAnalysis.description) {
            return this.currentAnalysis.description;
        }
        return `(${fromX},${fromY})->(${toX},${toY})`;
    }

    getLegalTargets(pos) {
        if (!this.boardState) return [];
        const pieces = this.boardState.pieces;
        const side = this.boardState.sideToMove;

        const piece = pieces.find(p => p.x === pos.x && p.y === pos.y && p.side === side);
        if (!piece) return [];

        return this._generateRawMoves(pieces, piece, pos, side);
    }

    _generateRawMoves(pieces, piece, from, side) {
        const pt = piece.type;
        const moves = [];

        if (pt === 'King') {
            for (const [dx, dy] of [[0,1],[0,-1],[1,0],[-1,0]]) {
                const nx = from.x + dx, ny = from.y + dy;
                if (nx >= 0 && nx < 9 && ny >= 0 && ny < 10) {
                    if (side === 'red' ? (nx >= 3 && nx <= 5 && ny >= 7 && ny <= 9) : (nx >= 3 && nx <= 5 && ny >= 0 && ny <= 2)) {
                        const target = pieces.find(p => p.x === nx && p.y === ny);
                        if (!target || target.side !== side) moves.push({ x: nx, y: ny });
                    }
                }
            }
        } else if (pt === 'Advisor') {
            for (const [dx, dy] of [[1,1],[1,-1],[-1,1],[-1,-1]]) {
                const nx = from.x + dx, ny = from.y + dy;
                if (nx >= 0 && nx < 9 && ny >= 0 && ny < 10) {
                    if (side === 'red' ? (nx >= 3 && nx <= 5 && ny >= 7 && ny <= 9) : (nx >= 3 && nx <= 5 && ny >= 0 && ny <= 2)) {
                        const target = pieces.find(p => p.x === nx && p.y === ny);
                        if (!target || target.side !== side) moves.push({ x: nx, y: ny });
                    }
                }
            }
        } else if (pt === 'Bishop') {
            for (const [dx, dy] of [[2,2],[2,-2],[-2,2],[-2,-2]]) {
                const nx = from.x + dx, ny = from.y + dy;
                if (nx >= 0 && nx < 9 && ny >= 0 && ny < 10) {
                    const ownTerritory = side === 'red' ? ny >= 5 : ny <= 4;
                    if (!ownTerritory) continue;
                    const ex = from.x + dx/2, ey = from.y + dy/2;
                    const eye = pieces.find(p => p.x === ex && p.y === ey);
                    if (eye) continue;
                    const target = pieces.find(p => p.x === nx && p.y === ny);
                    if (!target || target.side !== side) moves.push({ x: nx, y: ny });
                }
            }
        } else if (pt === 'Knight') {
            for (const [dx,dy,bdx,bdy] of [[2,1,1,0],[2,-1,1,0],[-2,1,-1,0],[-2,-1,-1,0],[1,2,0,1],[1,-2,0,-1],[-1,2,0,1],[-1,-2,0,-1]]) {
                const nx = from.x + dx, ny = from.y + dy;
                if (nx >= 0 && nx < 9 && ny >= 0 && ny < 10) {
                    const bx = from.x + bdx, by = from.y + bdy;
                    const block = pieces.find(p => p.x === bx && p.y === by);
                    if (block) continue;
                    const target = pieces.find(p => p.x === nx && p.y === ny);
                    if (!target || target.side !== side) moves.push({ x: nx, y: ny });
                }
            }
        } else if (pt === 'Rook') {
            for (const [dx, dy] of [[0,1],[0,-1],[1,0],[-1,0]]) {
                let nx = from.x + dx, ny = from.y + dy;
                while (nx >= 0 && nx < 9 && ny >= 0 && ny < 10) {
                    const target = pieces.find(p => p.x === nx && p.y === ny);
                    if (target) {
                        if (target.side !== side) moves.push({ x: nx, y: ny });
                        break;
                    }
                    moves.push({ x: nx, y: ny });
                    nx += dx; ny += dy;
                }
            }
        } else if (pt === 'Cannon') {
            for (const [dx, dy] of [[0,1],[0,-1],[1,0],[-1,0]]) {
                let nx = from.x + dx, ny = from.y + dy;
                let jumped = false;
                while (nx >= 0 && nx < 9 && ny >= 0 && ny < 10) {
                    const target = pieces.find(p => p.x === nx && p.y === ny);
                    if (target) {
                        if (!jumped) { jumped = true; }
                        else {
                            if (target.side !== side) moves.push({ x: nx, y: ny });
                            break;
                        }
                    } else {
                        if (!jumped) moves.push({ x: nx, y: ny });
                    }
                    nx += dx; ny += dy;
                }
            }
        } else if (pt === 'Pawn') {
            const fwd = side === 'red' ? -1 : 1;
            const ny = from.y + fwd;
            if (ny >= 0 && ny < 10) {
                const target = pieces.find(p => p.x === from.x && p.y === ny);
                if (!target || target.side !== side) moves.push({ x: from.x, y: ny });
            }
            const pastRiver = side === 'red' ? from.y <= 4 : from.y >= 5;
            if (pastRiver) {
                for (const nx of [from.x - 1, from.x + 1]) {
                    if (nx >= 0 && nx < 9) {
                        const target = pieces.find(p => p.x === nx && p.y === from.y);
                        if (!target || target.side !== side) moves.push({ x: nx, y: from.y });
                    }
                }
            }
        }
        return moves;
    }
}
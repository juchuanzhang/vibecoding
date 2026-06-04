import { BoardRenderer } from './board.js';
import { Game } from './game.js';

class MainController {
    constructor() {
        this.game = new Game();
        this.boardRenderer = null;
        this.fenInput = null;
    }

    async init() {
        const canvas = document.getElementById('chessBoard');
        this.boardRenderer = new BoardRenderer(canvas);
        this.fenInput = document.getElementById('fenInput');
        this.bindEvents();

        showLoading('正在加载引擎...');
        try {
            await this.game.initEngine();
            this.updateView();
            hideLoading();
        } catch (e) {
            showError(e.message);
            hideLoading();
        }
    }

    bindEvents() {
        document.getElementById('chessBoard').addEventListener('click', (e) => this.onBoardClick(e));
        document.getElementById('btnNewGame').addEventListener('click', () => this.onNewGame());
        document.getElementById('btnUndo').addEventListener('click', () => this.onUndo());
        document.getElementById('btnAnalyze').addEventListener('click', () => this.onAnalyze());
        document.getElementById('depthSelect').addEventListener('change', (e) => {
            this.game.analysisDepth = parseInt(e.target.value);
        });
        document.getElementById('btnImport').addEventListener('click', () => this.onImport());
        document.getElementById('btnExport').addEventListener('click', () => this.onExport());
        window.addEventListener('resize', () => {
            this.boardRenderer.resize();
            this.updateView();
        });
    }

    onBoardClick(event) {
        const pos = this.boardRenderer.handleClick(event);
        if (!pos) return;
        if (this.game.isGameOver() !== 'playing') return;

        if (this.boardRenderer.selectedPos) {
            const from = this.boardRenderer.selectedPos;
            const to = pos;
            const isLegal = this.game.getLegalTargets(from).some(t => t.x === to.x && t.y === to.y);

            if (isLegal) {
                this.game.makeMove(from, to);
                this.boardRenderer.selectedPos = null;
                this.boardRenderer.legalTargets = [];
                this.updateView();
                if (this.game.isGameOver() === 'playing') {
                    this.autoAnalyze();
                }
                return;
            }

            const state = this.game.getBoardState();
            const targetPiece = state ? state.pieces.find(p => p.x === pos.x && p.y === pos.y) : null;
            if (targetPiece && targetPiece.side === state.sideToMove) {
                this.boardRenderer.selectedPos = pos;
                this.boardRenderer.legalTargets = this.game.getLegalTargets(pos);
                this.updateView();
                return;
            }

            this.boardRenderer.selectedPos = null;
            this.boardRenderer.legalTargets = [];
            this.updateView();
        } else {
            const state = this.game.getBoardState();
            if (!state) return;
            const piece = state.pieces.find(p => p.x === pos.x && p.y === pos.y && p.side === state.sideToMove);
            if (piece) {
                this.boardRenderer.selectedPos = pos;
                this.boardRenderer.legalTargets = this.game.getLegalTargets(pos);
                this.updateView();
            }
        }
    }

    autoAnalyze() {
        if (this.game.isAnalyzing) return;
        showAnalyzing('快速分析中...');
        setTimeout(() => {
            const quickResult = this.game.analyze(2);
            if (quickResult) {
                this.boardRenderer.candidates = quickResult.candidates;
                this.boardRenderer.recommendedMove = quickResult.bestMove;
                this.boardRenderer.searchPath = quickResult.searchPath;
                this.updateAnalysisPanel(quickResult, 2);
                this.updateView();
            }
            hideAnalyzing();
            const targetDepth = this.game.analysisDepth;
            if (targetDepth > 2) {
                setTimeout(() => {
                    showAnalyzing('深度分析中(' + targetDepth + '层)...');
                    setTimeout(() => {
                        const deepResult = this.game.analyze(targetDepth);
                        if (deepResult) {
                            this.boardRenderer.candidates = deepResult.candidates;
                            this.boardRenderer.recommendedMove = deepResult.bestMove;
                            this.boardRenderer.searchPath = deepResult.searchPath;
                            this.updateAnalysisPanel(deepResult, targetDepth);
                            this.updateView();
                        }
                        hideAnalyzing();
                    }, 10);
                }, 50);
            }
        }, 10);
    }

    onNewGame() {
        this.game.reset();
        this.boardRenderer.selectedPos = null;
        this.boardRenderer.legalTargets = [];
        this.boardRenderer.recommendedMove = null;
        this.boardRenderer.candidates = [];
        this.boardRenderer.searchPath = [];
        this.updateView();
    }

    onUndo() {
        this.game.undoMove();
        this.boardRenderer.selectedPos = null;
        this.boardRenderer.legalTargets = [];
        this.boardRenderer.candidates = [];
        this.updateView();
        if (this.game.isGameOver() === 'playing') {
            this.autoAnalyze();
        }
    }

    onAnalyze() {
        if (this.game.isAnalyzing) return;
        const depth = this.game.analysisDepth;
        showAnalyzing('分析中(' + depth + '层)...');
        setTimeout(() => {
            const result = this.game.analyze(depth);
            if (result) {
                this.boardRenderer.candidates = result.candidates;
                this.boardRenderer.recommendedMove = result.bestMove;
                this.boardRenderer.searchPath = result.searchPath;
                this.updateAnalysisPanel(result, depth);
            }
            this.updateView();
            hideAnalyzing();
        }, 10);
    }

    onImport() {
        const fen = this.fenInput.value.trim();
        if (!fen) { showError('请输入FEN字符串'); return; }
        const success = this.game.importFEN(fen);
        if (!success) { showError('FEN格式无效'); return; }
        this.boardRenderer.selectedPos = null;
        this.boardRenderer.legalTargets = [];
        this.boardRenderer.recommendedMove = null;
        this.boardRenderer.candidates = [];
        this.updateView();
        if (this.game.isGameOver() === 'playing') {
            this.autoAnalyze();
        }
    }

    onExport() {
        this.fenInput.value = this.game.exportFEN();
    }

    updateView() {
        const state = this.game.getBoardState();
        if (!state) return;
        this.boardRenderer.pieces = state.pieces;
        this.boardRenderer.sideToMove = state.sideToMove;
        this.boardRenderer.lastMove = state.lastMove;
        this.boardRenderer.isInCheck = state.isInCheck;
        this.boardRenderer.gameOver = state.gameOver;
        this.boardRenderer.render();
        this.updateSideInfo(state);
        this.updateHistoryPanel();
        this.updateScoreDisplay();
    }

    updateSideInfo(state) {
        const sideEl = document.getElementById('sideInfo');
        const checkEl = document.getElementById('checkWarning');
        const gameOverEl = document.getElementById('gameOverMsg');

        if (state.sideToMove === 'red') {
            sideEl.textContent = '红方走棋';
            sideEl.className = 'side-info red-side';
        } else {
            sideEl.textContent = '黑方走棋';
            sideEl.className = 'side-info black-side';
        }

        checkEl.style.display = state.isInCheck ? 'block' : 'none';
        if (state.isInCheck) checkEl.textContent = '将军！';

        if (state.gameOver === 'red_win') {
            gameOverEl.textContent = '红方胜！';
            gameOverEl.style.display = 'block';
        } else if (state.gameOver === 'black_win') {
            gameOverEl.textContent = '黑方胜！';
            gameOverEl.style.display = 'block';
        } else if (state.gameOver === 'draw') {
            gameOverEl.textContent = '和棋！';
            gameOverEl.style.display = 'block';
        } else {
            gameOverEl.style.display = 'none';
        }
    }

    updateScoreDisplay() {
        const score = this.game.getScore();
        const scoreValue = document.getElementById('scoreValue');
        const scoreBarFill = document.getElementById('scoreBarFill');
        const scoreText = document.getElementById('scoreText');

        scoreValue.textContent = score > 0 ? '+' + score : score.toString();

        const maxScore = 2000;
        const pct = Math.min(Math.abs(score) / maxScore * 100, 100);

        if (score > 0) {
            scoreValue.className = 'score-value score-red';
            scoreBarFill.style.width = (50 + pct / 2) + '%';
            scoreBarFill.style.background = '#ff4444';
            scoreBarFill.style.marginLeft = 'auto';
            scoreBarFill.style.marginRight = '0';
            scoreText.textContent = '红方领先 ' + score + ' 分';
            scoreText.style.color = '#ff4444';
        } else if (score < 0) {
            scoreValue.className = 'score-value score-black';
            scoreBarFill.style.width = (50 + pct / 2) + '%';
            scoreBarFill.style.background = '#333';
            scoreBarFill.style.marginLeft = '0';
            scoreBarFill.style.marginRight = 'auto';
            scoreText.textContent = '黑方领先 ' + Math.abs(score) + ' 分';
            scoreText.style.color = '#aaa';
        } else {
            scoreValue.className = 'score-value score-even';
            scoreBarFill.style.width = '50%';
            scoreBarFill.style.background = '#888';
            scoreBarFill.style.marginLeft = '0';
            scoreBarFill.style.marginRight = '0';
            scoreText.textContent = '双方均势';
            scoreText.style.color = '#888';
        }
    }

    updateAnalysisPanel(result, depth) {
        const candidatesList = document.getElementById('candidatesList');
        const pathDisplay = document.getElementById('pathDisplay');
        const statusInfo = document.getElementById('statusInfo');

        candidatesList.innerHTML = '';
        for (let i = 0; i < result.candidates.length; i++) {
            const c = result.candidates[i];
            const li = document.createElement('li');
            li.className = 'candidate-item' + (i === 0 ? ' best' : '');
            li.innerHTML = `<span>${c.description}</span><span>${c.score > 0 ? '+' + c.score : c.score}</span>`;
            candidatesList.appendChild(li);
        }

        let pathText = '';
        for (let i = 0; i < result.searchPath.length; i++) {
            const m = result.searchPath[i];
            const desc = this.game.describeMove(m.from.x, m.from.y, m.to.x, m.to.y);
            pathText += desc + ' ';
        }
        pathDisplay.textContent = pathText || '无推演路径';
        statusInfo.innerHTML = `节点: ${result.nodesSearched.toLocaleString()} | 深度: ${depth}层`;
    }

    updateHistoryPanel() {
        const historyEl = document.getElementById('historyList');
        let html = '';
        for (let i = 0; i < this.game.moveHistory.length; i++) {
            const m = this.game.moveHistory[i];
            const side = i % 2 === 0 ? '红' : '黑';
            const num = Math.floor(i / 2) + 1;
            const desc = m.description || this.game.describeMove(m.from.x, m.from.y, m.to.x, m.to.y);
            html += `<div class="history-item"><span>${num}. ${side}</span><span>${desc}</span></div>`;
        }
        historyEl.innerHTML = html;
        if (historyEl.lastChild) historyEl.lastChild.scrollIntoView();
    }
}

function showLoading(msg) {
    const el = document.getElementById('loadingMsg');
    el.textContent = msg;
    el.style.display = 'block';
}

function hideLoading() {
    document.getElementById('loadingMsg').style.display = 'none';
}

function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = msg;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
}

function showAnalyzing(msg) {
    const el = document.getElementById('analyzingIndicator');
    el.textContent = msg || '分析中...';
    el.style.display = 'block';
    document.getElementById('btnAnalyze').disabled = true;
}

function hideAnalyzing() {
    document.getElementById('analyzingIndicator').style.display = 'none';
    document.getElementById('btnAnalyze').disabled = false;
}

let controller;

async function main() {
    controller = new MainController();
    await controller.init();
}

window.addEventListener('DOMContentLoaded', main);
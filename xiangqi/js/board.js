class BoardRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.cellSize = 60;
        this.padding = 30;
        this.selectedPos = null;
        this.legalTargets = [];
        this.lastMove = null;
        this.recommendedMove = null;
        this.searchPath = [];
        this.pieces = [];
        this.sideToMove = 'red';
        this.isInCheck = false;
        this.gameOver = 'playing';
        this.resize();
    }

    resize() {
        const containerWidth = this.canvas.parentElement.clientWidth;
        const maxWidth = Math.min(containerWidth - 20, 540);
        this.cellSize = Math.floor((maxWidth - 2 * this.padding) / 8);
        const boardWidth = this.cellSize * 8 + 2 * this.padding;
        const boardHeight = this.cellSize * 9 + 2 * this.padding;
        this.canvas.width = boardWidth;
        this.canvas.height = boardHeight;
        this.canvas.style.width = boardWidth + 'px';
        this.canvas.style.height = boardHeight + 'px';
    }

    posToPixel(pos) {
        return {
            x: this.padding + pos.x * this.cellSize,
            y: this.padding + pos.y * this.cellSize
        };
    }

    pixelToPos(px, py) {
        const x = Math.round((px - this.padding) / this.cellSize);
        const y = Math.round((py - this.padding) / this.cellSize);
        if (x >= 0 && x <= 8 && y >= 0 && y <= 9) {
            return { x, y };
        }
        return null;
    }

    render() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.drawBackground();
        this.drawGrid();
        this.drawRiver();
        this.drawPalaceLines();
        this.drawLastMove();
        this.drawRecommendedMove();
        this.drawLegalTargets();
        this.drawPieces();
        this.drawSelectedHighlight();
        this.drawCheckHighlight();
    }

    drawBackground() {
        this.ctx.fillStyle = '#d4a862';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    drawGrid() {
        this.ctx.strokeStyle = '#5c3a1e';
        this.ctx.lineWidth = 1.5;

        for (let y = 0; y <= 9; y++) {
            this.ctx.beginPath();
            const start = this.posToPixel({ x: 0, y });
            const end = this.posToPixel({ x: 8, y });
            this.ctx.moveTo(start.x, start.y);
            this.ctx.lineTo(end.x, end.y);
            this.ctx.stroke();
        }

        for (let x = 0; x <= 8; x++) {
            this.ctx.beginPath();
            const top = this.posToPixel({ x, y: 0 });
            const mid1 = this.posToPixel({ x, y: 4 });
            const mid2 = this.posToPixel({ x, y: 5 });
            const bottom = this.posToPixel({ x, y: 9 });
            this.ctx.moveTo(top.x, top.y);
            this.ctx.lineTo(mid1.x, mid1.y);
            this.ctx.moveTo(mid2.x, mid2.y);
            this.ctx.lineTo(bottom.x, bottom.y);
            this.ctx.stroke();
        }
    }

    drawRiver() {
        const left = this.posToPixel({ x: 0, y: 4 });
        const right = this.posToPixel({ x: 8, y: 5 });
        const midY = (left.y + right.y) / 2;
        this.ctx.fillStyle = '#5c3a1e';
        this.ctx.font = `bold ${this.cellSize * 0.5}px serif`;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText('楚 河', left.x + this.cellSize * 2, midY);
        this.ctx.fillText('汉 界', right.x - this.cellSize * 2, midY);
    }

    drawPalaceLines() {
        this.ctx.strokeStyle = '#5c3a1e';
        this.ctx.lineWidth = 1;

        const drawCross = (xStart, yStart, xEnd, yEnd) => {
            const s = this.posToPixel({ x: xStart, y: yStart });
            const e = this.posToPixel({ x: xEnd, y: yEnd });
            this.ctx.beginPath();
            this.ctx.moveTo(s.x, s.y);
            this.ctx.lineTo(e.x, e.y);
            this.ctx.stroke();
        };

        drawCross(3, 0, 5, 2);
        drawCross(5, 0, 3, 2);
        drawCross(3, 7, 5, 9);
        drawCross(5, 7, 3, 9);
    }

    drawLastMove() {
        if (!this.lastMove) return;
        const alpha = 0.35;
        this.ctx.fillStyle = `rgba(255, 200, 0, ${alpha})`;

        const from = this.posToPixel(this.lastMove.from);
        const to = this.posToPixel(this.lastMove.to);

        const r = this.cellSize * 0.42;
        this.ctx.beginPath();
        this.ctx.arc(from.x, from.y, r, 0, 2 * Math.PI);
        this.ctx.fill();

        this.ctx.beginPath();
        this.ctx.arc(to.x, to.y, r, 0, 2 * Math.PI);
        this.ctx.fill();
    }

    drawRecommendedMove() {
        if (!this.recommendedMove) return;

        const from = this.posToPixel(this.recommendedMove.from);
        const to = this.posToPixel(this.recommendedMove.to);

        this.ctx.strokeStyle = '#2ecc71';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(from.x, from.y);
        this.ctx.lineTo(to.x, to.y);
        this.ctx.stroke();

        const headLen = this.cellSize * 0.3;
        const angle = Math.atan2(to.y - from.y, to.x - from.x);
        this.ctx.beginPath();
        this.ctx.moveTo(to.x, to.y);
        this.ctx.lineTo(to.x - headLen * Math.cos(angle - Math.PI / 6), to.y - headLen * Math.sin(angle - Math.PI / 6));
        this.ctx.lineTo(to.x - headLen * Math.cos(angle + Math.PI / 6), to.y - headLen * Math.sin(angle + Math.PI / 6));
        this.ctx.closePath();
        this.ctx.fillStyle = '#2ecc71';
        this.ctx.fill();
    }

    drawLegalTargets() {
        for (const pos of this.legalTargets) {
            const px = this.posToPixel(pos);
            const targetPiece = this.pieces.find(p => p.x === pos.x && p.y === pos.y);
            const r = this.cellSize * 0.42;

            if (targetPiece) {
                this.ctx.strokeStyle = 'rgba(46, 204, 113, 0.7)';
                this.ctx.lineWidth = 2.5;
                this.ctx.beginPath();
                this.ctx.arc(px.x, px.y, r, 0, 2 * Math.PI);
                this.ctx.stroke();
            } else {
                this.ctx.fillStyle = 'rgba(46, 204, 113, 0.4)';
                this.ctx.beginPath();
                this.ctx.arc(px.x, px.y, this.cellSize * 0.15, 0, 2 * Math.PI);
                this.ctx.fill();
            }
        }
    }

    drawPieces() {
        const pieceRadius = this.cellSize * 0.4;

        for (const piece of this.pieces) {
            const px = this.posToPixel({ x: piece.x, y: piece.y });

            this.ctx.beginPath();
            this.ctx.arc(px.x, px.y, pieceRadius, 0, 2 * Math.PI);
            this.ctx.fillStyle = '#f5deb3';
            this.ctx.fill();
            this.ctx.strokeStyle = piece.side === 'red' ? '#cc0000' : '#1a1a1a';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();

            this.ctx.beginPath();
            this.ctx.arc(px.x, px.y, pieceRadius - 4, 0, 2 * Math.PI);
            this.ctx.strokeStyle = piece.side === 'red' ? '#cc0000' : '#1a1a1a';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();

            this.ctx.fillStyle = piece.side === 'red' ? '#cc0000' : '#1a1a1a';
            this.ctx.font = `bold ${this.cellSize * 0.45}px serif`;
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            this.ctx.fillText(piece.name, px.x, px.y);
        }
    }

    drawSelectedHighlight() {
        if (!this.selectedPos) return;
        const px = this.posToPixel(this.selectedPos);
        const r = this.cellSize * 0.42;

        this.ctx.strokeStyle = '#00aaff';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.arc(px.x, px.y, r + 2, 0, 2 * Math.PI);
        this.ctx.stroke();
    }

    drawCheckHighlight() {
        if (!this.isInCheck) return;
        const king = this.pieces.find(p =>
            p.piece_type === 'King' && p.side === this.sideToMove
        );
        if (!king) return;
        const px = this.posToPixel({ x: king.x, y: king.y });
        const r = this.cellSize * 0.42;

        this.ctx.strokeStyle = '#ff0000';
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([5, 3]);
        this.ctx.beginPath();
        this.ctx.arc(px.x, px.y, r + 4, 0, 2 * Math.PI);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }

    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        const px = (event.clientX - rect.left) * scaleX;
        const py = (event.clientY - rect.top) * scaleY;
        return this.pixelToPos(px, py);
    }
}
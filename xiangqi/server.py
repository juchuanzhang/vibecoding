import json
import asyncio
import time
import logging
import sys
from aiohttp import web
from engine import Board, Move, Position, Side
from engine.move_gen import generate_legal_moves
from engine.rules import is_legal_move, is_in_check
from engine.describe import describe_move as describe_move_func
from engine.fast_engine import FastBoard, FastEngine, describe_move as fast_describe

DEBUG = '--debug' in sys.argv or '-d' in sys.argv
THREAD_COUNT = None
for i, arg in enumerate(sys.argv):
    if arg == '--threads' and i + 1 < len(sys.argv):
        THREAD_COUNT = int(sys.argv[i + 1])
        break

logger = logging.getLogger('xiangqi')
logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(handler)


class GameSession:
    def __init__(self):
        self.board = Board()
        self.fast_board = FastBoard()
        self.engine = FastEngine(thread_count=THREAD_COUNT)
        self.move_records = []
        self.move_number = 0
        self.analyzing = False
        logger.debug("GameSession created, initial FEN: %s", self.board.to_fen())

    def make_move(self, from_x, from_y, to_x, to_y):
        from_pos = Position(from_x, from_y)
        to_pos = Position(to_x, to_y)

        piece = self.board.piece_at(from_pos)
        if piece is None or piece.side != self.board.side_to_move:
            logger.warning("Illegal move: no piece or wrong side at (%d,%d)", from_x, from_y)
            return {"type": "error", "message": "illegal_side"}

        if not is_legal_move(self.board, from_pos, to_pos):
            logger.warning("Illegal move: (%d,%d)->(%d,%d) not legal for %s %s",
                           from_x, from_y, to_x, to_y, piece.side, piece.piece_type.name)
            return {"type": "error", "message": "illegal_move"}

        desc = describe_move_func(self.board, from_x, from_y, to_x, to_y)
        captured = self.board.piece_at(to_pos)
        logger.debug("Move: %s (%d,%d)->(%d,%d), captured=%s",
                     desc, from_x, from_y, to_x, to_y,
                     captured.display_name() if captured else None)
        self.board.make_move_internal(Move(from_pos, to_pos))
        self.fast_board.make_move(from_x, from_y, to_x, to_y)

        self.move_number += 1
        self.move_records.append({
            "from": [from_x, from_y],
            "to": [to_x, to_y],
            "description": desc,
            "move_number": self.move_number,
            "side": "red" if piece.side == Side.Red else "black",
            "captured": captured.display_name() if captured else None,
        })

        game_status = self._get_game_status()
        logger.debug("Game status after move: %s, FEN: %s", game_status, self.board.to_fen())

        return {
            "type": "move_result",
            "move_description": desc,
            "side": "red" if piece.side == Side.Red else "black",
            "game_status": game_status,
            "move_history": self.move_records,
        }

    def undo_move(self):
        logger.debug("Undo move, current moves: %d", len(self.move_records))
        if not self.board.undo_move_internal() or not self.fast_board.undo_move():
            logger.warning("Cannot undo: no history")
            return {"type": "error", "message": "cannot_undo"}
        if self.move_records:
            self.move_records.pop()
        self.move_number = len(self.move_records)
        logger.debug("Undo successful, remaining moves: %d, FEN: %s",
                     len(self.move_records), self.board.to_fen())
        return {"type": "undo_result", "move_history": self.move_records}

    def new_game(self):
        logger.debug("New game")
        self.board = Board()
        self.fast_board = FastBoard()
        self.engine.clear()
        self.move_records = []
        self.move_number = 0
        return {"type": "new_game_result"}

    def import_fen(self, fen):
        logger.debug("Import FEN: %s", fen)
        new_board = Board.from_fen(fen)
        if new_board is None:
            logger.warning("Invalid FEN: %s", fen)
            return {"type": "error", "message": "invalid_fen"}
        self.board = new_board
        new_fb = FastBoard()
        if not new_fb.from_fen(fen):
            logger.warning("FastBoard cannot parse FEN: %s", fen)
            return {"type": "error", "message": "invalid_fen"}
        self.fast_board = new_fb
        self.engine.clear()
        self.move_records = []
        self.move_number = 0
        logger.debug("FEN imported successfully")
        return {"type": "import_result", "fen": fen}

    def get_board_state(self):
        pieces = []
        for y in range(10):
            for x in range(9):
                pos = Position(x, y)
                piece = self.board.piece_at(pos)
                if piece is not None:
                    pieces.append({
                        "x": x, "y": y,
                        "type": piece.piece_type.name,
                        "side": "red" if piece.side == Side.Red else "black",
                        "name": piece.display_name(),
                    })

        side = "red" if self.board.side_to_move == Side.Red else "black"
        in_check = is_in_check(self.board, self.board.side_to_move)
        game_status = self._get_game_status()

        last_move = None
        lm = self.board.get_last_move()
        if lm:
            last_move = {
                "from": [lm.from_pos.x, lm.from_pos.y],
                "to": [lm.to_pos.x, lm.to_pos.y],
            }

        return {
            "type": "board_state",
            "pieces": pieces,
            "side": side,
            "in_check": in_check,
            "game_status": game_status,
            "fen": self.board.to_fen(),
            "last_move": last_move,
            "move_history": self.move_records,
        }

    def _get_game_status(self):
        moves = generate_legal_moves(self.board)
        if not moves:
            if is_in_check(self.board, self.board.side_to_move):
                winner = "black" if self.board.side_to_move == Side.Red else "red"
                logger.info("Game over: %s wins by checkmate", winner)
                return f"{winner}_win"
            logger.info("Game over: stalemate draw")
            return "draw"
        return "playing"


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    game = GameSession()
    logger.debug("WebSocket connected")

    await ws.send_json(game.get_board_state())

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from client")
                await ws.send_json({"type": "error", "message": "invalid_json"})
                continue

            msg_type = data.get("type")
            logger.debug("Received: type=%s, data=%s", msg_type, json.dumps(data, ensure_ascii=False)[:200])

            if msg_type == "move":
                from_pos = data.get("from", [0, 0])
                to_pos = data.get("to", [0, 0])
                result = game.make_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1])
                await ws.send_json(result)
                await ws.send_json(game.get_board_state())

            elif msg_type == "undo":
                result = game.undo_move()
                await ws.send_json(result)
                await ws.send_json(game.get_board_state())

            elif msg_type == "new_game":
                result = game.new_game()
                await ws.send_json(result)
                await ws.send_json(game.get_board_state())

            elif msg_type == "import_fen":
                fen = data.get("fen", "")
                result = game.import_fen(fen)
                await ws.send_json(result)
                await ws.send_json(game.get_board_state())

            elif msg_type == "analyze":
                depth = data.get("depth", 4)
                logger.info("Analysis request: depth=%d", depth)
                if game.analyzing:
                    logger.warning("Already analyzing, rejected")
                    await ws.send_json({"type": "error", "message": "already_analyzing"})
                    continue
                game.analyzing = True

                try:
                    t0 = time.time()
                    for d in range(1, depth + 1):
                        logger.debug("Searching depth %d...", d)
                        result = game.engine._search_depth(game.fast_board, d)
                        elapsed = time.time() - t0
                        best = result.get('best')
                        if best:
                            fx, fy, tx, ty = best
                            desc = fast_describe(game.fast_board.cells, fx, fy, tx, ty)
                            logger.info("Depth %d: best=%s score=%d nodes=%d elapsed=%.1fs",
                                        d, desc, result['score'], result['nodes'], elapsed)
                            await ws.send_json({
                                "type": "analysis_progress",
                                "depth": d,
                                "score": result['score'],
                                "best_move_description": desc,
                                "best_move": {"from": [fx, fy], "to": [tx, ty]},
                            })

                    candidates_json = []
                    for c, score in result.get('candidates', []):
                        c_desc = fast_describe(game.fast_board.cells, c[0], c[1], c[2], c[3])
                        candidates_json.append({
                            "from": [c[0], c[1]],
                            "to": [c[2], c[3]],
                            "description": c_desc,
                            "score": score,
                        })

                    search_path_json = []
                    for m in result.get('path', []):
                        search_path_json.append({
                            "from": [m[0], m[1]],
                            "to": [m[2], m[3]],
                        })

                    best = result.get('best')
                    best_json = None
                    if best:
                        fx, fy, tx, ty = best
                        desc = fast_describe(game.fast_board.cells, fx, fy, tx, ty)
                        best_json = {"from": [fx, fy], "to": [tx, ty], "description": desc}

                    total_elapsed = time.time() - t0
                    logger.info("Analysis complete: depth=%d score=%d nodes=%d total=%.1fs",
                                result['depth'], result['score'], result['nodes'], total_elapsed)

                    await ws.send_json({
                        "type": "analysis_complete",
                        "depth": result['depth'],
                        "score": result['score'],
                        "best_move": best_json,
                        "candidates": candidates_json,
                        "search_path": search_path_json,
                        "nodes": result['nodes'],
                        "time_ms": int(total_elapsed * 1000),
                    })
                except Exception as e:
                    logger.error("Analysis error: %s", e, exc_info=True)
                    await ws.send_json({"type": "error", "message": str(e)})
                finally:
                    game.analyzing = False

        elif msg.type == web.WSMsgType.ERROR:
            logger.error("WebSocket error: %s", msg.data)
            break

    logger.debug("WebSocket disconnected")
    return ws


async def index_handler(request):
    return web.FileResponse('./index.html')


app = web.Application()
app.router.add_get('/', index_handler)
app.router.add_static('/js', './js')
app.router.add_static('/css', './css')
app.router.add_get('/ws', websocket_handler)

if __name__ == '__main__':
    logger.info("Starting server on localhost:8080 (debug=%s threads=%d)", DEBUG, THREAD_COUNT or os.cpu_count() or 4)
    web.run_app(app, host='localhost', port=8080)
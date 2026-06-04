from .types import Piece, PieceType, Side, Position, Move, AnalysisResult, CandidateMove
from .board import Board
from .move_gen import generate_legal_moves, sort_moves, PIECE_SORT_VALUES
from .rules import is_in_check
from .evaluation import evaluate
from .describe import describe_move
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from typing import Optional


INFINITY = 99999


class EntryFlag(Enum):
    Exact = 0
    LowerBound = 1
    UpperBound = 2


class TableEntry:
    __slots__ = ('depth', 'score', 'best_move', 'flag')

    def __init__(self, depth, score, best_move, flag):
        self.depth = depth
        self.score = score
        self.best_move = best_move
        self.flag = flag


class Engine:
    def __init__(self, thread_count: Optional[int] = None):
        import os
        self.thread_count = thread_count or os.cpu_count() or 4
        self.transposition_table: dict[int, TableEntry] = {}
        self.killer_moves: list[list[Optional[Move]]] = [[None, None] for _ in range(64)]
        self.nodes_searched = 0
        self.history_table: list[list[int]] = [[0] * 9 for _ in range(10)]

    def clear_table(self):
        self.transposition_table.clear()
        self.killer_moves = [[None, None] for _ in range(64)]
        self.history_table = [[0] * 9 for _ in range(10)]

    def analyze(self, board: Board, depth: int) -> AnalysisResult:
        self.nodes_searched = 0
        start_time = time.time()

        moves = generate_legal_moves(board)
        if not moves:
            score = -INFINITY if is_in_check(board, board.side_to_move) else 0
            return AnalysisResult(
                best_move=None, score=score, candidates=[], search_path=[],
                nodes_searched=0, time_ms=0, depth=depth
            )

        best_result = None
        for d in range(1, depth + 1):
            result = self._search_at_depth(board, d)
            best_result = result

        elapsed = int((time.time() - start_time) * 1000)
        best_result.time_ms = elapsed
        best_result.depth = depth
        return best_result

    def analyze_multithread(self, board: Board, depth: int, progress_callback=None) -> AnalysisResult:
        self.nodes_searched = 0
        start_time = time.time()

        moves = generate_legal_moves(board)
        if not moves:
            score = -INFINITY if is_in_check(board, board.side_to_move) else 0
            return AnalysisResult(
                best_move=None, score=score, candidates=[], search_path=[],
                nodes_searched=0, time_ms=0, depth=depth
            )

        for d in range(1, min(depth, 3) + 1):
            result = self._search_at_depth(board, d)
            if progress_callback:
                desc = describe_move(board, result.best_move.from_pos.x, result.best_move.from_pos.y,
                                     result.best_move.to_pos.x, result.best_move.to_pos.y) if result.best_move else ""
                progress_callback(d, result.score, desc, result.candidates)

        if depth > 3:
            best_result = self._parallel_deep_search(board, depth, progress_callback)
        else:
            best_result = result

        elapsed = int((time.time() - start_time) * 1000)
        best_result.time_ms = elapsed
        best_result.depth = depth
        return best_result

    def _parallel_deep_search(self, board: Board, depth: int, progress_callback=None) -> AnalysisResult:
        root_moves = generate_legal_moves(board)
        self._order_root_moves(board, root_moves)

        if not root_moves:
            score = -INFINITY if is_in_check(board, board.side_to_move) else 0
            return AnalysisResult(
                best_move=None, score=score, candidates=[], search_path=[],
                nodes_searched=self.nodes_searched, time_ms=0, depth=depth
            )

        maximizing = board.side_to_move == Side.Red
        results = {}

        def search_root_move(mv):
            search_board = board.clone_for_search()
            search_board.make_move_internal(mv)
            engine_copy = Engine.__new__(Engine)
            engine_copy.transposition_table = self.transposition_table.copy()
            engine_copy.killer_moves = [[None, None] for _ in range(64)]
            engine_copy.nodes_searched = 0
            engine_copy.history_table = [[0] * 9 for _ in range(10)]

            score = engine_copy._iterative_deepening(search_board, depth - 1, not maximizing)
            self.nodes_searched += engine_copy.nodes_searched

            for k, v in engine_copy.transposition_table.items():
                existing = self.transposition_table.get(k)
                if existing is None or v.depth >= existing.depth:
                    self.transposition_table[k] = v

            return mv, score

        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            futures = {executor.submit(search_root_move, mv): mv for mv in root_moves}
            for future in as_completed(futures):
                mv, score = future.result()
                results[mv] = score
                if progress_callback:
                    current_best = max(results.values()) if maximizing else min(results.values())
                    best_mv = max(results, key=results.get) if maximizing else min(results, key=results.get)
                    desc = describe_move(board, best_mv.from_pos.x, best_mv.from_pos.y,
                                         best_mv.to_pos.x, best_mv.to_pos.y)
                    progress_callback(depth, current_best, desc, [])

        if maximizing:
            best_move = max(results, key=results.get)
            best_score = results[best_move]
        else:
            best_move = min(results, key=results.get)
            best_score = results[best_move]

        candidates = []
        for mv, score in results.items():
            candidates.append(CandidateMove(move=mv, score=score))
        if maximizing:
            candidates.sort(key=lambda c: -c.score)
        else:
            candidates.sort(key=lambda c: c.score)
        candidates = candidates[:3]

        search_path = self._get_search_path(board, best_move, depth)

        return AnalysisResult(
            best_move=best_move, score=best_score, candidates=candidates,
            search_path=search_path, nodes_searched=self.nodes_searched, time_ms=0, depth=depth
        )

    def _iterative_deepening(self, board: Board, max_depth: int, maximizing: bool) -> int:
        best_score = -INFINITY if maximizing else INFINITY
        for d in range(1, max_depth + 1):
            score = self._alpha_beta(board, d, -INFINITY, INFINITY, maximizing, 0)
            if maximizing:
                best_score = max(best_score, score)
            else:
                best_score = min(best_score, score)
        return best_score

    def _search_at_depth(self, board: Board, depth: int) -> AnalysisResult:
        moves = generate_legal_moves(board)
        if not moves:
            score = -INFINITY if is_in_check(board, board.side_to_move) else 0
            return AnalysisResult(
                best_move=None, score=score, candidates=[], search_path=[],
                nodes_searched=self.nodes_searched, time_ms=0, depth=depth
            )

        self._order_root_moves(board, moves)

        maximizing = board.side_to_move == Side.Red
        best_score = -INFINITY if maximizing else INFINITY
        best_move = moves[0]
        candidates: list[CandidateMove] = []

        search_board = board.clone_for_search()

        for mv in moves:
            search_board.make_move_internal(mv)
            score = self._alpha_beta(search_board, depth - 1, -INFINITY, INFINITY, not maximizing, 0)
            search_board.undo_move_internal()

            candidates.append(CandidateMove(move=mv, score=score))

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_move = mv
            else:
                if score < best_score:
                    best_score = score
                    best_move = mv

        if maximizing:
            candidates.sort(key=lambda c: -c.score)
        else:
            candidates.sort(key=lambda c: c.score)
        candidates = candidates[:3]

        search_path = self._get_search_path(board, best_move, depth)

        return AnalysisResult(
            best_move=best_move, score=best_score, candidates=candidates,
            search_path=search_path, nodes_searched=self.nodes_searched, time_ms=0, depth=depth
        )

    def _order_root_moves(self, board: Board, moves: list[Move]):
        moves.sort(key=lambda m: -PIECE_SORT_VALUES.get(
            board.piece_at(m.to_pos).piece_type if board.piece_at(m.to_pos) else PieceType.Pawn, 0))

        hash_val = board.zobrist_hash
        entry = self.transposition_table.get(hash_val)
        if entry and entry.best_move:
            tt_move = entry.best_move
            for i, m in enumerate(moves):
                if m == tt_move:
                    moves.insert(0, moves.pop(i))
                    break

        ply = 0
        for k in range(2):
            killer = self.killer_moves[ply][k]
            if killer:
                for i in range(1, len(moves)):
                    if moves[i] == killer and i > k:
                        moves.insert(k + 1, moves.pop(i))
                        break

    def _alpha_beta(self, board: Board, depth: int, alpha: int, beta: int, maximizing: bool, ply: int) -> int:
        self.nodes_searched += 1

        hash_val = board.zobrist_hash
        entry = self.transposition_table.get(hash_val)
        if entry and entry.depth >= depth:
            if entry.flag == EntryFlag.Exact:
                return entry.score
            elif entry.flag == EntryFlag.LowerBound:
                if entry.score >= beta:
                    return entry.score
                if entry.score > alpha:
                    alpha = entry.score
            elif entry.flag == EntryFlag.UpperBound:
                if entry.score <= alpha:
                    return entry.score
                if entry.score < beta:
                    beta = entry.score

        if depth == 0:
            return self._quiescence(board, alpha, beta, maximizing, ply, 6)

        moves = generate_legal_moves(board)
        if not moves:
            if is_in_check(board, board.side_to_move):
                return -INFINITY + ply if maximizing else INFINITY - ply
            return 0

        self._order_moves(board, moves, ply)

        original_alpha = alpha
        best_score = -INFINITY if maximizing else INFINITY
        best_move_in_node = moves[0]

        for mv in moves:
            is_capture = board.piece_at(mv.to_pos) is not None
            board.make_move_internal(mv)
            score = self._alpha_beta(board, depth - 1, alpha, beta, not maximizing, ply + 1)
            board.undo_move_internal()

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_move_in_node = mv
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    if not is_capture and ply < 64:
                        self.killer_moves[ply][1] = self.killer_moves[ply][0]
                        self.killer_moves[ply][0] = mv
                    self.history_table[mv.from_pos.y][mv.from_pos.x] += depth * depth
                    break
            else:
                if score < best_score:
                    best_score = score
                    best_move_in_node = mv
                if score < beta:
                    beta = score
                if beta <= alpha:
                    if not is_capture and ply < 64:
                        self.killer_moves[ply][1] = self.killer_moves[ply][0]
                        self.killer_moves[ply][0] = mv
                    self.history_table[mv.from_pos.y][mv.from_pos.x] += depth * depth
                    break

        flag = EntryFlag.Exact
        if best_score <= original_alpha:
            flag = EntryFlag.UpperBound
        elif best_score >= beta:
            flag = EntryFlag.LowerBound

        self.transposition_table[hash_val] = TableEntry(depth, best_score, best_move_in_node, flag)

        return best_score

    def _quiescence(self, board: Board, alpha: int, beta: int, maximizing: bool, ply: int, max_depth: int) -> int:
        self.nodes_searched += 1

        stand_pat = evaluate(board)

        if maximizing:
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat
        else:
            if stand_pat <= alpha:
                return alpha
            if stand_pat < beta:
                beta = stand_pat

        if max_depth == 0:
            return stand_pat

        moves = generate_legal_moves(board)
        capture_moves = [m for m in moves if board.piece_at(m.to_pos) is not None]

        if not capture_moves and not is_in_check(board, board.side_to_move):
            return stand_pat

        search_moves = capture_moves if capture_moves else moves
        sorted_moves = sort_moves(board, search_moves)

        best_score = stand_pat

        for mv in sorted_moves:
            board.make_move_internal(mv)
            score = self._quiescence(board, alpha, beta, not maximizing, ply + 1, max_depth - 1)
            board.undo_move_internal()

            if maximizing:
                if score > best_score:
                    best_score = score
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    return beta
            else:
                if score < best_score:
                    best_score = score
                if score < beta:
                    beta = score
                if beta <= alpha:
                    return alpha

        return best_score

    def _order_moves(self, board: Board, moves: list[Move], ply: int):
        def move_score(mv):
            score = 0

            hash_val = board.zobrist_hash
            entry = self.transposition_table.get(hash_val)
            if entry and entry.best_move == mv:
                score += 10000

            target = board.piece_at(mv.to_pos)
            if target is not None:
                attacker = board.piece_at(mv.from_pos)
                score += PIECE_SORT_VALUES.get(target.piece_type, 0) * 10 - PIECE_SORT_VALUES.get(attacker.piece_type, 0)

            if ply < 64:
                for k in range(2):
                    if self.killer_moves[ply][k] == mv:
                        score += 9000 - k * 100

            score += self.history_table[mv.from_pos.y][mv.from_pos.x]

            return score

        moves.sort(key=lambda m: -move_score(m))

    def _get_search_path(self, board: Board, first_move: Move, depth: int) -> list[Move]:
        path = [first_move]
        search_board = board.clone_for_search()
        search_board.make_move_internal(first_move)

        for _ in range(1, depth):
            hash_val = search_board.zobrist_hash
            entry = self.transposition_table.get(hash_val)
            if entry and entry.best_move:
                legal_moves = generate_legal_moves(search_board)
                if entry.best_move in legal_moves:
                    path.append(entry.best_move)
                    search_board.make_move_internal(entry.best_move)
                    continue
            break

        return path
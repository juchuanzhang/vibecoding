/* tslint:disable */
/* eslint-disable */

export class JsAnalysisResult {
    private constructor();
    free(): void;
    [Symbol.dispose](): void;
    get_best_move_from_x(): number;
    get_best_move_from_y(): number;
    get_best_move_to_x(): number;
    get_best_move_to_y(): number;
    get_candidates(): JsCandidateMove[];
    get_nodes_searched(): number;
    get_score(): number;
    get_search_path_from_x(): Uint8Array;
    get_search_path_from_y(): Uint8Array;
    get_search_path_to_x(): Uint8Array;
    get_search_path_to_y(): Uint8Array;
}

export class JsBoardState {
    private constructor();
    free(): void;
    [Symbol.dispose](): void;
    get_game_over(): string;
    get_is_in_check(): boolean;
    get_last_move_json(): string;
    get_pieces_json(): string;
    get_side_to_move(): string;
}

export class JsCandidateMove {
    private constructor();
    free(): void;
    [Symbol.dispose](): void;
    get_from_x(): number;
    get_from_y(): number;
    get_score(): number;
    get_to_x(): number;
    get_to_y(): number;
}

export class JsPieceInfo {
    private constructor();
    free(): void;
    [Symbol.dispose](): void;
    get_name(): string;
    get_piece_type(): string;
    get_side(): string;
    get_x(): number;
    get_y(): number;
}

export class JsPosition {
    free(): void;
    [Symbol.dispose](): void;
    get_x(): number;
    get_y(): number;
    constructor(x: number, y: number);
}

export class XiangQiEngine {
    free(): void;
    [Symbol.dispose](): void;
    analyze(depth: number): JsAnalysisResult;
    evaluate(): number;
    static from_fen(fen: string): XiangQiEngine;
    get_board_state(): JsBoardState;
    get_legal_moves_at(x: number, y: number): JsPosition[];
    import_fen(fen: string): boolean;
    is_game_over(): string;
    is_in_check(): boolean;
    make_move(from_x: number, from_y: number, to_x: number, to_y: number): boolean;
    constructor();
    reset(): void;
    to_fen(): string;
    undo_move(): boolean;
}

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly __wbg_jsanalysisresult_free: (a: number, b: number) => void;
    readonly __wbg_jsboardstate_free: (a: number, b: number) => void;
    readonly __wbg_jscandidatemove_free: (a: number, b: number) => void;
    readonly __wbg_jspieceinfo_free: (a: number, b: number) => void;
    readonly __wbg_jsposition_free: (a: number, b: number) => void;
    readonly __wbg_xiangqiengine_free: (a: number, b: number) => void;
    readonly jsanalysisresult_get_best_move_from_x: (a: number) => number;
    readonly jsanalysisresult_get_best_move_from_y: (a: number) => number;
    readonly jsanalysisresult_get_best_move_to_x: (a: number) => number;
    readonly jsanalysisresult_get_best_move_to_y: (a: number) => number;
    readonly jsanalysisresult_get_candidates: (a: number, b: number) => void;
    readonly jsanalysisresult_get_nodes_searched: (a: number) => number;
    readonly jsanalysisresult_get_score: (a: number) => number;
    readonly jsanalysisresult_get_search_path_from_x: (a: number, b: number) => void;
    readonly jsanalysisresult_get_search_path_from_y: (a: number, b: number) => void;
    readonly jsanalysisresult_get_search_path_to_x: (a: number, b: number) => void;
    readonly jsanalysisresult_get_search_path_to_y: (a: number, b: number) => void;
    readonly jsboardstate_get_game_over: (a: number, b: number) => void;
    readonly jsboardstate_get_is_in_check: (a: number) => number;
    readonly jsboardstate_get_last_move_json: (a: number, b: number) => void;
    readonly jsboardstate_get_pieces_json: (a: number, b: number) => void;
    readonly jsboardstate_get_side_to_move: (a: number, b: number) => void;
    readonly jscandidatemove_get_from_x: (a: number) => number;
    readonly jscandidatemove_get_from_y: (a: number) => number;
    readonly jscandidatemove_get_score: (a: number) => number;
    readonly jscandidatemove_get_to_x: (a: number) => number;
    readonly jscandidatemove_get_to_y: (a: number) => number;
    readonly jspieceinfo_get_name: (a: number, b: number) => void;
    readonly jspieceinfo_get_piece_type: (a: number, b: number) => void;
    readonly jspieceinfo_get_side: (a: number, b: number) => void;
    readonly jspieceinfo_get_x: (a: number) => number;
    readonly jspieceinfo_get_y: (a: number) => number;
    readonly jsposition_get_x: (a: number) => number;
    readonly jsposition_get_y: (a: number) => number;
    readonly jsposition_new: (a: number, b: number) => number;
    readonly xiangqiengine_analyze: (a: number, b: number) => number;
    readonly xiangqiengine_evaluate: (a: number) => number;
    readonly xiangqiengine_from_fen: (a: number, b: number, c: number) => void;
    readonly xiangqiengine_get_board_state: (a: number) => number;
    readonly xiangqiengine_get_legal_moves_at: (a: number, b: number, c: number, d: number) => void;
    readonly xiangqiengine_import_fen: (a: number, b: number, c: number) => number;
    readonly xiangqiengine_is_game_over: (a: number, b: number) => void;
    readonly xiangqiengine_is_in_check: (a: number) => number;
    readonly xiangqiengine_make_move: (a: number, b: number, c: number, d: number, e: number) => number;
    readonly xiangqiengine_new: () => number;
    readonly xiangqiengine_reset: (a: number) => void;
    readonly xiangqiengine_to_fen: (a: number, b: number) => void;
    readonly xiangqiengine_undo_move: (a: number) => number;
    readonly __wbindgen_add_to_stack_pointer: (a: number) => number;
    readonly __wbindgen_export: (a: number, b: number, c: number) => void;
    readonly __wbindgen_export2: (a: number, b: number) => number;
    readonly __wbindgen_export3: (a: number, b: number, c: number, d: number) => number;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;

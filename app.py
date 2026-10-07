import streamlit as st
from dataclasses import dataclass
from typing import Optional


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="온라인 장기",
    page_icon="♟️",
    layout="centered",
)

ROWS = 10
COLS = 9

RED = "한"
BLUE = "초"


# ============================================================
# 말 정의
# ============================================================

@dataclass
class Piece:
    side: str
    kind: str


# 화면에 표시할 문자
PIECE_SYMBOLS = {
    ("한", "궁"): "漢",
    ("한", "사"): "士",
    ("한", "차"): "車",
    ("한", "포"): "包",
    ("한", "마"): "馬",
    ("한", "상"): "象",
    ("한", "병"): "卒",

    ("초", "궁"): "楚",
    ("초", "사"): "士",
    ("초", "차"): "車",
    ("초", "포"): "包",
    ("초", "마"): "馬",
    ("초", "상"): "象",
    ("초", "병"): "卒",
}


# ============================================================
# 궁성
# ============================================================

def in_board(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS


def in_red_palace(r, c):
    return 0 <= r <= 2 and 3 <= c <= 5


def in_blue_palace(r, c):
    return 7 <= r <= 9 and 3 <= c <= 5


def in_palace(side, r, c):
    if side == RED:
        return in_red_palace(r, c)
    return in_blue_palace(r, c)


# 궁성의 대각선 연결
PALACE_DIAGONALS = [
    ((0, 3), (1, 4)),
    ((0, 5), (1, 4)),
    ((2, 3), (1, 4)),
    ((2, 5), (1, 4)),

    ((7, 3), (8, 4)),
    ((7, 5), (8, 4)),
    ((9, 3), (8, 4)),
    ((9, 5), (8, 4)),
]


def palace_diagonal_connected(r1, c1, r2, c2):
    return ((r1, c1), (r2, c2)) in PALACE_DIAGONALS or (
        (r2, c2), (r1, c1)
    ) in PALACE_DIAGONALS


# ============================================================
# 초기 장기판
# ============================================================

def create_initial_board():
    board = [[None for _ in range(COLS)] for _ in range(ROWS)]

    # 초 - 위쪽
    board[0][0] = Piece(BLUE, "차")
    board[0][1] = Piece(BLUE, "상")
    board[0][2] = Piece(BLUE, "마")
    board[0][4] = Piece(BLUE, "궁")
    board[0][6] = Piece(BLUE, "마")
    board[0][7] = Piece(BLUE, "상")
    board[0][8] = Piece(BLUE, "차")

    board[1][3] = Piece(BLUE, "사")
    board[1][5] = Piece(BLUE, "사")

    board[2][1] = Piece(BLUE, "포")
    board[2][7] = Piece(BLUE, "포")

    for c in [0, 2, 4, 6, 8]:
        board[3][c] = Piece(BLUE, "병")

    # 한 - 아래쪽
    board[9][0] = Piece(RED, "차")
    board[9][1] = Piece(RED, "상")
    board[9][2] = Piece(RED, "마")
    board[9][4] = Piece(RED, "궁")
    board[9][6] = Piece(RED, "마")
    board[9][7] = Piece(RED, "상")
    board[9][8] = Piece(RED, "차")

    board[8][3] = Piece(RED, "사")
    board[8][5] = Piece(RED, "사")

    board[7][1] = Piece(RED, "포")
    board[7][7] = Piece(RED, "포")

    for c in [0, 2, 4, 6, 8]:
        board[6][c] = Piece(RED, "병")

    return board


# ============================================================
# 이동 관련
# ============================================================

DIRECTIONS_4 = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1),
]


def path_clear(board, r1, c1, r2, c2):
    """
    두 칸 사이가 직선으로 연결되어 있고 중간에 말이 없는지 확인
    """
    dr = r2 - r1
    dc = c2 - c1

    if dr != 0 and dc != 0:
        return False

    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
    step_c = 0 if dc == 0 else (1 if dc > 0 else -1)

    r = r1 + step_r
    c = c1 + step_c

    while (r, c) != (r2, c2):
        if board[r][c] is not None:
            return False

        r += step_r
        c += step_c

    return True


def count_between(board, r1, c1, r2, c2):
    """
    두 위치 사이에 있는 말의 수
    """
    dr = r2 - r1
    dc = c2 - c1

    if dr != 0 and dc != 0:
        return -1

    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
    step_c = 0 if dc == 0 else (1 if dc > 0 else -1)

    count = 0

    r = r1 + step_r
    c = c1 + step_c

    while (r, c) != (r2, c2):
        if board[r][c] is not None:
            count += 1

        r += step_r
        c += step_c

    return count


# ============================================================
# 말별 이동
# ============================================================

def legal_piece_moves(board, r, c):
    """
    해당 말이 이동할 수 있는 기본적인 위치를 반환한다.
    """
    piece = board[r][c]

    if piece is None:
        return []

    side = piece.side
    kind = piece.kind

    moves = []

    # --------------------------------------------------------
    # 궁
    # --------------------------------------------------------
    if kind == "궁":
        for dr, dc in DIRECTIONS_4:
            nr = r + dr
            nc = c + dc

            if in_board(nr, nc) and in_palace(side, nr, nc):
                target = board[nr][nc]

                if target is None or target.side != side:
                    moves.append((nr, nc))

        # 궁성 대각선
        for nr, nc in palace_diagonal_targets(r, c):
            if in_palace(side, nr, nc):
                target = board[nr][nc]

                if target is None or target.side != side:
                    moves.append((nr, nc))

        return unique_moves(moves)

    # --------------------------------------------------------
    # 사
    # --------------------------------------------------------
    if kind == "사":
        for dr, dc in DIRECTIONS_4:
            nr = r + dr
            nc = c + dc

            if in_board(nr, nc) and in_palace(side, nr, nc):
                target = board[nr][nc]

                if target is None or target.side != side:
                    moves.append((nr, nc))

        for nr, nc in palace_diagonal_targets(r, c):
            if in_palace(side, nr, nc):
                target = board[nr][nc]

                if target is None or target.side != side:
                    moves.append((nr, nc))

        return unique_moves(moves)

    # --------------------------------------------------------
    # 차
    # --------------------------------------------------------
    if kind == "차":
        for dr, dc in DIRECTIONS_4:
            nr = r + dr
            nc = c + dc

            while in_board(nr, nc):
                target = board[nr][nc]

                if target is None:
                    moves.append((nr, nc))
                else:
                    if target.side != side:
                        moves.append((nr, nc))
                    break

                nr += dr
                nc += dc

        # 궁성 내부 대각선 이동
        for nr, nc in palace_diagonal_targets(r, c):
            if in_palace(side, nr, nc):
                target = board[nr][nc]

                if target is None or target.side != side:
                    moves.append((nr, nc))

        return unique_moves(moves)

    # --------------------------------------------------------
    # 포
    # --------------------------------------------------------
    if kind == "포":
        for dr, dc in DIRECTIONS_4:
            nr = r + dr
            nc = c + dc

            while in_board(nr, nc):
                if board[nr][nc] is None:
                    nr += dr
                    nc += dc
                    continue

                # 첫 번째 말을 포 받침으로 사용
                nr2 = nr + dr
                nc2 = nc + dc

                while in_board(nr2, nc2):
                    target = board[nr2][nc2]

                    if target is not None:
                        if target.kind != "포":
                            if target.side != side:
                                moves.append((nr2, nc2))
                        break

                    # 포는 궁성에서도 대각선은 별도 처리
                    nr2 += dr
                    nc2 += dc

                break

        # 궁성 대각선 포 이동
        for nr, nc in palace_diagonal_targets(r, c):
            # 대각선에서는 가운데 한 칸에 받침이 있어야 함
            mr = (r + nr) // 2
            mc = (c + nc) // 2

            if board[mr][mc] is None:
                continue

            if board[mr][mc].kind == "포":
                continue

            target = board[nr][nc]

            if target is None:
                moves.append((nr, nc))
            elif target.side != side and target.kind != "포":
                moves.append((nr, nc))

        return unique_moves(moves)

    # --------------------------------------------------------
    # 마
    # --------------------------------------------------------
    if kind == "마":
        horse_patterns = [
            (-2, -1, -1, 0),
            (-2, 1, -1, 0),
            (2, -1, 1, 0),
            (2, 1, 1, 0),

            (-1, -2, 0, -1),
            (1, -2, 0, -1),
            (-1, 2, 0, 1),
            (1, 2, 0, 1),
        ]

        for dr, dc, br, bc in horse_patterns:
            block_r = r + br
            block_c = c + bc
            nr = r + dr
            nc = c + dc

            if not in_board(block_r, block_c):
                continue

            if board[block_r][block_c] is not None:
                continue

            if not in_board(nr, nc):
                continue

            target = board[nr][nc]

            if target is None or target.side != side:
                moves.append((nr, nc))

        return moves

    # --------------------------------------------------------
    # 상
    # --------------------------------------------------------
    if kind == "상":
        elephant_patterns = [
            (-3, -2, -1, -1, -2, -1),
            (-3, 2, -1, 1, -2, 1),
            (3, -2, 1, -1, 2, -1),
            (3, 2, 1, 1, 2, 1),

            (-2, -3, -1, -1, -1, -2),
            (2, -3, 1, -1, 1, -2),
            (-2, 3, -1, 1, -1, 2),
            (2, 3, 1, 1, 1, 2),
        ]

        for dr, dc, br1, bc1, br2, bc2 in elephant_patterns:
            block1_r = r + br1
            block1_c = c + bc1

            block2_r = r + br2
            block2_c = c + bc2

            nr = r + dr
            nc = c + dc

            if not in_board(block1_r, block1_c):
                continue

            if not in_board(block2_r, block2_c):
                continue

            if board[block1_r][block1_c] is not None:
                continue

            if board[block2_r][block2_c] is not None:
                continue

            if not in_board(nr, nc):
                continue

            target = board[nr][nc]

            if target is None or target.side != side:
                moves.append((nr, nc))

        return moves

    # --------------------------------------------------------
    # 병
    # --------------------------------------------------------
    if kind == "병":
        # 초는 아래 방향으로 이동
        # 한은 위 방향으로 이동
        forward = 1 if side == BLUE else -1

        possible = [
            (r + forward, c),
            (r, c - 1),
            (r, c + 1),
        ]

        # 궁성 내부에서는 전진 대각선도 가능
        for nr, nc in palace_diagonal_targets(r, c):
            if nr - r == forward:
                possible.append((nr, nc))

        for nr, nc in possible:
            if not in_board(nr, nc):
                continue

            target = board[nr][nc]

            if target is None or target.side != side:
                moves.append((nr, nc))

        return unique_moves(moves)

    return []


def palace_diagonal_targets(r, c):
    result = []

    for a, b in PALACE_DIAGONALS:
        if (r, c) == a:
            result.append(b)
        elif (r, c) == b:
            result.append(a)

    return result


def unique_moves(moves):
    return list(dict.fromkeys(moves))


# ============================================================
# 장군 / 장기 체크
# ============================================================

def find_general(board, side):
    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]

            if piece and piece.side == side and piece.kind == "궁":
                return (r, c)

    return None


def is_attacked(board, r, c, by_side):
    """
    특정 칸이 상대방 말에 의해 공격받는지 확인
    """

    for rr in range(ROWS):
        for cc in range(COLS):
            piece = board[rr][cc]

            if piece is None or piece.side != by_side:
                continue

            # 궁의 위치 자체는 기본 이동으로 판단
            moves = legal_piece_moves(board, rr, cc)

            if (r, c) in moves:
                return True

    return False


def is_in_check(board, side):
    general = find_general(board, side)

    if general is None:
        return True

    opponent = RED if side == BLUE else BLUE

    return is_attacked(
        board,
        general[0],
        general[1],
        opponent,
    )


def copy_board(board):
    new_board = []

    for row in board:
        new_row = []

        for piece in row:
            if piece is None:
                new_row.append(None)
            else:
                new_row.append(
                    Piece(piece.side, piece.kind)
                )

        new_board.append(new_row)

    return new_board


def apply_move(board, source, target):
    new_board = copy_board(board)

    sr, sc = source
    tr, tc = target

    new_board[tr][tc] = new_board[sr][sc]
    new_board[sr][sc] = None

    return new_board


def legal_moves(board, r, c):
    piece = board[r][c]

    if piece is None:
        return []

    candidate_moves = legal_piece_moves(board, r, c)

    result = []

    for nr, nc in candidate_moves:
        new_board = apply_move(
            board,
            (r, c),
            (nr, nc),
        )

        # 자신의 궁이 잡히거나 체크 상태가 되는 수 방지
        if find_general(new_board, piece.side) is None:
            continue

        if not is_in_check(new_board, piece.side):
            result.append((nr, nc))

    return result


def has_any_legal_move(board, side):
    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]

            if piece and piece.side == side:
                if legal_moves(board, r, c):
                    return True

    return False


# ============================================================
# 게임 상태
# ============================================================

def reset_game():
    st.session_state.board = create_initial_board()
    st.session_state.turn = BLUE
    st.session_state.selected = None
    st.session_state.message = "초부터 시작합니다."
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.move_count = 0


if "board" not in st.session_state:
    reset_game()


# ============================================================
# 말 표시
# ============================================================

def piece_html(piece):
    if piece is None:
        return ""

    symbol = PIECE_SYMBOLS[(piece.side, piece.kind)]

    color = "#b30000" if piece.side == RED else "#174ea6"

    return f"""
    <span style="
        color:{color};
        font-size:26px;
        font-weight:800;
        font-family:serif;
    ">
        {symbol}
    </span>
    """


# ============================================================
# UI
# ============================================================

st.title("🏯 장기 게임")

st.caption(
    "Streamlit으로 만든 2인용 한국 장기 게임 · "
    "초 vs 한"
)


# 사이드바
with st.sidebar:
    st.header("게임 정보")

    if st.button("🔄 새 게임", use_container_width=True):
        reset_game()
        st.rerun()

    st.divider()

    st.markdown(
        """
        ### 사용 방법

        1. 자신의 말을 클릭합니다.
        2. 이동할 칸을 클릭합니다.
        3. 상대 말을 잡을 수도 있습니다.
        4. 이동이 끝나면 자동으로 턴이 넘어갑니다.

        ### 진영

        🔵 초  
        🔴 한
        """
    )


# 상태 표시
turn_color = "🔵" if st.session_state.turn == BLUE else "🔴"

st.subheader(
    f"{turn_color} {st.session_state.turn} 차례"
)

if st.session_state.message:
    st.info(st.session_state.message)


# 체크 상태
if not st.session_state.game_over:
    if is_in_check(st.session_state.board, st.session_state.turn):
        st.warning(
            f"⚠️ {st.session_state.turn}의 궁이 장군입니다!"
        )


# ============================================================
# 보드 출력
# ============================================================

board = st.session_state.board
selected = st.session_state.selected

selected_moves = []

if selected:
    sr, sc = selected
    selected_moves = legal_moves(board, sr, sc)


# CSS
st.markdown(
    """
    <style>
    .board-row {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .cell {
        width: 48px;
        height: 48px;
        border: 1px solid #805b2a;
        background-color: #e8bd70;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .cell-dark {
        background-color: #ddb064;
    }

    .board-title {
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }

    @media (max-width: 600px) {
        .cell {
            width: 35px;
            height: 35px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Streamlit 버튼으로 각 칸 구현
for r in range(ROWS):

    cols = st.columns(COLS, gap="small")

    for c in range(COLS):

        piece = board[r][c]

        is_selected = selected == (r, c)
        is_move_target = (r, c) in selected_moves

        label = " "

        if piece:
            symbol = PIECE_SYMBOLS[(piece.side, piece.kind)]

            if piece.side == RED:
                label = f"🔴 {symbol}"
            else:
                label = f"🔵 {symbol}"

        elif is_move_target:
            label = "●"

        else:
            label = "·"

        # 선택된 칸 강조
        if is_selected:
            label = f"🟡 {label}"

        with cols[c]:
            clicked = st.button(
                label,
                key=f"cell_{r}_{c}",
                use_container_width=True,
            )

            if clicked and not st.session_state.game_over:

                # 이미 말을 선택한 상태
                if selected:

                    sr, sc = selected
                    selected_piece = board[sr][sc]

                    # 같은 말을 다시 클릭
                    if (r, c) == (sr, sc):
                        st.session_state.selected = None
                        st.session_state.message = "선택을 취소했습니다."
                        st.rerun()

                    # 이동 가능한 칸을 클릭
                    elif (r, c) in selected_moves:

                        target_piece = board[r][c]

                        captured_text = ""

                        if target_piece:
                            captured_text = (
                                f" {target_piece.kind}을(를) 잡았습니다."
                            )

                        # 실제 이동
                        st.session_state.board = apply_move(
                            board,
                            (sr, sc),
                            (r, c),
                        )

                        st.session_state.selected = None
                        st.session_state.move_count += 1

                        # 상대편으로 턴 변경
                        next_side = (
                            RED
                            if st.session_state.turn == BLUE
                            else BLUE
                        )

                        st.session_state.turn = next_side

                        st.session_state.message = (
                            f"{selected_piece.kind} 이동 완료."
                            f"{captured_text}"
                        )

                        # 상대 궁이 잡혔는지 확인
                        if find_general(
                            st.session_state.board,
                            next_side,
                        ) is None:

                            winner = (
                                RED
                                if next_side == BLUE
                                else BLUE
                            )

                            st.session_state.game_over = True
                            st.session_state.winner = winner
                            st.session_state.message = (
                                f"🏆 {winner} 승리!"
                            )

                        # 상대가 체크인데 움직일 수 없는 경우
                        elif (
                            is_in_check(
                                st.session_state.board,
                                next_side,
                            )
                            and not has_any_legal_move(
                                st.session_state.board,
                                next_side,
                            )
                        ):

                            winner = (
                                RED
                                if next_side == BLUE
                                else BLUE
                            )

                            st.session_state.game_over = True
                            st.session_state.winner = winner

                            st.session_state.message = (
                                f"🏆 {winner} 승리! "
                                f"{next_side}이(가) 더 이상 "
                                f"합법적인 수를 둘 수 없습니다."
                            )

                        st.rerun()

                    # 자신의 다른 말을 클릭
                    elif (
                        board[r][c] is not None
                        and board[r][c].side
                        == st.session_state.turn
                    ):

                        st.session_state.selected = (r, c)

                        st.session_state.message = (
                            f"{board[r][c].kind}을(를) 선택했습니다."
                        )

                        st.rerun()

                    else:
                        st.session_state.message = (
                            "그 위치로는 이동할 수 없습니다."
                        )
                        st.rerun()

                # 아직 말을 선택하지 않음
                else:

                    if (
                        piece is not None
                        and piece.side
                        == st.session_state.turn
                    ):

                        moves = legal_moves(
                            board,
                            r,
                            c,
                        )

                        if moves:
                            st.session_state.selected = (
                                r,
                                c,
                            )

                            st.session_state.message = (
                                f"{piece.kind}을(를) 선택했습니다. "
                                f"노란색 표시가 이동 위치입니다."
                            )
                        else:
                            st.session_state.message = (
                                "현재 이동할 수 없는 말입니다."
                            )

                        st.rerun()


# ============================================================
# 게임 종료
# ============================================================

if st.session_state.game_over:

    st.success(
        f"🏆 게임 종료 — "
        f"{st.session_state.winner} 승리!"
    )

    if st.button(
        "새 게임 시작",
        use_container_width=True,
    ):
        reset_game()
        st.rerun()


# ============================================================
# 하단 정보
# ============================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "현재 차례",
        st.session_state.turn,
    )

with col2:
    st.metric(
        "수",
        st.session_state.move_count,
    )

with col3:
    status = (
        "종료"
        if st.session_state.game_over
        else "진행 중"
    )

    st.metric(
        "게임 상태",
        status,
    )


st.caption(
    "※ 현재 버전은 웹에서 두 사람이 번갈아 플레이하는 로컬 대국 버전입니다."
)

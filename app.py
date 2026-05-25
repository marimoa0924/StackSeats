from __future__ import annotations

import datetime

import plotly.graph_objects as go
import streamlit as st

from seat_config import (
    ALL_GRADES,
    CHARGE_AMOUNT,
    INITIAL_CASH,
    ROW_ORDER,
    ROW_TO_GRADE,
    SEAT_LAYOUT,
    SEAT_TO_GRADE,
)
from ticket_manager import TicketManager

# ─── Page config (must be first Streamlit call) ───────────────────────────────

st.set_page_config(
    page_title="StackSeats 취켓팅",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Dark cinema background */
    .stApp { background-color: #0d0d18; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 12px 16px;
        border: 1px solid #2d2d4e;
    }

    /* Tab bar */
    .stTabs [data-baseweb="tab-list"] {
        background: #12122a;
        border-radius: 8px;
        gap: 4px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        color: #aaa;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: #1e1e4a !important;
        color: #fff !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background: #0a0a1a; }

    /* Containers */
    [data-testid="stVerticalBlock"] > div > [data-testid="stVerticalBlock"] {
        border-radius: 10px;
    }

    /* Stack boxes */
    .stack-box {
        display: inline-block;
        padding: 5px 10px;
        margin: 2px;
        border-radius: 5px;
        font-size: 13px;
        font-weight: bold;
        font-family: monospace;
        color: #111;
    }
    .stack-top {
        border: 2px solid #fff;
        box-shadow: 0 0 8px rgba(255,255,255,0.4);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Session State ─────────────────────────────────────────────────────────────


def _init() -> None:
    defaults: dict = {
        "manager": TicketManager(),
        "cash": INITIAL_CASH,
        "log": [],             # list[str] newest-first
        "my_tickets": [],      # list[dict] (claimed tickets)
        "selected_seat": None, # dict {seat_id, grade} | None
        "last_popped": None,   # dict | None  (shown after successful POP)
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init()
manager: TicketManager = st.session_state["manager"]


def _log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state["log"].insert(0, f"[{ts}]  {msg}")
    if len(st.session_state["log"]) > 50:
        st.session_state["log"] = st.session_state["log"][:50]


# ─── Plotly Seat Map ──────────────────────────────────────────────────────────


def _create_seat_figure(
    cancelled_seats: set[str],
    selected_seat: dict | None,
    clickable: bool = True,
) -> go.Figure:
    xs: list[float] = []
    ys: list[float] = []
    colors: list[str] = []
    border_colors: list[str] = []
    border_widths: list[int] = []
    texts: list[str] = []
    customdata: list[list[str]] = []
    hover_texts: list[str] = []

    for row_idx, row in enumerate(ROW_ORDER):
        grade = ROW_TO_GRADE[row]
        width = SEAT_LAYOUT[grade]["rows"][row]
        grade_color = SEAT_LAYOUT[grade]["color"]
        y = -float(row_idx)

        for col in range(1, width + 1):
            seat_id = f"{row}-{col}"
            x = (col - 1) - (width - 1) / 2.0

            xs.append(x)
            ys.append(y)
            texts.append(str(col))
            customdata.append([seat_id, grade])

            if selected_seat and seat_id == selected_seat["seat_id"]:
                colors.append("#FFFFFF")
                border_colors.append("#FF8C00")
                border_widths.append(3)
                hover_texts.append(f"✅ 선택됨: {seat_id} ({grade}석)")
            elif seat_id in cancelled_seats:
                colors.append("#FF4444")
                border_colors.append("#FF0000")
                border_widths.append(2)
                hover_texts.append(f"🔴 취소표 있음: {seat_id} ({grade}석)")
            else:
                colors.append(grade_color)
                border_colors.append("#333")
                border_widths.append(1)
                hover_texts.append(f"{seat_id}  ({grade}석)<br>클릭하여 선택")

    fig = go.Figure()

    # Stage
    fig.add_shape(
        type="rect",
        x0=-7.5, x1=7.5, y0=0.7, y1=1.2,
        fillcolor="#2d2d2d",
        line_color="#555",
    )
    fig.add_annotation(
        x=0, y=0.95,
        text="🎭  S T A G E",
        showarrow=False,
        font=dict(color="#aaa", size=13, family="monospace"),
    )

    # Row labels (left side)
    for row_idx, row in enumerate(ROW_ORDER):
        grade = ROW_TO_GRADE[row]
        color = SEAT_LAYOUT[grade]["color"]
        fig.add_annotation(
            x=-7.2,
            y=-float(row_idx),
            text=f"<b>{row}</b>",
            showarrow=False,
            font=dict(color=color, size=12),
            xanchor="right",
        )

    # Seats
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(
                symbol="square",
                size=22,
                color=colors,
                line=dict(color=border_colors, width=border_widths),
            ),
            text=texts,
            textposition="middle center",
            textfont=dict(size=9, color="#111"),
            customdata=customdata,
            hovertext=hover_texts,
            hoverinfo="text",
            showlegend=False,
        )
    )

    # Grade legend annotations
    legend_items = [
        ("VIP", SEAT_LAYOUT["VIP"]["color"], -7.5, -6.2),
        ("S",   SEAT_LAYOUT["S"]["color"],   -5.5, -6.2),
        ("A",   SEAT_LAYOUT["A"]["color"],   -3.5, -6.2),
        ("취소표", "#FF4444",                -1.2, -6.2),
        ("선택됨", "#FFFFFF",                 1.3, -6.2),
    ]
    for label, color, lx, ly in legend_items:
        fig.add_shape(
            type="rect",
            x0=lx - 0.3, x1=lx + 0.3,
            y0=ly - 0.25, y1=ly + 0.25,
            fillcolor=color,
            line_color="#555",
        )
        fig.add_annotation(
            x=lx + 0.6, y=ly,
            text=label,
            showarrow=False,
            font=dict(color="#ccc", size=11),
            xanchor="left",
        )

    fig.update_layout(
        paper_bgcolor="#0d0d18",
        plot_bgcolor="#0d0d18",
        font_color="#eee",
        showlegend=False,
        margin=dict(l=40, r=20, t=20, b=60),
        height=400,
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[-8, 8],
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[-6.7, 1.5],
        ),
        clickmode="event+select" if clickable else "none",
        dragmode=False,
    )
    return fig


# ─── Stack Visualization (HTML) ───────────────────────────────────────────────


def _render_stack_html(grade: str, items: list[dict]) -> None:
    color = SEAT_LAYOUT[grade]["color"]
    price = SEAT_LAYOUT[grade]["price"]

    header_color = {"VIP": "#FFD700", "S": "#4FC3F7", "A": "#A5D6A7"}[grade]
    st.sidebar.markdown(
        f"<span style='color:{header_color}; font-weight:700; font-size:15px;'>"
        f"■ {grade}석</span>"
        f"<span style='color:#888; font-size:12px;'>  {len(items)}개 &nbsp;|&nbsp; {price:,}C</span>",
        unsafe_allow_html=True,
    )

    if not items:
        st.sidebar.markdown(
            "<p style='color:#555; font-size:12px; margin:2px 0 6px 8px;'>"
            "스택 비어있음 (Empty)</p>",
            unsafe_allow_html=True,
        )
        return

    boxes = ""
    for i, seat in enumerate(reversed(items)):  # reversed: TOP first (visually top)
        is_top = i == 0
        extra_style = (
            "border:2px solid #fff; box-shadow:0 0 6px rgba(255,255,255,.35);"
            if is_top
            else "border:1px solid #555; opacity:.8;"
        )
        top_label = " ←TOP" if is_top else ""
        boxes += (
            f"<div style='background:{color}; color:#111; padding:4px 8px; "
            f"margin:2px 0; border-radius:4px; font-family:monospace; "
            f"font-size:12px; font-weight:{'700' if is_top else '400'}; {extra_style}'>"
            f"{seat['seat_id']}{top_label}</div>"
        )

    st.sidebar.markdown(
        f"<div style='margin:2px 0 2px 4px;'>"
        f"<div style='color:#777;font-size:10px;margin-bottom:2px;'>▲ TOP (최신 취소표)</div>"
        f"{boxes}"
        f"<div style='color:#777;font-size:10px;margin-top:2px;'>▼ BOTTOM</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ─── Sidebar ──────────────────────────────────────────────────────────────────


def _render_sidebar() -> None:
    st.sidebar.markdown(
        "<h2 style='color:#fff; margin-bottom:0;'>🎭 StackSeats</h2>"
        "<p style='color:#888; font-size:12px; margin-top:2px;'>"
        "Stack 자료구조 기반 취켓팅 플랫폼</p>",
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    # ── Cash ──────────────────────────────────────────────────────────────────
    cash = st.session_state["cash"]
    st.sidebar.markdown(
        f"<div style='background:#1a1a2e; border-radius:10px; padding:12px 16px; "
        f"border:1px solid #2d2d4e;'>"
        f"<p style='color:#aaa; font-size:12px; margin:0;'>💰 내 캐시 잔액</p>"
        f"<p style='color:#FFD700; font-size:26px; font-weight:700; margin:4px 0 0;'>"
        f"{cash:,} <span style='font-size:16px;'>C</span></p></div>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button(f"충전 +{CHARGE_AMOUNT:,}C", use_container_width=True):
        st.session_state["cash"] += CHARGE_AMOUNT
        _log(f"[충전] +{CHARGE_AMOUNT:,}C → 잔액 {st.session_state['cash']:,}C")
        st.rerun()

    st.sidebar.divider()

    # ── Stack state ───────────────────────────────────────────────────────────
    st.sidebar.markdown(
        "<p style='color:#4FC3F7; font-weight:700; font-size:14px; margin-bottom:4px;'>"
        "📚 등급별 Stack 현황</p>"
        "<p style='color:#666; font-size:11px; margin-top:0;'>"
        "취소표는 LIFO 스택으로 관리됩니다</p>",
        unsafe_allow_html=True,
    )
    for grade in ALL_GRADES:
        _render_stack_html(grade, manager.get_stack_state(grade))
        st.sidebar.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.sidebar.divider()

    # ── My tickets ────────────────────────────────────────────────────────────
    my_tickets: list[dict] = st.session_state["my_tickets"]
    st.sidebar.markdown(
        f"<p style='color:#A5D6A7; font-weight:700; font-size:14px; margin-bottom:4px;'>"
        f"🎟 나의 취소표 ({len(my_tickets)})</p>",
        unsafe_allow_html=True,
    )
    if not my_tickets:
        st.sidebar.caption("아직 받은 취소표가 없습니다.")
    else:
        for ticket in reversed(my_tickets):
            with st.sidebar.expander(f"🎫  {ticket['seat_id']}  ({ticket['grade']}석)"):
                st.markdown(
                    f"**등급**: {ticket['grade']}  \n"
                    f"**판매자 연락처 끝자리**: `****-{ticket['seller_phone']}`  \n"
                    f"**결제 금액**: {ticket['price']:,} C"
                )
                if ticket.get("receipt_bytes"):
                    st.download_button(
                        label="📄 예매내역서 다운로드",
                        data=ticket["receipt_bytes"],
                        file_name=ticket.get("receipt_filename", "receipt"),
                        key=f"dl_{ticket['seat_id']}_{id(ticket)}",
                        use_container_width=True,
                    )

    st.sidebar.divider()

    # ── Log ───────────────────────────────────────────────────────────────────
    st.sidebar.markdown(
        "<p style='color:#888; font-size:12px; font-weight:600;'>📋 작업 로그</p>",
        unsafe_allow_html=True,
    )
    log: list[str] = st.session_state["log"]
    if not log:
        st.sidebar.caption("(로그 없음)")
    for entry in log[:8]:
        st.sidebar.markdown(
            f"<p style='font-family:monospace; font-size:11px; color:#666; margin:1px 0;'>"
            f"{entry}</p>",
            unsafe_allow_html=True,
        )


# ─── Stack Explainer ──────────────────────────────────────────────────────────


def _render_explainer() -> None:
    with st.expander("📚 Stack 자료구조란?  ← 클릭하여 개념 보기", expanded=False):
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown(
                """
**Stack(스택)** 은 **LIFO — Last In, First Out** 원칙을 따르는 선형 자료구조입니다.

| 연산 | 설명 | 시간복잡도 | 이 시스템에서 |
|------|------|-----------|-------------|
| **PUSH** | TOP에 데이터 삽입 | O(1) | 취소표 등록 |
| **POP**  | TOP에서 데이터 제거 | O(1) | 취소표 받기 |
| **PEEK** | TOP 데이터 조회 (제거 없음) | O(1) | 다음 배정 미리보기 |

> 📌 **가장 최근에 등록된 취소표**가 가장 먼저 배정됩니다.
                """
            )
        with col_r:
            st.markdown(
                """
```
취소표 등록 시 → PUSH
┌──────────────────────┐
│  [B-3]  ← TOP (최신) │
│  [A-5]               │
│  [A-1]  ← BOTTOM     │
└──────────────────────┘

취소표 받기 시 → POP
┌──────────────────────┐
│  [A-5]  ← 이제 TOP   │
│  [A-1]  ← BOTTOM     │
└──────────────────────┘
  ↓
 [B-3] 이 배정됨
```
                """
            )


# ─── Tab 1: 등록 (PUSH) ───────────────────────────────────────────────────────


def _render_register_tab() -> None:
    st.markdown(
        "<h3 style='color:#FFD700;'>⚡ PUSH — 취소표 등록</h3>"
        "<p style='color:#888;'>취소할 좌석을 클릭하여 선택한 뒤 정보를 입력하세요.</p>",
        unsafe_allow_html=True,
    )

    cancelled_seats = manager.get_all_cancelled_seats()
    sel: dict | None = st.session_state["selected_seat"]

    fig = _create_seat_figure(cancelled_seats, sel, clickable=True)
    event = st.plotly_chart(
        fig,
        on_select="rerun",
        selection_mode="points",
        key="seat_map_register",
        use_container_width=True,
    )

    # Handle click → update selected_seat
    if event and event.selection and event.selection.points:
        pt = event.selection.points[0]
        cd = pt.get("customdata") or []
        if len(cd) >= 2:
            clicked_id, clicked_grade = cd[0], cd[1]
            if clicked_id in cancelled_seats:
                st.warning(f"⚠️ {clicked_id} 는 이미 취소표가 등록된 좌석입니다.")
            elif not sel or sel["seat_id"] != clicked_id:
                st.session_state["selected_seat"] = {
                    "seat_id": clicked_id,
                    "grade": clicked_grade,
                }
                st.rerun()

    # ── Registration form ──────────────────────────────────────────────────────
    st.markdown("---")
    if not sel:
        st.info("👆 위 좌석표에서 취소할 좌석을 클릭하세요.")
        return

    price = SEAT_LAYOUT[sel["grade"]]["price"]
    grade_color = SEAT_LAYOUT[sel["grade"]]["color"]

    st.markdown(
        f"<div style='background:#1a1a2e; border-radius:10px; padding:16px; "
        f"border-left:4px solid {grade_color};'>"
        f"<p style='margin:0; font-size:18px; font-weight:700; color:#fff;'>"
        f"선택된 좌석: <span style='color:{grade_color};'>{sel['seat_id']}</span>"
        f"  ({sel['grade']}석)</p>"
        f"<p style='margin:4px 0 0; color:#aaa; font-size:14px;'>"
        f"판매 캐시: {price:,} C</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    with st.form("register_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input(
                "📱 판매자 연락처 뒤 4자리",
                max_chars=4,
                placeholder="예: 1234",
            )
        with col2:
            receipt = st.file_uploader(
                "📄 예매내역서 첨부 (이미지/PDF)",
                type=["png", "jpg", "jpeg", "pdf"],
            )

        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            submitted = st.form_submit_button(
                "⚡  PUSH → 스택에 취소표 등록",
                use_container_width=True,
                type="primary",
            )
        with col_btn2:
            cancelled_btn = st.form_submit_button(
                "✕ 선택 취소",
                use_container_width=True,
            )

    if cancelled_btn:
        st.session_state["selected_seat"] = None
        st.rerun()

    if submitted:
        if not phone or len(phone) != 4 or not phone.isdigit():
            st.error("연락처 뒤 4자리를 숫자로 정확히 입력하세요.")
            return
        if receipt is None:
            st.error("예매내역서를 첨부해 주세요.")
            return

        seat_data = {
            "seat_id": sel["seat_id"],
            "grade": sel["grade"],
            "seller_phone": phone,
            "receipt_bytes": receipt.read(),
            "receipt_filename": receipt.name,
            "price": price,
            "registered_at": datetime.datetime.now().strftime("%H:%M:%S"),
        }
        ok = manager.push(seat_data)
        if ok:
            _log(
                f"[PUSH] {sel['seat_id']} ({sel['grade']}석) 등록 → "
                f"스택 크기: {manager.get_size(sel['grade'])}"
            )
            st.session_state["selected_seat"] = None
            st.toast(
                f"✅ {sel['seat_id']} 취소표가 스택에 등록되었습니다! (PUSH)",
                icon="📚",
            )
            st.rerun()
        else:
            st.error("이미 등록된 좌석입니다. 다른 좌석을 선택하세요.")


# ─── Tab 2: 받기 (POP) ───────────────────────────────────────────────────────


def _render_claim_tab() -> None:
    st.markdown(
        "<h3 style='color:#4FC3F7;'>🚀 POP — 취소표 받기</h3>"
        "<p style='color:#888;'>원하는 등급을 선택하고 취소표를 받아보세요.</p>",
        unsafe_allow_html=True,
    )

    # Grade cards (PEEK preview)
    cols = st.columns(3)
    for i, grade in enumerate(ALL_GRADES):
        top_ticket = manager.peek(grade)
        cnt = manager.get_size(grade)
        price = SEAT_LAYOUT[grade]["price"]
        gc = SEAT_LAYOUT[grade]["color"]
        with cols[i]:
            if top_ticket:
                st.markdown(
                    f"<div style='background:#1a1a2e; border-radius:10px; padding:14px; "
                    f"border-top:3px solid {gc}; text-align:center;'>"
                    f"<p style='color:{gc}; font-size:16px; font-weight:700; margin:0;'>"
                    f"{grade}석</p>"
                    f"<p style='color:#fff; font-size:22px; font-weight:700; margin:4px 0;'>"
                    f"{top_ticket['seat_id']}</p>"
                    f"<p style='color:#aaa; font-size:12px; margin:0;'>"
                    f"PEEK ← 다음 배정 좌석</p>"
                    f"<p style='color:#888; font-size:11px; margin:4px 0 0;'>"
                    f"대기 {cnt}개  |  {price:,}C</p></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:#111; border-radius:10px; padding:14px; "
                    f"border-top:3px solid #333; text-align:center; opacity:.5;'>"
                    f"<p style='color:#888; font-size:16px; font-weight:700; margin:0;'>"
                    f"{grade}석</p>"
                    f"<p style='color:#555; font-size:18px; margin:4px 0;'>— 없음 —</p>"
                    f"<p style='color:#555; font-size:12px; margin:0;'>스택 비어있음</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # Show result from previous POP (persisted across rerun)
    last_popped: dict | None = st.session_state.get("last_popped")
    if last_popped:
        lc = SEAT_LAYOUT[last_popped["grade"]]["color"]
        st.markdown(
            f"<div style='background:#0a2a0a; border-radius:10px; padding:20px; "
            f"border:1px solid #2a5a2a;'>"
            f"<p style='color:#A5D6A7; font-size:18px; font-weight:700; margin:0;'>"
            f"🎉 취소표 배정 성공!</p>"
            f"<p style='color:#fff; font-size:22px; font-weight:700; margin:8px 0 4px;'>"
            f"<span style='color:{lc};'>{last_popped['seat_id']}</span>"
            f"  ({last_popped['grade']}석)</p>"
            f"<p style='color:#aaa; font-size:14px; margin:4px 0;'>"
            f"📞 판매자 연락처 끝자리: "
            f"<code>****-{last_popped['seller_phone']}</code></p>"
            f"<p style='color:#888; font-size:12px; margin:4px 0 0;'>"
            f"결제 금액: {last_popped['price']:,} C  |  "
            f"등록 시각: {last_popped.get('registered_at', '-')}</p></div>",
            unsafe_allow_html=True,
        )
        if last_popped.get("receipt_bytes"):
            st.download_button(
                label="📄 예매내역서 다운로드",
                data=last_popped["receipt_bytes"],
                file_name=last_popped.get("receipt_filename", "receipt"),
                key="last_popped_dl",
            )
        if st.button("✕ 닫기", key="close_popped"):
            st.session_state["last_popped"] = None
            st.rerun()
        st.markdown("---")

    # Claim form
    with st.form("claim_form"):
        grade = st.radio(
            "원하는 등급 선택",
            options=ALL_GRADES,
            horizontal=True,
            key="pop_grade_radio",
        )
        price = SEAT_LAYOUT[grade]["price"]
        cash = st.session_state["cash"]

        st.markdown(
            f"결제 금액: **{price:,} C**  &nbsp;|&nbsp;  내 잔액: **{cash:,} C**"
            + ("  &nbsp;🔴 잔액 부족" if cash < price else "  &nbsp;✅"),
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button(
            f"🚀  POP ← {grade}석 취소표 받기",
            use_container_width=True,
            type="primary",
            disabled=(cash < price),
        )

    if submitted:
        if manager.is_empty(grade):
            st.warning(f"⚠️ {grade}석 취소표가 없습니다.")
            return

        ticket = manager.pop(grade)
        if ticket:
            st.session_state["cash"] -= price
            ticket["price"] = price
            st.session_state["my_tickets"].append(ticket)
            st.session_state["last_popped"] = ticket
            _log(
                f"[POP] {ticket['seat_id']} ({grade}석) "
                f"→ -{price:,}C  |  잔액: {st.session_state['cash']:,}C"
            )
            st.rerun()


# ─── Tab 3: 현황판 ────────────────────────────────────────────────────────────


def _render_status_tab() -> None:
    st.markdown(
        "<h3 style='color:#A5D6A7;'>📊 실시간 현황판</h3>",
        unsafe_allow_html=True,
    )

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 취소표", f"{manager.total_count()} 개")
    col2.metric("VIP석", f"{manager.get_size('VIP')} 개")
    col3.metric("S석", f"{manager.get_size('S')} 개")
    col4.metric("A석", f"{manager.get_size('A')} 개")

    st.markdown("---")

    # Read-only seat map
    st.markdown(
        "<p style='color:#888; font-size:13px; margin-bottom:4px;'>"
        "🔴 빨간 좌석 = 취소표 있음 (매칭 가능)</p>",
        unsafe_allow_html=True,
    )
    cancelled = manager.get_all_cancelled_seats()
    fig = _create_seat_figure(cancelled, selected_seat=None, clickable=False)
    st.plotly_chart(fig, use_container_width=True, key="seat_map_status")

    st.markdown("---")

    # Per-grade horizontal stack visualization
    st.markdown(
        "<p style='color:#4FC3F7; font-weight:700;'>등급별 Stack 시각화</p>"
        "<p style='color:#666; font-size:12px; margin-top:-8px;'>"
        "왼쪽 = BOTTOM (오래된 순)  /  오른쪽 = TOP (최신 → 다음 배정)</p>",
        unsafe_allow_html=True,
    )

    for grade in ALL_GRADES:
        items = manager.get_stack_state(grade)
        gc = SEAT_LAYOUT[grade]["color"]

        with st.container():
            st.markdown(
                f"<span style='color:{gc}; font-weight:700;'>■ {grade}석</span>"
                f"  <span style='color:#666; font-size:12px;'>"
                f"({len(items)}개 대기중)</span>",
                unsafe_allow_html=True,
            )

            if not items:
                st.markdown(
                    "<span style='color:#444; font-style:italic; font-size:13px;'>"
                    "스택 비어있음</span>",
                    unsafe_allow_html=True,
                )
            else:
                boxes = ""
                for i, seat in enumerate(items):  # index 0=BOTTOM, -1=TOP
                    is_top = i == len(items) - 1
                    bg = "#FF4444" if is_top else gc
                    text_color = "#fff" if is_top else "#111"
                    border = "border:2px solid #fff; box-shadow:0 0 6px rgba(255,255,255,.3);" if is_top else "border:1px solid #333;"
                    label = f"{seat['seat_id']} ← TOP" if is_top else seat["seat_id"]
                    boxes += (
                        f"<span style='background:{bg}; color:{text_color}; "
                        f"padding:5px 10px; margin:2px; border-radius:5px; "
                        f"font-family:monospace; font-size:13px; "
                        f"font-weight:{'700' if is_top else '400'}; {border} "
                        f"display:inline-block;'>{label}</span>"
                    )

                st.markdown(
                    f"<div style='margin:4px 0 8px;'>"
                    f"<span style='color:#555; font-size:11px;'>BOTTOM → </span>"
                    f"{boxes}"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    _render_sidebar()

    st.markdown(
        "<h1 style='color:#fff; margin-bottom:0;'>🎫 StackSeats 취켓팅 시스템</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#888; font-size:15px; margin-top:4px;'>"
        "Stack 자료구조 기반 실시간 취소표 매칭 플랫폼 — "
        "PUSH로 등록, POP으로 배정, PEEK으로 미리보기</p>",
        unsafe_allow_html=True,
    )

    _render_explainer()
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(
        ["⚡ 취소표 등록 (PUSH)", "🚀 취소표 받기 (POP)", "📊 현황판 (STATUS)"]
    )
    with tab1:
        _render_register_tab()
    with tab2:
        _render_claim_tab()
    with tab3:
        _render_status_tab()


if __name__ == "__main__":
    main()

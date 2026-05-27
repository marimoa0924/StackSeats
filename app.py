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
)
from ticket_manager import TicketManager

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="StackSeats 취켓팅",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px; padding: 6px; border-radius: 10px;
        background: rgba(255,255,255,0.04);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; font-weight: 600; font-size: 15px;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255,215,0,0.15) !important;
        color: #FFD700 !important;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 14px 18px;
    }

    /* Step badge */
    .step-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 28px; height: 28px; border-radius: 50%;
        background: #FFD700; color: #000;
        font-weight: 800; font-size: 14px; margin-right: 8px;
        flex-shrink: 0;
    }
    .step-row {
        display: flex; align-items: center;
        padding: 10px 14px;
        background: rgba(255,215,0,0.07);
        border-left: 3px solid #FFD700;
        border-radius: 0 8px 8px 0;
        margin-bottom: 14px;
        font-size: 15px; font-weight: 600; color: #FFD700;
    }

    /* Stack box animations */
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: none; } }
    .stack-item { animation: fadeIn 0.25s ease; }

    /* Info box */
    .how-to-card {
        background: rgba(79,195,247,0.08);
        border: 1px solid rgba(79,195,247,0.2);
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 8px;
    }

    /* Divider spacing */
    hr { margin: 18px 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Session State ─────────────────────────────────────────────────────────────


def _init() -> None:
    defaults: dict = {
        "manager": TicketManager(),
        "cash": INITIAL_CASH,
        "log": [],
        "my_tickets": [],
        "selected_seat": None,   # {"seat_id": str, "grade": str} | None
        "last_popped": None,     # dict | None
        "register_msg": None,    # {"type": "error"|"warning", "text": str} | None
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
    seat_numbers: list[str] = []
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
            seat_numbers.append(str(col))
            customdata.append([seat_id, grade])

            if selected_seat and seat_id == selected_seat["seat_id"]:
                colors.append("#FFFFFF")
                border_colors.append("#FFD700")
                border_widths.append(3)
                hover_texts.append(f"✅ 선택됨: {seat_id} ({grade}석)")
            elif seat_id in cancelled_seats:
                colors.append("#FF4444")
                border_colors.append("#FF0000")
                border_widths.append(2)
                hover_texts.append(f"🔴 취소표 있음: {seat_id} ({grade}석)<br>다른 좌석을 선택하세요")
            else:
                colors.append(grade_color)
                border_colors.append("#2a2a3a")
                border_widths.append(1)
                action = "클릭하여 선택" if clickable else ""
                hover_texts.append(f"<b>{seat_id}</b>  ({grade}석)  {SEAT_LAYOUT[grade]['price']:,}C<br>{action}")

    fig = go.Figure()

    # Stage
    fig.add_shape(
        type="rect",
        x0=-7.2, x1=7.2, y0=0.65, y1=1.15,
        fillcolor="#1e1e2e",
        line_color="#555",
        line_width=1,
    )
    fig.add_annotation(
        x=0, y=0.9,
        text="🎭  S T A G E",
        showarrow=False,
        font=dict(color="#888", size=13, family="monospace"),
    )

    # Row labels (left)
    for row_idx, row in enumerate(ROW_ORDER):
        grade = ROW_TO_GRADE[row]
        fig.add_annotation(
            x=-7.0,
            y=-float(row_idx),
            text=f"<b>{row}</b>",
            showarrow=False,
            font=dict(color=SEAT_LAYOUT[grade]["color"], size=12),
            xanchor="right",
        )

    # Grade zone labels (right)
    zone_items = [
        ("VIP 구역", -0.5, "VIP"),
        ("S 구역",  -2.5, "S"),
        ("A 구역",  -4.5, "A"),
    ]
    for label, ly, grade in zone_items:
        gc = SEAT_LAYOUT[grade]["color"]
        fig.add_shape(
            type="rect",
            x0=7.3, x1=10.2,
            y0=ly - 0.9, y1=ly + 0.9,
            fillcolor=f"rgba({int(gc[1:3],16)},{int(gc[3:5],16)},{int(gc[5:7],16)},0.08)",
            line_color=gc,
            line_width=1,
        )
        fig.add_annotation(
            x=8.75, y=ly,
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(color=gc, size=11),
            xanchor="center",
        )

    # Seats scatter
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(
                symbol="square",
                size=24,
                color=colors,
                line=dict(color=border_colors, width=border_widths),
            ),
            text=seat_numbers,
            textposition="middle center",
            textfont=dict(size=9, color="#111"),
            customdata=customdata,
            hovertext=hover_texts,
            hoverinfo="text",
            showlegend=False,
        )
    )

    # Bottom legend
    legend_items: list[tuple] = [
        ("VIP", SEAT_LAYOUT["VIP"]["color"]),
        ("S",   SEAT_LAYOUT["S"]["color"]),
        ("A",   SEAT_LAYOUT["A"]["color"]),
        ("취소표 있음", "#FF4444"),
    ]
    if clickable:
        legend_items.append(("선택됨", "#FFFFFF"))

    lx_start = -6.5
    for i, (label, color) in enumerate(legend_items):
        lx = lx_start + i * 2.7
        fig.add_shape(
            type="rect",
            x0=lx - 0.25, x1=lx + 0.25,
            y0=-6.5 - 0.22, y1=-6.5 + 0.22,
            fillcolor=color,
            line_color="#555",
            line_width=1,
        )
        fig.add_annotation(
            x=lx + 0.45, y=-6.5,
            text=label,
            showarrow=False,
            font=dict(color="#bbb", size=11),
            xanchor="left",
        )

    fig.update_layout(
        paper_bgcolor="#0d0d18",
        plot_bgcolor="#0d0d18",
        font_color="#eee",
        showlegend=False,
        margin=dict(l=30, r=10, t=10, b=30),
        height=420,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-8, 10.5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-7.2, 1.5]),
        clickmode="event+select" if clickable else "none",
        dragmode=False,
    )
    return fig


# ─── Stack Sidebar Visualization ──────────────────────────────────────────────


def _render_stack_sidebar(grade: str, items: list[dict]) -> None:
    gc = SEAT_LAYOUT[grade]["color"]
    price = SEAT_LAYOUT[grade]["price"]
    cnt = len(items)

    st.sidebar.markdown(
        f"<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;'>"
        f"<span style='color:{gc}; font-weight:700; font-size:14px;'>■ {grade}석</span>"
        f"<span style='color:#666; font-size:12px;'>{cnt}개 &nbsp;·&nbsp; {price:,}C</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not items:
        st.sidebar.markdown(
            "<div style='color:#444; font-size:12px; padding:4px 8px 8px; "
            "font-style:italic;'>비어있음 (Empty)</div>",
            unsafe_allow_html=True,
        )
        return

    html = (
        "<div style='font-size:10px; color:#666; margin-bottom:3px;'>"
        "▲ TOP — 다음 배정될 취소표</div>"
    )
    for i, seat in enumerate(reversed(items)):
        is_top = i == 0
        style = (
            f"background:{gc}; color:#111; border:2px solid #fff; "
            "box-shadow:0 0 6px rgba(255,255,255,.25); font-weight:700;"
            if is_top
            else f"background:{gc}cc; color:#111; border:1px solid #444; opacity:.75;"
        )
        top_tag = " <small style='font-size:9px;'>TOP</small>" if is_top else ""
        html += (
            f"<div class='stack-item' style='padding:4px 8px; margin:2px 0; border-radius:4px; "
            f"font-family:monospace; font-size:12px; {style}'>"
            f"{seat['seat_id']}{top_tag}</div>"
        )
    html += "<div style='font-size:10px; color:#666; margin-top:3px;'>▼ BOTTOM</div>"

    st.sidebar.markdown(html, unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────


def _render_sidebar() -> None:
    st.sidebar.markdown(
        "<h2 style='margin-bottom:2px; color:#fff;'>🎭 StackSeats</h2>"
        "<p style='color:#666; font-size:12px; margin:0 0 12px;'>"
        "Stack 자료구조 기반 취켓팅 시스템</p>",
        unsafe_allow_html=True,
    )

    # ── Cash ──────────────────────────────────────────────────────────────────
    cash = st.session_state["cash"]
    st.sidebar.markdown(
        f"<div style='background:rgba(255,215,0,0.08); border:1px solid rgba(255,215,0,0.2); "
        f"border-radius:10px; padding:12px 16px; margin-bottom:8px;'>"
        f"<p style='color:#aaa; font-size:11px; margin:0;'>💰 내 캐시 잔액</p>"
        f"<p style='color:#FFD700; font-size:28px; font-weight:800; margin:4px 0 0; line-height:1;'>"
        f"{cash:,}<span style='font-size:16px; font-weight:400;'> C</span></p></div>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button(f"⚡ 충전  +{CHARGE_AMOUNT:,}C", use_container_width=True):
        st.session_state["cash"] += CHARGE_AMOUNT
        _log(f"[충전] +{CHARGE_AMOUNT:,}C → 잔액 {st.session_state['cash']:,}C")
        st.rerun()

    st.sidebar.divider()

    # ── Stack visualization ────────────────────────────────────────────────────
    st.sidebar.markdown(
        "<p style='color:#4FC3F7; font-weight:700; font-size:13px; margin-bottom:6px;'>"
        "📚 Stack 실시간 현황</p>"
        "<p style='color:#555; font-size:11px; margin:-4px 0 8px;'>"
        "LIFO: 최근 등록 취소표가 먼저 배정됩니다</p>",
        unsafe_allow_html=True,
    )
    for grade in ALL_GRADES:
        _render_stack_sidebar(grade, manager.get_stack_state(grade))
        st.sidebar.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.sidebar.divider()

    # ── My tickets ────────────────────────────────────────────────────────────
    my_tickets: list[dict] = st.session_state["my_tickets"]
    cnt = len(my_tickets)
    st.sidebar.markdown(
        f"<p style='color:#A5D6A7; font-weight:700; font-size:13px; margin-bottom:6px;'>"
        f"🎟 나의 취소표 ({cnt}장)</p>",
        unsafe_allow_html=True,
    )
    if not my_tickets:
        st.sidebar.markdown(
            "<p style='color:#444; font-size:12px; font-style:italic;'>"
            "아직 받은 취소표가 없습니다.</p>",
            unsafe_allow_html=True,
        )
    else:
        for idx, ticket in enumerate(reversed(my_tickets)):
            with st.sidebar.expander(f"🎫 {ticket['seat_id']}  ({ticket['grade']}석)"):
                st.markdown(
                    f"**등급**: {ticket['grade']}석  \n"
                    f"**판매자 연락처 끝**: `****-{ticket['seller_phone']}`  \n"
                    f"**결제**: {ticket['price']:,} C  \n"
                    f"**등록 시각**: {ticket.get('registered_at', '-')}"
                )
                if ticket.get("receipt_bytes"):
                    st.download_button(
                        "📄 예매내역서",
                        data=ticket["receipt_bytes"],
                        file_name=ticket.get("receipt_filename", "receipt"),
                        key=f"sb_dl_{idx}_{ticket['seat_id']}",
                        use_container_width=True,
                    )
                else:
                    st.caption("영수증 미첨부")

    st.sidebar.divider()

    # ── Log ───────────────────────────────────────────────────────────────────
    with st.sidebar.expander("📋 작업 로그", expanded=False):
        log: list[str] = st.session_state["log"]
        if not log:
            st.caption("(로그 없음)")
        for entry in log[:12]:
            st.markdown(
                f"<p style='font-family:monospace; font-size:10px; color:#666; margin:2px 0;'>"
                f"{entry}</p>",
                unsafe_allow_html=True,
            )


# ─── Stack Explainer ──────────────────────────────────────────────────────────


def _render_explainer() -> None:
    with st.expander("📚 Stack 자료구조란?  (클릭해서 펼치기)", expanded=False):
        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.markdown(
                """
**Stack(스택)** 은 **LIFO — Last In, First Out** 원칙의 선형 자료구조입니다.

| 연산 | 설명 | 시간복잡도 | 이 시스템에서 |
|------|------|:---------:|-------------|
| **PUSH** | TOP에 데이터 삽입 | O(1) | 취소표 등록 |
| **POP**  | TOP에서 데이터 제거 | O(1) | 취소표 받기 |
| **PEEK** | TOP 조회 (제거 없음) | O(1) | 다음 배정 미리보기 |

> **📌 가장 최근에 등록된 취소표**가 가장 먼저 배정됩니다.
> 등급별(VIP/S/A)로 독립된 스택을 사용하여 O(1) 매칭을 보장합니다.
                """
            )
        with col_r:
            st.markdown(
                """
```
취소표 등록 → PUSH
┌─────────────────┐
│ [B-3] ← TOP(최신)│
│ [A-5]            │
│ [A-1] ← BOTTOM  │
└─────────────────┘

취소표 받기 → POP
[B-3] 배정됨 ↓

┌─────────────────┐
│ [A-5] ← 새 TOP  │
│ [A-1] ← BOTTOM  │
└─────────────────┘
```
                """
            )


# ─── Tab 1: 취소표 등록 (PUSH) ────────────────────────────────────────────────


def _render_register_tab() -> None:
    cancelled_seats = manager.get_all_cancelled_seats()
    sel: dict | None = st.session_state["selected_seat"]

    # ── Step 1: Seat map ──────────────────────────────────────────────────────
    st.markdown(
        "<div class='step-row'><span class='step-badge'>1</span>"
        "좌석표에서 취소할 좌석을 클릭하세요</div>",
        unsafe_allow_html=True,
    )

    fig = _create_seat_figure(cancelled_seats, sel, clickable=True)
    event = st.plotly_chart(
        fig,
        on_select="rerun",
        selection_mode="points",
        key="seat_map_register",
        use_container_width=True,
    )

    # Handle seat click
    if event and event.selection and event.selection.points:
        pt = event.selection.points[0]
        cd = pt.get("customdata") or []
        if len(cd) >= 2:
            clicked_id, clicked_grade = cd[0], cd[1]
            if clicked_id in cancelled_seats:
                # Show warning once via session state, not inline (avoids repetition on reruns)
                if st.session_state.get("register_msg", {}).get("seat_id") != clicked_id:
                    st.session_state["register_msg"] = {
                        "type": "warning",
                        "text": f"**{clicked_id}** 는 이미 취소표가 등록된 좌석입니다. 다른 좌석을 클릭하세요.",
                        "seat_id": clicked_id,
                    }
                    st.rerun()
            elif not sel or sel["seat_id"] != clicked_id:
                st.session_state["selected_seat"] = {"seat_id": clicked_id, "grade": clicked_grade}
                st.session_state["register_msg"] = None
                st.rerun()

    # Show one-shot message from previous click
    msg = st.session_state.get("register_msg")
    if msg and msg.get("type") == "warning":
        st.warning(msg["text"])

    # ── Step 2: Registration form ─────────────────────────────────────────────
    st.markdown(
        "<div class='step-row'><span class='step-badge'>2</span>"
        "선택된 좌석 정보를 확인하고 연락처와 예매내역서를 입력하세요</div>",
        unsafe_allow_html=True,
    )

    if not sel:
        st.markdown(
            "<div class='how-to-card'>"
            "<p style='margin:0; color:#888;'>👆 위 좌석표에서 취소할 좌석을 클릭하면 여기에 정보가 표시됩니다.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    price = SEAT_LAYOUT[sel["grade"]]["price"]
    gc = SEAT_LAYOUT[sel["grade"]]["color"]

    # Selected seat summary
    with st.container(border=True):
        col_seat, col_grade, col_price, col_cancel = st.columns([2, 1, 1, 1])
        with col_seat:
            st.markdown(
                f"<p style='margin:0; font-size:13px; color:#aaa;'>선택된 좌석</p>"
                f"<p style='margin:0; font-size:22px; font-weight:800; color:{gc};'>{sel['seat_id']}</p>",
                unsafe_allow_html=True,
            )
        with col_grade:
            st.markdown(
                f"<p style='margin:0; font-size:13px; color:#aaa;'>등급</p>"
                f"<p style='margin:0; font-size:18px; font-weight:700; color:#fff;'>{sel['grade']}석</p>",
                unsafe_allow_html=True,
            )
        with col_price:
            st.markdown(
                f"<p style='margin:0; font-size:13px; color:#aaa;'>판매 가격</p>"
                f"<p style='margin:0; font-size:18px; font-weight:700; color:#FFD700;'>{price:,} C</p>",
                unsafe_allow_html=True,
            )
        with col_cancel:
            st.markdown("<p style='margin:0; font-size:13px; color:transparent;'>.</p>", unsafe_allow_html=True)
            if st.button("✕ 다른 좌석", use_container_width=True, key="deselect_btn"):
                st.session_state["selected_seat"] = None
                st.session_state["register_msg"] = None
                st.rerun()

    # Form — clear_on_submit=False so errors don't wipe inputs
    # Seat-specific widget keys ensure fresh inputs on seat change
    seat_key = sel["seat_id"].replace("-", "_")
    with st.form("register_form", clear_on_submit=False):
        col_ph, col_rc = st.columns(2)
        with col_ph:
            phone = st.text_input(
                "📱 판매자 연락처 뒤 4자리  *(필수)*",
                max_chars=4,
                placeholder="예: 1234",
                key=f"phone_{seat_key}",
                help="구매자에게 연락처 끝 4자리가 공개됩니다.",
            )
        with col_rc:
            receipt = st.file_uploader(
                "📄 예매내역서  *(선택)*",
                type=["png", "jpg", "jpeg", "pdf"],
                key=f"receipt_{seat_key}",
                help="첨부하지 않아도 등록 가능하지만, 신뢰도를 높이려면 첨부하세요.",
            )

        submitted = st.form_submit_button(
            f"⚡  PUSH → 스택에 취소표 등록  ({price:,}C 판매)",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        if not phone or len(phone) != 4 or not phone.isdigit():
            st.error("📱 연락처 뒤 4자리를 숫자로 입력해 주세요. (예: 1234)")
            return

        seat_data = {
            "seat_id": sel["seat_id"],
            "grade": sel["grade"],
            "seller_phone": phone,
            "receipt_bytes": receipt.read() if receipt else None,
            "receipt_filename": receipt.name if receipt else None,
            "price": price,
            "registered_at": datetime.datetime.now().strftime("%H:%M:%S"),
        }
        ok = manager.push(seat_data)
        if ok:
            _log(f"[PUSH] {sel['seat_id']} ({sel['grade']}석) — 스택 크기: {manager.get_size(sel['grade'])}")
            st.session_state["selected_seat"] = None
            st.session_state["register_msg"] = None
            st.toast(f"✅ {sel['seat_id']} 취소표가 스택에 PUSH되었습니다!", icon="📚")
            st.rerun()
        else:
            st.error("이미 등록된 좌석입니다.")


# ─── Tab 2: 취소표 받기 (POP) ─────────────────────────────────────────────────


def _render_claim_tab() -> None:
    # ── PEEK preview cards ────────────────────────────────────────────────────
    st.markdown(
        "<p style='color:#aaa; font-size:13px; margin-bottom:8px;'>"
        "📌 각 등급별로 다음에 배정될 취소표를 미리 확인합니다 (PEEK 연산)</p>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for i, grade in enumerate(ALL_GRADES):
        top = manager.peek(grade)
        cnt = manager.get_size(grade)
        price = SEAT_LAYOUT[grade]["price"]
        gc = SEAT_LAYOUT[grade]["color"]

        with cols[i]:
            if top:
                st.markdown(
                    f"<div style='background:rgba({int(gc[1:3],16)},{int(gc[3:5],16)},{int(gc[5:7],16)},0.1); "
                    f"border:1px solid {gc}44; border-top:3px solid {gc}; "
                    f"border-radius:10px; padding:16px; text-align:center;'>"
                    f"<p style='color:{gc}; font-size:13px; font-weight:700; margin:0;'>{grade}석</p>"
                    f"<p style='color:#fff; font-size:26px; font-weight:800; margin:6px 0 4px; "
                    f"font-family:monospace;'>{top['seat_id']}</p>"
                    f"<p style='color:#888; font-size:11px; margin:0;'>"
                    f"PEEK · 다음 배정  |  {cnt}개 대기</p>"
                    f"<p style='color:{gc}; font-size:14px; font-weight:600; margin:6px 0 0;'>"
                    f"{price:,} C</p></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:rgba(255,255,255,0.02); border:1px solid #333; "
                    f"border-top:3px solid #333; border-radius:10px; padding:16px; text-align:center; opacity:.5;'>"
                    f"<p style='color:#666; font-size:13px; font-weight:700; margin:0;'>{grade}석</p>"
                    f"<p style='color:#444; font-size:20px; margin:6px 0 4px;'>— 없음 —</p>"
                    f"<p style='color:#444; font-size:11px; margin:0;'>스택 비어있음 (Empty)</p>"
                    f"<p style='color:#444; font-size:14px; margin:6px 0 0;'>{price:,} C</p></div>",
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── Show last POP result ───────────────────────────────────────────────────
    last_popped: dict | None = st.session_state.get("last_popped")
    if last_popped:
        lc = SEAT_LAYOUT[last_popped["grade"]]["color"]
        with st.container(border=True):
            st.markdown(
                f"<p style='color:#A5D6A7; font-size:17px; font-weight:700; margin:0 0 8px;'>"
                f"🎉 취소표 배정 완료!</p>",
                unsafe_allow_html=True,
            )
            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.markdown(
                    f"**좌석**: <span style='color:{lc}; font-size:20px; font-weight:800;"
                    f"font-family:monospace;'>{last_popped['seat_id']}</span>"
                    f" ({last_popped['grade']}석)",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"📞 **판매자 연락처 끝 4자리**: `****-{last_popped['seller_phone']}`  \n"
                    f"💳 **결제 금액**: {last_popped['price']:,} C  \n"
                    f"🕐 **등록 시각**: {last_popped.get('registered_at', '-')}"
                )
            with col_b:
                st.markdown(
                    "<p style='color:#888; font-size:12px;'>판매자에게 연락하여 좌석을 양도받으세요.</p>"
                )
                if last_popped.get("receipt_bytes"):
                    st.download_button(
                        "📄 예매내역서 다운로드",
                        data=last_popped["receipt_bytes"],
                        file_name=last_popped.get("receipt_filename", "receipt"),
                        key="claim_receipt_dl",
                        use_container_width=True,
                        type="primary",
                    )
                else:
                    st.info("예매내역서 미첨부")
                if st.button("✅ 확인했어요", key="dismiss_popped", use_container_width=True):
                    st.session_state["last_popped"] = None
                    st.rerun()
        st.divider()

    # ── Grade selection (OUTSIDE form for live price updates) ─────────────────
    st.markdown(
        "<div class='step-row'><span class='step-badge'>1</span>"
        "원하는 등급을 선택하세요</div>",
        unsafe_allow_html=True,
    )

    grade = st.radio(
        "등급 선택",
        options=ALL_GRADES,
        horizontal=True,
        key="claim_grade",
        label_visibility="collapsed",
        format_func=lambda g: f"{g}석  ({SEAT_LAYOUT[g]['price']:,}C)",
    )

    price = SEAT_LAYOUT[grade]["price"]
    cash = st.session_state["cash"]
    cnt = manager.get_size(grade)
    can_pop = cash >= price and cnt > 0

    # Live info strip
    col1, col2, col3 = st.columns(3)
    col1.metric("결제 금액", f"{price:,} C")
    col2.metric("내 잔액", f"{cash:,} C", delta=f"→ {cash - price:,} C" if can_pop else None)
    col3.metric("대기 취소표", f"{cnt}개")

    if cash < price:
        st.warning(f"캐시가 부족합니다. 사이드바에서 충전하세요. (필요: {price:,}C, 보유: {cash:,}C)")
    elif cnt == 0:
        st.info(f"{grade}석 취소표가 없습니다. 잠시 후 다시 확인해 보세요.")

    # ── POP form ─────────────────────────────────────────────────────────────
    st.markdown(
        "<div class='step-row'><span class='step-badge'>2</span>"
        "취소표를 받으세요</div>",
        unsafe_allow_html=True,
    )

    with st.form("claim_form"):
        st.markdown(
            f"<p style='color:#aaa; font-size:13px; margin:0 0 12px;'>"
            f"버튼을 누르면 스택에서 <b>POP</b>하여 {grade}석 취소표를 배정받습니다.<br>"
            f"<span style='color:#FFD700;'>{price:,}C</span>가 즉시 차감됩니다.</p>",
            unsafe_allow_html=True,
        )
        submitted = st.form_submit_button(
            f"🎯  POP ← {grade}석 취소표 받기  ({price:,}C)",
            use_container_width=True,
            type="primary",
            disabled=not can_pop,
        )

    if submitted:
        # Re-read grade from session state (grade radio is outside form)
        grade = st.session_state.get("claim_grade", "VIP")
        price = SEAT_LAYOUT[grade]["price"]
        cash = st.session_state["cash"]

        if manager.is_empty(grade):
            st.warning(f"{grade}석 취소표가 없습니다.")
        elif cash < price:
            st.error("잔액이 부족합니다.")
        else:
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
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 취소표", f"{manager.total_count()} 개")
    col2.metric("VIP석", f"{manager.get_size('VIP')} 개")
    col3.metric("S석", f"{manager.get_size('S')} 개")
    col4.metric("A석", f"{manager.get_size('A')} 개")

    st.divider()

    # Read-only seat map
    st.markdown(
        "<p style='color:#888; font-size:13px; margin-bottom:6px;'>"
        "🔴 빨간 좌석 = 취소표 있음 (매칭 가능)  ·  클릭 비활성화 (읽기 전용)</p>",
        unsafe_allow_html=True,
    )
    cancelled = manager.get_all_cancelled_seats()
    fig = _create_seat_figure(cancelled, selected_seat=None, clickable=False)
    st.plotly_chart(fig, use_container_width=True, key="seat_map_status")

    st.divider()

    # Per-grade horizontal stack visualization
    st.markdown(
        "<p style='color:#4FC3F7; font-weight:700; font-size:15px; margin-bottom:2px;'>"
        "등급별 Stack 시각화</p>"
        "<p style='color:#666; font-size:12px; margin:0 0 12px;'>"
        "왼쪽 = BOTTOM (오래된 취소표)  →  오른쪽 = TOP (다음 배정될 취소표)</p>",
        unsafe_allow_html=True,
    )

    for grade in ALL_GRADES:
        items = manager.get_stack_state(grade)
        gc = SEAT_LAYOUT[grade]["color"]

        with st.container(border=True):
            header_col, cnt_col = st.columns([4, 1])
            with header_col:
                st.markdown(
                    f"<span style='color:{gc}; font-weight:700; font-size:15px;'>■ {grade}석</span>",
                    unsafe_allow_html=True,
                )
            with cnt_col:
                st.markdown(
                    f"<span style='color:#666; font-size:13px;'>{len(items)}개</span>",
                    unsafe_allow_html=True,
                )

            if not items:
                st.markdown(
                    "<span style='color:#444; font-style:italic; font-size:13px;'>"
                    "스택 비어있음 — 등록된 취소표 없음</span>",
                    unsafe_allow_html=True,
                )
            else:
                boxes = ""
                for i, seat in enumerate(items):
                    is_top = i == len(items) - 1
                    if is_top:
                        bg, tc = "#FF4444", "#fff"
                        border = "border:2px solid #fff; box-shadow:0 0 8px rgba(255,68,68,.5);"
                        label = f"{seat['seat_id']}&nbsp;←&nbsp;TOP"
                    else:
                        bg, tc = gc + "bb", "#111"
                        border = "border:1px solid #333;"
                        label = seat["seat_id"]
                    boxes += (
                        f"<span style='background:{bg}; color:{tc}; padding:6px 12px; "
                        f"margin:2px 3px; border-radius:6px; font-family:monospace; "
                        f"font-size:13px; font-weight:{'700' if is_top else '400'}; "
                        f"{border} display:inline-block; white-space:nowrap;'>{label}</span>"
                    )
                st.markdown(
                    f"<div style='overflow-x:auto; padding:4px 0 8px;'>"
                    f"<span style='color:#555; font-size:11px; vertical-align:middle;'>BOTTOM → </span>"
                    f"{boxes}"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    _render_sidebar()

    # Header
    st.markdown(
        "<h1 style='margin-bottom:2px;'>🎫 StackSeats 취켓팅 시스템</h1>"
        "<p style='color:#888; font-size:14px; margin:0 0 16px;'>"
        "Stack 자료구조 기반 실시간 취소표 매칭 플랫폼 "
        "— PUSH로 등록 · POP으로 배정 · PEEK으로 미리보기</p>",
        unsafe_allow_html=True,
    )

    _render_explainer()
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(
        ["📥 취소표 등록 (PUSH)", "🎯 취소표 받기 (POP)", "📊 현황판 (STATUS)"]
    )
    with tab1:
        _render_register_tab()
    with tab2:
        _render_claim_tab()
    with tab3:
        _render_status_tab()


if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
_api_key = os.getenv("GEMINI_API_KEY", "")
_gemini_ok = bool(_api_key and _api_key != "your_gemini_api_key_here")
if _gemini_ok:
    _genai_client = genai.Client(api_key=_api_key)

st.set_page_config(
    page_title="서울 부동산 거래현황 대시보드",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 데이터 로딩 ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    base = "data/"
    return {
        "monthly":      pd.read_csv(base + "monthly_transaction.csv", encoding="utf-8-sig"),
        "detailed":     pd.read_csv(base + "detailed_transaction.csv", encoding="utf-8-sig"),
        "building":     pd.read_csv(base + "building_type_analysis.csv", encoding="utf-8-sig"),
        "transaction":  pd.read_csv(base + "transaction_type_analysis.csv", encoding="utf-8-sig"),
        "regional":     pd.read_csv(base + "regional_monthly_summary.csv", encoding="utf-8-sig"),
        "price_index":  pd.read_csv(base + "price_index_timeseries.csv", encoding="utf-8-sig"),
        "division":     pd.read_csv(base + "division_analysis.csv", encoding="utf-8-sig"),
        "construction": pd.read_csv(base + "construction_year_analysis.csv", encoding="utf-8-sig"),
    }

data = load_data()

# ── 사이드바 필터 ────────────────────────────────────────────────
with st.sidebar:
    st.title("🏢 서울 부동산")
    st.subheader("필터 설정")

    all_months = sorted(data["monthly"]["거래년월"].unique())
    month_start, month_end = st.select_slider(
        "기간 선택",
        options=all_months,
        value=(all_months[0], all_months[-1])
    )

    all_regions = sorted(data["monthly"]["지역명"].unique())
    sel_regions = st.multiselect("지역 선택", all_regions, default=all_regions)

    all_building = sorted(data["monthly"]["건물유형"].unique())
    sel_building = st.multiselect("건물유형 선택", all_building, default=all_building)

    if not sel_regions:
        sel_regions = all_regions
    if not sel_building:
        sel_building = all_building

# ── 필터 적용 헬퍼 ───────────────────────────────────────────────
def filter_monthly(df):
    return df[
        df["거래년월"].between(month_start, month_end) &
        df["지역명"].isin(sel_regions) &
        df["건물유형"].isin(sel_building)
    ]

def filter_by_month(df):
    return df[df["거래년월"].between(month_start, month_end)]

def build_data_context():
    lines = [
        "# 서울 부동산 거래 데이터",
        f"분석 기간: {month_start} ~ {month_end}",
        f"선택 지역 ({len(sel_regions)}개): {', '.join(sorted(sel_regions)[:10])}{'...' if len(sel_regions) > 10 else ''}",
        f"건물유형: {', '.join(sel_building)}",
        "",
    ]

    df_m = filter_monthly(data["monthly"])
    if not df_m.empty:
        total_count  = int(df_m["거래건수"].sum())
        total_amount = df_m["거래액(억원)"].sum()
        avg_price    = df_m["평균가격(만원)"].mean()
        lines += [
            "## 전체 거래 요약",
            f"- 총 거래건수: {total_count:,}건",
            f"- 총 거래액: {total_amount:,.0f}억원",
            f"- 평균 거래가: {avg_price:,.0f}만원",
            "",
        ]

    df_reg = filter_by_month(data["regional"])
    if not sel_regions or set(sel_regions) != set(all_regions):
        df_reg = df_reg[df_reg["지역명"].isin(sel_regions)]
    if not df_reg.empty:
        reg_top = (
            df_reg.groupby("지역명")
            .agg({"거래건수": "sum", "거래액(억원)": "sum", "평균가격(만원)": "mean"})
            .nlargest(15, "거래건수")
            .reset_index()
        )
        lines.append("## 지역별 거래 현황 (상위 15)")
        for _, r in reg_top.iterrows():
            lines.append(f"- {r['지역명']}: {int(r['거래건수']):,}건, {r['거래액(억원)']:,.0f}억원, 평균 {r['평균가격(만원)']:,.0f}만원")
        lines.append("")

    df_bld = filter_by_month(data["building"])
    if not df_bld.empty:
        bld = df_bld.groupby("건물유형").agg({"거래건수": "sum", "평균거래가(만원)": "mean"}).reset_index()
        lines.append("## 건물유형별 거래")
        for _, r in bld.iterrows():
            lines.append(f"- {r['건물유형']}: {int(r['거래건수']):,}건, 평균 {r['평균거래가(만원)']:,.0f}만원")
        lines.append("")

    df_trx = filter_by_month(data["transaction"])
    if not df_trx.empty:
        trx = df_trx.groupby("거래유형")["거래건수"].sum().reset_index()
        lines.append("## 거래유형별 현황")
        for _, r in trx.iterrows():
            lines.append(f"- {r['거래유형']}: {int(r['거래건수']):,}건")
        lines.append("")

    df_div = filter_by_month(data["division"])
    if not df_div.empty:
        div = df_div.groupby("권역").agg({"거래건수": "sum", "거래액(억원)": "sum", "평균가격(만원)": "mean"}).reset_index()
        lines.append("## 권역별 현황")
        for _, r in div.iterrows():
            lines.append(f"- {r['권역']}: {int(r['거래건수']):,}건, {r['거래액(억원)']:,.0f}억원, 평균 {r['평균가격(만원)']:,.0f}만원")
        lines.append("")

    df_pi = filter_by_month(data["price_index"])
    if not df_pi.empty:
        latest = df_pi.sort_values("거래년월").iloc[-1]
        lines += [
            f"## 최신 가격지수 ({latest['거래년월']})",
            f"- 종합지수: {latest.get('종합지수', 'N/A')}",
            f"- 매매지수: {latest.get('매매지수', 'N/A')}",
            f"- 전세지수: {latest.get('전세지수', 'N/A')}",
            f"- 월세지수: {latest.get('월세지수', 'N/A')}",
            "",
        ]

    return "\n".join(lines)

# ── 탭 레이아웃 ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 개요", "🗺️ 지역별 분석", "🏗️ 건물/거래유형", "🧭 권역별 분석", "🔍 상세 거래조회", "🤖 AI 분석"
])

# ══════════════════════════════════════════════════════════════════
# 탭 1 : 개요
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.header("서울 부동산 거래현황 개요")

    df_m = filter_monthly(data["monthly"])
    df_pi = filter_by_month(data["price_index"])
    df_div = filter_by_month(data["division"])

    # KPI 카드
    total_count  = int(df_m["거래건수"].sum())
    total_amount = df_m["거래액(억원)"].sum()
    avg_price    = df_m["평균가격(만원)"].mean()

    monthly_cnt = df_m.groupby("거래년월")["거래건수"].sum().sort_index()
    if len(monthly_cnt) >= 2:
        mom_change = (monthly_cnt.iloc[-1] - monthly_cnt.iloc[-2]) / monthly_cnt.iloc[-2] * 100
    else:
        mom_change = 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 거래건수", f"{total_count:,}건")
    col2.metric("총 거래액", f"{total_amount:,.0f}억원")
    col3.metric("평균 거래가", f"{avg_price:,.0f}만원")
    col4.metric("전월 대비 거래건수", f"{mom_change:+.1f}%")

    st.divider()

    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.subheader("부동산 가격지수 추이")
        if not df_pi.empty:
            fig_pi = go.Figure()
            colors = {"종합지수": "#1f77b4", "매매지수": "#ff7f0e", "전세지수": "#2ca02c", "월세지수": "#d62728"}
            for col_name, color in colors.items():
                fig_pi.add_trace(go.Scatter(
                    x=df_pi["거래년월"], y=df_pi[col_name],
                    mode="lines+markers", name=col_name,
                    line=dict(color=color, width=2)
                ))
            fig_pi.update_layout(
                height=350, margin=dict(t=20, b=20),
                xaxis_title="년월", yaxis_title="지수",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig_pi, width="stretch")
        else:
            st.info("해당 기간의 가격지수 데이터가 없습니다.")

    with col_r:
        st.subheader("권역별 거래건수")
        if not df_div.empty:
            div_agg = df_div.groupby("권역")["거래건수"].sum().reset_index()
            fig_donut = px.pie(
                div_agg, values="거래건수", names="권역",
                hole=0.45, color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_donut.update_layout(height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig_donut, width="stretch")
        else:
            st.info("해당 기간의 권역 데이터가 없습니다.")

    st.subheader("월별 거래건수 추이")
    if not df_m.empty:
        monthly_trend = df_m.groupby("거래년월")["거래건수"].sum().reset_index()
        fig_bar = px.bar(
            monthly_trend, x="거래년월", y="거래건수",
            color_discrete_sequence=["#4C78A8"]
        )
        fig_bar.update_layout(height=280, margin=dict(t=20, b=20))
        st.plotly_chart(fig_bar, width="stretch")

# ══════════════════════════════════════════════════════════════════
# 탭 2 : 지역별 분석
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.header("지역별 부동산 거래 분석")

    df_reg = filter_by_month(data["regional"])
    if not sel_regions or set(sel_regions) != set(all_regions):
        df_reg = df_reg[df_reg["지역명"].isin(sel_regions)]

    col_l, col_r = st.columns([2, 3])

    with col_l:
        st.subheader("지역별 총 거래건수 (상위 10)")
        if not df_reg.empty:
            reg_agg = df_reg.groupby("지역명")["거래건수"].sum().nlargest(10).reset_index()
            fig_hbar = px.bar(
                reg_agg, x="거래건수", y="지역명",
                orientation="h",
                color="거래건수", color_continuous_scale="Blues"
            )
            fig_hbar.update_layout(height=400, margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_hbar, width="stretch")

    with col_r:
        st.subheader("지역별 월별 거래액 추이")
        if not df_reg.empty:
            top8 = df_reg.groupby("지역명")["거래건수"].sum().nlargest(8).index.tolist()
            df_top8 = df_reg[df_reg["지역명"].isin(top8)]
            fig_line = px.line(
                df_top8, x="거래년월", y="거래액(억원)", color="지역명",
                markers=True
            )
            fig_line.update_layout(
                height=400, margin=dict(t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig_line, width="stretch")

    st.subheader("지역 × 월별 평균가격 히트맵 (만원)")
    if not df_reg.empty:
        pivot = df_reg.pivot_table(
            index="지역명", columns="거래년월", values="평균가격(만원)", aggfunc="mean"
        )
        fig_heat = px.imshow(
            pivot, aspect="auto",
            color_continuous_scale="RdYlGn",
            labels=dict(color="평균가격(만원)")
        )
        fig_heat.update_layout(height=500, margin=dict(t=20, b=20))
        st.plotly_chart(fig_heat, width="stretch")

# ══════════════════════════════════════════════════════════════════
# 탭 3 : 건물/거래유형
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.header("건물유형 및 거래유형 분석")

    df_bld = filter_by_month(data["building"])
    df_trx = filter_by_month(data["transaction"])

    if not sel_building or set(sel_building) != set(all_building):
        df_bld = df_bld[df_bld["건물유형"].isin(sel_building)]

    st.subheader("건물유형별 분석")
    col1, col2 = st.columns(2)

    with col1:
        if not df_bld.empty:
            bld_agg = df_bld.groupby("건물유형")["거래건수"].sum().reset_index()
            fig_pie_b = px.pie(
                bld_agg, values="거래건수", names="건물유형",
                title="건물유형별 거래건수 비중",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie_b.update_layout(height=350)
            st.plotly_chart(fig_pie_b, width="stretch")

    with col2:
        if not df_bld.empty:
            fig_line_b = px.line(
                df_bld, x="거래년월", y="거래건수", color="건물유형",
                title="건물유형별 월별 거래건수 추이",
                markers=True
            )
            fig_line_b.update_layout(
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig_line_b, width="stretch")

    if not df_bld.empty:
        df_bld_copy = df_bld.copy()
        if df_bld_copy["가격상승률(%)"].dtype == object:
            df_bld_copy["가격상승률(%)"] = df_bld_copy["가격상승률(%)"].str.replace("%", "").astype(float)
        fig_box = px.box(
            df_bld_copy, x="건물유형", y="가격상승률(%)",
            title="건물유형별 가격상승률 분포 (%)",
            color="건물유형",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig_box.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_box, width="stretch")

    st.divider()
    st.subheader("거래유형별 분석")
    col3, col4 = st.columns(2)

    with col3:
        if not df_trx.empty:
            trx_agg = df_trx.groupby("거래유형")["거래건수"].sum().reset_index()
            fig_pie_t = px.pie(
                trx_agg, values="거래건수", names="거래유형",
                title="거래유형별 거래건수 비중",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie_t.update_layout(height=350)
            st.plotly_chart(fig_pie_t, width="stretch")

    with col4:
        if not df_trx.empty:
            df_trx_copy = df_trx.copy()
            if df_trx_copy["전월대비(%)"].dtype == object:
                df_trx_copy["전월대비(%)"] = df_trx_copy["전월대비(%)"].str.replace("%", "").astype(float)
            trx_avg_mom = df_trx_copy.groupby("거래유형")["전월대비(%)"].mean().reset_index()
            fig_bar_t = px.bar(
                trx_avg_mom, x="거래유형", y="전월대비(%)",
                title="거래유형별 평균 전월대비 변동률 (%)",
                color="전월대비(%)",
                color_continuous_scale="RdYlGn",
                text_auto=".1f"
            )
            fig_bar_t.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_bar_t, width="stretch")

# ══════════════════════════════════════════════════════════════════
# 탭 4 : 권역별 분석
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.header("서울 권역별 분석")

    df_div2 = filter_by_month(data["division"])

    st.subheader("권역별 월별 거래건수 추이")
    if not df_div2.empty:
        fig_div_line = px.line(
            df_div2, x="거래년월", y="거래건수", color="권역",
            markers=True,
            color_discrete_sequence=["#E45756", "#4C78A8", "#72B7B2", "#F58518"]
        )
        fig_div_line.update_layout(
            height=350, margin=dict(t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig_div_line, width="stretch")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("권역별 평균가격 (만원)")
        if not df_div2.empty:
            div_price = df_div2.groupby(["거래년월", "권역"])["평균가격(만원)"].mean().reset_index()
            fig_stacked = px.bar(
                div_price, x="거래년월", y="평균가격(만원)", color="권역",
                barmode="group",
                color_discrete_sequence=["#E45756", "#4C78A8", "#72B7B2", "#F58518"]
            )
            fig_stacked.update_layout(
                height=350, margin=dict(t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig_stacked, width="stretch")

    with col_r:
        st.subheader("권역별 재계약률 추이 (%)")
        if not df_div2.empty:
            df_div_copy = df_div2.copy()
            if df_div_copy["재계약률(%)"].dtype == object:
                df_div_copy["재계약률(%)"] = df_div_copy["재계약률(%)"].str.replace("%", "").astype(float)
            fig_renew = px.line(
                df_div_copy, x="거래년월", y="재계약률(%)", color="권역",
                markers=True,
                color_discrete_sequence=["#E45756", "#4C78A8", "#72B7B2", "#F58518"]
            )
            fig_renew.update_layout(
                height=350, margin=dict(t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig_renew, width="stretch")

    st.subheader("권역별 총 거래액 비교")
    if not df_div2.empty:
        div_amount = df_div2.groupby("권역")["거래액(억원)"].sum().reset_index()
        fig_div_bar = px.bar(
            div_amount, x="권역", y="거래액(억원)",
            color="권역", text_auto=".0f",
            color_discrete_sequence=["#E45756", "#4C78A8", "#72B7B2", "#F58518"]
        )
        fig_div_bar.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_div_bar, width="stretch")

# ══════════════════════════════════════════════════════════════════
# 탭 5 : 상세 거래조회
# ══════════════════════════════════════════════════════════════════
with tab5:
    st.header("상세 거래 데이터 조회")

    df_det = data["detailed"].copy()

    with st.expander("상세 필터", expanded=True):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            all_trx_types = sorted(df_det["거래유형"].unique())
            sel_trx = st.multiselect("거래유형", all_trx_types, default=all_trx_types, key="det_trx")
        with fc2:
            year_min, year_max = int(df_det["준공연도"].min()), int(df_det["준공연도"].max())
            sel_year = st.slider("준공연도 범위", year_min, year_max, (year_min, year_max))
        with fc3:
            price_min = int(df_det["거래금액(만원)"].min())
            price_max = int(df_det["거래금액(만원)"].max())
            sel_price = st.slider("거래금액 범위 (만원)", price_min, price_max, (price_min, price_max))

    mask = (
        df_det["지역명"].isin(sel_regions) &
        df_det["거래유형"].isin(sel_trx) &
        df_det["준공연도"].between(sel_year[0], sel_year[1]) &
        df_det["거래금액(만원)"].between(sel_price[0], sel_price[1])
    )
    df_filtered = df_det[mask]

    st.caption(f"조건에 맞는 거래: **{len(df_filtered):,}건** / 전체 {len(df_det):,}건")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("면적 vs 거래금액")
        if not df_filtered.empty:
            sample = df_filtered.sample(min(500, len(df_filtered)), random_state=42)
            fig_scatter = px.scatter(
                sample,
                x="면적(㎡)", y="거래금액(만원)",
                color="거래유형", opacity=0.6,
                hover_data=["지역명", "건물유형", "준공연도"]
            )
            fig_scatter.update_layout(height=380, margin=dict(t=20, b=20))
            st.plotly_chart(fig_scatter, width="stretch")
        else:
            st.info("조건에 맞는 데이터가 없습니다.")

    with col_r:
        st.subheader("준공연도별 평균 거래가격")
        if not df_filtered.empty:
            year_avg = df_filtered.groupby("준공연도")["거래금액(만원)"].mean().reset_index()
            fig_year = px.bar(
                year_avg, x="준공연도", y="거래금액(만원)",
                color="거래금액(만원)", color_continuous_scale="Blues"
            )
            fig_year.update_layout(height=380, margin=dict(t=20, b=20), showlegend=False)
            st.plotly_chart(fig_year, width="stretch")

    st.subheader("거래 데이터 테이블")
    display_cols = ["거래일자", "지역명", "지역상세", "건물유형", "거래유형",
                    "거래금액(만원)", "면적(㎡)", "층수", "준공연도", "거래중개"]
    st.dataframe(
        df_filtered[display_cols].sort_values("거래일자", ascending=False),
        width="stretch",
        height=350
    )

# ══════════════════════════════════════════════════════════════════
# 탭 6 : AI 분석
# ══════════════════════════════════════════════════════════════════
with tab6:
    st.header("AI 데이터 분석")
    st.caption("사이드바 필터에 맞는 데이터를 바탕으로 부동산 거래에 대해 자유롭게 질문하세요.")

    if not _gemini_ok:
        st.error("`.env` 파일에 `GEMINI_API_KEY`를 설정해 주세요. [API 키 발급](https://aistudio.google.com/app/apikey)")
        st.stop()

    # 세션 초기화
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # 상단 컨트롤
    ctrl_col, info_col = st.columns([1, 4])
    with ctrl_col:
        if st.button("대화 초기화", type="secondary", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    with info_col:
        st.info(f"현재 필터 → 기간: **{month_start} ~ {month_end}** | 지역: **{len(sel_regions)}개** | 건물유형: **{len(sel_building)}개**")

    # 빠른 질문 버튼 (대화가 없을 때만 표시)
    if not st.session_state.chat_messages:
        st.markdown("**빠른 질문 예시**")
        quick_qs = [
            "거래가 가장 많은 지역 Top 5는?",
            "아파트와 오피스텔 거래 비교",
            "최근 가격 트렌드는?",
            "매매 vs 전세 비율 분석",
            "가격이 가장 높은 지역은?",
            "권역별 거래 특징을 분석해줘",
        ]
        q_cols = st.columns(3)
        _clicked_q = None
        for i, q in enumerate(quick_qs):
            with q_cols[i % 3]:
                if st.button(q, key=f"quick_{i}", use_container_width=True):
                    _clicked_q = q
    else:
        _clicked_q = None

    # 채팅 기록 표시
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 입력 처리
    user_input = st.chat_input("데이터에 대해 질문하세요...")
    if _clicked_q:
        user_input = _clicked_q

    if user_input:
        # 유저 메시지 표시 & 저장
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_messages.append({"role": "user", "content": user_input})

        # AI 응답
        with st.chat_message("assistant"):
            with st.spinner("분석 중..."):
                try:
                    system_prompt = (
                        "당신은 서울 부동산 거래 데이터 분석 전문가입니다. "
                        "아래 제공된 데이터를 기반으로 사용자의 질문에 한국어로 명확하고 통찰력 있게 답변하세요. "
                        "수치를 인용할 때는 구체적인 숫자를 사용하고, 필요하면 비교나 해석도 포함하세요.\n\n"
                        + build_data_context()
                    )

                    # 이전 대화 히스토리 구성 (현재 질문 제외)
                    history = []
                    for m in st.session_state.chat_messages[:-1]:
                        role = "user" if m["role"] == "user" else "model"
                        history.append(genai_types.Content(role=role, parts=[genai_types.Part(text=m["content"])]))

                    response = _genai_client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=history + [genai_types.Content(role="user", parts=[genai_types.Part(text=user_input)])],
                        config=genai_types.GenerateContentConfig(system_instruction=system_prompt),
                    )
                    answer = response.text

                    st.markdown(answer)
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    err = f"오류 발생: {e}"
                    st.error(err)
                    st.session_state.chat_messages.append({"role": "assistant", "content": err})

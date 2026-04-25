import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# --- ページ設定 ---
st.set_page_config(page_title="Owner's Eye", layout="wide")
st.title("🏇 Owner's Eye")

# --- Google Analytics (GA4) の導入 ---
ga_tracking_id = "G-06K8TPML0W"
ga_code = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={ga_tracking_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{ga_tracking_id}');
</script>
"""
# 画面に見えない形でHTMLコードを埋め込む
components.html(ga_code, height=0, width=0)

# --- カスタムCSSの適用（ダイアログの縦幅を広げる） ---
st.markdown("""
<style>
/* ダイアログウィンドウ全体の最小高さを画面の80%に設定 */
div[data-testid="stDialog"] > div {
    min-height: 80vh;
}

/* マルチセレクト（種牡馬・厩舎の選択タグ一覧）の表示エリアの最大高さを大幅に広げる */
div[data-baseweb="select"] > div {
    max-height: 60vh !important;
}

/* === キャロットクラブ風の配色設定 === */
/* 見出し（タイトル、サブタイトル）をキャロットグリーンに */
h1, h2, h3 {
    color: #004d25 !important;
}

/* サマリーの数値（KPI）をキャロットオレンジに */
div[data-testid="stMetricValue"] {
    color: #f05a28 !important;
}

/* プライマリボタン（ダイアログの「決定して閉じる」など）をキャロットグリーンに */
button[kind="primary"] {
    background-color: #004d25 !important;
    border-color: #004d25 !important;
    color: white !important;
}

/* 通常のボタン（サイドバーの「選択する」など）の枠線・文字色をキャロットグリーンに */
button[kind="secondary"] {
    border-color: #004d25 !important;
    color: #004d25 !important;
}
button[kind="secondary"]:hover {
    background-color: #004d25 !important;
    color: white !important;
}

/* スライダーの色をキャロットグリーンに */
div.stSlider > div > div > div > div {
    background-color: #004d25 !important;
}

/* マルチセレクトの選択タグ（チップ）の色をキャロットグリーンに強制変更 */
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background-color: #004d25 !important;
    background: #004d25 !important;
}
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span {
    color: white !important;
}
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
    fill: white !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# --- データの読み込み ---
@st.cache_data
def load_data():
    # CSVの読み込み（Windows/Macのエンコーディングの違いを吸収）
    try:
        df = pd.read_csv("list.csv", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv("list.csv", encoding="cp932")
    
    # 生年月日のデータ型を日付型（datetime）に変換し、月を取り出す処理を追加
    if '生年月日' in df.columns:
        df['誕生月'] = pd.to_datetime(df['生年月日'], format='%m/%d', errors='coerce').dt.month
        
    # 💡 カンマが含まれる文字列データなどが計算でエラーにならないように数値型に変換
    for col in ['募集価格', '体高', '胸囲', '管囲', '馬体重']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            
    # ★ 独自指標の計算（リスク＆コスパ分析）を追加 ★
    if '管囲' in df.columns and '馬体重' in df.columns:
        # 管囲(cm) / 馬体重(kg) * 100 で比率を計算（脚元リスクの目安）
        df['管囲体重比(%)'] = (df['管囲'] / df['馬体重'] * 100).round(2)
        
    if '募集価格' in df.columns and '馬体重' in df.columns:
        # 1kgあたりの募集価格（万円）を計算（コスパの目安）
        df['体重単価(万円/kg)'] = (df['募集価格'] / df['馬体重']).round(2)
    
    return df

# データを読み込む
df = load_data()

# --- サイドバーのレイアウト枠を作成（表示順を固定） ---
sidebar_main = st.sidebar.container()
sidebar_footer = st.sidebar.container()

# --- 選択肢の準備とセッションステートの初期化 ---
sire_options = sorted(df['父名'].dropna().unique()) if '父名' in df.columns else []
bms_options = sorted(df['母父'].dropna().unique()) if '母父' in df.columns else []
trainer_options = sorted(df['厩舎'].dropna().unique()) if '厩舎' in df.columns else []

if 'selected_sire' not in st.session_state:
    st.session_state.selected_sire = sire_options
if 'selected_bms' not in st.session_state:
    st.session_state.selected_bms = bms_options
if 'selected_trainer' not in st.session_state:
    st.session_state.selected_trainer = trainer_options

# --- ダイアログ（モーダルウィンドウ）の定義 ---
@st.dialog("🐎 種牡馬の選択", width="large")
def sire_dialog():
    st.markdown("不要な種牡馬を「×」で消してください。枠内をクリックして検索も可能です。")
    selected = st.multiselect(
        "父名（種牡馬）", 
        options=sire_options, 
        default=st.session_state.selected_sire,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("✅ 決定して閉じる", key="sire_close", use_container_width=True, type="primary"):
            st.session_state.selected_sire = selected
            st.rerun()
    with col2:
        if st.button("🔄 全選択", key="sire_all", use_container_width=True):
            st.session_state.selected_sire = sire_options
            st.rerun()
    with col3:
        if st.button("🗑️ 全解除", key="sire_clear", use_container_width=True):
            st.session_state.selected_sire = []
            st.rerun()

@st.dialog("🐴 母父の選択", width="large")
def bms_dialog():
    st.markdown("不要な母父を「×」で消してください。枠内をクリックして検索も可能です。")
    selected = st.multiselect(
        "母父", 
        options=bms_options, 
        default=st.session_state.selected_bms,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("✅ 決定して閉じる", key="bms_close", use_container_width=True, type="primary"):
            st.session_state.selected_bms = selected
            st.rerun()
    with col2:
        if st.button("🔄 全選択", key="bms_all", use_container_width=True):
            st.session_state.selected_bms = bms_options
            st.rerun()
    with col3:
        if st.button("🗑️ 全解除", key="bms_clear", use_container_width=True):
            st.session_state.selected_bms = []
            st.rerun()

@st.dialog("🏢 厩舎の選択", width="large")
def trainer_dialog():
    st.markdown("不要な厩舎を「×」で消してください。枠内をクリックして検索も可能です。")
    selected = st.multiselect(
        "厩舎", 
        options=trainer_options, 
        default=st.session_state.selected_trainer,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("✅ 決定して閉じる", key="trainer_close", use_container_width=True, type="primary"):
            st.session_state.selected_trainer = selected
            st.rerun()
    with col2:
        if st.button("🔄 全選択", key="trainer_all", use_container_width=True):
            st.session_state.selected_trainer = trainer_options
            st.rerun()
    with col3:
        if st.button("🗑️ 全解除", key="trainer_clear", use_container_width=True):
            st.session_state.selected_trainer = []
            st.rerun()

# --- サイドバー：フィルター機能 ---
with sidebar_main:
    st.header("🔍 分析条件の設定")
    st.caption("※不要な項目の「×」を押して対象を絞り込んでください。")

    if st.button("🔄 すべての条件をリセット", type="primary", use_container_width=True):
        st.session_state.selected_sire = sire_options
        st.session_state.selected_bms = bms_options
        st.session_state.selected_trainer = trainer_options
        st.session_state.key_shozoku = sorted(df['所属'].dropna().unique()) if '所属' in df.columns else []
        st.session_state.key_sex = sorted(df['性'].dropna().unique()) if '性' in df.columns else []
        st.session_state.key_bousyu = sorted(df['母優'].dropna().unique()) if '母優' in df.columns else []
        st.session_state.key_farm = sorted(df['育成牧場'].dropna().unique()) if '育成牧場' in df.columns else []
        
        # 💡 空欄データ(NaN)によるエラーを防ぐための安全な書き方に変更
        st.session_state.key_month = (int(df['誕生月'].dropna().min()), int(df['誕生月'].dropna().max())) if '誕生月' in df.columns and not df['誕生月'].dropna().empty else (1, 12)
        st.session_state.key_price = (int(df['募集価格'].dropna().min()), int(df['募集価格'].dropna().max())) if '募集価格' in df.columns and not df['募集価格'].dropna().empty else (0, 10000)
        st.session_state.key_height = (float(df['体高'].dropna().min()), float(df['体高'].dropna().max())) if '体高' in df.columns and not df['体高'].dropna().empty else (0.0, 200.0)
        st.session_state.key_chest = (float(df['胸囲'].dropna().min()), float(df['胸囲'].dropna().max())) if '胸囲' in df.columns and not df['胸囲'].dropna().empty else (0.0, 250.0)
        st.session_state.key_canon = (float(df['管囲'].dropna().min()), float(df['管囲'].dropna().max())) if '管囲' in df.columns and not df['管囲'].dropna().empty else (0.0, 30.0)
        st.session_state.key_weight = (float(df['馬体重'].dropna().min()), float(df['馬体重'].dropna().max())) if '馬体重' in df.columns and not df['馬体重'].dropna().empty else (0.0, 600.0)
        st.rerun()

    # 所属フィルターを追加
    shozoku_options = sorted(df['所属'].dropna().unique())
    selected_shozoku = st.multiselect(
        "所属", 
        options=shozoku_options, 
        default=shozoku_options,
        key="key_shozoku"
    )
    filter_shozoku = selected_shozoku

    # 性別フィルター
    sex_options = sorted(df['性'].dropna().unique())
    selected_sex = st.multiselect(
        "性別", 
        options=sex_options, 
        default=sex_options,
        key="key_sex"
    )
    filter_sex = selected_sex

    # 母優先フィルターを追加
    bousyu_options = sorted(df['母優'].dropna().unique())
    selected_bousyu = st.multiselect(
        "母優先", 
        options=bousyu_options, 
        default=bousyu_options,
        key="key_bousyu"
    )
    filter_bousyu = selected_bousyu

    # 育成牧場フィルター
    farm_options = sorted(df['育成牧場'].dropna().unique())
    selected_farm = st.multiselect(
        "育成牧場", 
        options=farm_options, 
        default=farm_options,
        key="key_farm"
    )
    filter_farm = selected_farm

    # ダイアログを呼び出すボタン（種牡馬）
    st.markdown("---")
    st.subheader("🐎 種牡馬")
    if st.button("🔍 種牡馬を選択する", use_container_width=True):
        sire_dialog()
    st.caption(f"選択中: {len(st.session_state.selected_sire)} / {len(sire_options)} 種類")

    # ダイアログを呼び出すボタン（母父）
    st.markdown("---")
    st.subheader("🐴 母父")
    if st.button("🔍 母父を選択する", use_container_width=True):
        bms_dialog()
    st.caption(f"選択中: {len(st.session_state.selected_bms)} / {len(bms_options)} 種類")

    # ダイアログを呼び出すボタン（厩舎）
    st.markdown("---")
    st.subheader("🏢 厩舎")
    if st.button("🔍 厩舎を選択する", use_container_width=True):
        trainer_dialog()
    st.caption(f"選択中: {len(st.session_state.selected_trainer)} / {len(trainer_options)} 厩舎")

    # 誕生月フィルターを追加（スライダー）
    min_month = int(df['誕生月'].dropna().min()) if '誕生月' in df.columns and not df['誕生月'].dropna().empty else 1
    max_month = int(df['誕生月'].dropna().max()) if '誕生月' in df.columns and not df['誕生月'].dropna().empty else 12
    if min_month == max_month: max_month = min_month + 1
    selected_month_range = st.slider(
        "誕生月",
        min_value=min_month,
        max_value=max_month,
        value=(min_month, max_month),
        key="key_month"
    )

    # 価格情報フィルター（スライダー）を追加
    st.markdown("---")
    st.subheader("💰 価格情報の設定")

    min_price = int(df['募集価格'].dropna().min()) if '募集価格' in df.columns and not df['募集価格'].dropna().empty else 0
    max_price = int(df['募集価格'].dropna().max()) if '募集価格' in df.columns and not df['募集価格'].dropna().empty else 10000
    if min_price == max_price: max_price = min_price + 100
    selected_price = st.slider(
        "募集価格 (万円)", 
        min_value=min_price, 
        max_value=max_price, 
        value=(min_price, max_price),
        step=100,
        key="key_price"
    )

    # 体部情報フィルター（スライダー）を追加
    st.markdown("---")
    st.subheader("📐 体部情報の設定")

    min_height = float(df['体高'].dropna().min()) if '体高' in df.columns and not df['体高'].dropna().empty else 0.0
    max_height = float(df['体高'].dropna().max()) if '体高' in df.columns and not df['体高'].dropna().empty else 200.0
    if min_height == max_height: max_height = min_height + 1.0
    selected_height = st.slider("体高 (cm)", min_value=min_height, max_value=max_height, value=(min_height, max_height), key="key_height")

    min_chest = float(df['胸囲'].dropna().min()) if '胸囲' in df.columns and not df['胸囲'].dropna().empty else 0.0
    max_chest = float(df['胸囲'].dropna().max()) if '胸囲' in df.columns and not df['胸囲'].dropna().empty else 250.0
    if min_chest == max_chest: max_chest = min_chest + 1.0
    selected_chest = st.slider("胸囲 (cm)", min_value=min_chest, max_value=max_chest, value=(min_chest, max_chest), key="key_chest")

    min_canon = float(df['管囲'].dropna().min()) if '管囲' in df.columns and not df['管囲'].dropna().empty else 0.0
    max_canon = float(df['管囲'].dropna().max()) if '管囲' in df.columns and not df['管囲'].dropna().empty else 30.0
    if min_canon == max_canon: max_canon = min_canon + 1.0
    selected_canon = st.slider("管囲 (cm)", min_value=min_canon, max_value=max_canon, value=(min_canon, max_canon), key="key_canon")

    min_weight = float(df['馬体重'].dropna().min()) if '馬体重' in df.columns and not df['馬体重'].dropna().empty else 0.0
    max_weight = float(df['馬体重'].dropna().max()) if '馬体重' in df.columns and not df['馬体重'].dropna().empty else 600.0
    if min_weight == max_weight: max_weight = min_weight + 1.0
    selected_weight = st.slider("馬体重 (kg)", min_value=min_weight, max_value=max_weight, value=(min_weight, max_weight), key="key_weight")

# --- バージョン情報 ---
with sidebar_footer:
    st.caption("🥕 Owner's Eye")
    st.caption("Version 1.2.0")

# フィルターの適用
filtered_df = df[
    (df['所属'].isin(filter_shozoku)) & 
    (df['性'].isin(filter_sex)) & 
    (df['母優'].isin(filter_bousyu)) &
    (df['父名'].isin(st.session_state.selected_sire)) &
    (df['母父'].isin(st.session_state.selected_bms)) &
    (df['厩舎'].isin(st.session_state.selected_trainer)) &
    (df['育成牧場'].isin(filter_farm)) &
    (df['誕生月'].between(selected_month_range[0], selected_month_range[1])) &
    (df['募集価格'].between(selected_price[0], selected_price[1]) if '募集価格' in df.columns else True) &
    (df['体高'].between(selected_height[0], selected_height[1])) &
    (df['胸囲'].between(selected_chest[0], selected_chest[1])) &
    (df['管囲'].between(selected_canon[0], selected_canon[1])) &
    (df['馬体重'].between(selected_weight[0], selected_weight[1]))
]

# --- メイン画面：サマリ（KPI） ---
st.subheader("📊 サマリ情報")
col1, col2, col3, col4 = st.columns(4)
col1.metric("対象馬数", f"{len(filtered_df)} 頭")

if len(filtered_df) > 0:
    col2.metric("平均馬体重", f"{filtered_df['馬体重'].mean():.1f} kg")
    col3.metric("平均管囲", f"{filtered_df['管囲'].mean():.1f} cm")
    if '募集価格' in filtered_df.columns:
        col4.metric("平均募集価格", f"{filtered_df['募集価格'].mean():.1f} 万円")
else:
    st.warning("条件に一致する馬がいません。フィルターを変更してください。")

# キャロット風カラーパレット（グリーン、オレンジ、ゴールド等を基調に）
carrot_colors = ['#004d25', '#f05a28', '#a38753', '#1c2833', '#7b241c', '#0e6655', '#d35400', '#17202a']

# --- 可視化1：散布図 ---
st.subheader("📈 馬体重 × 管囲 × 募集価格 の関係")
st.markdown("横軸に馬体重、縦軸に管囲を取り、**バブルの大きさで募集価格**、**色で種牡馬**を表現しています。マウスを合わせると詳細が表示されます。")

if len(filtered_df) > 0 and '募集価格' in filtered_df.columns:
    fig_scatter = px.scatter(
        filtered_df, 
        x="馬体重", 
        y="管囲", 
        size="募集価格", 
        color="父名",
        hover_name="募集馬名",
        hover_data={"厩舎": True, "生年月日": True, "募集価格": True},
        height=500,
        color_discrete_sequence=carrot_colors
    )
    # グラフのレイアウト調整
    fig_scatter.update_layout(xaxis_title="馬体重 (kg)", yaxis_title="管囲 (cm)")
    st.plotly_chart(fig_scatter, use_container_width=True)

# グラフを横に並べるためのレイアウト（2カラム）
col_g1, col_g2 = st.columns(2)

# --- 可視化2：募集価格の分布（ヒストグラム） ---
with col_g1:
    st.subheader("💴 募集価格の分布")
    if len(filtered_df) > 0 and '募集価格' in filtered_df.columns:
        fig_price = px.histogram(
            filtered_df,
            x="募集価格",
            color="性",
            title="募集価格別の募集馬数",
            labels={"募集価格": "募集価格 (万円)", "性": "性別"},
            nbins=20,
            color_discrete_sequence=['#004d25', '#f05a28'] # 牡と牝の色分け
        )
        fig_price.update_layout(yaxis_title="頭数", height=400)
        st.plotly_chart(fig_price, use_container_width=True)

# --- 可視化3：種牡馬別の募集馬頭数（横棒グラフ） ---
with col_g2:
    st.subheader("🐎 種牡馬別の募集馬頭数")
    if len(filtered_df) > 0:
        # 種牡馬ごとの頭数をカウント
        sire_counts = filtered_df['父名'].value_counts().reset_index()
        sire_counts.columns = ['父名', '頭数']
        
        # 上位15頭のみ表示（見やすさのため）
        top_sires = sire_counts.head(15)
        
        fig_sire = px.bar(
            top_sires,
            x='頭数',
            y='父名',
            orientation='h', # 横向きの棒グラフ
            title="種牡馬別の頭数ランキング (上位15種牡馬)",
            text_auto=True,
            color='頭数',
            color_continuous_scale=['#cce3d5', '#004d25'] # キャロットグリーンのグラデーション
        )
        fig_sire.update_layout(yaxis={'categoryorder':'total ascending'}, height=400) # 頭数順に並び替え
        st.plotly_chart(fig_sire, use_container_width=True)

# --- 可視化4：厩舎別の平均馬体重・管囲（棒グラフ） ---
st.subheader("🏢 厩舎別の体部アベレージ")
if len(filtered_df) > 0:
    # 厩舎ごとの平均を計算
    trainer_stats = filtered_df.groupby('厩舎')[['馬体重', '管囲']].mean().reset_index()
    
    # 馬体重の棒グラフ
    fig_trainer = px.bar(
        trainer_stats, 
        x='厩舎', 
        y='馬体重', 
        title="厩舎別の平均馬体重",
        text_auto='.1f',
        color='馬体重',
        color_continuous_scale=['#cce3d5', '#004d25'] # 薄緑からキャロットグリーンへのグラデーション
    )
    fig_trainer.update_layout(xaxis_tickangle=-45, height=500) # 厩舎名が重ならないように斜めにする
    st.plotly_chart(fig_trainer, use_container_width=True)

# --- 独自分析：リスク＆コスパ ---
st.markdown("---")
st.subheader("👁️ Owner's Eye 独自指標ランキング")
st.markdown("マニアックな視点で算出した独自の指標に基づき、現在のフィルター条件内でのランキングを表示します。")

col_a1, col_a2 = st.columns(2)

with col_a1:
    if len(filtered_df) > 0 and '管囲体重比(%)' in filtered_df.columns:
        st.markdown("##### 🛡️ 脚元安心度 (管囲/馬体重)")
        st.caption("※体重に対して管囲が太い（比率が高い）上位10頭")
        # 値が大きい順に10頭取得
        top_risk = filtered_df.dropna(subset=['管囲体重比(%)']).sort_values('管囲体重比(%)', ascending=False).head(10)
        fig_risk = px.bar(
            top_risk,
            x='管囲体重比(%)',
            y='募集馬名',
            orientation='h',
            text_auto='.2f',
            color='管囲体重比(%)',
            color_continuous_scale=['#cce3d5', '#004d25']
        )
        fig_risk.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
        st.plotly_chart(fig_risk, use_container_width=True)

with col_a2:
    if len(filtered_df) > 0 and '体重単価(万円/kg)' in filtered_df.columns:
        st.markdown("##### 🛒 お買い得度 (1kgあたり単価)")
        st.caption("※1kgあたりの価格が安い（コスパが良い）上位10頭")
        # 値が小さい順に10頭取得
        top_cospa = filtered_df.dropna(subset=['体重単価(万円/kg)']).sort_values('体重単価(万円/kg)', ascending=True).head(10)
        fig_cospa = px.bar(
            top_cospa,
            x='体重単価(万円/kg)',
            y='募集馬名',
            orientation='h',
            text_auto='.2f',
            color='体重単価(万円/kg)',
            color_continuous_scale=['#f05a28', '#fce5cd'] # 安い方が濃いオレンジになるように配色
        )
        # 安い順なので、値が小さいものが上に来るように設定
        fig_cospa.update_layout(yaxis={'categoryorder':'total descending'}, height=400) 
        st.plotly_chart(fig_cospa, use_container_width=True)

# --- データテーブル ---
st.subheader("📋 募集馬リスト")

# ★表示項目に「管囲体重比(%)」と「体重単価(万円/kg)」を追加！
default_display_columns = ["No.", "募集馬名", "所属", "父名", "母父", "母優", "性", "生年月日", "厩舎", "募集価格", "体高", "胸囲", "管囲", "馬体重", "管囲体重比(%)", "体重単価(万円/kg)", "育成牧場"]
display_columns = [col for col in default_display_columns if col in filtered_df.columns]

csv_data = filtered_df[display_columns].to_csv(index=False).encode('utf-8-sig')

# ダウンロードボタンを左側に配置
col_dl1, col_dl2 = st.columns([1, 2])
with col_dl1:
    st.download_button(
        label="📥 表示中のリストをCSVでダウンロード",
        data=csv_data,
        file_name="carrot_filtered_list.csv",
        mime="text/csv",
        use_container_width=True
    )

# 💡 データ件数に合わせて表の高さを自動計算し、内部スクロールをなくす（1行あたり約35px ＋ ヘッダー部分40px）
table_height = max(len(filtered_df) * 35 + 40, 150)

# hide_index=True で左端の不要な連番(0,1,2...)を隠してスッキリ見せます
st.dataframe(
    filtered_df[display_columns], 
    use_container_width=True, 
    height=table_height, 
    hide_index=True
)

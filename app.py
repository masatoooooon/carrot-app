import streamlit as st
import pandas as pd
import plotly.express as px

# --- ページ設定 ---
st.set_page_config(page_title="Stallion Select", layout="wide")
st.title("🏇 Stallion Select")

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
</style>
""", unsafe_allow_html=True)

# --- データの読み込み ---
@st.cache_data
def load_data(uploaded_file=None):
    # CSVの読み込み（Windows/Macのエンコーディングの違いを吸収）
    try:
        if uploaded_file is not None:
            # アップロードされたファイルを読み込む
            df = pd.read_csv(uploaded_file, encoding="utf-8")
        else:
            # 指定がない場合はデフォルトのファイルを読み込む
            df = pd.read_csv("list.csv", encoding="utf-8")
    except UnicodeDecodeError:
        if uploaded_file is not None:
            # エンコーディングエラーの場合はポインタを戻して再読み込み
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding="cp932")
        else:
            df = pd.read_csv("list.csv", encoding="cp932")
    
    # 生年月日のデータ型を日付型（datetime）に変換し、月を取り出す処理を追加
    if '生年月日' in df.columns:
        df['誕生月'] = pd.to_datetime(df['生年月日'], format='%m/%d', errors='coerce').dt.month
    
    return df

# --- サイドバーのレイアウト枠を作成（表示順を固定） ---
sidebar_main = st.sidebar.container()
sidebar_upload = st.sidebar.container()
sidebar_footer = st.sidebar.container()

# --- サイドバー：データのアップロード（下部に配置） ---
with sidebar_upload:
    st.markdown("---")
    st.header("📁 データの読み込み")
    st.caption("独自のCSVファイルをアップロードして分析できます。（指定しない場合はデフォルトデータを使用）")
    uploaded_file = st.file_uploader("CSVファイルを選択", type=["csv"])

# データを読み込む
df = load_data(uploaded_file)

# 💡 データが切り替わったときに、以前の選択状態をリセットする処理
current_file_name = uploaded_file.name if uploaded_file is not None else "default_list.csv"
if 'last_file_name' not in st.session_state or st.session_state.last_file_name != current_file_name:
    for key in ['selected_sire', 'selected_bms', 'selected_trainer']:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.last_file_name = current_file_name

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
        st.session_state.key_month = (int(df['誕生月'].min(skipna=True)), int(df['誕生月'].max(skipna=True))) if '誕生月' in df.columns else (1, 12)
        st.session_state.key_price = (int(df['価格帯'].min(skipna=True)), int(df['価格帯'].max(skipna=True))) if '価格帯' in df.columns else (0, 10000)
        st.session_state.key_height = (float(df['体高'].min(skipna=True)), float(df['体高'].max(skipna=True))) if '体高' in df.columns else (0.0, 200.0)
        st.session_state.key_chest = (float(df['胸囲'].min(skipna=True)), float(df['胸囲'].max(skipna=True))) if '胸囲' in df.columns else (0.0, 250.0)
        st.session_state.key_canon = (float(df['管囲'].min(skipna=True)), float(df['管囲'].max(skipna=True))) if '管囲' in df.columns else (0.0, 30.0)
        st.session_state.key_weight = (float(df['馬体重'].min(skipna=True)), float(df['馬体重'].max(skipna=True))) if '馬体重' in df.columns else (0.0, 600.0)
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
    min_month = int(df['誕生月'].min(skipna=True))
    max_month = int(df['誕生月'].max(skipna=True))
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

    min_price = int(df['価格帯'].min(skipna=True))
    max_price = int(df['価格帯'].max(skipna=True))
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

    min_height = float(df['体高'].min(skipna=True))
    max_height = float(df['体高'].max(skipna=True))
    selected_height = st.slider("体高 (cm)", min_value=min_height, max_value=max_height, value=(min_height, max_height), key="key_height")

    min_chest = float(df['胸囲'].min(skipna=True))
    max_chest = float(df['胸囲'].max(skipna=True))
    selected_chest = st.slider("胸囲 (cm)", min_value=min_chest, max_value=max_chest, value=(min_chest, max_chest), key="key_chest")

    min_canon = float(df['管囲'].min(skipna=True))
    max_canon = float(df['管囲'].max(skipna=True))
    selected_canon = st.slider("管囲 (cm)", min_value=min_canon, max_value=max_canon, value=(min_canon, max_canon), key="key_canon")

    min_weight = float(df['馬体重'].min(skipna=True))
    max_weight = float(df['馬体重'].max(skipna=True))
    selected_weight = st.slider("馬体重 (kg)", min_value=min_weight, max_value=max_weight, value=(min_weight, max_weight), key="key_weight")

# --- バージョン情報 ---
with sidebar_footer:
    st.caption("🥕 Stallion Select")
    st.caption("Version 1.0.0")

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
    (df['価格帯'].between(selected_price[0], selected_price[1])) &
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
    # 平均募集価格に変更（価格帯カラムの数値をそのまま万円として表示）
    col4.metric("平均募集価格", f"{filtered_df['価格帯'].mean():.1f} 万円")
else:
    st.warning("条件に一致する馬がいません。フィルターを変更してください。")

# キャロット風カラーパレット（グリーン、オレンジ、ゴールド等を基調に）
carrot_colors = ['#004d25', '#f05a28', '#a38753', '#1c2833', '#7b241c', '#0e6655', '#d35400', '#17202a']

# --- 可視化1：散布図 ---
st.subheader("📈 馬体重 × 管囲 × 価格帯 の関係")
st.markdown("横軸に馬体重、縦軸に管囲を取り、**バブルの大きさで価格帯**、**色で種牡馬**を表現しています。マウスを合わせると詳細が表示されます。")

if len(filtered_df) > 0:
    fig_scatter = px.scatter(
        filtered_df, 
        x="馬体重", 
        y="管囲", 
        size="価格帯", 
        color="父名",
        hover_name="募集馬名",
        # ツールチップに生年月日と厩舎を追加
        hover_data={"厩舎": True, "生年月日": True, "募集価格": True, "価格帯": False},
        height=500,
        color_discrete_sequence=carrot_colors
    )
    # グラフのレイアウト調整
    fig_scatter.update_layout(xaxis_title="馬体重 (kg)", yaxis_title="管囲 (cm)")
    st.plotly_chart(fig_scatter, use_container_width=True)

# グラフを横に並べるためのレイアウト（2カラム）
col_g1, col_g2 = st.columns(2)

# --- 可視化2：価格帯の分布（ヒストグラム） ---
with col_g1:
    st.subheader("💴 募集価格帯の分布")
    if len(filtered_df) > 0:
        fig_price = px.histogram(
            filtered_df,
            x="価格帯",
            color="性",
            title="価格帯別の募集馬数",
            labels={"価格帯": "募集価格 (万円)", "性": "性別"},
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

# --- データテーブル ---
st.subheader("📋 募集馬リスト")

# ダウンロード機能を追加
# Excelで開いたときの文字化けを防ぐために utf-8-sig (BOM付きUTF-8) に変換
default_display_columns = ["No.", "募集馬名", "所属", "父名", "母父", "母優", "性", "生年月日", "厩舎", "募集価格", "体高", "胸囲", "管囲", "馬体重", "育成牧場"]
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

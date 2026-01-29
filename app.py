import streamlit as st
import requests
import datetime

# GPSライブラリ
from streamlit_geolocation import streamlit_geolocation

# ==============================
# APIキー設定
# ==============================

api_key = "c23567c324324f8c2391bb05a866196f"

# ==============================
# ページ設定（スマホ風）
# ==============================

st.set_page_config(
    page_title="天気＆服装アプリ",
    page_icon="☁️",
    layout="centered"
)

# ==============================
# スマホ風CSS
# ==============================

st.markdown("""
<style>
.main {
    max-width: 420px;
    margin: auto;
}

h1 {
    text-align: center;
    font-size: 2.2em;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 22px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
    margin-top: 20px;
}

.big {
    font-size: 1.3em;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 地域入力対応（滋賀県大津市OK）
# ==============================

def parse_location(text):
    text = text.replace(" ", "")

    if "/" in text:
        pref, city = text.split("/")
        return pref, city

    for key in ["都", "道", "府", "県"]:
        if key in text:
            pref = text.split(key)[0] + key
            city = text.split(key)[1]
            return pref, city

    return None, None

# ==============================
# 服装アドバイス
# ==============================

def get_clothing_advice(temp):
    if temp is None:
        return "データ不足"
    elif temp >= 23:
        return "半袖がおすすめです👕"
    elif 16 <= temp <= 22:
        return "長袖＋羽織りがおすすめです🧥"
    else:
        return "厚着がおすすめです🧣"

# ==============================
# 天気取得（都市名）
# ==============================

def fetch_weather_by_city(prefecture, city):
    url = "http://api.openweathermap.org/data/2.5/forecast"

    params = {
        "q": f"{city},{prefecture},JP",
        "appid": api_key,
        "units": "metric",
        "lang": "ja"
    }

    response = requests.get(url, params=params)
    return response.json()

# ==============================
# 天気取得（GPS）
# ==============================

def fetch_weather_by_gps(lat, lon):
    url = "http://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "lang": "ja"
    }

    response = requests.get(url, params=params)
    return response.json()

# ==============================
# UI開始
# ==============================

st.title("☁️ 天気＆服装アプリ")

st.write("GPSでも手入力でも天気と服装をチェックできます！")

# ------------------------------
# 日付入力
# ------------------------------

date_input = st.date_input(
    "📅 調べたい日を選んでください",
    datetime.date.today()
)

# ------------------------------
# モード選択
# ------------------------------

mode = st.radio(
    "📍 地域の指定方法を選んでください",
    ["手入力する", "GPSで現在地取得"]
)

# ==============================
# 手入力モード
# ==============================

if mode == "手入力する":

    location_input = st.text_input(
        "地域を入力（例：滋賀県大津市 / 滋賀県/大津市）"
    )

    if st.button("天気を調べる"):

        pref, city = parse_location(location_input)

        if pref is None:
            st.error("入力形式が正しくありません")
            st.stop()

        data = fetch_weather_by_city(pref, city)

# ==============================
# GPSモード（完全自動）
# ==============================

else:
    st.info("📍 現在地を自動取得します（位置情報を許可してください）")

    location = streamlit_geolocation()

    if location is None:
        st.warning("位置情報がまだ取得できていません")
        st.stop()

    lat = location["latitude"]
    lon = location["longitude"]

    st.success(f"取得成功！緯度={lat:.4f}, 経度={lon:.4f}")

    if st.button("現在地の天気を調べる"):
        data = fetch_weather_by_gps(lat, lon)

# ==============================
# 結果処理
# ==============================

if "data" in locals():

    if "list" not in data:
        st.error("天気情報を取得できませんでした")
        st.stop()

    # 対象日のデータ抽出
    target_date = date_input.strftime("%Y-%m-%d")

    weather_data = [
        item for item in data["list"]
        if item["dt_txt"].startswith(target_date)
    ]

    if not weather_data:
        st.warning("その日の予報データがありません")
        st.stop()

    # 天気
    weather_main = weather_data[0]["weather"][0]["description"]

    # 雨チェック
    rain_forecast = any(
        "rain" in item["weather"][0]["main"].lower()
        for item in weather_data
    )

    rain_msg = "☔ 雨具が必要です" if rain_forecast else "✅ 雨具は不要です"

    # 気温まとめ
    temps = [item["main"]["temp"] for item in weather_data]

    avg_temp = sum(temps) / len(temps)
    min_temp = min(temps)
    max_temp = max(temps)

    # 日中と夜の平均
    daytime_hours = range(9, 18)

    daytime_temps = [
        item["main"]["temp"]
        for item in weather_data
        if datetime.datetime.strptime(
            item["dt_txt"], "%Y-%m-%d %H:%M:%S"
        ).hour in daytime_hours
    ]

    nighttime_temps = [
        item["main"]["temp"]
        for item in weather_data
        if datetime.datetime.strptime(
            item["dt_txt"], "%Y-%m-%d %H:%M:%S"
        ).hour not in daytime_hours
    ]

    daytime_avg = sum(daytime_temps) / len(daytime_temps)
    nighttime_avg = sum(nighttime_temps) / len(nighttime_temps)

    # 服装
    daytime_advice = get_clothing_advice(daytime_avg)
    nighttime_advice = get_clothing_advice(nighttime_avg)

    # ==============================
    # 表示（カードUI）
    # ==============================

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown(
        f"<p class='big'>🌤 天気：{weather_main}</p>",
        unsafe_allow_html=True
    )

    st.write(rain_msg)

    st.write("---")

    st.write(f"🌡 平均気温：{avg_temp:.1f}℃")
    st.write(f"⬇ 最低気温：{min_temp:.1f}℃")
    st.write(f"⬆ 最高気温：{max_temp:.1f}℃")

    st.write("---")

    st.write(f"☀️ 日中平均：{daytime_avg:.1f}℃ → {daytime_advice}")
    st.write(f"🌙 夜平均：{nighttime_avg:.1f}℃ → {nighttime_advice}")

    st.markdown("</div>", unsafe_allow_html=True)

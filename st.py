import streamlit as st
import streamlit.components.v1 as components
from streamlit.delta_generator import DeltaGenerator
import app
from modules.constants import RACEDATA
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime


def page_config():
    st.set_page_config(
        page_title="地方競馬",
        layout="wide",
        initial_sidebar_state="auto",
    )
    return datetime.date.today()


def exists_current_date_races(date):
    race_ids = app.find_race_ids_by_date(date)
    return len(race_ids) > 0


def current_date_race_ids(date) -> dict[str, list[str]]:
    """
    dateのレースIDを取得する
    """
    race_ids = app.find_race_ids_by_date(date)
    local_race_ids = {}
    for race_id in race_ids:
        local_name = RACEDATA.LOCALCODE_NAME[race_id[4:6]]
        if local_name not in local_race_ids.keys():
            local_race_ids.setdefault(local_name, [])
        local_race_ids[local_name].append(race_id)
    return local_race_ids


def select_race_id(container: DeltaGenerator, race_ids: dict):
    """
    レースIDを選択する
    """
    local_col, r_col = container.columns([1, 4])
    local = local_col.selectbox(
        label="開催地", options=race_ids.keys(), label_visibility="hidden"
    )
    r = r_col.select_slider(
        label="R",
        options=range(1, len(race_ids[local]) + 1, 1),
        label_visibility="hidden",
    )
    return race_ids[local][r - 1]  # type: ignore


def select_current_race_id(container: DeltaGenerator, date) -> str:
    """
    レースIDを選択する
    """
    race_ids = current_date_race_ids(date)
    return select_race_id(container, race_ids)


def find_current_pre_race(race_id: str):
    """
    レース事前情報を取得する
    """
    return app.find_pre_race(race_id)


def find_current_shutuba(race_id: str) -> pd.DataFrame:
    """
    出馬表を取得する
    """
    df = app.find_shutuba(race_id)
    df.drop(columns=["_id"], inplace=True)
    return df


@st.cache_data
def find_results(race_id: str, type: str) -> pd.DataFrame:
    """
    レースIDから過去戦績を取得する
    """
    horse_ids = app.find_horse_ids(race_id)
    ids_dict = {v: n for n, v in enumerate(horse_ids, 1)}
    with st.spinner("ローディング中..."):
        result_df = app.find_result_from_ids(ids_dict, type)
        return format_result_df(result_df)


def find_duplicate_other(info, df: pd.DataFrame, type: str, n: int = 3):
    """
    レース結果から馬が重複しているレースを取得する
    """
    if type not in ["horse", "jockey", "trainer"]:
        raise Exception(f"Error type: {type}")
    with st.spinner("ローディング中..."):
        duplicate_df = app.find_duplicate_other(
            df["race_id"].tolist(),
            df[f"{type}_id"].tolist(),
            type,
            n=n,
        )
        if len(duplicate_df) < 1:
            return pd.DataFrame()
        course = info["course"]
        distance = info["distance"]
        local = info["local"]
        start_date = datetime.datetime.strptime(
            info["date"], "%Y-%m-%d %H:%M"
        ).date() - datetime.timedelta(days=500)
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = datetime.datetime.strptime(
            info["date"], "%Y-%m-%d %H:%M"
        ).date() - datetime.timedelta(days=1)
        end_date = end_date.strftime("%Y-%m-%d")
        duplicate_df = duplicate_df[
            (duplicate_df["course"] == course)
            & (duplicate_df["distance"] == distance)
            & (duplicate_df["local"] == local)
            & (duplicate_df["date"] >= start_date)
            & (duplicate_df["date"] <= end_date)
        ]
        if len(duplicate_df) < 1:
            return pd.DataFrame()
        cnt = duplicate_df["cnt"].tolist()
        cnt_cnt = {v: cnt.count(v) for v in cnt}
        cnt_list = [k for k, v in cnt_cnt.items() if v >= n]
        if len(cnt_list) < 1:
            return pd.DataFrame()
        duplicate_df = duplicate_df[duplicate_df["cnt"].isin(cnt_list)]
        return format_result_df(duplicate_df)


def convert_time_to_sec(time_str: str) -> float:
    """
    時間を秒に変換する
    """
    try:
        time = time_str.split(":")
        if len(time) == 2:
            return int(time[0]) * 60 + float(time[1])
        else:
            try:
                return float(time_str)
            except Exception:
                raise Exception(f"Error converting time to sec: {time_str}")
    except Exception:
        raise Exception(f"Error converting time to sec: {time_str}")


def format_result_df(df: pd.DataFrame):
    """
    過去戦績のデータフレームを整形する
    """
    df.dropna(subset=["order_of_finish", "time"], inplace=True)
    df.drop(columns=["prize", "race_name"], inplace=True)
    df["date"] = df["date"].apply(
        lambda x: datetime.datetime.strptime(str(x).split(" ")[0], "%Y-%m-%d").date()
    )
    df["distance"] = df["distance"].apply(lambda x: int(x))
    df["time"] = df["time"].apply(lambda x: convert_time_to_sec(x))
    # cntカラムの名前を馬番に変更
    df["cnt"] = df["cnt"].apply(lambda x: int(x))
    return df.rename(columns={"cnt": "馬番"})


def config_result_df(
    sidebar: DeltaGenerator, pre_race, df: pd.DataFrame
) -> pd.DataFrame:
    """
    過去戦績のプロット設定
    """
    local_options = df["local"].unique().tolist()
    if pre_race["local"] in local_options:
        default_value = pre_race["local"]
    else:
        default_value = local_options
    local = sidebar.multiselect(
        label="開催地",
        options=local_options,
        default=default_value,
        label_visibility="hidden",
    )

    course_col, distance_col = sidebar.columns(2)
    course_options = df["course"].unique().tolist()
    if pre_race["course"] in course_options:
        course_options = sorted(
            course_options, key=lambda x: x == pre_race["course"], reverse=True
        )
    course = course_col.selectbox(
        label="コース",
        options=course_options,
        label_visibility="hidden",
    )
    distance_options = df["distance"].unique().tolist()
    if pre_race["distance"] in distance_options:
        distance_options = sorted(
            distance_options, key=lambda x: x == pre_race["distance"], reverse=True
        )
    distance = distance_col.selectbox(
        label="距離",
        options=distance_options,
        label_visibility="hidden",
    )

    gcol1, gcol2, gcol3, gcol4 = sidebar.columns(4)
    ground_state = []
    if gcol1.toggle("良", value=True):
        ground_state.append("良")
    if gcol2.toggle("稍", value=True):
        ground_state.append("稍")
    if gcol3.toggle("重", value=True):
        ground_state.append("重")
    if gcol4.toggle("不", value=True):
        ground_state.append("不")

    end_date = datetime.date.today() - datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=500)
    date_range = sidebar.slider(
        label="日付",
        min_value=df["date"].min(),
        max_value=df["date"].max(),
        value=(start_date, end_date),
        format="YYYY-MM-DD",
        key="date_range",
        label_visibility="hidden",
    )
    duplicate_check = sidebar.checkbox(
        label="重複のみ",
        value=True,
    )
    df = df[
        (df["local"].isin(local))
        & (df["course"] == course)
        & (df["distance"] == distance)
        & (df["ground_state"].isin(ground_state))
        & (df["date"] >= date_range[0])
        & (df["date"] <= date_range[1])
    ]
    if duplicate_check:
        # date, local, course, distanceが重複しているすべての行を抽出
        duplicate_index = df.duplicated(
            subset=["date", "local", "course", "distance"], keep=False
        )
        df = df.loc[duplicate_index, :]
    return df


def get_pre_race_shutuba(race_id: str):
    """
    レース事前情報を取得する
    """
    driver = app.get_driver()
    mongo = app.get_mongo_client()
    app.upsert_pre_race_shutuba(driver, mongo, race_id, force=True)


def get_horse(horse_ids: list[str], get_type: list[str]):
    """
    過去戦績を取得する
    """
    driver = app.get_driver()
    mongo = app.get_mongo_client()
    for horse_id in horse_ids:
        driver = app.upsert_horse_data(driver, mongo, horse_id, get_type)


def get_human(human_ids: list[str], type: str):
    """
    騎手、調教師のプロフィールを取得する
    """
    driver = app.get_driver()
    mongo = app.get_mongo_client()
    for human_id in human_ids:
        app.upsert_human_data(driver, mongo, human_id, type)


def update_data(container: DeltaGenerator, race_id: str):
    """
    データを更新する
    """
    select_col, update_col = container.columns([4, 1])
    update_is, get_type = [], []
    select_exp = select_col.expander("更新するデータ", expanded=False)
    if select_exp.checkbox("レース", value=True):
        update_is.append("race")
    if select_exp.checkbox("馬・騎手・調教師", value=False):
        get_type.append("profile")
        update_is.append("human")
    if select_exp.checkbox("馬の戦績", value=False):
        get_type.append("result")
    if select_exp.checkbox("血統", value=False):
        get_type.append("pedigree")

    if update_col.button("更新"):
        if len(update_is) < 1 and len(get_type) < 1:
            st.toast("更新するデータを選択してください。")
        if "race" in update_is:
            get_pre_race_shutuba(race_id)
            st.toast("レース情報を更新しました。")
        if len(get_type) > 0:
            horse_ids = app.find_horse_ids(race_id)
            get_horse(horse_ids, get_type)
            st.toast("馬情報を更新しました。")
        if "human" in update_is:
            jockey_ids = app.find_jockey_ids(race_id)
            get_human(jockey_ids, "jockey")
            st.toast("騎手情報を更新しました。")
            trainer_ids = app.find_trainer_ids(race_id)
            get_human(trainer_ids, "trainer")
            st.toast("調教師情報を更新しました。")


def display_pre_race(container: DeltaGenerator, race_id: str, pre_race):
    """
    レース事前情報を表示する
    """
    info_col, update_col = container.columns([3, 1])
    expander = info_col.expander(
        f"{pre_race['local']} | {pre_race['_id'][-2:]}R | {pre_race['date'][-5:]}",
        expanded=False,
    )

    # レース情報の更新
    update_data(update_col, race_id)

    expander.info(pre_race["race_name"])
    if "weather" not in pre_race.keys():
        pre_race["weather"] = "－"
    if "ground_state" not in pre_race.keys():
        pre_race["ground_state"] = "－"
    expander.write(f"- {pre_race['weather']}")
    expander.write(
        f"- {pre_race['around']} | {pre_race['course']} | {pre_race['distance']}m | {pre_race['ground_state']} | {pre_race['number_of_horses']}頭"
    )
    expander.write(f"- {pre_race['grade']} | {pre_race['prize']}万円")


def display_shutuba(container: DeltaGenerator, shutuba: pd.DataFrame):
    """
    出馬表を表示する
    """
    exp = container.expander("出馬表", expanded=False)
    shutuba["jin"] = shutuba["jin"].apply(lambda x: str(round(x, 1)))
    exp.table(
        data=shutuba,
    )


def display_result(df: pd.DataFrame):
    """
    過去戦績をテーブルで表示する
    馬番カラムは、背景色を馬番ごとに変える
    """
    display_df = df.copy()
    umaban_list = df["馬番"].unique().tolist()
    umaban_list = sorted(umaban_list, key=lambda x: int(x))
    color_palette = px.colors.qualitative.D3
    color_discrete_map = {
        str(umaban): color_palette[i % len(color_palette)]
        for i, umaban in enumerate(umaban_list)
    }

    display_df = display_df.loc[
        :,
        [
            "weather",
            "number_of_horses",
            "date",
            "ground_state",
            "馬番",
            "jockey",
            "umaban",
            "order_of_finish",
            "time",
            "difference",
            "passing",
            "pace",
            "up",
        ],
    ]
    display_df.columns = [
        "天候",
        "頭数",
        "日付",
        "馬場",
        "馬番",
        "騎手",
        "前番",
        "着順",
        "タイム",
        "着差",
        "通過",
        "ペース",
        "上り",
    ]
    display_html = display_df.to_html(index=False)
    len_df = len(display_df)
    cell_style_str = "color: #ffffff; border: 0;"
    for column in display_df.columns:
        display_html = display_html.replace(
            f"<th>{column}</th>",
            f'<th sorttable_customkey="{column}" onclick="sortTable({display_df.columns.tolist().index(column)})" style="{cell_style_str}">{column}</th>',
        )

    table_html = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
    }
    th {
        background-color: #2c2c2c;
        color: white;
    }
    th, td {
        text-align: left;
        padding: 8px;
        color: #ffffff;
    }
    tr:nth-child(4n) {
        background-color: #1f1f1f;
    }
    tr:hover {
        background-color: #3e3e3e;
    }
    </style>
    <script>
    function sortTable(n) {
        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
        table = document.getElementsByTagName("table")[0];
        switching = true;
        dir = "asc";
        while (switching) {
            switching = false;
            rows = table.rows;
            for (i = 1; i < (rows.length - 1); i++) {
                shouldSwitch = false;
                x = rows[i].getElementsByTagName("td")[n];
                y = rows[i + 1].getElementsByTagName("td")[n];
                if (dir == "asc") {
                    if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                        shouldSwitch = true;
                        break;
                    }
                } else if (dir == "desc") {
                    if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                        shouldSwitch = true;
                        break;
                    }
                }
            }
            if (shouldSwitch) {
                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                switching = true;
                switchcount++;
            } else {
                if (switchcount == 0 && dir == "asc") {
                    dir = "desc";
                    switching = true;
                }
            }
        }
    }
    </script>
    """
    for cnt, td in enumerate(display_html.split("</td>")):
        if cnt / 13 >= len_df:
            break
        if cnt % 13 == 4:
            umaban = td.split(">")[-1]
            td = td.replace(
                f">{umaban}",
                f' style="background-color: {color_discrete_map[umaban]};">{umaban}',
            )
        table_html += td + "</td>"
    components.html(table_html, height=650, width=1000, scrolling=True)


def plot_result(df: pd.DataFrame):
    """
    過去戦績をプロットする
    """
    umaban_list = df["馬番"].unique().tolist()
    umaban_list = sorted(umaban_list, key=lambda x: int(x))

    # 色とシンボルの設定
    color_palette = px.colors.qualitative.D3
    color_discrete_map = {
        umaban: color_palette[i % len(color_palette)]
        for i, umaban in enumerate(umaban_list)
    }
    symbol_map = {umaban: "circle" if umaban < 10 else "x" for umaban in umaban_list}

    # グラフの設定
    fig = go.Figure()

    # 馬番ごとにデータをプロット
    for umaban in umaban_list:
        df_filtered = df[df["馬番"] == umaban].sort_values("date", ascending=True)
        hover_text = [
            f"{umaban} {jockey}<br>{date} {local}<br>{time:.2f}秒<br>{ground_state} {course} {distance}"
            for date, local, time, ground_state, course, distance, jockey in zip(
                df_filtered["date"],
                df_filtered["local"],
                df_filtered["time"],
                df_filtered["ground_state"],
                df_filtered["course"],
                df_filtered["distance"],
                df_filtered["jockey"],
            )
        ]
        if len(df_filtered) < 1:
            # 折れ線グラフのトレースを追加
            fig.add_trace(
                go.Scatter(
                    x=df_filtered["date"],
                    y=df_filtered["time"],
                    mode="lines+markers",
                    name=f"{umaban}",
                    line=dict(color=color_discrete_map[umaban]),
                    marker=dict(symbol=symbol_map[umaban]),
                    text=hover_text,
                    hoverinfo="text",
                )
            )
        else:
            # 散布図のトレースを追加
            fig.add_trace(
                go.Scatter(
                    x=df_filtered["date"],
                    y=df_filtered["time"],
                    mode="markers",
                    name=f"{umaban}",
                    marker=dict(
                        color=color_discrete_map[umaban],
                        symbol=symbol_map[umaban],
                    ),
                    text=hover_text,
                    hoverinfo="text",
                )
            )

    # レイアウトの設定
    fig.update_layout(
        xaxis_title="日付",
        yaxis_title="タイム",
        legend_title="馬番",
        height=650,
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(
        tickformat="%Y-%m",
        dtick="M1",
        ticklabelmode="period",
        ticklabelposition="outside top",
    )
    # プロット
    st.plotly_chart(fig, use_container_width=True)


#########
# utils #
#########


def main():
    today = page_config()
    if not exists_current_date_races(today):
        st.warning(f"{today}のレースはまだ登録されていません。")
        st.info("レースの登録はサイドバーの「database」から行えます。")
        st.stop()
    else:
        race_id = select_current_race_id(st.container(), today)
        pre_race = find_current_pre_race(race_id)
        display_pre_race(st.container(), race_id, pre_race)
        shutuba = find_current_shutuba(race_id=race_id)
        display_shutuba(st.container(), shutuba)
        result_df = find_results(race_id, "horse")

        n = st.select_slider(label="重複数", options=range(1, 10, 1), value=3)
        duplicate_df = find_duplicate_other(pre_race, result_df, "horse", n)
        combined_df = pd.concat([result_df, duplicate_df])
        st.dataframe(
            data=combined_df.drop(columns=["_id", "race_id", "horse_id"]),
            hide_index=True,
        )
        df = config_result_df(st.sidebar, pre_race, combined_df)
        if len(df) < 1:
            st.warning("条件に合う過去戦績がありません。")
            st.stop()
        display_result(df)
        plot_result(df)


if __name__ == "__main__":
    main()

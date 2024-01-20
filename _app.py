from modules.scrape import (
    WebDriver,
    RaceIdGetter,
    GetPreData,
    GetResultData,
    GetHorseData,
)
from modules.database import ConnectMongoDB, InsertData, FindData
from modules.constants import RACEDATA
import datetime
import pandas as pd
from matplotlib import pyplot as plt, dates as mdates


###########
# find db #
###########


def get_mongo_client():
    return ConnectMongoDB().client


def get_day_race_ids(date: datetime.date) -> dict:
    """
    日付からレースIDを取得する
    """
    # レースIDの取得
    mongo = ConnectMongoDB()
    find = FindData(mongo.client)
    race_ids = find.find_race_ids(date, date)
    # dateのレースIDを取得
    race_ids = [race_id for race_id in race_ids if race_id[8:10] == str(date.day)]
    local_race_ids = {}
    for race_id in race_ids:
        local_code = race_id[4:6]
        local_name = RACEDATA.LOCALCODE_NAME[str(local_code)]
        # local_race_idsにlocal_nameがない場合は追加
        local_race_ids.setdefault(local_name, [])
        # 開催場ごとにレースIDを格納
        local_race_ids[local_name].append(race_id)
    return local_race_ids


def get_horse_ids(start_date: datetime.date, end_date: datetime.date):
    """
    日付からレースIDを取得し、そのレースIDから馬IDを取得する
    """
    find = FindData(ConnectMongoDB().client)
    race_ids = find.find_race_ids(start_date, end_date)
    horse_ids = []
    for race_id in race_ids:
        horse_id = find.find_horse_ids(race_id)
        horse_ids.extend(horse_id)
    return list(set(horse_ids))  # 重複を削除


def get_pre_race_data(race_id: str):
    """
    レースIDからレース事前情報を取得する
    """
    mongo = ConnectMongoDB()
    find = FindData(mongo.client)

    # レース情報
    return find.find_pre_race_data(race_id)


def find_horse_result_data(horse_ids: list[str]):
    """
    馬の過去戦績を取得する
    """
    mongo = ConnectMongoDB()
    find = FindData(mongo.client)
    combined_df = pd.DataFrame()
    for num, horse_id in enumerate(horse_ids, 1):
        result = find.find_horse_result(horse_id)
        result["馬番"] = num
        combined_df = pd.concat([combined_df, result])
    # order_of_finishがint以外の場合（除外、中止など）は除外
    if "order_of_finish" in combined_df.columns:
        combined_df = combined_df[
            combined_df["order_of_finish"].apply(lambda x: isinstance(x, int))
        ]
    return combined_df


###############
# render plot #
###############


def plot_horse_result(result_df):
    """
    馬のレース結果をプロットする
    """
    result_df["date"] = pd.to_datetime(result_df["date"])
    result_df["time"] = convert_time_to_second(result_df["time"])
    result_df = result_df[result_df["time"] != 0]

    # グラフの設定
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_subplot(111)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    unique_dates = result_df["date"].unique()
    if len(unique_dates) > 1:
        ax.set_xlim(result_df["date"].min(), result_df["date"].max())
    else:
        ax.set_xlim(
            unique_dates[0] - pd.Timedelta(days=1),
            unique_dates[0] + pd.Timedelta(days=1),
        )
    ax.set_ylim(result_df["time"].min() - 0.2, result_df["time"].max() + 0.2)
    ax.tick_params(colors="white", labelsize=6)

    colors = [f"C{i}" for i in range(24)]
    marks = ["o", "v", "s"]

    # 馬番ごとにデータをプロット
    result_df.sort_values(by=["馬番", "date"], inplace=True)
    for umaban in result_df["馬番"].unique():
        df = result_df[result_df["馬番"] == umaban]
        if len(df) > 1:
            # データが複数ある場合は線でプロット
            ax.plot(
                df["date"],
                df["time"],
                color=colors[umaban % 24 - 1],
                label=f"{umaban}",
                marker=marks[(umaban // 10) % 3 - 1],
                # linewidth=2,
            )
        else:
            # データが一つしかない場合は点でプロット
            ax.scatter(
                df["date"],
                df["time"],
                color=colors[umaban % 24 - 1],
                s=50,
                zorder=10,
                label=f"{umaban}",
                marker=marks[(umaban // 10) % 3 - 1],
            )

    # 軸の設定
    ax.invert_yaxis()
    ax.grid(axis="both", color="grey", alpha=0.2)
    legend_colors = [f"C{i - 1}" for i in result_df["馬番"].unique()]
    legend = ax.legend(
        loc="upper left",
        bbox_to_anchor=(1, 1),
        frameon=False,
        handletextpad=0,
        labelcolor=legend_colors,
    )
    legend.get_frame().set_alpha(0.05)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

    return fig


#########
# utils #
#########


def convert_time_to_second(time_column: pd.Series):
    """
    タイムを秒に変換する
    """
    # タイムがない場合は何もしない
    _time_column = time_column.fillna("0:0:0")

    time_split = _time_column.str.split(":")
    if len(time_split) == 1:
        if isinstance(time_split, float):
            minute_to_second = 0
            second = time_split.apply(lambda x: float(x[0]))
        else:
            minute_to_second, second = 0, 0
    else:
        minute_to_second = time_split.apply(lambda x: int(x[0]) * 60)
        second = time_split.apply(lambda x: float(x[1]))

    return minute_to_second + second


def strftime_to_date(date: datetime.date):
    return datetime.datetime.strptime(str(date), "%Y-%m-%d").date()

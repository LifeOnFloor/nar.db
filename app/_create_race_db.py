from modules.database import InsertData, FindData
from modules.scrape import GetPreData
import pandas as pd


def convert_date(race_id: str, time: str) -> str:
    """
    日付をstr型に変換する
    """
    return f"{race_id[:4]}-{race_id[6:8]}-{race_id[8:10]} {time}"


def upsert_shutuba_row(mongo, row, race_id: str):
    """
    一行の出馬表データをDBに格納する
    """
    try:
        find = FindData(mongo)
        if find.exists_shutuba(race_id, row["馬番"]):
            return
        insert = InsertData(mongo)
        insert.upsert_shutuba(
            race_id=race_id,
            umaban=row["馬番"],
            horse_id=row["horse_id"],
            jin=row["斤量"],
            jockey_id=row["jockey_id"],
            trainer_id=row["trainer_id"],
            weight=row["馬体重(増減)"],
        )
    except Exception as e:
        raise Exception(f"Error upserting shutuba row : {e}")


def upsert_many_shutuba(insert, race_id: str, df: pd.DataFrame):
    """
    出馬表データを一括挿入する
    """
    try:
        if df.empty:
            return

        insert_data = df.apply(
            lambda row: {
                "race_id": race_id,
                "umaban": row["馬番"],
                "horse_id": row["horse_id"],
                "jin": row["斤量"],
                "jockey_id": row["jockey_id"],
                "trainer_id": row["trainer_id"],
                "weight": row["馬体重(増減)"],
            },
            axis=1,
        ).tolist()
        insert.upsert_many_shutuba(insert_data)
    except Exception as e:
        raise Exception(f"Error upserting many shutuba : {e}")


def upsert_pre_race(insert, pre_data, race_id: str):
    """
    レースの事前情報を取得してDBに格納する
    """
    try:
        if "-" in pre_data["ground_state"]:
            pre_data["ground_state"] = ""
        insert.upsert_pre_race(
            race_id=race_id,
            race_name=pre_data["race_name"],
            date=convert_date(race_id, pre_data["date"]),
            course=pre_data["course"],
            distance=pre_data["distance"],
            around=pre_data["around"] if "around" in pre_data else "",
            weather=pre_data["weather"] if "weather" in pre_data else "",
            ground_state=pre_data["ground_state"] if "ground_state" in pre_data else "",
            local=pre_data["local"],
            grade=pre_data["grade"] if "grade" in pre_data else "",
            number_of_horses=pre_data["number_of_horses"],
            prize=pre_data["prize"] if "prize" in pre_data else 0,
        )
    except Exception as e:
        raise Exception(f"Error upserting pre race : {e}")


def upsert_pre_race_shutuba(driver, mongo, race_id: str, force: bool = False):
    """
    レースの事前情報と出馬表を取得してDBに格納する
    """
    try:
        find = FindData(mongo)
        insert = InsertData(mongo)
        get_pre_data = GetPreData(driver, race_id)

        # レースの事前情報をDBに格納
        if not find.exists_pre_race(race_id) or force:
            pre_race = get_pre_data.get_pre_data()
            upsert_pre_race(insert, pre_race, race_id)

        # 出馬表データをDBに一括挿入
        shutuba = get_pre_data.get_shutba_table()
        if force:
            upsert_many_shutuba(insert, race_id, shutuba)
        else:
            to_insert = shutuba[
                ~shutuba["馬番"].apply(
                    lambda umaban: find.exists_shutuba(race_id, umaban)
                )
            ]
            upsert_many_shutuba(insert, race_id, to_insert)
    except Exception as e:
        raise Exception(f"upserting pre race shutuba : {e}")
    return get_pre_data.driver

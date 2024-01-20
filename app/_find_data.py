from modules.database import FindData
import app
import pandas as pd


def find_result_from_ids(ids: dict, type: str) -> pd.DataFrame:
    """
    レース結果を取得する
    """
    mongo = app.get_mongo_client()
    find = FindData(mongo)
    df = find.find_result_from_ids(ids, type)
    # order_of_finishが除外、中止などの場合は除外
    if "order_of_finish" in df.columns:
        df = df[df["order_of_finish"].apply(lambda x: isinstance(x, (int, float)))]
    return df


def find_duplicate_other(
    shutuba_ids: list, target_ids: list, type: str, n: int
) -> pd.DataFrame:
    """
    レース結果を取得する
    """
    if type not in ["horse", "jockey", "trainer"]:
        raise Exception(f"Error type: {type}")
    mongo = app.get_mongo_client()
    find = FindData(mongo)
    ids = find.find_duplicate(shutuba_ids, type, n)
    ids = list(set(ids) - set(target_ids))
    if len(ids) == 0:
        return pd.DataFrame()
    else:
        pre_fix = 10 ** (len(type) - 3)
        ids = {v: f"{pre_fix + k}" for k, v in enumerate(ids, 1)}
    return find.find_result_from_ids(ids, type)


def find_shutuba(race_id: str) -> pd.DataFrame:
    """
    出馬表を取得する
    """
    mongo = app.get_mongo_client()
    find = FindData(mongo)
    return find.find_shutuba(race_id)


def find_pre_race(race_id: str):
    """
    レース事前情報を取得する
    """
    mongo = app.get_mongo_client()
    find = FindData(mongo)
    return find.find_pre_race(race_id)

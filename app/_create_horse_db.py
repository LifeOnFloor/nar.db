from modules.scrape import GetHorseData
from modules.database import InsertData, FindData
from modules.constants import RACEDATA
import pandas as pd
from app._prepare_id import generate_race_id


def get_horse_profile(get_horse_data) -> dict:
    """
    馬のプロフィールを取得する
    """
    try:
        return get_horse_data.get_horse_profile()
    except Exception as e:
        raise Exception(f"Error getting horse profile: {e}")


def get_horse_pedigree(get_horse_data) -> dict:
    """
    馬の血統データを取得する
    """
    try:
        return get_horse_data.get_horse_pedigree()
    except Exception as e:
        raise Exception(f"Error getting horse pedigree: {e}")


def get_horse_result(get_horse_data) -> pd.DataFrame:
    """
    馬の過去戦績を取得する
    """
    try:
        return get_horse_data.get_horse_result()
    except Exception as e:
        raise Exception(f"Error getting horse result: {e}")


def format_horse_result(df: pd.DataFrame) -> pd.DataFrame:
    """
    馬の過去戦績を整形する
    """
    try:
        df.columns = RACEDATA.HORSE_RESULT_COLUMNS_EN
        df["course"] = df["distance"].apply(lambda x: x[0])
        df["distance"] = df["distance"].apply(lambda x: x[1:])
        df["race_id"] = df.loc[:, ["date", "local", "r"]].apply(
            lambda row: generate_race_id(
                row["date"],
                row["local"],
                row["r"],
            ),
            axis=1,
        )
        df["date"] = df["date"].apply(lambda row: row.replace("/", "-"))
        return df
    except Exception as e:
        raise Exception(f"Error formatting horse result: {e}")


def upsert_horse_profile(insert, horse_id: str, profile_data):
    """
    馬のプロフィールをDBに格納する
    """
    try:
        insert.upsert_horse_data(
            horse_id=horse_id,
            name=profile_data["馬名"],
            birthday=profile_data["生年月日"],
            trainer_id=profile_data["trainer_id"],
            owner=profile_data["馬主"],
            breeder=profile_data["生産者"],
            origin=profile_data["産地"],
            price=profile_data["セリ取引価格"],
        )
    except Exception as e:
        raise Exception(f"Error upserting horse profile horse_id={horse_id}: {e}")


def upsert_horse_pedigree(insert, horse_id: str, pedigree_data):
    """
    馬の血統データをDBに格納する
    """
    try:
        insert.upsert_horse_pedigree(
            horse_id=horse_id,
            pedigree_data=pedigree_data,
        )
    except Exception as e:
        raise Exception(f"Error upserting horse pedigree horse_id={horse_id}: {e}")


def upsert_horse_result(insert, horse_id: str, result_data: pd.DataFrame):
    """
    馬の過去戦績をresult_data, pre_race, shutubaに分けてDBに格納する
    """
    try:
        if len(result_data) == 0:
            return
        to_insert_result_race = result_data.loc[
            :,
            RACEDATA.RESULT_COLUMNS_FOR_HORSE_PAGE,
        ].to_dict(orient="records")

        to_insert_pre_race = result_data.loc[
            :,
            RACEDATA.PRE_RACE_COLUMNS_FOR_HORSE_PAGE,
        ]
        to_insert_pre_race.columns = RACEDATA.FORMATTED_PRE_RACE_COLUMNS_FOR_HORSE_PAGE
        to_insert_pre_race = to_insert_pre_race.to_dict(orient="records")

        to_insert_shutuba = result_data.loc[
            :,
            RACEDATA.SHUTUBA_COLUMNS_FOR_HORSE_PAGE,
        ]
        to_insert_shutuba["horse_id"] = horse_id
        to_insert_shutuba = to_insert_shutuba.to_dict(orient="records")

        insert.upsert_many_result(to_insert_result_race)
        insert.upsert_many_pre_race(to_insert_pre_race)
        insert.upsert_many_shutuba(to_insert_shutuba)

    except Exception as e:
        raise Exception(f"Error upserting horse result horse_id={horse_id}: {e}")


def upsert_horse_data(
    driver,
    mongo,
    horse_id: str,
    get_type: list[str] = ["profile", "pedigree", "result"],
):
    """
    馬のプロフィールと過去戦績を取得してDBに格納する
    """
    try:
        find = FindData(mongo)
        exist_horse_data = find.exists_horse_data(horse_id)
        exist_horse_pedigree = find.exists_horse_pedigree(horse_id)

        get_horse_data = None
        insert = InsertData(mongo)
        if "profile" in get_type and not exist_horse_data:
            if get_horse_data is None:
                get_horse_data = GetHorseData(driver, horse_id)
            horse_profile = get_horse_profile(get_horse_data)
            upsert_horse_profile(insert, horse_id, horse_profile)
        if "pedigree" in get_type and not exist_horse_pedigree:
            if get_horse_data is None:
                get_horse_data = GetHorseData(driver, horse_id)
            pedigree_data = get_horse_pedigree(get_horse_data)
            upsert_horse_pedigree(insert, horse_id, pedigree_data)
        if "result" in get_type:
            if get_horse_data is None:
                get_horse_data = GetHorseData(driver, horse_id)
            try:
                result_data = get_horse_result(get_horse_data)
            except Exception as e:
                # 過去戦績がない場合
                if "no text parsed from document" in str(e):
                    return get_horse_data.driver
                else:
                    raise Exception(f"Error getting horse result: {e}")
            formatted_result_data = format_horse_result(result_data)
            formatted_result_data["trainer_id"] = find.get_trainer_id_by_horse_id(
                horse_id
            )
            upsert_horse_result(insert, horse_id, formatted_result_data)

    except Exception as e:
        raise Exception(f"Error upserting horse data horse_id={horse_id}: {e}")
    if get_horse_data is None:
        return driver
    return get_horse_data.driver

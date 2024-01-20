from modules.scrape import RaceIdGetter, WebDriver
from modules.database import ConnectMongoDB, FindData
from modules.constants import RACEDATA
import datetime
import re


def get_driver():
    return WebDriver().driver()


def get_mongo_client():
    return ConnectMongoDB().client


def get_mongo_database():
    return ConnectMongoDB().get_database()


def create_index(
    create_collection: list[str] = [
        "shutuba",
        "result",
        "horse",
        "jockey",
        "trainer",
        "pedigree",
        "pre_race",
    ]
):
    """
    インデックスを作成する
    """
    ConnectMongoDB().create_index(create_collection)


def get_race_ids(start_date: datetime.date, end_date: datetime.date):
    """
    日付(期間)からレースIDを取得する
    """
    driver = WebDriver().driver()
    race_id_getter = RaceIdGetter(driver)
    return race_id_getter.get_race_ids(start_date, end_date)


def get_local_race_ids(driver, race_id: str):
    """
    レースIDから開催場とその開催場のレースIDを取得する
    """
    race_id_getter = RaceIdGetter(driver)
    return race_id_getter.get_local_race_ids(race_id), race_id_getter.driver


def generate_race_id(yyyymmdd: str, local_name: str, r: int):
    """
    レースIDを生成する
    WARNING: 中央競馬のレースIDも地方競馬と同じく、yyyyllmmddrrの形式にしている。中央競馬のデータを取得する場合は注意
    """
    try:
        date = re.sub(r"\D", "", yyyymmdd)
        local_name = re.sub(r"\d", "", local_name)
        local_code = RACEDATA.LOCALNAME_CODE[local_name]
        if not isinstance(r, int):
            r = 0
        return f"{date[:4]}{local_code}{date[4:]}{int(r):02d}"
    except Exception as e:
        raise Exception(
            f"Error generating race id date:{yyyymmdd}, local_name:{local_name}, r:{r} : {e}"
        )


def find_race_ids_by_date(date: datetime.date):
    """
    日付からレースIDを取得する
    """
    mongo = ConnectMongoDB().client
    find = FindData(mongo)
    return find.get_race_ids_by_date(date, date)


def find_horse_ids(race_id: str):
    """
    レースIDから馬IDを取得する
    """
    mongo = ConnectMongoDB().client
    find = FindData(mongo)
    return find.get_horse_ids_by_race(race_id)


def find_jockey_ids(race_id: str):
    """
    レースIDから騎手IDを取得する
    """
    mongo = ConnectMongoDB().client
    find = FindData(mongo)
    return find.get_jockey_ids_by_race(race_id)


def find_trainer_ids(race_id: str):
    """
    レースIDから調教師IDを取得する
    """
    mongo = ConnectMongoDB().client
    find = FindData(mongo)
    return find.get_trainer_id_by_race(race_id)


def find_horse_ids_from_date(start_date: datetime.date, end_date: datetime.date):
    """
    日付からレースIDを取得し、そのレースIDから馬IDを取得する
    """
    try:
        mongo = ConnectMongoDB().client
        find = FindData(mongo)
        race_ids = find.get_race_ids_by_date(start_date, end_date)
        horse_id_list = []
        for race_id in race_ids:
            horse_ids = find.get_horse_ids_by_race(race_id)
            horse_id_list.extend(horse_ids)
        return list(set(horse_id_list))  # 重複を削除
    except Exception as e:
        raise Exception(
            f"Error finding horse ids from date {start_date} to {end_date}: {e}"
        )


def find_human_ids_for_db(type: str):
    """
    日付から騎手ID・調教師IDを取得する
    """
    try:
        mongo = ConnectMongoDB().client
        find = FindData(mongo)
        if type == "jockey":
            return find.get_jockey_ids_for_db()
        elif type == "trainer":
            return find.get_trainer_ids_for_db()
        else:
            raise Exception(f"Invalid type {type}. type must be jockey or trainer")
    except Exception as e:
        raise Exception(f"Error finding human ids: {e}")


def local_code_to_name(local_code: str):
    """
    開催場コードから開催場名を取得する
    """
    try:
        return RACEDATA.LOCALCODE_NAME[local_code]
    except Exception as e:
        raise Exception(f"Error converting local code {local_code} to name: {e}")

from modules.scrape import GetHumanData
from modules.database import InsertData, FindData


def upsert_human_data(
    driver,
    mongo,
    human_id: str,
    type: str,
):
    """
    騎手・調教師のプロフィールをDBに格納する

    Parameters
    ----------
    driver : WebDriver
        WebDriver
    mongo : PyMongo
        PyMongo
    human_id : str
        騎手・調教師ID
    type : str | "jockey" or "trainer"
        騎手か調教師か
    """
    try:
        get_human_data = GetHumanData(driver)
        insert = InsertData(mongo)
        find = FindData(mongo)
        if type == "jockey":
            if find.exists_jockey(human_id):
                return get_human_data.driver
            human_profile = get_human_data.get_jockey_profile(human_id)
            insert.upsert_jockey_profile(human_id, human_profile)
        elif type == "trainer":
            if find.exists_trainer(human_id):
                return get_human_data.driver
            human_profile = get_human_data.get_trainer_profile(human_id)
            insert.upsert_trainer_profile(human_id, human_profile)
    except Exception as e:
        raise Exception(f"Error upserting human profile type={type} {human_id}: {e}")
    return get_human_data.driver

from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError


class InsertData:
    def __init__(self, client: MongoClient):
        self.client = client
        self.db = self.client["nar"]

    def upsert_document(self, collection, query, data):
        try:
            self.db[collection].update_one(query, {"$set": data}, upsert=True)
        except PyMongoError as e:
            raise PyMongoError(f"Error in upserting document in {collection}: {e}")

    def upsert_jockey_profile(self, jockey_id: str, jockey_profile: dict):
        """
        騎手のプロフィールをデータベースに挿入する
        """
        try:
            self.upsert_document("jockey", {"_id": jockey_id}, jockey_profile)
        except PyMongoError as e:
            raise PyMongoError(f"Error in upserting jockey profile: {e}")

    def upsert_trainer_profile(self, trainer_id: str, trainer_profile: dict):
        """
        調教師のプロフィールをデータベースに挿入する
        """
        try:
            self.upsert_document("trainer", {"_id": trainer_id}, trainer_profile)
        except PyMongoError as e:
            raise PyMongoError(f"Error in upserting trainer profile: {e}")

    def upsert_pre_race(
        self,
        race_id: str,
        race_name: str,
        date: str,
        course: str = "",
        distance: int = 0,
        around: str = "",
        weather: str = "",
        ground_state: str = "",
        local: str = "",
        grade: str = "",
        number_of_horses: int = 0,
        prize: float = 0.0,
    ):
        data = {
            "race_name": race_name,
            "date": date,
            "course": course,
            "distance": distance,
            "around": around,
            "weather": weather,
            "ground_state": ground_state,
            "local": local,
            "grade": grade,
            "number_of_horses": number_of_horses,
            "prize": prize,
        }
        data = {k: v for k, v in data.items() if v != "" and v != 0}
        self.upsert_document("pre_race", {"_id": race_id}, data)

    def upsert_shutuba(
        self,
        race_id: str,
        umaban: int,
        horse_id: str,
        jin: float = 0.0,
        jockey_id: str = "",
        trainer_id: str = "",
        weight: str = "",
    ):
        data = {
            "race_id": race_id,
            "umaban": umaban,
            "horse_id": horse_id,
            "jin": jin,
            "jockey_id": jockey_id,
            "trainer_id": trainer_id,
            "weight": weight,
        }
        data = {k: v for k, v in data.items() if v != "" and v != 0}
        self.upsert_document("shutuba", {"race_id": race_id, "umaban": umaban}, data)

    def upsert_result_race(
        self,
        race_id: str,
        umaban: int,
        order_of_finish: int = 0,
        time: str = "",
        difference: str = "",
        passing: str = "",
        pace: str = "",
        up: float = 0.0,
    ):
        data = {
            "race_id": race_id,
            "umaban": umaban,
            "order_of_finish": order_of_finish,
            "time": time,
            "difference": difference,
            "passing": passing,
            "pace": pace,
            "up": up,
        }
        data = {k: v for k, v in data.items() if v != "" and v != 0}
        self.upsert_document("result", {"race_id": race_id, "umaban": umaban}, data)

    def upsert_horse_data(
        self,
        horse_id: str,
        name: str,
        birthday: str,
        trainer_id: str = "",
        owner: str = "",
        breeder: str = "",
        origin: str = "",
        price: str = "",
    ):
        data = {
            "name": name,
            "birthday": birthday,
            "trainer_id": trainer_id,
            "owner": owner,
            "breeder": breeder,
            "origin": origin,
            "price": price,
        }
        data = {k: v for k, v in data.items() if v != ""}
        self.upsert_document("horse", {"_id": horse_id}, data)

    def upsert_horse_pedigree(self, horse_id, pedigree_data):
        """
        馬の血統データをデータベースに挿入する
        """
        try:
            self.upsert_document("pedigree", {"_id": horse_id}, pedigree_data)
        except PyMongoError as e:
            raise PyMongoError(f"Error in upserting horse pedigree data: {e}")

    def upsert_many_documents(self, collection, insert_data):
        """
        複数のドキュメントを特定のコレクションにアップサートする
        """
        try:
            operations = []
            for data in insert_data:
                query = (
                    {"_id": data["_id"]}
                    if "_id" in data
                    else {"race_id": data["race_id"], "umaban": data["umaban"]}
                )
                operation = UpdateOne(query, update={"$set": data}, upsert=True)
                operations.append(operation)
            if operations:
                self.db[collection].bulk_write(operations)
        except PyMongoError as e:
            raise PyMongoError(
                f"Error in upserting many documents in {collection}: {e}"
            )

    def upsert_many_pre_race(self, insert_data: list):
        """
        複数のレース事前情報をデータベースに挿入する
        """
        self.upsert_many_documents("pre_race", insert_data)

    def upsert_many_shutuba(self, insert_data: list):
        """
        複数の出馬表データをデータベースに挿入する
        """
        self.upsert_many_documents("shutuba", insert_data)

    def upsert_many_result(self, insert_data: list):
        """
        複数のレース結果データをデータベースに挿入する
        """
        self.upsert_many_documents("result", insert_data)

from pymongo import MongoClient, DESCENDING


class ConnectMongoDB:
    def __init__(self):
        self.db_name = "nar"
        self.client = MongoClient(
            host="localhost", port=27017, username="####", password="####"
        )

    def get_client(self):
        return self.client

    def get_database(self):
        return self.client[self.db_name]

    def get_collection(self, db_name, collection_name):
        return self.client[db_name][collection_name]

    def close(self):
        self.client.close()

    def create_index(
        self,
        create_collection: list = [
            "shutuba",
            "result",
            "horse",
            "jockey",
            "trainer",
            "pedigree",
            "pre_race",
        ],
    ):
        """
        インデックスを作成する
        """
        _valid_collection = list(
            set(create_collection) - set(self.get_database().list_collection_names())
        )
        if len(_valid_collection) > 0:
            raise Exception(
                f"Error in create_index: {','.join(_valid_collection)} is not valid collection name"
            )
        try:
            if "shutuba" in create_collection:
                shutuba_collection = self.get_collection(self.db_name, "shutuba")
                shutuba_collection.create_index(
                    keys=[("race_id", DESCENDING), "umaban"], name="shutuba_index"
                )
                shutuba_collection.create_index(
                    keys="race_id", name="shutuba_race_id_index"
                )
            if "result" in create_collection:
                result_collection = self.get_collection(self.db_name, "result")
                result_collection.create_index(
                    keys=[("race_id", DESCENDING), "umaban"], name="result_index"
                )
                result_collection.create_index(
                    keys="race_id", name="result_race_id_index"
                )
            if "horse" in create_collection:
                horse_collection = self.get_collection(self.db_name, "horse")
                horse_collection.create_index(keys="_id", name="horse_index")
            if "jockey" in create_collection:
                jockey_collection = self.get_collection(self.db_name, "jockey")
                jockey_collection.create_index(keys="_id", name="jockey_index")
            if "trainer" in create_collection:
                trainer_collection = self.get_collection(self.db_name, "trainer")
                trainer_collection.create_index(keys="_id", name="trainer_index")
            if "pedigree" in create_collection:
                pedigree_collection = self.get_collection(self.db_name, "pedigree")
                pedigree_collection.create_index(keys="_id", name="pedigree_index")
            if "pre_race" in create_collection:
                pre_race_collection = self.get_collection(self.db_name, "pre_race")
                pre_race_collection.create_index(keys="_id", name="pre_race_index")
        except Exception as e:
            raise Exception(f"Error in create_index: {e}")

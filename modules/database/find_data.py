from pymongo import MongoClient
from pymongo.errors import PyMongoError
import datetime
import pandas as pd
from modules.database import ConnectMongoDB


class FindData:
    def __init__(self, client: MongoClient):
        self.client = client
        self.db = self.client["nar"]

    def get_all_race_ids(self) -> list[str]:
        """
        すべてのレースIDを取得する。
        """
        try:
            races = self.db["pre_race"].find({}, {"_id": 1})
            return [race["_id"] for race in races]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding all race IDs: {e}")

    def get_all_horse_ids(self) -> list[str]:
        """
        すべての馬IDを取得する。
        """
        try:
            horses = self.db["horse"].find({}, {"_id": 1})
            return [horse["_id"] for horse in horses]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding all horse IDs: {e}")

    def get_all_jockey_ids(self) -> list[str]:
        """
        すべての騎手IDを取得する。
        """
        try:
            jockeys = self.db["jockey"].find({}, {"_id": 1})
            return [jockey["_id"] for jockey in jockeys]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding all jockey IDs: {e}")

    def get_all_trainer_ids(self) -> list[str]:
        """
        すべての調教師IDを取得する。
        """
        try:
            trainers = self.db["trainer"].find({}, {"_id": 1})
            return [trainer["_id"] for trainer in trainers]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding all trainer IDs: {e}")

    def get_horse_ids_by_race(self, race_id: str) -> list[str]:
        """
        特定のレースIDに基づいて馬のIDを取得する。
        """
        try:
            shutubas = self.db["shutuba"].find({"race_id": race_id}, {"horse_id": 1})
            return [shutuba["horse_id"] for shutuba in shutubas]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding horse IDs for race {race_id}: {e}")

    def get_jockey_ids_by_race(self, race_id: str) -> list[str]:
        """
        特定のレースIDに基づいて騎手のIDを取得する。
        """
        try:
            shutubas = self.db["shutuba"].find({"race_id": race_id}, {"jockey_id": 1})
            return [shutuba["jockey_id"] for shutuba in shutubas]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding jockey IDs for race {race_id}: {e}")

    def get_trainer_id_by_race(self, race_id: str) -> list[str]:
        """
        特定のレースIDに基づいて調教師のIDを取得する。
        """
        try:
            shutubas = self.db["shutuba"].find({"race_id": race_id}, {"trainer_id": 1})
            return [shutuba["trainer_id"] for shutuba in shutubas]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding trainer IDs for race {race_id}: {e}")

    def get_race_ids_by_date(
        self, start_date: datetime.date, end_date: datetime.date
    ) -> list[str]:
        """
        指定された日付範囲内のレースIDを取得する。
        """
        try:
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            query = {
                "date": {
                    "$gte": f"{start_date_str} 00:00",
                    "$lte": f"{end_date_str} 23:59",
                }
            }
            races = self.db["pre_race"].find(query, {"_id": 1})
            return [race["_id"] for race in races]
        except PyMongoError as e:
            raise PyMongoError(
                f"Error finding race IDs between {start_date} and {end_date}: {e}"
            )

    def get_jockey_ids_for_db(self) -> list[str]:
        """
        shutubaに存在し、jockeyに存在しない騎手IDを取得する。
        """
        try:
            shutubas = self.db["shutuba"].distinct("jockey_id")
            jockeys = self.db["jockey"].distinct("_id")
            return list(set(shutubas) - set(jockeys) - set([""]))
        except PyMongoError as e:
            raise PyMongoError(f"Error finding jockey IDs by shutuba: {e}")

    def get_trainer_ids_for_db(self) -> list[str]:
        """
        shutubaに存在し、trainerに存在しない調教師IDを取得する。
        """
        try:
            shutubas = self.db["shutuba"].distinct("trainer_id")
            trainers = self.db["trainer"].distinct("_id")
            return list(set(shutubas) - set(trainers) - set([""]))
        except PyMongoError as e:
            raise PyMongoError(f"Error finding trainer IDs by shutuba: {e}")

    def get_trainer_id_by_horse_id(self, horse_id: str) -> str:
        """
        特定の馬IDに基づいて調教師IDを取得する。
        """
        try:
            horse = self.db["horse"].find_one({"_id": horse_id}, {"trainer_id": 1})
            if horse:
                return horse["trainer_id"]
            else:
                raise Exception(f"Trainer ID not found for horse {horse_id}")
        except PyMongoError as e:
            raise PyMongoError(f"Error finding trainer ID for horse {horse_id}: {e}")

    def exists_jockey(self, jockey_id: str) -> bool:
        """
        特定の騎手IDがjockeyに存在するか確認する。
        """
        try:
            return self.db["jockey"].count_documents({"_id": jockey_id}) > 0
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking existence of jockey ID {jockey_id}: {e}"
            )

    def exists_trainer(self, trainer_id: str) -> bool:
        """
        特定の調教師IDがtrainerに存在するか確認する。
        """
        try:
            return self.db["trainer"].count_documents({"_id": trainer_id}) > 0
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking existence of trainer ID {trainer_id}: {e}"
            )

    def exists_pre_race(self, race_id: str) -> bool:
        """
        特定のレースIDが存在するか確認する。
        """
        try:
            return self.db["pre_race"].count_documents({"_id": race_id}) > 0
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking existence of pre race ID {race_id}: {e}"
            )

    def exists_shutuba(self, race_id: str, umaban: int) -> bool:
        """
        特定のレースIDと馬番が存在するか確認する。
        """
        try:
            return (
                self.db["shutuba"].count_documents(
                    {"race_id": race_id, "umaban": umaban}
                )
                > 0
            )
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking existence of shutuba ID {race_id}, umaban {umaban}: {e}"
            )

    def exists_horse_data(self, horse_id: str) -> bool:
        """
        特定の馬IDがhorseに存在するか確認する。
        """
        try:
            return self.db["horse"].count_documents({"_id": horse_id}) > 0
        except PyMongoError as e:
            raise PyMongoError(f"Error checking existence of horse ID {horse_id}: {e}")

    def exists_result_after_date(self, horse_id: str, date: datetime.date) -> bool:
        """
        特定の馬IDと日付に基づいて、resultに存在するか確認する。
        """
        try:
            pipeline = [
                {"$match": {"horse_id": horse_id}},
                {
                    "$lookup": {
                        "from": "result",
                        "localField": "race_id",
                        "foreignField": "race_id",
                        "as": "race_results",
                    }
                },
                {
                    "$lookup": {
                        "from": "pre_race",
                        "localField": "race_id",
                        "foreignField": "_id",
                        "as": "race_info",
                    }
                },
                {"$unwind": "$race_results"},
                {"$unwind": "$race_info"},
                {
                    "$project": {
                        "date": "$race_info.date",
                    }
                },
            ]
            results = self.db["shutuba"].aggregate(pipeline)
            df = pd.DataFrame(results)
            df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=True)
            return (df["date"] > date).any()
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking existence of result after date {date} for horse ID {horse_id}: {e}"
            )

    def exists_horse_pedigree(self, horse_id: str) -> bool:
        """
        特定の馬IDがpedigreeに存在するか確認する。
        """
        try:
            return self.db["pedigree"].count_documents({"_id": horse_id}) > 0
        except PyMongoError as e:
            raise PyMongoError(f"Error checking existence of horse ID {horse_id}: {e}")

    def check_documents_existence(
        self, collection: str, query_list: list[dict]
    ) -> list[dict]:
        """
        指定したコレクション内で、複数のクエリに一致するドキュメントが存在するか確認する。
        """
        try:
            exist_list = []
            for query in query_list:
                document = self.db[collection].find_one(query, {"_id": 1})
                exist_list.append(
                    {"query": query, "_id": document["_id"] if document else None}
                )
            return exist_list
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking documents existence in {collection}: {e}"
            )

    def shutuba_weight_exists(self, race_id: str, umaban: int) -> bool:
        """
        特定のレースIDと馬番に体重データが存在するか確認する。
        """
        try:
            return (
                self.db["shutuba"].count_documents(
                    {"race_id": race_id, "umaban": umaban, "weight": {"$exists": True}}
                )
                > 0
            )
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking if weight exists for shutuba ID {race_id} umaban {umaban}: {e}"
            )

    def complete_race_result_exists(self, race_id: str, umaban: int) -> bool:
        """
        レース結果の完全版が特定のレースIDと馬番で存在するか確認する。
        """
        try:
            return (
                self.db["result"].count_documents(
                    {
                        "race_id": race_id,
                        "umaban": umaban,
                        "order_of_finish": {"$exists": True},
                        "passing": {"$ne": ""},
                    }
                )
                > 0
            )
        except PyMongoError as e:
            raise PyMongoError(
                f"Error checking if complete race result exists for ID {race_id} umaban {umaban}: {e}"
            )

    def find_pre_race(self, race_id: str):
        """
        特定のレースIDに基づいて、レースの事前情報を取得する。
        """
        try:
            return self.db["pre_race"].find_one({"_id": race_id})
        except PyMongoError as e:
            raise PyMongoError(f"Error finding pre race data for {race_id}: {e}")

    def find_shutuba(self, race_id: str) -> pd.DataFrame:
        """
        レースIDに基づいて、レース情報と出馬表情報を結合して取得する。
        """
        try:
            pipeline = [
                {"$match": {"race_id": race_id}},
                {
                    "$lookup": {
                        "from": "horse",
                        "localField": "horse_id",
                        "foreignField": "_id",
                        "as": "horse_data",
                    }
                },
                {
                    "$lookup": {
                        "from": "jockey",
                        "localField": "jockey_id",
                        "foreignField": "_id",
                        "as": "jockey_data",
                    }
                },
                {
                    "$lookup": {
                        "from": "trainer",
                        "localField": "trainer_id",
                        "foreignField": "_id",
                        "as": "trainer_data",
                    }
                },
                {"$unwind": "$horse_data"},
                {"$unwind": "$jockey_data"},
                {"$unwind": "$trainer_data"},
                {
                    "$project": {
                        "umaban": "$umaban",
                        "horse": "$horse_data.name",
                        "jin": "$jin",
                        "jockey": "$jockey_data.name",
                        "trainer": "$trainer_data.name",
                        "weight": "$weight",
                    }
                },
            ]
            results = self.db["shutuba"].aggregate(pipeline)
            return pd.DataFrame(results)
        except PyMongoError as e:
            raise PyMongoError(f"Error finding shutuba data for {race_id}: {e}")

    def _part_of_pipeline_lookup(
        self, type: str, pre_race: bool, result: bool
    ) -> list[dict]:
        """
        パイプラインのlookup部分を作成する。

        Parameters
        ----------
        type : str
            horse, jockey, trainerのいずれか。
        pre_race : bool
            pre_raceを結合するかどうか。
        target : bool
            targetを結合するかどうか。
        result : bool
            resultを結合するかどうか。

        Returns
        -------
        list[dict]
            lookup部分のリスト。
        """
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception(f"Invalid type: {type}")
        target = "horse" if type != "horse" else "jockey"
        pipeline = []
        if pre_race:
            pipeline.append(
                {
                    "$lookup": {
                        "from": "pre_race",
                        "localField": "race_id",
                        "foreignField": "_id",
                        "as": "race_info",
                    }
                }
            )
            pipeline.append({"$unwind": "$race_info"})
        if target:
            pipeline.append(
                {
                    "$lookup": {
                        "from": target,
                        "localField": f"{target}_id",
                        "foreignField": "_id",
                        "as": f"{target}_data",
                    }
                }
            )
            pipeline.append({"$unwind": f"${target}_data"})
        if result:
            pipeline.append(
                {
                    "$lookup": {
                        "from": "result",
                        "let": {"race_id": "$race_id", "umaban": "$umaban"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$and": [
                                            {"$eq": ["$race_id", "$$race_id"]},
                                            {"$eq": ["$umaban", "$$umaban"]},
                                        ]
                                    }
                                }
                            }
                        ],
                        "as": "race_results",
                    }
                }
            )
            pipeline.append({"$unwind": "$race_results"})
        return pipeline

    def _part_of_pipeline_project(
        self,
        type: str = "horse",
        umaban: bool = True,
        order_of_finish: bool = True,
        time: bool = True,
        difference: bool = True,
        passing: bool = True,
        pace: bool = True,
        up: bool = True,
        race_name: bool = True,
        local: bool = True,
        date: bool = True,
        course: bool = True,
        distance: bool = True,
        weather: bool = True,
        ground_state: bool = True,
        number_of_horses: bool = True,
        prize: bool = True,
        race_id: bool = True,
    ) -> dict:
        """
        パイプラインのproject部分を作成する。

        Parameters
        ----------
        type : str
            horse, jockey, trainerのいずれか。
        umaban : bool
            umabanをprojectするかどうか。
        order_of_finish : bool
            order_of_finishをprojectするかどうか。
        以下同様。

        Returns
        -------
        dict
            project部分。
        """
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception(f"Invalid type: {type}")
        target = "horse" if type != "horse" else "jockey"

        project = {}
        if umaban:
            project["umaban"] = 1
        if order_of_finish:
            project["order_of_finish"] = "$race_results.order_of_finish"
        if time:
            project["time"] = "$race_results.time"
        if difference:
            project["difference"] = "$race_results.difference"
        if passing:
            project["passing"] = "$race_results.passing"
        if pace:
            project["pace"] = "$race_results.pace"
        if up:
            project["up"] = "$race_results.up"
        if race_name:
            project["race_name"] = "$race_info.race_name"
        if local:
            project["local"] = "$race_info.local"
        if date:
            project["date"] = "$race_info.date"
        if course:
            project["course"] = "$race_info.course"
        if distance:
            project["distance"] = "$race_info.distance"
        if weather:
            project["weather"] = "$race_info.weather"
        if ground_state:
            project["ground_state"] = "$race_info.ground_state"
        if number_of_horses:
            project["number_of_horses"] = "$race_info.number_of_horses"
        if prize:
            project["prize"] = "$race_info.prize"
        project[target] = f"${target}_data.name"
        project[type + "_id"] = f"${type}_id"
        if race_id:
            project["race_id"] = "$race_id"

        return project

    def create_pipeline(self, target_id: str, type: str, cnt: int or str) -> list:
        """
        特定のIDに基づいて、MongoDBアグリゲーションパイプラインを作成します。
        """
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception(f"Invalid type: {type}")

        pipeline = [
            {"$match": {f"{type}_id": target_id}},
        ]
        pipeline.extend(self._part_of_pipeline_lookup(type, True, True))
        project = {"cnt": f"${cnt}"}
        project.update(self._part_of_pipeline_project(type))
        pipeline.append({"$project": project})
        return pipeline

    def create_pipeline_for_many(self, target_ids: dict, type: str) -> list:
        """
        特定のIDの辞書に基づいて、MongoDBアグリゲーションパイプラインを作成します。
        そのさい、indexを作成し、処理を高速化します。
        """
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception(f"Invalid type: {type}")
        ConnectMongoDB().create_index()
        pipeline = [
            {
                "$match": {
                    f"{type}_id": {"$in": list(target_ids.keys())},
                    "umaban": {"$ne": 0},
                }
            }
        ]
        pipeline.extend(self._part_of_pipeline_lookup(type, True, True))
        project = {
            "cnt": {
                "$arrayElemAt": [
                    list(target_ids.values()),
                    {"$indexOfArray": [list(target_ids.keys()), f"${type}_id"]},
                ]
            }
        }
        project.update(self._part_of_pipeline_project(type))
        pipeline.append({"$project": project})
        return pipeline

    def create_filtered_pipeline(
        self,
        race_name: str,
        local: str,
        course: str,
        distance: str,
        date1: str,
        date2: str,
        type_id: str,
        type: str,
    ) -> list:
        """
        特定の条件に基づいて、MongoDBアグリゲーションパイプラインを作成します。
        """
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception(f"Invalid type: {type}")

        def _if_all(_str: str, race_name: bool = False):
            if _str == "all":
                return {"$exists": 1}
            elif race_name:
                return {"$regex": _str}
            else:
                return _str

        _race_name = _if_all(race_name, race_name=True)
        _local = _if_all(local)
        _course = _if_all(course)
        _distance = _if_all(distance)
        _type_id = _if_all(type_id)
        if date1 == "1-1-1" and date2 == "1-1-1":
            _date = {"$exists": 1}
        elif date1 == "1-1-1" and date2 != "1-1-1":
            _date = {"$lte": date2}
        elif date2 == "1-1-1" and date1 != "1-1-1":
            _date = {"$gte": date1}
        else:
            _date = {
                "$gte": date1,
                "$lte": date2,
            }
        # local, course, distance, date, type_idで絞込み
        pipeline = []
        pipeline.extend(self._part_of_pipeline_lookup(type, True, True))
        project = self._part_of_pipeline_project(type)
        match = {
            "$match": {
                "race_info.race_name": _race_name,
                "race_info.local": _local,
                "race_info.course": _course,
                "race_info.distance": _distance,
                "race_info.date": _date,
                f"{type}_id": _type_id,
            }
        }
        pipeline.append({"$project": project})
        pipeline.insert(2, match)
        return pipeline

    def find_duplicate(self, race_ids: list[str], target: str, n: int) -> list[str]:
        """
        race_idのリストに基づいて、targetのIDがn回以上重複していたら、そのIDを返します。
        """
        try:
            ConnectMongoDB().create_index(["shutuba"])
            races = self.db["shutuba"].find(
                {"race_id": {"$in": race_ids}}, hint="shutuba_race_id_index"
            )
            target_ids = [race[target + "_id"] for race in races]
            cnt_dict = {}
            for target_id in target_ids:
                if target_id in cnt_dict:
                    cnt_dict[target_id] += 1
                else:
                    cnt_dict[target_id] = 1
            return [target_id for target_id, cnt in cnt_dict.items() if cnt >= n]
        except PyMongoError as e:
            raise PyMongoError(f"Error finding duplicate {target}: {e}")

    def find_shutuba_ids_from_race_id(self, race_id: str, type: str) -> pd.DataFrame:
        """
        特定のレースIDに基づいて、horse, jockey, またはtrainerの過去戦績を取得します。
        """
        try:
            shutubas = self.db["shutuba"].find({"race_id": race_id}, {type + "_id": 1})
            target_ids = [s[type + "_id"] for s in shutubas]
            pipeline = []
            for cnt, id in enumerate(target_ids, 1):
                pipeline.extend(self.create_pipeline(id, type, cnt))
            return pd.DataFrame(self.db["shutuba"].aggregate(pipeline))
        except PyMongoError as e:
            raise PyMongoError(f"Error finding shutuba ids from race id {race_id}: {e}")

    def find_result_from_ids(self, ids: dict, type: str) -> pd.DataFrame:
        """
        horse, jockey, またはtrainerのIDのリストに基づいて、レース結果を取得します。
        """
        try:
            pipeline = self.create_pipeline_for_many(ids, type)
            results = self.db["shutuba"].aggregate(pipeline)
            return pd.DataFrame(results)
        except PyMongoError as e:
            raise PyMongoError(f"Error finding result from {type} IDs: {e}")

    def find_horse_result(self, horse_id: str, cnt: int or str) -> pd.DataFrame:
        """
        特定の馬に関連する情報を取得し、Pandas DataFrameとして返します。
        """
        try:
            pipeline = self.create_pipeline(horse_id, type="horse", cnt=cnt)
            results = self.db["shutuba"].aggregate(pipeline)
            return pd.DataFrame(results)
        except PyMongoError as e:
            raise PyMongoError(f"Error finding horse result for {horse_id}: {e}")

    def exists_target_date_result(self, data: pd.DataFrame, date: str) -> bool:
        """
        特定の日付のレースがあるかどうかを確認する
        """
        print(data.columns)
        return len(data[data["date"].str[:10] == date]) > 0

    def find_filtered_race(
        self,
        race_name: str = "all",
        local: str = "all",
        course: str = "ダ",
        distance: str = "all",
        date1: str = "1-1-1",
        date2: str = "1-1-1",
        type_id: str = "all",
        type: str = "horse",
    ) -> pd.DataFrame:
        """
        特定の条件に基づいて、レースを取得する。
        """
        try:
            pipeline = self.create_filtered_pipeline(
                race_name, local, course, distance, date1, date2, type_id, type
            )
            results = self.db["shutuba"].aggregate(pipeline)
            return pd.DataFrame(results)
        except PyMongoError as e:
            raise PyMongoError(f"Error finding race: {e}")

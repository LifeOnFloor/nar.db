import pandas as pd

from sklearn.preprocessing import LabelEncoder

import app
from modules.database import FindData
from modules.constants import RACEDATA


class Preprocess:
    def __init__(self, type: str, include: dict = {}) -> None:
        """
        Parameters
        ----------
        type : str
            horse, jockey, trainer
        include : dict
            date, local, distance, course, ground_state
        --------------------
        Example:
        include = {
            "date": {
                "start_date": "2021-01-01",
                "end_date": "2021-12-31",
            },
            "local": "高知",
            "distance": "1200",
            "course": "ダ",
            "ground_state": "稍",
        }
        """
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception("type must be horse, jockey or trainer")
        self.type = type
        self.include = include
        self.mongo = app.get_mongo_client()
        self.find = FindData(self.mongo)
        self.df = None

    @property
    def formatted_result_df(self):
        if self.df is None:
            return self.get_formatted_result()
        else:
            return self.df

    def get_formatted_result(self) -> pd.DataFrame:
        """
        horse_id, jockey_id, trainer_idに基づいた過去戦績を取得する

        Parameters
        ----------
        ids : dict
            horse_id, jockey_id, trainer_id
        type : str
            horse, jockey, trainer

        Returns : pd.DataFrame
            機械学習用に整形された過去戦績
        -------
        """
        type = self.type
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception("type must be horse, jockey or trainer")
        try:
            if type == "horse":
                id_list = self.find.get_all_horse_ids()
                id_dict = {str(v): f"h_{n}" for n, v in enumerate(id_list)}
            elif type == "jockey":
                id_list = self.find.get_all_jockey_ids()
                id_dict = {str(v): f"j_{n}" for n, v in enumerate(id_list)}
            else:
                id_list = self.find.get_all_trainer_ids()
                id_dict = {str(v): f"t_{n}" for n, v in enumerate(id_list)}
            df = self.find.find_result_from_ids(
                id_dict,
                type,
            )
            df = self._select_include(df, self.include)
            self.df = self._format_result(type, df)
            return self.df
        except Exception as e:
            raise Exception(f"Error getting horse result: {e}")

    def _format_result(self, type: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        過去戦績を整形する
        """
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception("type must be horse, jockey or trainer")

        if type == "horse":
            target = "jockey"
        else:
            target = "horse"

        try:
            # 不要なカラムと欠損値を削除
            df.drop(
                columns=["_id", "cnt", "race_name", "race_id"], axis=1, inplace=True
            )
            df.dropna(
                subset=[
                    "time",
                    "ground_state",
                    "weather",
                    "passing",
                    "pace",
                ],
                how="any",
                inplace=True,
            )

            # データ型を変換
            df.loc[:, "order_of_finish"] = pd.to_numeric(
                df["order_of_finish"], errors="coerce"
            )
            df = df[df["order_of_finish"].notnull()]
            df.loc[:, "time"] = pd.to_numeric(
                df["time"].apply(lambda x: self._format_time(x)), errors="coerce"
            )
            df.loc[:, "distance"] = pd.to_numeric(
                df["distance"].apply(lambda x: int(x)), errors="coerce"
            )
            df = df[
                df["order_of_finish"].notnull()
                & df["distance"].notnull()
                & df["time"].notnull()
            ]

            # データ型を変換
            df.loc[:, "local"] = pd.Categorical(
                df["local"], RACEDATA.LOCALNAME_CODE.keys()
            )
            df.loc[:, "course"] = pd.Categorical(df["course"], RACEDATA.COURSE_LIST)
            df.loc[:, "weather"] = pd.Categorical(df["weather"], RACEDATA.WEATHER_LIST)
            df.loc[:, "ground_state"] = pd.Categorical(
                df["ground_state"], RACEDATA.GROUND_STATE_LIST
            )

            # カラムを分割
            df.loc[:, "passing"] = df["passing"].apply(
                lambda x: self._format_passing(x)
            )
            df = self._split_column(df, "passing")
            df.loc[:, "pace"] = df["pace"].apply(lambda x: self._format_pace(x))
            df = self._split_column(df, "pace")

            # ラベルエンコーディング
            le = LabelEncoder()
            df[target] = le.fit_transform(df[target])
            df[type + "_id"] = le.fit_transform(df[type + "_id"])
            df["local"] = le.fit_transform(df["local"])
            df["ground_state"] = le.fit_transform(df["ground_state"])
            df["weather"] = le.fit_transform(df["weather"])
            df["course"] = le.fit_transform(df["course"])

            df["order_of_finish"] = df["order_of_finish"].astype(int)
            df["time"] = df["time"].astype(float)
            df["distance"] = df["distance"].astype(float)

            # 日付をtype_idごとに最新の日付からの日数に変換
            df = self._convert_date_to_datedelta(type, df)
            return df
        except Exception as e:
            raise Exception(f"Error formatting horse result: {e}")

    def _format_time(self, time_str: str) -> float:
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

    def _format_passing(self, passing_str: str) -> list[int]:
        """
        通過順位をリストに変換する
        """
        try:
            pass_list = [0 for _ in range(4)]
            if "-" not in str(passing_str):
                passing_str = "0-" + str(passing_str)
            passing = passing_str.split("-")
            start_index = 4 - len(passing)
            if start_index < 0 or start_index > 3:
                raise Exception(
                    f"Error converting passing is out of range: {passing_str}: {passing}"
                )
            for i, p in enumerate(passing):
                pass_list.insert(start_index + i, int(p))
                pass_list.pop()
            return pass_list
        except Exception as e:
            raise Exception(f"Error converting passing to list: {passing_str}: {e}")

    def _format_pace(self, pace_str: str) -> list[float]:
        """
        ペースをリストに変換する
        """
        try:
            if "-" not in str(pace_str):
                pace_str = "0-" + str(pace_str)
            pace = pace_str.split("-")
            if len(pace) == 1:
                pace.insert(0, str(0))
            return [float(p) for p in pace]
        except Exception:
            raise Exception(f"Error converting pace to list: {pace_str}")

    def _split_column(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        カラムを分割する
        """
        try:
            _df = pd.DataFrame(df[column].to_list())
            n = len(_df.columns)
            _df.columns = [f"{column}_{i}" for i in range(1, n + 1)]
            _df.index = df.index
            df = pd.merge(df, _df, left_index=True, right_index=True)
            df.drop(columns=[column], inplace=True)
            return df
        except Exception as e:
            raise Exception(f"Error splitting column: {column}: {e}")

    def _convert_date_to_datedelta(self, type: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        type_idごとにgroupbyしたデータフレームの日付を、最新の日付からの日数に変換する
        """
        try:
            _df = df.copy()
            _df.loc[:, "date"] = pd.to_datetime(
                _df["date"], format="%Y-%m-%d", errors="coerce"
            )

            # 同じtype_idのなかで最大の日付を取得し、最大日付からの日数を計算する
            _df.loc[:, "max_date"] = _df.groupby(type + "_id")["date"].transform("max")
            _df.loc[:, "datedelta"] = _df.apply(
                lambda row: (row["max_date"] - row["date"]), axis=1
            )
            # intに変換
            _df["datedelta"] = pd.to_numeric(_df["datedelta"], errors="coerce")
            _df["datedelta"] = _df["datedelta"].apply(
                lambda x: x / 24 / 60 / 60 / (10**9)
            )
            # 不要なカラムを削除
            _df.drop(columns=["date", "max_date"], inplace=True)
            return _df
        except Exception as e:
            raise Exception(f"Error converting date to datedelta: {e}")

    def _select_include(self, df: pd.DataFrame, include: dict) -> pd.DataFrame:
        """
        includeに基づいてデータを絞り込む
        """
        if "date" in include.keys():
            df = self._match_date_range(df, include["date"])
        if "local" in include.keys():
            df = self._match_local(df, include["local"])
        if "distance" in include.keys():
            df = self._match_distance(df, include["distance"])
        if "course" in include.keys():
            df = self._match_course(df, include["course"])
        if "ground_state" in include.keys():
            df = self._match_ground_state(df, include["ground_state"])
        return df

    def _match_date_range(
        self,
        df: pd.DataFrame,
        date_range: dict = {"start_date": "1000-01-01", "end_date": "1000-01-01"},
    ) -> pd.DataFrame:
        """
        日付を範囲で一致させる
        """
        if "start_date" in date_range.keys():
            start_date = date_range["start_date"]
        else:
            start_date = "1000-01-01"
        if "end_date" in date_range.keys():
            end_date = date_range["end_date"]
        else:
            end_date = "1000-01-01"

        if start_date == "1000-01-01" and end_date == "1000-01-01":
            return df
        elif start_date == "1000-01-01":
            return df[df["date"] <= end_date]
        elif end_date == "1000-01-01":
            return df[df["date"] >= start_date]
        elif start_date > end_date:
            raise Exception(
                f"start_date must be earlier than end_date: {start_date} > {end_date}"
            )
        else:
            return df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    def _match_local(self, df: pd.DataFrame, local: str = "") -> pd.DataFrame:
        """
        開催地を一致させる
        """
        if local == "":
            return df
        else:
            return df[df["local"] == local]

    def _match_distance(self, df: pd.DataFrame, distance: int = 0) -> pd.DataFrame:
        """
        距離を一致させる
        """
        if distance == 0:
            return df
        else:
            return df[df["distance"] == distance]

    def _match_course(self, df: pd.DataFrame, course: str = "") -> pd.DataFrame:
        """
        コースを一致させる
        """
        if course == "":
            return df
        else:
            return df[df["course"] == course]

    def _match_ground_state(
        self, df: pd.DataFrame, ground_state: str = ""
    ) -> pd.DataFrame:
        """
        馬場状態を一致させる
        """
        if ground_state == "":
            return df
        else:
            return df[df["ground_state"] == ground_state]

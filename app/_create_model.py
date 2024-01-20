import pandas as pd
import numpy as np
from keras.metrics import RootMeanSquaredError
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Masking, Conv1D, GRU, Dense, Input
from keras.models import Sequential, load_model, Model
from keras.callbacks import EarlyStopping
from tensorflow import data


class Model:
    def __init__(
        self,
        df: pd.DataFrame,
        type: str,
        test_size: float = 0.2,
        y_col: str = "time",
        batch_size: int = 32,
    ):
        if type not in ["horse", "jockey", "trainer"]:
            raise ValueError("type must be 'horse', 'jockey' or 'trainer'")
        if y_col not in df.columns:
            raise ValueError(f"{y_col} column not found in DataFrame")

        self.df = df.copy()
        self.type = type
        self.test_size = test_size
        self.y_col = y_col
        self.batch_size = batch_size

    def _split_data(self, df: pd.DataFrame):
        """
        データをtype_idごとにtrainとtestに分割する

        Args:
            test_size (float): テストデータの割合 (0~1)

        Returns:
            train (pd.DataFrame): 訓練データ
            test (pd.DataFrame): テストデータ
        """
        unique_id_list = df[f"{self.type}_id"].unique()

        train_id_list = unique_id_list[
            : round(len(unique_id_list) * (1 - self.test_size))
        ]
        test_id_list = unique_id_list[
            round(len(unique_id_list) * (1 - self.test_size)) :
        ]

        # df をdateカラムでソートする
        # df.sort_values(by="datedelta", ascending=False, inplace=True)

        # データを分割する
        train = df[df[f"{self.type}_id"].isin(train_id_list)]
        test = df[df[f"{self.type}_id"].isin(test_id_list)]
        return train, test

    def _df_to_tensor(self, df: pd.DataFrame) -> np.ndarray:
        """
        データフレームをテンソルに変換する
        """
        X = df.drop([self.y_col, f"{self.type}_id"], axis=1).values
        X = X.reshape(-1, self.max_sequence_length, X.shape[1])
        y = df[self.y_col].values
        y = np.array(y).reshape(-1, self.max_sequence_length, 1)
        return np.concatenate([X, y], axis=2)

    def _pad_sequences(
        self, df: pd.DataFrame, max_sequence_length: int
    ) -> pd.DataFrame:
        """
        各IDに対してシーケンスをパディングする
        """
        padded_dfs = []
        for id, group in df.groupby(f"{self.type}_id"):
            # 特徴量データの取得とパディング
            features = group.drop([self.y_col, f"{self.type}_id", "datedelta"], axis=1)
            padded_features = pad_sequences(
                [features], maxlen=max_sequence_length, padding="post", dtype="float32"
            )[0]

            # 目的変数の取得とパディング
            target = group[self.y_col].values
            padded_target = pad_sequences(
                [target], maxlen=max_sequence_length, padding="post", dtype="float32"
            )[0]

            # パディングされたデータフレームの作成
            padded_df = pd.DataFrame(padded_features, columns=features.columns)
            padded_df[self.y_col] = padded_target
            padded_df[f"{self.type}_id"] = id

            padded_dfs.append(padded_df)

        return pd.concat(padded_dfs).reset_index(drop=True)

    def _get_max_datedelta(self, limit: int = 500) -> int:
        """
        datedeltaカラムの最大値を取得する
        もし、最大値が大きすぎる場合はdfをlimitで指定した値でフィルタリングする
        """
        if self.df["datedelta"].max() > limit:
            self.df = self.df[self.df["datedelta"] <= limit]
            return limit
        return self.df["datedelta"].max()

    def _filter_by_sequence_length(self, min_sequence_length: int = 5):
        """
        シーケンスの長さがmin_sequence_length未満のデータをフィルタリングする
        """
        self.df = self.df.groupby(f"{self.type}_id").filter(
            lambda x: len(x) >= min_sequence_length
        )

    def _df_to_dataset(self, df: pd.DataFrame) -> tuple[data.Dataset, data.Dataset]:
        """
        データフレームをデータセットに変換する
        """
        tensor = self._df_to_tensor(df)
        X, y = tensor[0], tensor[1]
        X = data.Dataset.from_tensor_slices(X).batch(self.batch_size)
        y = data.Dataset.from_tensor_slices(y).batch(self.batch_size)
        return X, y

    def _create_dataset(self):
        """
        データセットを作成する
        """
        # datedeltaカラムの最大値を取得する。もし、最大値が大きすぎる場合はdfをフィルタリングする
        self.max_sequence_length = self._get_max_datedelta(limit=150)
        print(f"max_sequence_length: {self.max_sequence_length}")
        print(f"initial data shape: {self.df.shape}")

        # シーケンスの長さがmin_sequence_length未満のデータをフィルタリングする
        self._filter_by_sequence_length(min_sequence_length=15)
        print(f"filtered data shape: {self.df.shape}")

        self.df = self._pad_sequences(self.df, self.max_sequence_length)
        print(f"padding data shape: {self.df.shape}")

        self.train_df, self.test_df = self._split_data(self.df)
        print(
            f"train data shape: {self.train_df.shape}, test data shape: {self.test_df.shape}"
        )

        self.train_Dataset = self._df_to_dataset(self.train_df)
        self.test_Dataset = self._df_to_dataset(self.test_df)

        print(
            f"train_Dataset: {self.train_Dataset[0].element_spec}, test_Dataset: {self.test_Dataset[1].element_spec}"
        )

    def _create_model(self):
        """
        モデルを作成する
        """
        model = Sequential()
        model.add(
            Masking(
                mask_value=0.0,
                input_shape=(
                    self.max_sequence_length,
                    self.train_df.drop([self.y_col, f"{self.type}_id"], axis=1).shape[1]
                    + 1,
                ),
            )
        )
        model.add(Conv1D(filters=64, kernel_size=3, activation="relu"))
        model.add(GRU(units=64, return_sequences=True))
        model.add(Dense(units=1))
        model.compile(optimizer="adam", loss="mse", metrics=[RootMeanSquaredError()])
        return model

    def train(self):
        """
        モデルを学習する
        """
        print("creating dataset...")
        self._create_dataset()
        print("creating model...")
        model = self._create_model()
        early_stopping = EarlyStopping(
            monitor="val_loss", patience=3, restore_best_weights=True
        )
        print("training...")
        model.fit(
            x=self.train_Dataset[0],
            epochs=100,
            validation_data=data.Dataset.zip(
                (self.test_Dataset[0], self.test_Dataset[1])
            ),
            callbacks=[early_stopping],
        )
        self.model = model
        print("evaluating...")
        rmse, loss = self.model.evaluate(
            self.test_Dataset, steps=len(self.test_df) // self.batch_size
        )
        print(f"RMSE: {rmse}, loss: {loss}")

    def save_model(self):
        """
        モデルを保存する
        """
        if self.model is None:
            raise Exception("Model is not trained yet")
        self.model.save(f"data/model/{self.type}_model.keras")
        print(f"data/model/{self.type}_model.keras is saved")

    def load_model(self):
        """
        モデルを読み込む
        """
        self.model = load_model(f"data/model/{self.type}_model.keras")
        print(f"data/model/{self.type}_model.keras is loaded")


'''class Model:
    def __init__(
        self, df: pd.DataFrame, type: str, test_size: float, valid_size: float
    ) -> None:
        if type not in ["horse", "jockey", "trainer"]:
            raise Exception("type must be horse, jockey or trainer")

        self.df = df.copy()
        self.type = type
        self.test_size = test_size
        self.valid_size = valid_size
        self.target = "jockey" if type == "horse" else "horse"
        self.gbm = None

    def _set_params(self) -> dict:
        """
        LightGBMのパラメータを設定する
        """
        params = {
            "objective": "regression",  # 目的関数: 二乗誤差
            "metric": "rmse",  # RMSE(平均二乗誤差の平方根)で評価
            "verbosity": -1,  # 学習の状況を表示しない
        }
        return params

    def _tune_hyper_params(self) -> dict:
        """
        ハイパーパラメータをチューニングする
        """
        params = self._set_params()
        lgb_optuna_train = lgb_o.LightGBMTuner(
            params=params,
            train_set=self.lgb_optuna_train,
            num_boost_round=1000,
            valid_sets=self.lgb_optuna_valid,
        )
        lgb_optuna_train.run()
        return lgb_optuna_train.best_params

    def _split_data(self, df: pd.DataFrame):
        """
        データをtype_idごとにtrainとtestに分割する

        Args:
            test_size (float): テストデータの割合 (0~1)

        Returns:
            train (pd.DataFrame): 訓練データ
            test (pd.DataFrame): テストデータ
        """
        unique_id_list = df[f"{self.type}_id"].unique()

        train_id_list = unique_id_list[
            : round(len(unique_id_list) * (1 - self.test_size))
        ]
        test_id_list = unique_id_list[
            round(len(unique_id_list) * (1 - self.test_size)) :
        ]

        # df をdateカラムでソートする
        df.sort_values(by="datedelta", ascending=False, inplace=True)
        train = df[df[f"{self.type}_id"].isin(train_id_list)]
        test = df[df[f"{self.type}_id"].isin(test_id_list)]
        return train, test

    def _create_dataset(self):
        """
        LightGBMのデータセットを作成する
        """
        self.train_df, self.test_df = self._split_data(self.df)
        self.optuna_train_df, self.optuna_valid_df = self._split_data(self.train_df)
        self.lgb_optuna_train = lgb_o.Dataset(
            self.optuna_train_df.drop(["time"], axis=1).values,
            self.optuna_train_df["time"],
        )
        self.lgb_optuna_valid = lgb_o.Dataset(
            self.optuna_valid_df.drop(["time"], axis=1).values,
            self.optuna_valid_df["time"],
        )
        self.lgb_train = lgb.Dataset(
            self.train_df.drop(["time"], axis=1).values,
            self.train_df["time"],
        )
        self.lgb_test = lgb.Dataset(
            self.test_df.drop(["time"], axis=1).values,
            self.test_df["time"],
        )

    def train(self):
        """
        モデルを学習する
        """
        self._create_dataset()
        params = self._tune_hyper_params()

        self.gbm = lgb.train(
            params,
            self.lgb_train,
            num_boost_round=100,
            valid_sets=[self.lgb_test, self.lgb_train],
        )
        y_pred = self._predict(self.test_df.drop(["time"], axis=1).values)
        rmse = self._evaluate(self.test_df["time"].values, y_pred)
        return rmse

    def _predict(self, X_test):
        """
        テストデータに対する予測を行う
        """
        if self.gbm is None:
            raise Exception("Model is not trained yet")
        return self.gbm.predict(X_test, num_iteration=self.gbm.best_iteration)

    def _evaluate(self, y_test, y_pred):
        """
        予測の精度を評価する
        """
        rmse = mean_squared_error(y_test, y_pred, squared=False)
        return rmse

    def plot_importance(self):
        """
        重要な特徴量を表示する
        """
        if self.gbm is None:
            raise Exception("Model is not trained yet")
        importance = lgb.plot_importance(self.gbm, max_num_features=15)
        return importance

    def save_model(self):
        """
        モデルを保存する
        """
        if self.gbm is None:
            raise Exception("Model is not trained yet")
        self.gbm.save_model(f"model/{self.type}_model.txt")
'''

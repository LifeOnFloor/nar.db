import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import datetime
import pandas as pd

import app
from modules.constants import RACEDATA


def page_config():
    st.set_page_config(
        page_title="Model",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def select_analyze_type(
    container: DeltaGenerator,
) -> tuple[str, datetime.date, list[str]]:
    """
    分析対象を選択する
    """
    # TODO: local,
    type = container.selectbox(
        label="分析対象を選択してください",
        options=["horse", "jockey", "trainer"],
        label_visibility="hidden",
    )
    date = container.slider(
        label="分析対象の期間を選択してください",
        min_value=datetime.date(2016, 1, 1),
        max_value=datetime.date(2023, 12, 31),
        value=datetime.date.today() - datetime.timedelta(days=365),
        format="YYYY-MM-DD",
        label_visibility="hidden",
    )
    date = datetime.datetime.strptime(str(date), "%Y-%m-%d").date()
    local_keys = []
    local_values = [f"{i:02d}" for i in range(11, 60, 1)]
    for k, v in RACEDATA.LOCALNAME_CODE.items():
        if v in local_values:
            local_keys.append(k)
    local = container.multiselect(
        label="分析対象の開催地を選択してください",
        options=local_keys,
        label_visibility="hidden",
    )
    return str(type), date, local


def get_result(type: str):
    """
    分析対象の過去戦績を取得する

    Args:
        type (str): 分析対象 (horse, jockey, trainer)

    Returns:
        pd.DataFrame: 分析対象の過去戦績

    --------------------

    Example:
        >>> get_result("horse")
        >>> get_result("jockey")
        >>> get_result("trainer")
    """
    try:
        preprocess = app.Preprocess()
        return preprocess.get_formatted_result(type)
    except Exception as e:
        raise Exception(f"Error getting result: {e}")


def main():
    page_config()
    settings = select_analyze_type(st.sidebar)
    if st.sidebar.button("モデル作成"):
        container = st.empty()
        container = container.container()
        result = container.status("データ取得中...")
        df = get_result(settings[0])
        result.write(df.shape)
        result.write(df)
        result.update(label="データ取得完了！", state="complete")

        model_container = container.status("モデル作成中...")
        model = app.Model(df, settings[0])
        rmse = model.train()
        model.plot_importance()
        model.save_model()
        model_container.write(f"RMSE: {rmse}")
        model_container.update(label="モデル作成完了！", state="complete")


if __name__ == "__main__":
    main()

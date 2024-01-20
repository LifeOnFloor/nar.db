from streamlit.delta_generator import DeltaGenerator
import streamlit as st
from datetime import datetime
import time


class ModStreamlit:
    """
    streamlitを変更する関数をまとめたクラス
    """

    def __init__(self, container: DeltaGenerator):
        self.container = container

    def progress(self, value: int or float, text: str = ""):
        """
        streamlit.progressの表示内容を変更する
        """

        # 前回実行した時の時間を取得
        @st.cache_data
        def get_start_time():
            return datetime.now()

        start_time = get_start_time()

        def _progress(
            value: int or float, text: str = "", start_time: datetime = start_time
        ):
            """
            streamlit.progressの表示内容を変更する
            """

            self.container.progress(value)
            self.container.write(f"実行時間: {datetime.now() - start_time}")
            self.container.write(
                f"残り時間: {(datetime.now() - start_time) / value * (100 - value)}"
            )


def mod_progress(
    container: DeltaGenerator,
    start_time: datetime,
    value: float or int = 0,
    text: str = "",
):
    """
    streamlit.progressの表示内容を変更する
    変更前は、streamlit.progressの表示内容は、
    0%から100%までのバーとなっている。
    この関数を用いることで、
    0%から100%までのバーとともに、
    実行時間と残り時間を表示することができる。
    """
    _start_time = datetime.now()

    def progress(
        value: int or float, text: str = "", _start_time: datetime = _start_time
    ):
        """
        streamlit.progressの表示内容を変更する
        """
        container.progress(value)
        container.write(f"実行時間: {datetime.now() - start_time}")
        container.write(
            f"残り時間: {(datetime.now() - start_time) / value * (100 - value)}"
        )

from bs4 import BeautifulSoup
from modules.constants import URL
from time import sleep
import pandas as pd
from io import StringIO


class GetResultData:
    def __init__(self, driver, race_id: str):
        self.url = URL.NAR_RESULT + race_id
        self.driver = driver
        self.soup = self.get_data()
        self.result_order = self.get_result_order(self.soup)

    @property
    def result(self):
        return self.result_order

    def get_data(self):
        """
        レース結果ページからデータを取得します。
        """
        self.driver.get(self.url)
        sleep(URL.WAIT_TIME)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        return soup

    def get_result_order(self, soup: BeautifulSoup):
        """
        レース結果ページから着順を取得します。
        """
        result_table = soup.find("table", {"id": "All_Result_Table"})
        html_string_io = StringIO(str(result_table))
        result_df = pd.read_html(html_string_io)[0]
        result_df.columns = [
            "着順",
            "枠",
            "馬番",
            "馬名",
            "性齢",
            "斤量",
            "騎手",
            "タイム",
            "着差",
            "人気",
            "単勝オッズ",
            "後3F",
            "厩舎",
            "馬体重(増減)",
        ]

        # horse_id, jockey_id, trainer_idを取得
        result_table = BeautifulSoup(html_string_io, "html.parser")
        horse_ids = result_table.select("span.Horse_Name > a")
        horse_ids = [str(horse_id["href"]).split("/")[-2] for horse_id in horse_ids]
        jockey_ids = result_table.select("td.Jockey > a")
        jockey_ids = [str(jockey_id["href"]).split("/")[-2] for jockey_id in jockey_ids]
        trainer_ids = result_table.select("td.Trainer > a")
        trainer_ids = [
            str(trainer_id["href"]).split("/")[-1] for trainer_id in trainer_ids
        ]
        result_df["horse_id"] = horse_ids
        result_df["jockey_id"] = jockey_ids
        result_df["trainer_id"] = trainer_ids

        return result_df

from modules.constants import URL, RACEDATA
from modules.scrape import WebDriver
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from time import sleep
import re


class GetPreData:
    def __init__(self, driver, race_id: str):
        self.driver = driver
        self.race_id = race_id
        self.html: str = ""

    def get_pre_page(self) -> str:
        """
        ページを取得します。
        """
        url = URL.NAR_SHUTUBA + self.race_id
        for _ in range(URL.RETRY_COUNT):
            try:
                self.driver.get(url)
                sleep(URL.WAIT_TIME)
                return self.driver.page_source
            except WebDriverException as e:
                if _ < URL.RETRY_COUNT - 1:
                    sleep(URL.RETRY_WAIT_TIME)
                    self.driver = WebDriver().driver()
                    continue
                raise WebDriverException(f"Error loading page {url} : {e}")
        raise WebDriverException(f"Not found page {url}")

    def get_pre_data(self) -> dict:
        """
        レース事前情報を取得します。
        """
        try:
            if self.html == "":
                self.html = self.get_pre_page()
            soup = BeautifulSoup(self.html, "html.parser")
            race_details_div = soup.find("div", {"class": "RaceList_Item02"})
            if not race_details_div:
                raise Exception("Race details not found")
            race_details = race_details_div.get_text(separator="|", strip=True)
            return self.converta_race_details_to_dict(race_details)
        except Exception as e:
            raise Exception(f"Error getting race info : {e}")

    def converta_race_details_to_dict(self, details: str) -> dict:
        """
        レース情報をdictに変換します。
        """
        try:
            info_list = details.split("|")
            temp_dict = self._convert_to_dict(info_list, RACEDATA.TEMP_RACE_INFO_KEYS)
            temp_dict["course"] = temp_dict["course_and_distance"][0]
            temp_dict["distance"] = temp_dict["course_and_distance"][1]
            temp_dict["around"] = temp_dict["around_and_weather"][0]
            temp_dict["weather"] = temp_dict["around_and_weather"][1]
            temp_dict.pop("course_and_distance")
            temp_dict.pop("around_and_weather")
            return temp_dict
        except Exception as e:
            raise Exception(f"Error extracting info : {e}")

    def _convert_to_dict(self, info_list: list, keys: list) -> dict:
        """
        info_listからkeysに対応する情報を抽出してdictにして返します。
        """
        try:
            formatted_info_dict = {}
            for num, info in enumerate(info_list):
                if "発走" not in info_list[1] and num > 1:
                    num -= 1
                elif "発走" not in info_list[1] and num == 1:
                    continue
                case = {
                    0: self.not_format,  # title
                    1: self.format_date,  # date
                    2: self.format_course_and_distance,  # course_and_distance
                    3: self.format_around_and_weather,  # around_and_weather
                    4: self.format_after_colon,  # ground_state
                    5: self.not_format,  # no use
                    6: self.not_format,  # local
                    7: self.not_format,  # no use
                    8: self.not_format,  # grade
                    9: self.format_number_of_horses,  # number_of_horses
                    10: self.format_prize,  # prize
                }
                formatted_info_dict.update({keys[num]: case[num](info)})
            return formatted_info_dict
        except Exception as e:
            raise Exception(f"Error converting to dict : {e}")

    def not_format(self, info: str) -> str:
        return info

    def format_date(self, info: str) -> str:
        return info.split("発走")[0]

    def format_course_and_distance(self, info: str) -> list:
        return [re.sub(r"\d+m", "", info), int(re.sub(r"\D", "", info))]

    def format_around_and_weather(self, info: str) -> list[str]:
        around = re.findall(r"\((.+?)\)", info)[0]
        weather = info.split(":")[-1] if "天候" in info else ""
        return [around, weather]

    def format_after_colon(self, info: str) -> str:
        return info.split(":")[-1]

    def format_number_of_horses(self, info: str) -> int:
        return int(re.sub(r"\D", "", info))

    def format_prize(self, info: str) -> float:
        return float(info.split("、")[0].replace("本賞金:", ""))

    def get_shutba_table(self) -> pd.DataFrame:
        """
        出馬表を取得します。
        """
        try:
            if self.html == "":
                self.html = self.get_pre_page()
            soup = BeautifulSoup(self.html, "html.parser")
            shutuba_table = soup.find("table", {"class": "ShutubaTable"})
            html_string_io = StringIO(str(shutuba_table))
            shutuba_table_df = pd.read_html(html_string_io)[0]
            shutuba_table_df.columns = shutuba_table_df.columns.droplevel()
            shutuba_table_df = shutuba_table_df.iloc[:, [0, 1, 3, 4, 5, 6, 7, 8, 9, 10]]
            shutuba_table_df.columns = RACEDATA.SHUTUBA_COLUMNS

            # horse_id, jockey_id, trainer_idの取得
            shutuba_table = BeautifulSoup(html_string_io, "html.parser")
            horse_ids = shutuba_table.select("span.HorseName > a")
            horse_ids = [str(horse_id["href"]).split("/")[-1] for horse_id in horse_ids]
            shutuba_table_df["horse_id"] = horse_ids

            jockey_ids = shutuba_table.select("span.Jockey > a")
            jockey_ids = [
                str(jockey_id["href"]).split("/")[-1] for jockey_id in jockey_ids
            ]
            shutuba_table_df["jockey_id"] = jockey_ids

            trainer_ids = shutuba_table.select("td.Trainer > a")
            trainer_ids = [
                str(trainer_id["href"]).split("/")[-1] for trainer_id in trainer_ids
            ]
            shutuba_table_df["trainer_id"] = trainer_ids
            return shutuba_table_df
        except Exception as e:
            raise Exception(f"Error getting shutuba table : {e}")

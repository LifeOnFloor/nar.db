import pandas as pd
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from io import StringIO
from time import sleep
from functools import lru_cache
import re

from modules.constants import URL, RACEDATA
from modules.scrape import WebDriver


class GetHorseData:
    def __init__(self, driver, horse_id: str):
        self.driver = driver
        self.horse_id = horse_id
        self.horse_page_soup = None

    @lru_cache(maxsize=URL.CACHE_SIZE)
    def _get_soup(self, url: str) -> BeautifulSoup:
        """
        指定されたURLからBeautifulSoupオブジェクトを取得する。
        """
        for r in range(URL.RETRY_COUNT):
            try:
                self.driver.get(url)
                sleep(URL.WAIT_TIME)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                if soup:
                    return soup
            except Exception:
                sleep(URL.RETRY_WAIT_TIME)
                self.driver = WebDriver().driver()
                continue
        raise WebDriverException(f"Error getting soup from {url}")

    def _select_element(self, soup: BeautifulSoup, selector: str) -> BeautifulSoup:
        """
        指定されたセレクターからBeautifulSoupオブジェクトを取得する。
        """
        try:
            element = soup.select_one(selector)
            if element:
                return BeautifulSoup(str(element), "html.parser")
            else:
                return BeautifulSoup("", "html.parser")
        except Exception as e:
            raise Exception(f"Error selecting element {selector}: {e}")

    def _select_all_elements(self, soup: BeautifulSoup, selector: str) -> BeautifulSoup:
        """
        指定されたセレクターに一致するすべてのBeautifulSoupオブジェクトを取得する。
        """
        try:
            elements = soup.select(selector)
            if elements:
                return BeautifulSoup(str(elements), "html.parser")
            else:
                return BeautifulSoup("", "html.parser")
        except Exception as e:
            raise Exception(f"Error selecting element {selector}: {e}")

    def _get_splitted_href(self, soup: BeautifulSoup, selector: str) -> str:
        """
        指定されたセレクターからhrefを/で分割して最後の要素を返す。
        """
        try:
            element = soup.select_one(selector)
            if element:
                href = str(element.get("href"))
                return href.split("/")[-2]
            else:
                return ""
        except Exception as e:
            raise Exception(f"Error selecting element {selector}: {e}")

    def get_horse_profile(self) -> dict:
        """
        馬のプロフィールを取得する
        """
        try:
            url = URL.HORSE + self.horse_id
            if not self.horse_page_soup:
                self.horse_page_soup = self._get_soup(url)
            soup = self.horse_page_soup
            name_soup = self._select_element(soup, "div.horse_title > h1")
            name = name_soup.get_text() if name_soup else ""
            data_soup = self._select_element(soup, "div.db_prof_area_02")
            trainer_id = self._get_splitted_href(data_soup, "a")
            data = data_soup.get_text(separator="|", strip=True).split("|")
            horse_profile = {
                column: data[data.index(column) + 1]
                for column in RACEDATA.HORSE_PROFILE_COLUMNS
            }
            horse_profile["馬名"] = name
            horse_profile["trainer_id"] = trainer_id
            return horse_profile
        except Exception as e:
            raise Exception(f"Error getting horse profile: {e}")

    def get_horse_pedigree(self) -> dict:
        """
        馬の血統を取得する
        """
        try:
            soup = self._get_soup(URL.HROSE_PED + self.horse_id)
            table = self._select_element(soup, "table.blood_table")
            return self.parse_pedigree(str(table))
        except Exception as e:
            raise Exception(f"Error getting horse pedigree: {e}")

    def generate_pedigree_key(self, depth: int, current_depth_count: int) -> str:
        """
        テーブルの行数と列数から血統のキーを生成する
        """
        key_map = {
            16: "f",
            8: "ff",
            4: "fff",
            2: "ffff",
            1: "fffff",
        }
        binary = bin(current_depth_count)[2:].zfill(len(key_map.get(depth, "")))
        return binary.replace("0", "f").replace("1", "m")

    def parse_pedigree(self, html) -> dict:
        """
        血統のテーブルから血統データを取得する
        """
        soup = BeautifulSoup(html, "html.parser")
        pedigree_data = {}
        depth_count = {16: 0, 8: 0, 4: 0, 2: 0, 1: 0}
        for tr in soup.find_all("tr"):
            tds = BeautifulSoup(str(tr), "html.parser").find_all("td")
            for td in tds:
                rowspan = int(td.get("rowspan", 1))
                key = self.generate_pedigree_key(rowspan, depth_count[rowspan])
                depth_count[rowspan] += 1
                pedigree_data[key] = self._get_splitted_href(td, "a")
        return pedigree_data

    def format_local_name(self, local: str) -> str:
        """
        開催地名から数字を削除する
        """
        try:
            return re.sub(r"\d", "", local)
        except Exception as e:
            raise Exception(f"Error parsing local {local}: {e}")

    def get_horse_result(self) -> pd.DataFrame:
        """
        馬の過去戦績を取得する
        """
        try:
            if not self.horse_page_soup:
                self.horse_page_soup = self._get_soup(URL.HORSE + self.horse_id)
            soup = self.horse_page_soup
            table = self._select_element(soup, "table.db_h_race_results.nk_tb_common")
            if table:
                df = pd.read_html(StringIO(str(table)))[0]
                df.columns = RACEDATA.HORSE_RESULT_COLUMNS
                df.drop(columns=RACEDATA.HORSE_RESULT_DROP_COLUMNS, inplace=True)
                df["jockey_id"] = [
                    self._get_splitted_href(BeautifulSoup(str(td), "html.parser"), "a")
                    for num, td in enumerate(
                        self._select_all_elements(table, "td:nth-of-type(13)")
                    )
                    if num % 2 == 1
                ]
                df["race_id"] = [
                    self._get_splitted_href(BeautifulSoup(str(td), "html.parser"), "a")
                    for num, td in enumerate(
                        self._select_all_elements(table, "td:nth-of-type(5)")
                    )
                    if num % 2 == 1
                ]
                df["開催"] = df["開催"].apply(self.format_local_name)
            else:
                df = pd.DataFrame()
            return df
        except Exception as e:
            raise Exception(f"Error getting horse result: {e}")

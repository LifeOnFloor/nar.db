from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import datetime
from time import sleep

from modules.constants import URL
from modules.scrape import WebDriver


class RaceIdGetter:
    def __init__(self, driver):
        self.driver = driver

    def _get_soup(self, url: str):
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

    def get_race_ids(self, start_date: datetime.date, end_date: datetime.date):
        """
        指定された期間に存在するレースIDを取得します。
        """
        race_ids = []

        current_date = end_date
        while current_date >= start_date:
            # カレンダーのURLにアクセス
            url = (
                URL.NAR_CALENDER
                + f"?year={current_date.year}&month={current_date.month}"
            )
            soup = self._get_soup(url)
            local_1st_race_ids = self.get_month_local_pages(soup, current_date)
            if (
                current_date.year == start_date.year
                and current_date.month == start_date.month
            ):
                local_1st_race_ids = self.filter_race_id(
                    local_1st_race_ids, start_date, start=True
                )
            if (
                current_date.year == end_date.year
                and current_date.month == end_date.month
            ):
                local_1st_race_ids = self.filter_race_id(
                    local_1st_race_ids, end_date, start=False
                )
            race_ids.extend(local_1st_race_ids)

            current_date = self.get_pre_month(current_date)
        return race_ids

    def filter_race_id(self, race_ids: list, date: datetime.date, start: bool):
        """
        指定された日付でフィルタリングします。
        start == True: 指定された日付以降のレースIDを取得します。
        start == False: 指定された日付以前のレースIDを取得します。
        """
        if start:
            return [race_id for race_id in race_ids if int(race_id[8:10]) >= date.day]
        else:
            return [race_id for race_id in race_ids if int(race_id[8:10]) <= date.day]

    def get_pre_month(self, date: datetime.date):
        """
        指定された日付の前月を取得します。
        """
        if date.month == 1:
            return datetime.date(date.year - 1, 12, 1)
        else:
            return datetime.date(date.year, date.month - 1, 1)

    def get_month_local_pages(self, soup: BeautifulSoup, current_date: datetime.date):
        """
        レースカレンダーのページから、その月のレースカレンダーのページのリンクを取得します。
        ただし、帯広競馬場は除く。
        """
        local_1st_race_ids = []
        local_page_links = soup.select("div.RaceKaisaiBox > div > a")
        for link in local_page_links:
            href = link["href"]
            if "&kaisai_id=" in href:
                href = str(href).split("&kaisai_id=")[-1]
                if href.startswith(f"{current_date.year}65"):
                    # 帯広競馬場は除く
                    continue
                local_1st_race_ids.append(f"{href}01")
        return local_1st_race_ids

    def get_local_race_ids(self, race_id: str):
        url = URL.NAR_SHUTUBA + race_id
        soup = self._get_soup(url)
        num_wrap = soup.find("div", {"class": "RaceNumWrap"})
        links = BeautifulSoup(str(num_wrap), "html.parser").find_all("a")
        return [link["href"].split("race_id=")[-1] for link in links]

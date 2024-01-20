from modules.constants import URL
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from time import sleep


class GetOddsData:
    def __init__(self, driver, race_id: str):
        self.driver = driver
        self.race_id = race_id

    def get_tanfuku(self):
        url = URL.NAR_TAN + self.race_id
        self.driver.get(url)
        sleep(URL.WAIT_TIME)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

    def get_tan(self, soup: BeautifulSoup):
        """
        単勝のオッズを取得する
        """
        div = soup.find("div", {"id": "odds_tan_block"})

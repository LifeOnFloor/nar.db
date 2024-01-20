from bs4 import BeautifulSoup
from time import sleep
from selenium.common.exceptions import WebDriverException

from modules.constants import URL
from modules.scrape import WebDriver


class GetHumanData:
    def __init__(self, driver):
        self.driver = driver

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

    def _get_text(self, soup: BeautifulSoup, selector: str) -> str:
        """
        指定されたセレクターからテキストを取得する。
        """
        try:
            element = soup.select_one(selector)
            if element:
                return element.text.strip()
            else:
                return ""
        except Exception as e:
            raise Exception(f"Error selecting element {selector}: {e}")

    def _export_text(self, str: str) -> str:
        """
        指定された文字列から不要な文字を削除する。
        """
        try:
            return (
                str.replace("\n", "")
                .replace("\t", "")
                .replace(" ", "")
                .replace("(", "")
                .replace(")", "")
                .replace("\xa0", "")
            )
        except Exception as e:
            raise Exception(f"Error exporting text {str}: {e}")

    def _format_birthday(self, birthday_str: str) -> str:
        """
        誕生日をyyyy-mm-ddの形式に変換する。
        """
        try:
            birthday_str = self._export_text(birthday_str)
            return birthday_str.replace("/", "-")
        except Exception as e:
            raise Exception(f"Error converting birthday {birthday_str}: {e}")

    def _get_human_profile(self, url) -> dict:
        """
        騎手・調教師のプロフィールを取得する。
        """
        try:
            soup = self._get_soup(url)
            div = soup.find("div", {"class": "Name"})
            name = self._get_text(BeautifulSoup(str(div), "html.parser"), "h1").split(
                "\n"
            )
            name_kaki = self._export_text(name[0])
            name_yomi = self._export_text(name[-1])
            birthday = self._get_text(
                BeautifulSoup(str(div), "html.parser"), "p"
            ).split(" ")[0]
            birthday = self._format_birthday(birthday)
            return {"name": name_kaki, "yomi": name_yomi, "birthday": birthday}
        except Exception as e:
            raise Exception(f"Error retrieving human profile: {e}")

    def get_jockey_profile(self, human_id: str) -> dict:
        try:
            return self._get_human_profile(URL.JOCKEY + human_id)
        except WebDriverException as e:
            raise WebDriverException(f"Error loading Jockey profile page: {e}")

    def get_trainer_profile(self, human_id: str) -> dict:
        try:
            return self._get_human_profile(URL.TRAINER + human_id)
        except WebDriverException as e:
            raise WebDriverException(f"Error loading Trainer profile page: {e}")

from modules.constants.metaclass import ConstantMeta


class URL(metaclass=ConstantMeta):
    """
    URLを定義するクラス
    """

    # URLを取得するための待機時間
    WAIT_TIME: float = 3
    RETRY_COUNT: int = 2
    RETRY_WAIT_TIME: int = 60
    CACHE_SIZE: int = 3

    # ログインページ
    LOGIN_URL: str = "https://regist.netkeiba.com/account/?pid=login"

    # ドメイン
    NAR_DOMAIN: str = "https://nar.netkeiba.com/"
    DB_DOMAIN: str = "https://db.netkeiba.com/"

    # レースカレンダー
    NAR_CALENDER: str = f"{NAR_DOMAIN}top/calendar.html"

    # レース結果
    NAR_RESULT: str = f"{NAR_DOMAIN}race/result.html?race_id="

    # 出馬表
    NAR_SHUTUBA: str = f"{NAR_DOMAIN}race/shutuba.html?race_id="

    # 地方競馬オッズ
    NAR_TAN: str = f"{NAR_DOMAIN}odds/index.html?type=b1&race_id="
    NAR_2FUKU: str = f"{NAR_DOMAIN}odds/index.html?type=b4&race_id="
    NAR_WIDE: str = f"{NAR_DOMAIN}odds/index.html?type=b5&race_id="
    NAR_2TAN: str = f"{NAR_DOMAIN}odds/index.html?type=b6&race_id="
    NAR_3FUKU: str = f"{NAR_DOMAIN}odds/index.html?type=b7&race_id="
    NAR_3TAN: str = f"{NAR_DOMAIN}odds/index.html?type=b8&race_id="

    # 馬のページ
    HORSE: str = f"{DB_DOMAIN}horse/"
    HROSE_PED: str = f"{DB_DOMAIN}horse/ped/"

    # 騎手のページ
    JOCKEY: str = f"{DB_DOMAIN}jockey/"

    # 調教師のページ
    TRAINER: str = f"{DB_DOMAIN}trainer/"

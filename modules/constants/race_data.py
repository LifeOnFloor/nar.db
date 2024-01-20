from modules.constants.metaclass import ConstantMeta


class RACEDATA(metaclass=ConstantMeta):
    """
    レースデータに関する定数
    """

    ##########
    # 競馬場 #
    ##########

    LOCALNAME_CODE: dict = {
        "札幌": "01",
        "函館": "02",
        "福島": "03",
        "新潟": "04",
        "東京": "05",
        "中山": "06",
        "中京": "07",
        "京都": "08",
        "阪神": "09",
        "小倉": "10",
        "門別": "30",
        "北見": "31",
        "岩見沢": "32",
        "帯広": "33",
        "旭川": "34",
        "盛岡": "35",
        "水沢": "36",
        "上山": "37",
        "三条": "38",
        "足利": "39",
        "宇都宮": "40",
        "高崎": "41",
        "浦和": "42",
        "船橋": "43",
        "大井": "44",
        "川崎": "45",
        "金沢": "46",
        "笠松": "47",
        "名古屋": "48",
        "園田": "50",
        "姫路": "51",
        "益田": "52",
        "福山": "53",
        "高知": "54",
        "佐賀": "55",
        "荒尾": "56",
        "中津": "57",
        "札幌（地方競馬）": "58",
        "函館（地方競馬）": "59",
        "新潟（地方競馬）": "60",
        "中京（地方競馬）": "61",
        "帯広ば": "65",
        "アスコッ": "A0",  # イギリス:アスコット競馬場
        "アメリカ": "A4",  # アメリカ
        "イギリス": "A6",  # イギリス
        "フランス": "A8",  # フランス
        "グッドウ": "AF",  # イギリス:グッドウッド競馬場
        "カラ": "B0",  # アイルランド:カラ競馬場
        "オースト": "B6",  # オーストラリア
        "カナダ": "B8",  # カナダ
        "ドーヴィ": "C4",  # フランス:ドーヴィル競馬場
        "アラブ首": "C7",  # アラブ首長国連邦
        "ロンシャ": "C8",  # フランス:ロンシャン競馬場
        "ウッドバ": "E3",  # カナダ:ウッドバイン競馬場
        "トルコ": "E8",  # トルコ
        "サンタア": "F3",  # アメリカ:サンタアニタパーク競馬場
        "チャーチ": "F4",  # アメリカ:チャーチルダウンズ競馬場
        "ベルモン": "FD",  # アメリカ:ベルモントパーク競馬場
        "香港": "G0",  # 香港
        "フレミン": "G4",  # オーストラリア:フレミントン競馬場
        "ムーニー": "G5",  # オーストラリア:ムーニーバレー競馬場
        "コーフィ": "G6",  # オーストラリア:コーフィールド競馬場
        "シャティ": "H1",  # 香港:シャティン競馬場
        "メイダン": "J0",  # アラブ首長国連邦:メイダン競馬場
        "ソウル": "K0",  # 韓国:ソウル競馬場
        "シンガポ": "M0",  # シンガポール
        "キングア": "P0",  # サウジアラビア:キングアブドゥルアジーズ競馬場
    }
    # 海外競馬場の一覧が掲載されているページ
    # https://www.jairs.jp/contents/courses/index.html

    LOCALCODE_NAME: dict = {k: v for v, k in LOCALNAME_CODE.items()}

    ###############
    # レースページ #
    ###############

    # レースページの出馬表の列名
    SHUTUBA_COLUMNS: list[str] = [
        "枠",
        "馬番",
        "馬名",
        "性齢",
        "斤量",
        "騎手",
        "厩舎",
        "馬体重(増減)",
        "単勝",
        "人気",
    ]

    # レースページの事前情報のキー
    TEMP_RACE_INFO_KEYS: list[str] = [
        "race_name",
        "date",
        "course_and_distance",
        "around_and_weather",
        "ground_state",
        "no_use",
        "local",
        "no_use",
        "grade",
        "number_of_horses",
        "prize",
    ]

    # レースページの天気のリスト
    WEATHER_LIST: tuple = ("晴", "曇", "小雨", "雨", "小雪", "雪")

    # レースページの馬場のリスト
    GROUND_STATE_LIST: tuple = ("良", "稍重", "重", "不良")

    # レースページのコースのリスト
    COURSE_LIST: tuple = ("芝", "ダ", "障")

    ###########
    # 馬ページ #
    ###########

    # 馬ページのプロフィールの列名
    HORSE_PROFILE_COLUMNS: list[str] = [
        "生年月日",
        "調教師",
        "馬主",
        "生産者",
        "産地",
        "セリ取引価格",
    ]

    # 馬ページの過去戦績の列名
    HORSE_RESULT_COLUMNS: list[str] = [
        "日付",
        "開催",
        "天気",
        "R",
        "レース名",
        "映像",
        "頭数",
        "枠番",
        "馬番",
        "オッズ",
        "人気",
        "着順",
        "騎手",
        "斤量",
        "距離",
        "馬場",
        "馬場指数",
        "タイム",
        "着差",
        "ﾀｲﾑ指数",
        "通過",
        "ペース",
        "上り",
        "馬体重",
        "厩舎コメント",
        "備考",
        "勝ち馬(2着馬)",
        "賞金",
    ]

    HORSE_RESULT_DROP_COLUMNS: list[str] = ["馬場指数", "ﾀｲﾑ指数", "映像", "厩舎コメント", "備考"]

    HORSE_RESULT_COLUMNS_EN: list[str] = [
        "date",
        "local",
        "weather",
        "r",
        "race_name",
        "number_of_horses",
        "waku",
        "umaban",
        "odds",
        "popularity",
        "order_of_finish",
        "jockey",
        "jin",
        "distance",
        "ground_state",
        "time",
        "difference",
        "passing",
        "pace",
        "up",
        "weight",
        "win_horse",
        "prize",
        "jockey_id",
        "race_id",
    ]

    # 馬ページの事前情報関連の列名
    PRE_RACE_COLUMNS_FOR_HORSE_PAGE: list[str] = [
        "race_id",
        "race_name",
        "date",
        "course",
        "distance",
        # "around",
        "weather",
        "ground_state",
        "local",
        # "grade",
        "number_of_horses",
        # "prize",
    ]

    FORMATTED_PRE_RACE_COLUMNS_FOR_HORSE_PAGE: list[str] = [
        "_id",
        "race_name",
        "date",
        "course",
        "distance",
        "weather",
        "ground_state",
        "local",
        "number_of_horses",
    ]

    # 馬ページのレース結果関連の列名
    RESULT_COLUMNS_FOR_HORSE_PAGE: list[str] = [
        "race_id",
        "umaban",
        "order_of_finish",
        "time",
        "difference",
        "passing",
        "pace",
        "up",
    ]

    # 馬ページの出馬表関連の列名
    SHUTUBA_COLUMNS_FOR_HORSE_PAGE: list[str] = [
        "race_id",
        "umaban",
        "jin",
        "jockey_id",
        "trainer_id",
        "weight",
    ]

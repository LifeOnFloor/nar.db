import streamlit as st
import app
import datetime
from time import sleep
from streamlit.delta_generator import DeltaGenerator

# TODO: 一度取得した馬情報を更新するさいの処理を追加する
# DONE: 2022年11月20日から2023年11月20日までのレースを取得した


def explanation():
    expander = st.expander("注意事項", expanded=False)
    expander.info("netkeiba.comからデータを取得させていただいております。サーバーに負荷をかけないように、頻繁な更新はお控えください。")
    expander.warning("更新している間はブラウザを閉じないでください。")


def get_date_range(container: DeltaGenerator):
    container.info("取得する日付範囲を選択してください。")
    today = datetime.datetime.today()
    start_date, end_date = None, None

    default_date_col, custom_date_col = container.columns(2)
    toggle_custom = default_date_col.toggle(label="日付範囲をカスタムする", value=False)
    if not toggle_custom:
        toggle_yesterday = default_date_col.toggle(label="昨日のレースを取得する", value=True)
        default_date_col.toggle(label="今日のレースを取得する", value=True, disabled=True)
        toggle_tomorrow = default_date_col.toggle(label="明日のレースを取得する", value=False)

        if toggle_tomorrow and toggle_yesterday:
            start_date = today - datetime.timedelta(days=1)
            end_date = today + datetime.timedelta(days=1)
        elif toggle_yesterday:
            start_date = today - datetime.timedelta(days=1)
            end_date = today
        elif toggle_tomorrow:
            start_date = today
            end_date = today + datetime.timedelta(days=1)
        else:
            start_date, end_date = today, today
    else:
        start_date = today - datetime.timedelta(days=365)
        end_date = today

    start_date = custom_date_col.date_input(
        label="開始日（含む）",
        value=start_date,
        min_value=datetime.date(2016, 1, 1),
        max_value=today + datetime.timedelta(days=1),
        format="YYYY-MM-DD",
        disabled=not toggle_custom,
    )
    end_date = custom_date_col.date_input(
        label="終了日（含む）",
        value=end_date,
        min_value=datetime.date(2016, 1, 1),
        max_value=today + datetime.timedelta(days=1),
        format="YYYY-MM-DD",
        disabled=not toggle_custom,
    )
    start_date = datetime.datetime.strptime(str(start_date), "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(str(end_date), "%Y-%m-%d").date()
    if start_date > end_date:
        container.error("開始日は終了日以前の日付にしてください。")
        st.stop()
    return start_date, end_date


def get_update_settings(container: DeltaGenerator):
    container.info("更新するデータを選択してください。")
    race_col, horse_col, human_col = container.columns(3)
    (
        races_update_toggle,
        horse_profile_toggle,
        pedigree_toggle,
        results_toggle,
        jockey_toggle,
        trainer_toggle,
    ) = (None, None, None, None, None, None)

    races_update_toggle = race_col.toggle(label="レース", value=True)
    horse_profile_toggle = horse_col.toggle(label="馬プロフィール", value=True)
    pedigree_toggle = horse_col.toggle(label="血統データ", value=False)
    results_toggle = horse_col.toggle(label="過去戦績", value=True)
    jockey_toggle = human_col.toggle(label="騎手", value=True)
    trainer_toggle = human_col.toggle(label="調教師", value=True)
    return (
        races_update_toggle,
        horse_profile_toggle,
        pedigree_toggle,
        results_toggle,
        jockey_toggle,
        trainer_toggle,
    )


def get_update_waiting_time(container: DeltaGenerator):
    """
    更新時間を設定する
    """
    container.info("更新時間を設定してください。（設定しない場合はすぐに更新します）")
    set_update_time = container.checkbox(label="更新時間を設定する", value=False)
    if set_update_time:
        current_datetime = datetime.datetime.now()
        current_plus_1hour = current_datetime + datetime.timedelta(hours=1)
        current_plus_1hour = current_plus_1hour.replace(
            minute=0, second=0, microsecond=0
        )
        update_time = container.time_input(
            label="更新時間",
            value=current_plus_1hour,
        )

        if current_datetime.time() >= update_time:
            update_datetime = datetime.datetime.combine(
                current_datetime.date() + datetime.timedelta(days=1), update_time
            )
        else:
            update_datetime = datetime.datetime.combine(
                current_datetime.date(), update_time
            )
        waiting_seconds = (update_datetime - current_datetime).seconds
        waiting_minutes = int(waiting_seconds / 60)
        container.info(f'更新時間は{update_datetime.strftime("%Y-%m-%d %H:%M:%S")}です。')
    else:
        waiting_minutes = 0
    return waiting_minutes


def wait_for_update(waiting_minutes: int, interval_seconds: int = 60):
    """
    更新時間まで待機する
    """
    log_wait_time = st.status("更新時間まで待機中...", expanded=True)
    progress_bar = log_wait_time.progress(0)
    if waiting_minutes > 0:
        for i in range(waiting_minutes):
            progress_bar.progress(i / waiting_minutes, f"{i} / {waiting_minutes} 分経過")
            sleep(interval_seconds)
    log_wait_time.update(label="待機完了", state="complete", expanded=False)


def update_race_data(start_date, end_date):
    """
    レース情報と出馬表をデータベースに格納する
    """
    log_races_update = st.status("レースの更新中...", expanded=True)
    log_races_update.info("レースIDを取得中...")
    progress_bar = log_races_update.progress(0)
    race_ids = app.get_race_ids(start_date, end_date)
    race_id_list = []
    driver = app.get_driver()
    for num, race_id in enumerate(race_ids):
        local_race_ids, driver = app.get_local_race_ids(driver, race_id)
        race_id_list.extend(local_race_ids)
        progress_bar.progress(
            num / len(race_ids), f"{num} / {len(race_ids)} race id: {race_id}"
        )
    driver.quit()
    progress_bar.progress(1.0, "レースIDを取得しました。")

    log_races_update.info("レース情報と出馬表をデータベースに格納中...")
    predict_complete_time = len(race_id_list) * 3 / 60
    log_races_update.write(f"予想時間：{predict_complete_time}分")
    progress_bar = log_races_update.progress(0)
    driver = app.get_driver()
    mongo = app.get_mongo_client()
    for num, race_id in enumerate(race_id_list):
        driver = app.upsert_pre_race_shutuba(driver, mongo, race_id, force=True)
        progress_bar.progress(
            num / len(race_id_list),
            f"{num} / {len(race_id_list)} race id: {race_id}",
        )
    driver.quit()
    mongo.close()
    progress_bar.progress(1.0, "レース情報と出馬表をデータベースに格納しました。")
    log_races_update.update(label="レースの更新完了", state="complete", expanded=False)


def update_horse_data(
    start_date, end_date, horse_profile_toggle, pedigree_toggle, results_toggle
):
    log_horses_update = st.status("馬情報の更新中...", expanded=True)
    log_horses_update.info("馬IDを取得中...")
    horse_id_list = app.find_horse_ids_from_date(start_date, end_date)
    log_horses_update.progress(1.0, "馬IDを取得しました。")

    get_type, message_list = [], []
    if horse_profile_toggle:
        get_type.append("profile")
        message_list.append("馬プロフィール")
    if pedigree_toggle:
        get_type.append("pedigree")
        message_list.append("血統データ")
    if results_toggle:
        get_type.append("result")
        message_list.append("過去戦績")
    log_horses_update.info(f"{message_list}をデータベースに格納中...")
    predict_complete_time = (
        len(horse_id_list) * len(get_type) * 5 / 60 if len(get_type) > 0 else 0
    )
    log_horses_update.write(f"予想時間：{predict_complete_time}分")

    progress_bar = log_horses_update.progress(0)
    driver = app.get_driver()
    mongo = app.get_mongo_client()
    for num, horse_id in enumerate(horse_id_list):
        try:
            driver = app.upsert_horse_data(driver, mongo, horse_id, get_type)
        except Exception:
            driver = app.get_driver()
            mongo = app.get_mongo_client()
            driver = app.upsert_horse_data(driver, mongo, horse_id, get_type)
        progress_bar.progress(
            num / len(horse_id_list),
            f"{num} / {len(horse_id_list)} horse id: {horse_id}",
        )
    driver.quit()
    mongo.close()
    progress_bar.progress(1.0, "馬情報をデータベースに格納しました。")
    log_horses_update.update(label="馬情報の更新完了", state="complete", expanded=False)


def update_human_data(type: str):
    """
    騎手または調教師の情報をデータベースに格納する

    Parameters
    ----------
    type : str | "jockey" or "trainer"
        騎手か調教師か
    """
    if type == "jockey":
        type_message = "騎手"
    elif type == "trainer":
        type_message = "調教師"
    else:
        raise Exception(f"Invalid type: {type}")

    log_human_update = st.status(f"{type_message}の更新中...", expanded=True)
    log_human_update.info(f"{type_message}IDを取得中...")

    human_id_list = app.find_human_ids_for_db(type)

    progress_bar = log_human_update.progress(0)
    driver = app.get_driver()
    mongo = app.get_mongo_client()
    for num, human_id in enumerate(human_id_list):
        try:
            driver = app.upsert_human_data(driver, mongo, human_id, type)
        except Exception:
            driver = app.get_driver()
            mongo = app.get_mongo_client()
            driver = app.upsert_human_data(driver, mongo, human_id, type)
        progress_bar.progress(
            num / len(human_id_list),
            f"{num} / {len(human_id_list)} {type} id: {human_id}",
        )
    driver.quit()
    mongo.close()
    progress_bar.progress(1.0, f"{type_message}情報をデータベースに格納しました。")
    log_human_update.update(
        label=f"{type_message}の更新完了", state="complete", expanded=False
    )


def update_database(
    update_settings,
    start_date,
    end_date,
):
    (
        races_update_toggle,
        horse_profile_toggle,
        pedigree_toggle,
        results_toggle,
        jockey_toggle,
        trainer_toggle,
    ) = update_settings
    if races_update_toggle:
        update_race_data(start_date, end_date)
    if horse_profile_toggle or pedigree_toggle:
        update_horse_data(
            start_date, end_date, horse_profile_toggle, pedigree_toggle, results_toggle
        )
    if jockey_toggle:
        update_human_data("jockey")
    if trainer_toggle:
        update_human_data("trainer")
    st.success("finished! 🎉🎉🎉")


def create_index(container: DeltaGenerator):
    """
    データベースのインデックスを作成する
    """
    index_container = container.expander("インデックスの作成", expanded=False)
    all_check = index_container.checkbox("すべて", value=True, key="create_all_index")
    create_index_list = []
    if not all_check:
        if index_container.checkbox("レース情報", value=True, key="create_pre_race_index"):
            create_index_list.append("pre_race")
        if index_container.checkbox("出馬表", value=True, key="create_shutuba_index"):
            create_index_list.append("shutuba")
        if index_container.checkbox("レース結果", value=True, key="create_result_index"):
            create_index_list.append("result")
        if index_container.checkbox("馬情報", value=True, key="create_horse_index"):
            create_index_list.append("horse")
        if index_container.checkbox("騎手情報", value=True, key="create_jockey_index"):
            create_index_list.append("jockey")
        if index_container.checkbox("調教師情報", value=True, key="create_trainer_index"):
            create_index_list.append("trainer")
        if index_container.checkbox("血統情報", value=True, key="create_pedigree_index"):
            create_index_list.append("pedigree")
    else:
        create_index_list = [
            "pre_race",
            "shutuba",
            "result",
            "horse",
            "jockey",
            "trainer",
            "pedigree",
        ]
    if index_container.button("インデックスを作成する", use_container_width=True):
        index_container.info("インデックスを作成中...")
        app.create_index(create_index_list)
        index_container.success("インデックスの作成が完了しました。")


def settings(container: DeltaGenerator) -> tuple:
    start_date, end_date = get_date_range(container)
    if start_date is None or end_date is None:
        st.stop()

    update_settings = get_update_settings(container)
    waiting_minutes = get_update_waiting_time(container)
    if container.button("更新する", use_container_width=True):
        return start_date, end_date, update_settings, waiting_minutes
    else:
        st.stop()
        return None, None, None, None


def display_settings(start_date, end_date, update_settings, container: DeltaGenerator):
    start_date_col, end_date_col = container.columns(2)
    start_date_col.date_input(
        label="開始日", value=start_date, disabled=True, key="start_date_input_display"
    )
    end_date_col.date_input(
        label="終了日", value=end_date, disabled=True, key="end_date_input_display"
    )
    container.info("更新するデータ")
    if update_settings[0]:
        container.write("- レース")
    if update_settings[1]:
        container.write("- 馬プロフィール")
    if update_settings[2]:
        container.write("- 血統データ")
    if update_settings[3]:
        container.write("- 過去戦績")
    if update_settings[4]:
        container.write("- 騎手")
    if update_settings[5]:
        container.write("- 調教師")


def main():
    st.set_page_config(
        page_title="地方競馬",
        layout="centered",
        initial_sidebar_state="auto",
    )
    explanation()

    create_index(st.sidebar)

    placeholder = st.empty()
    start_date, end_date, update_settings, waiting_minutes = settings(
        placeholder.container()
    )

    if start_date and end_date and update_settings:
        placeholder.empty()
        display_settings(start_date, end_date, update_settings, placeholder.container())
        wait_for_update(waiting_minutes)
        update_database(
            update_settings,
            start_date,
            end_date,
        )

    if st.button("設定画面に戻る", use_container_width=True):
        st.experimental_rerun()


if __name__ == "__main__":
    main()

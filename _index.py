import streamlit as st
import app
import datetime
import pandas as pd
from time import sleep

#################
# Global Config #
#################

st.set_page_config(
    page_title="data",
    layout="wide",
    initial_sidebar_state="auto",
)


today = datetime.date.today()
sidebar = st.sidebar

race_col, analyze_col, database_col = sidebar.tabs(["race", "analyze", "database"])
current_date = race_col.date_input(
    label="current_date",
    value="today",
    min_value=datetime.date(2020, 1, 1),
    max_value=today + datetime.timedelta(days=1),
    format="YYYY-MM-DD",
    label_visibility="hidden",
)
current_date = datetime.datetime.strptime(str(current_date), "%Y-%m-%d").date()


###################
# race select tab #
###################

race_id_dict = get_day_race_ids(current_date)
local = race_col.selectbox(
    label="local", options=race_id_dict.keys(), label_visibility="hidden"
)
r = race_col.select_slider(
    label="r",
    options=range(1, len(race_id_dict[local]) + 1, 1),
    label_visibility="hidden",
)
race_id = race_id_dict[local][r - 1]  # type: ignore


pre_race_data = app.get_pre_race_data(race_id)
info = pre_race_data["pre_race_data"]
# horse_result_df = app.get_horse_result_data(pre_race_data["shutuba"]["horse_id"].values)

horse_result_df = get_horse_result_data(pre_race_data["shutuba"]["horse_id"].values)


# display the race info
if info and len(horse_result_df) > 0:
    race_col.info(f'{info["date"].hour}:{info["date"].minute} | {info["title"]}')
    race_col.info(
        f'{info["course"]}/{info["around"]}/{info["distance"]}/{info["ground_state"]}/{info["weather"]}'
    )
    race_col.info(f'{info["grade"]}/{info["number_of_horses"]}頭')
    if race_col.button("update pre race data"):
        for race_id in race_id_dict[local]:
            app.update_pre_race_data(race_id)
else:
    race_col.info("no data")
    analyze_col.info("no data")
    horse_result_df = pd.DataFrame(columns=["date", "time", "馬番"])
horse_result_df_columns = []


###############
# analyze tab #
###############

if len(horse_result_df) > 0:
    analyze_col.info(f"{local} {current_date} {r}R")
    # select columns to plot
    horse_result_columns_expander = analyze_col.expander(
        label="select horse_result_df columns", expanded=False
    )
    horse_result_df_columns = horse_result_columns_expander.multiselect(
        label="select columns",
        options=horse_result_df.columns,
        default=[
            "weather",
            "date",
            "course",
            "distance",
            "ground_state",
            "local",
            "number_of_horses",
            "馬番",
            "order_of_finish",
            "time",
            "difference",
            "passing",
            "pace",
            "up",
            # "grade",
        ],
        label_visibility="hidden",
    )

    # select the date range to plot
    horse_result_df["date"] = pd.to_datetime(
        horse_result_df["date"], errors="coerce"
    ).dt.date
    start_date_col, end_date_col = analyze_col.columns(2)
    start_date = start_date_col.date_input(
        label="start_date",
        value=current_date - datetime.timedelta(days=365),
        min_value=current_date - datetime.timedelta(days=365 * 5),
        max_value=current_date,
        format="YYYY-MM-DD",
        label_visibility="hidden",
    )
    end_date = end_date_col.date_input(
        label="end_date",
        value=current_date - datetime.timedelta(days=1),
        min_value=current_date - datetime.timedelta(days=365 * 5),
        max_value=current_date,
        format="YYYY-MM-DD",
        label_visibility="hidden",
    )
    start_date = datetime.datetime.strptime(str(start_date), "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(str(end_date), "%Y-%m-%d").date()

    # select umaban to plot
    order_select = analyze_col.multiselect(
        label="order",
        options=horse_result_df.loc[:, "馬番"].unique(),
        default=horse_result_df.loc[:, "馬番"].unique(),
        label_visibility="hidden",
    )

    # select ground_state to plot
    ground_state_select = analyze_col.multiselect(
        label="ground_state",
        options=horse_result_df.loc[:, "ground_state"].unique(),
        default=horse_result_df.loc[:, "ground_state"].unique(),
        label_visibility="hidden",
    )

    # select local to plot
    local_select = analyze_col.multiselect(
        label="local",
        options=horse_result_df.loc[:, "local"].unique(),
        default=info["local"] if info else horse_result_df.loc[:, "local"].unique(),
        label_visibility="hidden",
    )

    # select course to plot
    course_select = analyze_col.multiselect(
        label="course",
        options=horse_result_df.loc[:, "course"].unique(),
        default=info["course"] if info else horse_result_df.loc[:, "course"].unique(),
        label_visibility="hidden",
    )

    # select distance to plot
    distance_select = analyze_col.multiselect(
        label="distance",
        options=horse_result_df.loc[:, "distance"].unique(),
        default=info["distance"]
        if info
        else horse_result_df.loc[:, "distance"].unique(),
        label_visibility="hidden",
    )

    # filter horse_result_df
    horse_result_plot_df = horse_result_df[
        (horse_result_df["date"] <= end_date)
        & (horse_result_df["date"] >= start_date)
        & (horse_result_df["馬番"].isin(order_select))
        & (horse_result_df["ground_state"].isin(ground_state_select))
        & (horse_result_df["local"].isin(local_select))
        & (horse_result_df["course"].isin(course_select))
        & (horse_result_df["distance"].isin(distance_select))
    ][["date", "time", "馬番"]]

    # sort horse_result_df


else:
    horse_result_plot_df = pd.DataFrame()


###################
# Database Column #
###################

start_date = database_col.date_input(
    label="start_date",
    value=today,
    min_value=datetime.date(2016, 1, 1),
    max_value=today + datetime.timedelta(days=1),
    format="YYYY-MM-DD",
    label_visibility="hidden",
)
end_date = database_col.date_input(
    label="end_date",
    value=today,
    min_value=datetime.date(2016, 1, 1),
    max_value=today + datetime.timedelta(days=1),
    format="YYYY-MM-DD",
    label_visibility="hidden",
)
start_date = datetime.datetime.strptime(str(start_date), "%Y-%m-%d").date()
end_date = datetime.datetime.strptime(str(end_date), "%Y-%m-%d").date()

########
# display
########


@st.cache_data
def get_race_ids(start_date, end_date):
    return app.get_race_ids(start_date, end_date)


database_container = st.container()
if database_col.button("insert"):
    insert_cancel_flag = False
    database_container_delete_button = database_container.button(
        "delete insert container"
    )
    if database_container_delete_button:
        insert_cancel_flag = True

    race_ids = get_race_ids(start_date, end_date)
    database_container.write(race_ids)
    progress_bar = database_container.progress(0)
    while True:
        try:
            for num, race_id in enumerate(race_ids):
                progress_bar.progress(num / len(race_ids), str(race_id))
                app.insert_pre_race_data(race_id)
            break
        except Exception as e:
            database_container.write(e)
            database_container.write("retry in 60 seconds...")
            sleep(60)
            continue
    progress_bar.progress(1.0)
    database_container.write("inserted")

if database_col.button("update horse result"):
    database_container_delete_button = database_container.button(
        "DELETE container for update horse result"
    )
    if database_container_delete_button:
        database_container.empty()
    horse_ids = app.get_horse_ids(start_date, end_date)
    database_container.write(start_date)
    database_container.write(end_date)
    database_container.write(horse_ids)
    progress_bar = database_container.progress(0)

    while True:
        try:
            driver = app.get_driver()
            mongo = app.get_mongo_client()
            for num, horse_id in enumerate(horse_ids):
                progress_bar.progress(num / len(horse_ids), str(horse_id))
                app.insert_horse_data(driver, mongo, horse_id)
            break
        except Exception as e:
            database_container.write(e)
            database_container.write("retry in 60 seconds...")
            sleep(60)
            continue
    progress_bar.progress(1.0)
    database_container.write("inserted")
    driver.quit()
    mongo.close()


################
# display data #
################

# plot horse_result_df
if len(horse_result_plot_df) > 0:
    st.pyplot(
        app.plot_horse_result(horse_result_plot_df),
        clear_figure=True,
        dpi=600,
    )
else:
    st.info("result data is not found")

# display shutuba data
if len(pre_race_data["shutuba"]) > 0:
    st.dataframe(
        data=pre_race_data["shutuba"].loc[
            :, ["umaban", "horse_id", "jin", "jockey_id", "trainer_id", "weight"]
        ],
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("shutuba data is not found")

# display horse result data
if len(horse_result_df) > 0:
    st.dataframe(
        data=horse_result_df[horse_result_df_columns],
        use_container_width=True,
        hide_index=True,
    )

import os
import sys

sys.path.append(os.path.abspath("."))

import streamlit as st
from streamlit.elements.lib.column_types import ColumnConfig
from pandas import DataFrame
from data_classes.game_json import History, Session
from data_classes.session_df import SessionDf
from data_classes.enums import Attack, Poignee
import random as rd


st.set_page_config(layout="wide", page_title="Tarot Score Tracker", page_icon="🃏")


def landing_page_display_session(session: Session):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load this session"):
            st.session_state.session = SessionDf.from_json(session)
            st.rerun()
        st.markdown(f"##### {session.date_}")
        st.json(session.scores())
    with col2:
        st.pyplot(session.plot_score_evolution())


@st.dialog("Start new game")
def new_game():
    hist: History = st.session_state.history
    with st.form("New game form"):
        players: list[str] = st.multiselect("Players", options=hist.players)
        if not st.form_submit_button():
            return
        if len(players) < 5:
            st.warning("There should be at least 5 players")
            return
        hist.players = players
        hist.save()
        st.session_state.session = SessionDf.empty(players)
        st.rerun()


@st.fragment()
def landing_page_sidebar():
    hist: History = st.session_state.history
    players: list[str] = list(st.data_editor(DataFrame(hist.players, columns=["Players"]), num_rows="dynamic")["Players"])
    if len(set(players)) < len(players):
        st.error("Error: Duplicates in player list")
        return
    if st.button("Save Player modifications"):
        hist.players = players
        st.rerun()
    if st.button("Start new game"):
        new_game()


def landing_page():
    with st.sidebar:
        landing_page_sidebar()
    hist: History = st.session_state.history
    for i, session in enumerate(hist.history):
        with st.container(key=f"Session {i}"):
            landing_page_display_session(session)


def score_tracker():
    session: SessionDf = st.session_state.session
    column_config: dict[str, ColumnConfig] = {
        SessionDf.Rows.ATTAQUER.value: st.column_config.SelectboxColumn(
            SessionDf.Rows.ATTAQUER.value, options=session.players, required=True, width="small"
        ),
        SessionDf.Rows.CALLED.value: st.column_config.SelectboxColumn(
            SessionDf.Rows.CALLED.value, options=session.players, required=True, width="small"
        ),
        SessionDf.Rows.DEFENSE.value: st.column_config.SelectboxColumn(
            SessionDf.Rows.DEFENSE.value, options=session.players, required=True, width="small"
        ),
        SessionDf.Rows.PRISE.value: st.column_config.SelectboxColumn(
            SessionDf.Rows.PRISE.value, options=[e.value for e in Attack], required=True, default=Attack.GUARDE.value, width="small"
        ),
        SessionDf.Rows.SCORE.value: st.column_config.NumberColumn(SessionDf.Rows.SCORE.value, format="%.0f", required=True, width="small"),
        SessionDf.Rows.BOUTS.value: st.column_config.SelectboxColumn(
            SessionDf.Rows.BOUTS.value, options=[0, 1, 2, 3], default=0, required=True, width="small"
        ),
        SessionDf.Rows.PETIT_AU_BOUT.value: st.column_config.CheckboxColumn(SessionDf.Rows.PETIT_AU_BOUT.value, default=False, width="small"),
        SessionDf.Rows.POIGNEE.value: st.column_config.SelectboxColumn(
            SessionDf.Rows.POIGNEE.value, options=[e.value for e in Poignee], default=Poignee.NONE.value, width="small", required=True
        ),
    } | {p: st.column_config.NumberColumn(label=p, format="%.0f", disabled=True) for p in session.players}

    edited_df = st.data_editor(session.df, column_config=column_config, num_rows="dynamic")
    if st.button("Save", key="Save dataframe"):
        session.df = edited_df
        st.rerun


def display_player_graphs(): ...


def session_sidebar():
    st.button("Home", icon=":material/home:", type="tertiary")
    session: SessionDf = st.session_state.session
    st.table(session.players)
    if st.button("Shuffle players"):
        rd.shuffle(session.players)


def session_page():
    score_tracker_tab, graphs_tab = st.tabs(["Score tracker", "Graphs"])
    with st.sidebar:
        session_sidebar()
    with score_tracker_tab:
        score_tracker()
    with graphs_tab:
        display_player_graphs()


def main():
    if not st.session_state.session:
        landing_page()
        return
    session_page()


if "session" not in st.session_state:
    st.session_state.session = None
    st.session_state.history = History.load()
main()

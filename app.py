import os
import sys

sys.path.append(os.path.abspath("."))

import streamlit as st
from streamlit.elements.lib.column_types import ColumnConfig
from pandas import DataFrame
from data_classes.game_json import History, Session, Round5P

# from data_classes.session_df import SessionDf
from data_classes.enums import Attack, Poignee, PetitAuBout
import random as rd


st.set_page_config(layout="wide", page_title="Tarot Score Tracker", page_icon="🃏")


@st.dialog("Delete session")
def delete_session(session: Session, i: int):
    hist: History = st.session_state.history
    if st.button("Confirm", key=f"Confirm delete {i}", use_container_width=True):
        hist.history.remove(session)
        hist.save()
        st.rerun()


def landing_page_display_session(session: Session, i: int):
    col1, col2 = st.columns(2)
    with col1:
        col_date, col_delete, _ = st.columns([1, 1, 3])
        with col_date:
            if st.button(str(session.date_), type="primary", key=f"Play session {i}", use_container_width=True):
                st.session_state.session = session
                st.rerun()
        with col_delete:
            st.button("delete", key=f"delete{i}", icon=":material/delete:", on_click=delete_session, args=(session, i), use_container_width=True)
        st.dataframe(session.scores_df(), use_container_width=True)
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
        session = Session.new_game(players=hist.players)
        st.session_state.session = session
        hist.history.append(session)
        st.rerun()


@st.fragment()
def landing_page_sidebar():
    hist: History = st.session_state.history
    players: list[str] = list(st.data_editor(DataFrame(hist.players, columns=["Players"]), num_rows="dynamic", use_container_width=True)["Players"])
    if len(set(players)) < len(players):
        st.error("Error: Duplicates in player list")
        return
    if st.button("Save Player modifications"):
        hist.players = players
        hist.save()
        st.rerun()
    if st.button("Start new game"):
        new_game()


def landing_page():
    with st.sidebar:
        landing_page_sidebar()
    hist: History = st.session_state.history
    print(len(hist.history))
    for i, session in enumerate(hist.history[::-1]):
        with st.container(key=f"Session {i}"):
            landing_page_display_session(session, i)


def score_tracker():
    session: Session = st.session_state.session
    for i, round in enumerate(session.rounds):
        col1, col2 = st.columns(2)
        with col1:
            col_name, col_selec, col_score = st.columns([2, 1, 1])
            with col_name:
                round.attack = st.selectbox(
                    "Preneur",
                    options=session.players,
                    key=f"Preneur {i}",
                    index=session.players.index(round.attack),
                    on_change=lambda x: round.set_attack(st.session_state[x]),
                    args=(f"Preneur {i}",),
                )
                round.appel = st.selectbox(
                    "Appelé",
                    options=session.players,
                    key=f"Called {i}",
                    index=session.players.index(round.appel),
                    on_change=lambda x: round.set_appel(st.session_state[x]),
                    args=(f"Called {i}",),
                )
                round.defense = st.multiselect(
                    "Défense",
                    options=session.players,
                    key=f"defense {i}",
                    default=round.defense,
                    on_change=lambda x: round.set_defense(st.session_state[x]),
                    args=(f"defense {i}",),
                )

            with col_selec:
                round.attack_type = Attack(
                    st.selectbox(
                        "Prise",
                        list(Attack),
                        index=list(Attack).index(round.attack_type),
                        key=f"attack_type {i}",
                        on_change=lambda x: round.set_attack_type(st.session_state[x]),
                        args=(f"attack_type {i}",),
                    )
                )
                round.poignees = st.pills(
                    "Poignée",
                    [Poignee.SIMPLE, Poignee.SIMPLE, Poignee.DOUBLE, Poignee.DOUBLE, Poignee.TRIPLE],
                    selection_mode="multi",
                    key=f"poignee {i}",
                    on_change=lambda x: round.set_poignee(st.session_state[x]),
                    args=(f"poignee {i}",),
                    help="Simple, double, triple. Les points de la poignée sont toujours remportés par l'équipe gagnante",
                )

                round.bouts = st.selectbox(
                    "Bouts",
                    options=[0, 1, 2, 3],
                    index=round.bouts,
                    key=f"bouts {i}",
                    on_change=lambda x: round.set_bouts(st.session_state[x]),
                    args=(f"bouts {i}",),
                )

            with col_score:
                round.points = st.number_input(
                    "Score",
                    value=round.points,
                    min_value=0.0,
                    max_value=91.0,
                    step=0.5,
                    format="%0.1f",
                    key=f"points {i}",
                    on_change=lambda x: round.set_points(st.session_state[x]),
                    args=(f"points {i}",),
                    placeholder=None,
                )
                round.petit_au_bout = st.pills(
                    "Petit au bout",
                    options=list(PetitAuBout),
                    key=f"petit_au_bout {i}",
                    on_change=lambda x: round.set_petit_au_bout(st.session_state[x]),
                    args=(f"petit_au_bout {i}",),
                    help="Les points vont à l'équipe remportant le petit au bout",
                )
            if round.attack in round.defense or round.appel in round.defense:
                st.warning("One player is defending and attacking")
                return
        with col2:
            st.dataframe(round.scores_df(), use_container_width=True)
        st.divider()


def display_player_graphs():
    session: Session = st.session_state.session
    st.pyplot(session.plot_score_evolution())
    st.divider()
    fig = session.plot_player_roles()
    st.pyplot(fig)
    st.divider()
    fig2 = session.plot_role_distribution_per_player()
    st.pyplot(fig2)


@st.dialog("New round")
def new_round():
    session: Session = st.session_state.session
    with st.form("New round form"):
        col_name, col_selec = st.columns(2)
        with col_name:
            attack = st.selectbox("Preneur", options=session.players, key=f"Preneur new round", index=None)
            appel = st.selectbox("Appelé", options=session.players, key=f"Called new round", index=None)
            defense = st.multiselect("Défense", options=session.players, key=f"defense new round", default=None)
        with col_selec:
            attack_type = st.segmented_control("Prise", list(Attack))
            poignees = st.pills(
                "Poignée",
                [Poignee.SIMPLE, Poignee.SIMPLE, Poignee.DOUBLE, Poignee.DOUBLE, Poignee.TRIPLE],
                selection_mode="multi",
                help="Simple, double, triple. Les points de la poignée sont toujours remportés par l'équipe gagnante",
            )
            bouts = st.segmented_control("Bouts", options=[0, 1, 2, 3], default=0)
        st.divider()
        col_p, col_c = st.columns([3, 2])
        with col_p:
            points = st.number_input("Score", min_value=0.0, max_value=91.0, step=0.5, format="%0.1f", placeholder="Score", value=None)
        with col_c:
            petit_au_bout = st.pills("Petit au bout", options=list(PetitAuBout), help="Les points vont à l'équipe remportant le petit au bout")

        if st.form_submit_button():
            print(attack, appel, defense, attack_type, bouts, points)
            if not attack or not appel or not defense or not attack_type or bouts == None or not points:
                st.error("Fill before submitting")
                return
            if attack in defense or appel in defense:
                st.error("One player is defending and attacking")
                return
            if len(poignees) > 2:
                st.error("Combien d'atouts en une seule game????")
            session.rounds.append(
                Round5P(
                    attack=attack,
                    appel=appel,
                    defense=defense,
                    attack_type=attack_type,
                    poignees=poignees,
                    bouts=bouts,
                    petit_au_bout=petit_au_bout,
                    points=points,
                )
            )
            st.rerun()


def session_sidebar():
    session: Session = st.session_state.session
    if st.button("Home", icon=":material/home:", type="tertiary"):
        st.session_state.session = None
        st.rerun()
    st.table(session.scores_df())
    st.button("Shuffle players", use_container_width=True, on_click=rd.shuffle, args=(session.players,))
    if st.button("New round", type="primary", use_container_width=True):
        new_round()


def session_page():
    score_tracker_tab, graphs_tab = st.tabs(["Score tracker", "Graphs"])
    with st.sidebar:
        session_sidebar()
    with score_tracker_tab:
        score_tracker()
    with graphs_tab:
        display_player_graphs()


def main():
    hist: History = st.session_state.history
    if not st.session_state.session:
        landing_page()
        return
    session_page()
    hist.save()


if "session" not in st.session_state:
    st.session_state.session = None
    st.session_state.history = History.load()
main()

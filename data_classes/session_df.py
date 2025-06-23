from pandas import DataFrame
from data_classes.enums import Attack, Poignee
from data_classes.game_json import Session, History, Round5P
from enum import Enum
from datetime import date

points_per_bout: list[int] = [56, 51, 41, 36]


class SessionDf:

    class Rows(Enum):
        ATTAQUER = "Preneur"
        CALLED = "Appelé"
        DEFENSE = "Défenseur"

        PRISE = "Prise"
        SCORE = "Score"
        BOUTS = "Nombre de bouts"
        PETIT_AU_BOUT = "Petit au bout"
        POIGNEE = "Poignee"

    def __init__(self, players: list[str], df: DataFrame) -> None:
        self._players: list[str] = sorted(players)
        assert set(df.columns) == set([e.value for e in SessionDf.Rows]) | set(players)
        self._df: DataFrame = df

    @classmethod
    def empty(cls, players: list[str]) -> "SessionDf":
        param_columns = [e.value for e in cls.Rows]
        all_columns = param_columns + players
        df = DataFrame(columns=all_columns)
        return cls(players=players, df=df)

    @classmethod
    def from_json(cls, session: Session) -> "SessionDf":
        players = session.players
        param_columns = [e.value for e in cls.Rows]
        all_columns = param_columns + players
        rows = []

        for round in session.rounds:
            row: dict[str, str | list[str] | int | bool] = {
                cls.Rows.ATTAQUER.value: round.attack,
                cls.Rows.CALLED.value: round.appel,
                cls.Rows.DEFENSE.value: round.defense,
                cls.Rows.PRISE.value: round.attack_type.value,
                cls.Rows.SCORE.value: round.scores.get(round.attack, 0),
                cls.Rows.BOUTS.value: round.bouts,
                cls.Rows.PETIT_AU_BOUT.value: round.petit_au_bout,
                cls.Rows.POIGNEE.value: round.poignee.value,
            }

            # Add one column per player with their individual score
            for p in session.players:
                row[p] = round.scores.get(p, 0)

            rows.append(row)

        df = DataFrame(rows, columns=all_columns)
        return cls(players=players, df=df)

    @property
    def players(self) -> list[str]:
        return self._players

    @players.setter
    def players(self, players: list[str]):
        self._players = sorted(players)

    @property
    def df(self) -> DataFrame:
        return self._df

    def _process_row(self, row) -> list[int]:
        score_base: int = row[self.Rows.SCORE.value]
        petit_au_bout: int = 10 if row[self.Rows.PETIT_AU_BOUT.value] else 0
        poignee_value: int = Poignee(row[self.Rows.POIGNEE.value]).score
        points_bouts: int = points_per_bout[row[self.Rows.BOUTS.value]]
        prise_mult = Attack(row[self.Rows.PRISE.value]).multiplicator
        attacker: str = row[self.Rows.ATTAQUER.value]
        called: str = row[self.Rows.CALLED.value]
        defense: list[str] = row[self.Rows.DEFENSE.value]

        score: int = score_base + petit_au_bout + poignee_value - points_bouts
        score += 25 if score >= 0 else -25
        score *= prise_mult

        scores: list[int] = [0] * len(self.players)
        scores[self.players.index(attacker)] += score * 2
        scores[self.players.index(called)] += score
        for d in defense:
            scores[self.players.index(row[d])] -= score
        return scores

    @df.setter
    def df(self, df: DataFrame):
        assert set(df.columns) == set([e.value for e in SessionDf.Rows]) | set(self.players)
        df[self.players] = df.apply(self._process_row, axis=1, result_type="expand")
        self._df = df

    def to_json(self):
        rounds: list[Round5P] = list()
        for _, row in self._df.iterrows():
            attack: str = row[SessionDf.Rows.ATTAQUER.value]
            appel: str = row[SessionDf.Rows.CALLED.value]
            defense: list[str] = [name for name in row[SessionDf.Rows.DEFENSE.value]]

            prise = Attack(row[SessionDf.Rows.PRISE.value])
            poignee = Poignee(row[SessionDf.Rows.POIGNEE.value])

            rounds.append(
                Round5P(
                    attack=attack,
                    appel=appel,
                    defense=[Player(d) for d in defense],  # type:ignore
                    attack_type=prise,
                    points=int(row[SessionDf.Rows.SCORE.value]),
                    bouts=int(row[SessionDf.Rows.BOUTS.value]),
                    petit_au_bout=bool(row[SessionDf.Rows.PETIT_AU_BOUT.value]),
                    poignee=poignee,
                    _score=None,
                )
            )

        return Session(date_=date.today(), players=self.players, rounds=rounds)

    def save_json(self, history: History):
        history.save_session(self.to_json())

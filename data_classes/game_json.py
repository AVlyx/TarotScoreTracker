from typing import Self, overload
from pydantic import BaseModel
from data_classes.enums import Poignee, Attack
from pandas import DataFrame
from datetime import date
import os
from matplotlib import pyplot as plt
from pathlib import Path
import json


STORAGE = Path("./TarotScoreTracker/History.json")

points_per_bout: list[int] = [56, 51, 41, 36]


class Round5P(BaseModel):
    attack: str
    appel: str
    defense: list[str]

    attack_type: Attack
    points: int
    bouts: int
    petit_au_bout: bool
    poignee: Poignee

    _score: dict[str, int] | None

    def __setattr__(self, name, value):
        self._score = None
        super(Round5P, self).__setattr__(name, value)

    @property
    def scores(self) -> dict[str, int]:
        if self._score:
            return self._score
        score: int = self.points - points_per_bout[self.bouts]
        score += 10 if self.petit_au_bout else 0
        score += self.poignee.score
        score *= self.attack_type.multiplicator
        self._score = {self.attack: score * 2, self.appel: score} | {def_: score for def_ in self.defense}
        return self._score


class Session(BaseModel):
    date_: date
    players: list[str]
    rounds: list[Round5P]

    def scores(self) -> dict[str, int]:
        scores: dict[str, int] = dict.fromkeys(self.players, 0)
        for r in self.rounds:
            for player, score in r.scores.items():
                scores[player] += score
        return scores

    def scores_over_time(self) -> DataFrame:
        # Initialize score tracking
        cumulative_scores: dict[str, list[int]] = {player: [0] for player in self.players}

        # Compute cumulative scores round by round
        for r in self.rounds:
            round_scores: dict[str, int] = r.scores
            for player in self.players:
                name: str = player
                prev_score: int = cumulative_scores[name][-1]
                cumulative_scores[name].append(prev_score + round_scores.get(player, 0))

        # Build DataFrame
        df = DataFrame(cumulative_scores)
        df.index.name = "Round"
        return df

    def plot_score_evolution(self):
        # Prepare cumulative scores
        cumulative_scores = {player: [0] for player in self.players}

        for r in self.rounds:
            round_scores = r.scores
            for player in self.players:
                name = player
                prev = cumulative_scores[name][-1]
                cumulative_scores[name].append(prev + round_scores.get(player, 0))

        # Create the plot
        fig, ax = plt.subplots(figsize=(8, 5))

        for name, scores in cumulative_scores.items():
            ax.plot(range(len(scores)), scores, label=name, marker="o")

        ax.set_title("Score Progression During Game")
        ax.set_xlabel("Round")
        ax.set_ylabel("Cumulative Score")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()

        return fig


class History(BaseModel):
    history: list[Session]
    players: list[str]

    @staticmethod
    def load() -> "History":
        if not os.path.exists(STORAGE):
            return History(history=[], players=[])
        with open(STORAGE, "r") as f:
            json_content: str = f.read()
        return History.model_validate(json.loads(json_content))

    def save(self):
        content: str = self.model_dump_json()
        STORAGE.parent.mkdir(parents=True, exist_ok=True)
        STORAGE.write_text(content)

    def save_session(self, session: Session):
        self.history.append(session)
        self.save()
        self.history.pop()

from typing import Self, overload
from pydantic import BaseModel
from data_classes.enums import Poignee, Attack, PetitAuBout
from pandas import DataFrame
from datetime import date
import os
from matplotlib import pyplot as plt
from collections import Counter, defaultdict
from pathlib import Path
import json


STORAGE = Path("./TarotScoreTracker/History.json")

points_per_bout: list[float] = [56.0, 51.0, 41.0, 36.0]


class Round5P(BaseModel):
    attack: str
    appel: str
    defense: list[str]

    attack_type: Attack
    points: float
    bouts: int
    petit_au_bout: PetitAuBout | None
    poignees: list[Poignee]

    def set_attack(self, attack: str):
        self.attack = attack

    def set_appel(self, appel: str):
        self.appel = appel

    def set_defense(self, defense: list[str]):
        self.defense = defense

    def set_attack_type(self, attack_type: Attack):
        self.attack_type = attack_type

    def set_points(self, points: float):
        self.points = points

    def set_bouts(self, bouts: int):
        self.bouts = bouts

    def set_petit_au_bout(self, petit_au_bout: PetitAuBout | None):
        self.petit_au_bout = petit_au_bout

    def set_poignee(self, poignees: list[Poignee]):
        self.poignees = poignees

    def scores(self) -> dict[str, float]:
        win: int = 1 if self.points >= points_per_bout[self.bouts] else -1  # 1 if at tack won -1 if defense won
        score: float = (self.points - points_per_bout[self.bouts]) * win  # absolute value of score
        score += 25  # base score that will be won / lost
        score += sum(p.score for p in self.poignees)  # bonus points from poignee go to winning team. There can be up to 2 poignee in a round
        score += 0 if not self.petit_au_bout else self.petit_au_bout.score * win  # points go to team with petit au bout. Not winning team
        score *= self.attack_type.multiplicator
        score *= win
        if self.attack == self.appel:
            scores: dict[str, float] = {self.attack: score * 4} | {def_: -score for def_ in self.defense}
        else:
            scores: dict[str, float] = {self.attack: score * 2, self.appel: score} | {def_: -score for def_ in self.defense}
        return scores

    def scores_df(self) -> DataFrame:
        scores = self.scores()
        data: list[tuple[str, str]] = [(player, f"{scores.get(player, 0):.1f}") for player in list(scores.keys())]
        return DataFrame(data, columns=["Players", "Scores"])


class Session(BaseModel):
    date_: date
    players: list[str]
    rounds: list[Round5P]

    def scores(self) -> dict[str, float]:
        scores: dict[str, float] = dict.fromkeys(self.players, 0)
        for r in self.rounds:
            for player, score in r.scores().items():
                scores[player] += score
        return scores

    def scores_df(self) -> DataFrame:
        scores = self.scores()
        data: list[tuple[str, str]] = [(player, f"{scores.get(player, 0):.1f}") for player in self.players]
        return DataFrame(data, columns=["Players", "Scores"])

    def scores_over_time(self) -> DataFrame:
        # Initialize score tracking
        cumulative_scores: dict[str, list[float]] = {player: [0] for player in self.players}

        # Compute cumulative scores round by round
        for r in self.rounds:
            round_scores: dict[str, float] = r.scores()
            for player in self.players:
                name: str = player
                prev_score: float = cumulative_scores[name][-1]
                cumulative_scores[name].append(prev_score + round_scores.get(player, 0))

        # Build DataFrame
        df = DataFrame(cumulative_scores)
        df.index.name = "Round"
        return df

    def plot_score_evolution(self):
        # Prepare cumulative scores
        cumulative_scores = {player: [0.0] for player in self.players}

        for r in self.rounds:
            round_scores = r.scores()
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

    def plot_player_roles(self):
        # Create counters for each role
        roles_count = {"attack": Counter(), "appel": Counter(), "defense": Counter()}

        for r in self.rounds:
            roles_count["attack"][r.attack] += 1
            roles_count["appel"][r.appel] += 1
            for defender in r.defense:
                roles_count["defense"][defender] += 1

        # Create subplots
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))

        for ax, (role, counter) in zip(axs, roles_count.items()):
            labels = list(counter.keys())
            sizes = list(counter.values())
            ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.set_title(f"Role: {role.capitalize()}")

        fig.tight_layout()
        return fig

    def plot_role_distribution_per_player(self):
        # Count roles per player
        player_roles = defaultdict(lambda: {"attack": 0, "appel": 0, "defense": 0})

        for r in self.rounds:
            player_roles[r.attack]["attack"] += 1
            player_roles[r.appel]["appel"] += 1
            for defender in r.defense:
                player_roles[defender]["defense"] += 1

        # Create one pie chart per player
        n_players = len(self.players)
        cols = min(n_players, 3)
        rows = (n_players + cols - 1) // cols

        fig, axs = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
        axs = axs.flatten() if n_players > 1 else [axs]

        for idx, player in enumerate(self.players):
            role_counts = player_roles[player]
            total = sum(role_counts.values())

            if total == 0:
                labels = ["No Data"]
                sizes = [1]
            else:
                labels = list(role_counts.keys())
                sizes = list(role_counts.values())

            axs[idx].pie(sizes, labels=labels, autopct=lambda p: f"{p:.1f}%" if p > 0 else "", startangle=90)
            axs[idx].set_title(player)

        # Hide unused subplots
        for ax in axs[n_players:]:
            ax.axis("off")

        fig.tight_layout()
        return fig

    @classmethod
    def new_game(cls, players: list[str]):
        return cls(date_=date.today(), players=players, rounds=[])


class History(BaseModel):
    history: list[Session]
    players: list[str]

    @staticmethod
    def load() -> "History":
        if not os.path.exists(STORAGE):
            return History(history=[], players=[])
        with open(STORAGE, "r", encoding="utf-8") as f:
            json_content: str = f.read()
        return History.model_validate(json.loads(json_content))

    def save(self):
        content: str = self.model_dump_json()
        STORAGE.parent.mkdir(parents=True, exist_ok=True)
        print(content)
        STORAGE.write_text(content, encoding="utf-8")

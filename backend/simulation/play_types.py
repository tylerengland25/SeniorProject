import random
from abc import ABC, abstractmethod


class Play(ABC):
    def __init__(self) -> None:
        self.play_type = None
        self.yds_gained = None
        self.duration = random.randint(5, 15)
        self.change_of_possession = False

    @abstractmethod
    def sim(self):
        pass


class Pass(Play):
    def __init__(self) -> None:
        super().__init__()
        self.play_type = "pass"

    def sim(self):
        defensive_play = random.choice(["run", "pass"])
        if defensive_play == "pass":
            self.yds_gained = random.randint(-5, 5)
        else:
            self.yds_gained = random.randint(0, 20)
        self.change_of_possession = random.choice(
            [True] * 5 + [False] * 95
        )


class Rush(Play):
    def __init__(self) -> None:
        super().__init__()
        self.play_type = "rush" 

    def sim(self):
        defensive_play = random.choice(["run", "pass"])
        if defensive_play == "run":
            self.yds_gained = random.randint(-5, 5)
        else:
            self.yds_gained = random.randint(0, 10)
        self.change_of_possession = random.choice(
            [True] * 5 + [False] * 95
        )


class Kick(Play):
    def __init__(self) -> None:
        super().__init__()
        self.play_type = "kickoff"
        self.yds_kicked = random.randint(40, 80)
        self.touchback = True if self.yds_kicked > 65 else False

    def sim(self):
        return_yds = random.randint(0, 30)
        self.yds_gained = 40 if self.touchback else self.yds_kicked - return_yds
        self.change_of_possession = True


class Punt(Play):
    def __init__(self, yds_to_goal) -> None:
        super().__init__()
        self.play_type = "punt"
        self.yds_punted = random.randint(30, 60)
        self.yds_to_goal = yds_to_goal
        self.touchback = True if self.yds_punted > self.yds_to_goal else False

    def sim(self):
        return_yds = random.randint(0, 30)
        self.yds_gained = self.yds_to_goal - 25 if self.touchback else self.yds_punted - return_yds
        self.change_of_possession = True


class FieldGoal(Play):
    def __init__(self, yds_to_goal) -> None:
        super().__init__()
        self.play_type = "field goal"
        self.yds_kicked = random.randint(30, 60)
        self.made = True if self.yds_kicked > yds_to_goal + 17 else False

    def sim(self):
        self.yds_gained = 0
        self.change_of_possession = True
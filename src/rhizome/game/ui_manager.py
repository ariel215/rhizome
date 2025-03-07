from dataclasses import dataclass
from typing import List, Protocol
from tcod.console import Console
from tcod.event import Event

__all__ = ["Push", "Pop", "StateAction", "UIManager"]

class Push:
    def __init__(self, state):
        self.state = state

class Pop:
    pass

class Update:
    def __init__(self, *args: list, **kwargs: dict):
        self.args = args
        self.kwargs = kwargs

class Replace:
    def __init__(self, new_state: "State"):
        self.new_state = new_state


type StateAction = Push | Pop | Update | None

class State(Protocol):
    def draw(console: Console) -> None: 
        ...
    
    def on_event(event: Event) -> StateAction | List[StateAction]:
        ...

    def update(*args, **kwargs) -> None:
        ...

class UIManager:
    def __init__(self, initial_states: List[State]):
        self.states = initial_states

    def update(self, action: StateAction):
        match action:
            case Push(state=state):
                self.states.append(state)
            case Pop():
                self.states.pop()
            case Update(args=args, kwargs=kwargs):
                self.states[-1].update(*args, **kwargs)
            case Replace(new_state = new_state):
                self.states[-1] = new_state
            case [*actions]:
                for action in actions:
                    self.update(action)
            case None:
                return

    def draw(self, console: Console):
        for state in self.states:
            state.draw(console)
        
    def on_event(self,event: Event):
        action = self.states[-1].on_event(event)
        self.update(action)

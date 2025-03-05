from dataclasses import dataclass
from typing import List, Protocol
from tcod.console import Console
from tcod.event import Event

__all__ = ["Push", "Pop", "StateAction", "StateManager"]

class Push:
    def __init__(self, state):
        self.state = state

class Pop:
    pass

type StateAction = Push | Pop | None

class State(Protocol):
    def draw(console: Console) -> None: 
        ...
    
    def on_event(event: Event) -> StateAction | List[StateAction]:
        ...

class StateManager:
    def __init__(self, initial_states: List[State]):
        self.states = initial_states

    def update(self, action: StateAction):
        match action:
            case Push(state=state):
                self.states.append(state)
            case Pop():
                self.states.pop()
            case [*actions]:
                for action in actions:
                    self.update(action)
            case None:
                return
        if not self.states:
            raise SystemExit

    def draw(self, console: Console):
        for state in self.states:
            state.draw(console)
        
    def on_event(self,event: Event):
        action = self.states[-1].on_event(event)
        self.update(action)
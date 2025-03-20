from enum import Enum, auto
from typing import Literal, Optional
from microstate import (
    StateMachine,
    define_transitions,
    overload_signature,
    P,
)


class MarioState(Enum):
    """Example Enum for states."""

    NORMAL = auto()
    SUPER = auto()
    CAPE = auto()
    FIRE = auto()
    DEAD = auto()


class Item(Enum):
    MUSHROOM = auto()
    FLOWER = auto()
    FEATHER = auto()


class SuperMarioStateMachine(
    StateMachine[MarioState, P], start_state=MarioState.NORMAL
):
    @overload_signature
    def update(self, item: Optional[Item] = None) -> MarioState: ...

    with define_transitions(update) as transition:
        # All transitions encode state changes when Mario picks up an item (or not!)
        @transition(MarioState.NORMAL)
        def from_mario(
            self, item: Optional[Item] = None
        ) -> Literal[
            MarioState.SUPER, MarioState.FIRE, MarioState.CAPE, MarioState.NORMAL
        ]:
            match item:
                case Item.MUSHROOM:
                    return MarioState.SUPER
                case Item.FLOWER:
                    return MarioState.FIRE
                case Item.FEATHER:
                    return MarioState.CAPE

            return MarioState.NORMAL

        @transition(MarioState.SUPER)
        def from_super_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE, MarioState.CAPE, MarioState.SUPER]:
            match item:
                case Item.FLOWER:
                    return MarioState.FIRE
                case Item.FEATHER:
                    return MarioState.CAPE
            return MarioState.SUPER

        @transition(MarioState.FIRE)
        def from_fire_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE, MarioState.FIRE]:
            if item is Item.FEATHER:
                return MarioState.CAPE
            return MarioState.FIRE

        @transition(MarioState.CAPE)
        def from_cape_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE, MarioState.CAPE]:
            if item is Item.FLOWER:
                return MarioState.FIRE
            return MarioState.CAPE

        # You can implement your own methods to encode custom actions and state changes.
        def take_damage(self) -> MarioState:
            match self.current_state:
                case MarioState.NORMAL:
                    self.current_state = MarioState.DEAD
                case MarioState.SUPER:
                    self.current_state = MarioState.NORMAL
                case MarioState.DEAD:
                    self.current_state = MarioState.DEAD
                case _:
                    self.current_state = MarioState.SUPER
            return self.current_state


if __name__ == "__main__":
    mario = SuperMarioStateMachine()
    assert mario.update() is MarioState.NORMAL  # returns MarioState.NORMAL
    assert mario.update(Item.FLOWER) is MarioState.FIRE
    assert mario.take_damage() is MarioState.SUPER
    assert mario.take_damage() is MarioState.NORMAL
    assert mario.update(Item.MUSHROOM) is MarioState.SUPER

    assert mario.take_damage() is MarioState.NORMAL
    assert mario.take_damage() is MarioState.DEAD
    # There is no registered transition from the "dead Mario" state (RIP)
    assert mario.update(Item.FLOWER) is MarioState.DEAD
    assert mario.take_damage() is MarioState.DEAD

from enum import Enum, auto
from typing import Literal, Optional
from microstate import (
    StateMachine,
    TransitionRegistry,
    overload_signature,
)


class MarioState(Enum):
    """Example Enum for states."""

    NORMAL = auto()
    SUPER = auto()
    CAPE = auto()
    FIRE = auto()
    GAME_OVER = auto()


class Item(Enum):
    MUSHROOM = auto()
    FLOWER = auto()
    FEATHER = auto()


class SuperMarioStateMachine(StateMachine, start_state=MarioState.NORMAL):
    @overload_signature
    def update(self, item: Optional[Item] = None) -> MarioState: ...

    with TransitionRegistry(update) as register:
        # All transitions encode state changes when Mario picks up an item (or not!)
        @register.new(MarioState.NORMAL)
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

        @register.new(MarioState.SUPER)
        def from_super_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE, MarioState.CAPE, MarioState.SUPER]:
            match item:
                case Item.FLOWER:
                    return MarioState.FIRE
                case Item.FEATHER:
                    return MarioState.CAPE
            return MarioState.SUPER

        @register.new(MarioState.FIRE)
        def from_fire_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE, MarioState.FIRE]:
            if item is Item.FEATHER:
                return MarioState.CAPE
            return MarioState.FIRE

        @register.new(MarioState.CAPE)
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
                    self.current_state = MarioState.GAME_OVER
                case MarioState.SUPER:
                    self.current_state = MarioState.NORMAL
                case MarioState.GAME_OVER:
                    self.current_state = MarioState.GAME_OVER
                case _:
                    self.current_state = MarioState.SUPER
            return self.current_state


def main():
    # We launch the game
    mario = SuperMarioStateMachine()

    # Nothing happens if Mario does not pick an object
    assert mario.update() is MarioState.NORMAL

    # Mario picks up an object and becomes Fire Mario!
    assert mario.update(Item.FLOWER) is MarioState.FIRE

    assert mario.take_damage() is MarioState.SUPER
    assert mario.take_damage() is MarioState.NORMAL
    # ... Git gud mate pls

    assert mario.update(Item.MUSHROOM) is MarioState.SUPER
    assert mario.take_damage() is MarioState.NORMAL
    # Too bad you didn't pick a 1 up.
    assert mario.take_damage() is MarioState.GAME_OVER

    # There is no registered transition from the "Game Over" state (RIP)
    assert mario.update(Item.FLOWER) is MarioState.GAME_OVER
    # This is just beating a dead horse already!
    assert mario.take_damage() is MarioState.GAME_OVER


if __name__ == "__main__":
    main()

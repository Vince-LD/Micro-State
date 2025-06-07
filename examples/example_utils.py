from enum import Enum, auto
from typing import Optional

from microstate import AbstractStateMachine, Transitions


class MarioState(Enum):
    """All states Mario can be in"""

    NORMAL = auto()
    SUPER = auto()
    CAPE = auto()
    FIRE = auto()
    GAME_OVER = auto()


class Item(Enum):
    """The items Mario can pick up"""

    MUSHROOM = auto()
    FLOWER = auto()
    FEATHER = auto()


class BaseSuperMarioMachine(AbstractStateMachine, init_state=MarioState.NORMAL):
    # We define a signature that all transitions must follow
    @Transitions.define_signature
    def update(self, item: Optional[Item] = None) -> MarioState: ...

    # You can implement "manual transitions" that will not be automatically called when
    # calling the `update` method because they do not explicitely depend on the current state.
    # Then can be used to force a new current state.
    with Transitions(update) as transitions:

        @transitions.manual
        def take_damage(self) -> MarioState | None:
            match self.current_state:
                case MarioState.NORMAL:
                    return MarioState.GAME_OVER
                case MarioState.SUPER:
                    return MarioState.NORMAL
                case MarioState.GAME_OVER:
                    return MarioState.GAME_OVER
                case _:
                    return MarioState.SUPER


def main(mario_machine_type: type[BaseSuperMarioMachine]):
    mario = mario_machine_type()

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

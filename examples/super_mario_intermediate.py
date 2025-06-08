from typing import Literal, Optional

from example_utils import BaseSuperMarioMachine, Item, MarioState, main

from microstate import (
    Transition,
)


class SuperMarioIntermediateExample(BaseSuperMarioMachine):
    with Transition(BaseSuperMarioMachine.update) as transitions:
        # All transitions encode state changes when Mario picks up an item (or not!)
        @transitions.new_from(MarioState.NORMAL)
        def from_mario(
            self, item: Optional[Item] = None
        ) -> (
            Literal[
                MarioState.SUPER, MarioState.FIRE, MarioState.CAPE, MarioState.NORMAL
            ]
            | None
        ):
            match item:
                case Item.MUSHROOM:
                    return MarioState.SUPER
                case Item.FLOWER:
                    return MarioState.FIRE
                case Item.FEATHER:
                    return MarioState.CAPE

        @transitions.new_from(MarioState.SUPER)
        def from_super_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE, MarioState.CAPE, MarioState.SUPER] | None:
            match item:
                case Item.FLOWER:
                    return MarioState.FIRE
                case Item.FEATHER:
                    return MarioState.CAPE

        @transitions.new_from(MarioState.FIRE)
        def from_fire_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE, MarioState.FIRE] | None:
            if item is Item.FEATHER:
                return MarioState.CAPE

        @transitions.new_from(MarioState.CAPE)
        def from_cape_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE, MarioState.CAPE] | None:
            if item is Item.FLOWER:
                return MarioState.FIRE


if __name__ == "__main__":
    main(SuperMarioIntermediateExample)

from typing import Literal, Optional

from example_utils import BaseSuperMarioMachine, Item, MarioState, main

from microstate import (
    Transition,
)


class SuperMarioLongerExample(BaseSuperMarioMachine):
    with Transition(BaseSuperMarioMachine.update) as transitions:
        # All transitions encode state changes when Mario picks up an item (or not!)
        @transitions.new_from(MarioState.NORMAL)
        def from_normal_to_super(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.SUPER] | None:
            if item is Item.MUSHROOM:
                return MarioState.SUPER

        @transitions.new_from(MarioState.NORMAL)
        def from_normal_to_fire(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FLOWER:
                return MarioState.FIRE

        @transitions.new_from(MarioState.NORMAL)
        def from_normal_to_cape(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE] | None:
            if item is Item.FEATHER:
                return MarioState.CAPE

        @transitions.new_from(MarioState.SUPER)
        def from_super_to_fire(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FLOWER:
                return MarioState.FIRE

        @transitions.new_from(MarioState.SUPER)
        def from_super_to_cape(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FEATHER:
                return MarioState.FIRE

        @transitions.new_from(MarioState.FIRE)
        def from_fire_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE] | None:
            if item is Item.FEATHER:
                return MarioState.CAPE

        @transitions.new_from(MarioState.CAPE)
        def from_cape_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FLOWER:
                return MarioState.FIRE


if __name__ == "__main__":
    main(SuperMarioLongerExample)

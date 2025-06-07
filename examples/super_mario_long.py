from typing import Literal, Optional

from example_utils import BaseSuperMarioMachine, Item, MarioState, main

from microstate import (
    Transitions,
)


class SuperMarioLongerExample(BaseSuperMarioMachine):
    with Transitions(BaseSuperMarioMachine.update) as transitions:
        # All transitions encode state changes when Mario picks up an item (or not!)
        @transitions.new(MarioState.NORMAL)
        def from_normal_to_super(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.SUPER] | None:
            if item is Item.MUSHROOM:
                return MarioState.SUPER

        @transitions.new(MarioState.NORMAL)
        def from_normal_to_fire(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FLOWER:
                return MarioState.FIRE

        @transitions.new(MarioState.NORMAL)
        def from_normal_to_cape(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE] | None:
            if item is Item.FEATHER:
                return MarioState.CAPE

        @transitions.new(MarioState.SUPER)
        def from_super_to_fire(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FLOWER:
                return MarioState.FIRE

        @transitions.new(MarioState.SUPER)
        def from_super_to_cape(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FEATHER:
                return MarioState.FIRE

        @transitions.new(MarioState.FIRE)
        def from_fire_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE] | None:
            if item is Item.FEATHER:
                return MarioState.CAPE

        @transitions.new(MarioState.CAPE)
        def from_cape_mario(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.FIRE] | None:
            if item is Item.FLOWER:
                return MarioState.FIRE


if __name__ == "__main__":
    main(SuperMarioLongerExample)

from typing import Literal, Optional

from example_utils import BaseSuperMarioMachine, Item, MarioState, main

from microstate import Transition


class SuperMarioShortenedExample(BaseSuperMarioMachine):
    with Transition(BaseSuperMarioMachine.update) as transition:
        # Here, only the NORMAL can end up to the Super Mario state when picking up an item
        @transition.new_from(MarioState.NORMAL)
        def to_super(self, item: Optional[Item] = None) -> MarioState | None:
            return item is Item.MUSHROOM and MarioState.SUPER or None

        # In this case, many states can transition to FIRE when uusing a Flower
        @transition.new_from((MarioState.NORMAL, MarioState.SUPER, MarioState.CAPE))
        def to_fire(self, item: Optional[Item] = None) -> MarioState | None:
            return item is Item.FLOWER and MarioState.FIRE or None

        # The library also supports Literal return types if you want maximum expliciteness
        @transition.new_from((MarioState.NORMAL, MarioState.SUPER, MarioState.FIRE))
        def to_cape(
            self, item: Optional[Item] = None
        ) -> Literal[MarioState.CAPE] | None:
            return item is Item.FEATHER and MarioState.CAPE or None


if __name__ == "__main__":
    main(SuperMarioShortenedExample)

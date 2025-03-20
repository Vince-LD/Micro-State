### EXAMPLE

I used the famous Super Mario state machine example to demonstrate a more interesting (yet still basic) example of how to use this library. The code is available in this file ([super_mario.py](./super_mario.py)) which was copied below.

![alt text](./mario-finite-state-machine.jpg)

First we create the Enums representing the states in which Mario can be and the items he can pick up.

```python
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
```

Then we create the state machine.

```python
class SuperMarioStateMachine(
    StateMachine[MarioState, P], start_state=MarioState.NORMAL
):
    # First, we define a signature for the update method which will be required for all transitions.
    @overload_signature
    def update(self, item: Optional[Item] = None) -> MarioState: ...

    # Second, we create a context specific decorator that will register the transitions.
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

        # You can implement your own methods perform custom actions and state changes.
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
```

Then we can play a game!

```python
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
```

A fun exercise could be to implement a "1Up" counter to avoir the Game Over. You could for example add a method that allows mario to pick up "1Up" items, through a custom method or directly in the different transitions.
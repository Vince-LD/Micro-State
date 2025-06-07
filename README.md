# 🤖 micro-state 🤖

## 🧑‍🏫 What is it 👩‍🏫

It is a **fast, simple, elegant, safe and dependency free** way to define a State Machine in Python. It is fully **type-checked** with great type hints that will allow you to be very explicit while writing minimal code. One of the consequences is that it is **fully supported by type-checkers** like Pyright and will work perfectly your **autocomplete**.

The code is fully contained in a single file, which allows you to easily check it and copy it into your project if needed. You only need to import two classes:

- `StateMachine` which is the abstract class that contains and handles the states and transitions. Transitions can be inherited from a parent (default) or reset if needed using an sublass argument.
- `Transitions` which is a context manager that allows you create and automatically register transitions

The `StateMachine` abstract class does not have an `__init__` method which allows you to easily add it to your own classes as a mixin and/or to easily instanciate your own, because the only things that you will need is an `Enum` containing all the states! 


## ✍️ Example ✍️

I used the famous Super Mario state machine example to demonstrate a more interesting (yet still basic) example of how to use this library. In the [example directory](./examples/) you can see several diffent ways of implementing the same state machine.

![alt text](./examples/mario-finite-state-machine.jpg)

First we create the Enums representing the states in which Mario can be and the items he can pick up.

```python
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
```

Then we create the base state machine that is used in all implementation examples.

```python
class BaseSuperMarioMachine(StateMachine, start_state=MarioState.NORMAL):
    @Transitions.define_signature
    def update(self, item: Optional[Item] = None) -> MarioState: ...

    # You can implement "manual transitions" that will not be automatically called when 
    # calling the `update` method because they do not explicitely depend on the current state.
    # Then can be used to force a new current state.
    @Transitions.manual
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
```

Now that the base State Machine class is defined and that we saw one type of transition, let's complete the state machine. You can define every possible transitions one by one, group them when multiple different starting state can result in the same final state or mix both approaches and define a method that handles multiple transitions from a same starting state. Here, I'm going to show you the second type of implementation, where we group transitions together.

```python

class SuperMarioShortenedExample(BaseSuperMarioMachine):
    with Transitions(BaseSuperMarioMachine.update) as transitions:
        # Here, only the NORMAL can end up to the Super Mario state when picking up an item
        @transitions.new(MarioState.NORMAL)
        def to_super(self, item: Optional[Item] = None) -> MarioState | None:
            return item is Item.MUSHROOM and MarioState.SUPER or None

        # In this case, many states can transition to FIRE when uusing a Flower
        @transitions.new((MarioState.NORMAL, MarioState.SUPER, MarioState.CAPE))
        def to_fire(self, item: Optional[Item] = None) -> MarioState | None:
            return item is Item.FLOWER and MarioState.FIRE or None

        # Same here with the cape
        @transitions.new((MarioState.NORMAL, MarioState.SUPER, MarioState.FIRE))
        def to_cape(self, item: Optional[Item] = None) -> MarioState | None:
            return item is Item.FEATHER and MarioState.CAPE or None
```

Now, let's play a game! 🎮

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

## 📝 Exercice 📝

Using the examples as a starting point (or not), create a state machine that include the damage mechanics directly in the automatic transitions. 
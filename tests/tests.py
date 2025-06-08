import unittest
from enum import Enum, auto
from typing import Optional

from microstate import (
    AbstractStateMachine,
    Transition,
    TransitionSignatureError,
    TransitionOutsiteContextError,
    InvalidStateInput,
)


class DoorState(Enum):
    LOCKED = auto()
    UNLOCKED = auto()
    BROKEN = auto()


class DoorEvent(Enum):
    INSERT_KEY = auto()
    BREAK = auto()
    REPAIR = auto()


class DoorStateMachine(AbstractStateMachine, init_state=DoorState.LOCKED):
    def __init_subclass__(
        cls, init_state: DoorState | None = None, inherit_transitions: bool = True
    ) -> None:
        print("===================================")
        return super().__init_subclass__(init_state, inherit_transitions)

    @Transition.signature
    def update(self, event: Optional[DoorEvent] = None) -> DoorState: ...

    with Transition(update) as Transition:

        @Transition.manual
        def force_open(self) -> Optional[DoorState]:
            if self.current_state == DoorState.LOCKED:
                return DoorState.UNLOCKED
            return None

        @Transition.new(DoorState.LOCKED)
        def to_unlocked(self, event: Optional[DoorEvent] = None) -> Optional[DoorState]:
            return DoorState.UNLOCKED if event is DoorEvent.INSERT_KEY else None

        @Transition.new(DoorState.UNLOCKED)
        def to_locked(self, event: Optional[DoorEvent] = None) -> Optional[DoorState]:
            return DoorState.LOCKED if event is DoorEvent.INSERT_KEY else None

        @Transition.new((DoorState.LOCKED, DoorState.UNLOCKED))
        def to_broken(self, event: Optional[DoorEvent] = None) -> Optional[DoorState]:
            return DoorState.BROKEN if event is DoorEvent.BREAK else None

        @Transition.new(DoorState.BROKEN)
        def to_locked_from_broken(
            self, event: Optional[DoorEvent] = None
        ) -> Optional[DoorState]:
            return DoorState.LOCKED if event is DoorEvent.REPAIR else None


class TestDoorStateMachine(unittest.TestCase):
    def setUp(self):
        self.door = DoorStateMachine()

    def test_initial_state(self):
        self.assertEqual(self.door.current_state, DoorState.LOCKED)

    def test_insert_key_unlocks_and_locks(self):
        # Insert key in locked -> unlocked
        new_state = self.door.update(DoorEvent.INSERT_KEY)
        self.assertEqual(new_state, DoorState.UNLOCKED)
        self.assertEqual(self.door.current_state, DoorState.UNLOCKED)
        # Insert key in unlocked -> locked
        new_state = self.door.update(DoorEvent.INSERT_KEY)
        self.assertEqual(new_state, DoorState.LOCKED)
        self.assertEqual(self.door.current_state, DoorState.LOCKED)

    def test_break_and_repair(self):
        # Break from locked
        new_state = self.door.update(DoorEvent.BREAK)
        self.assertEqual(new_state, DoorState.BROKEN)
        self.assertEqual(self.door.current_state, DoorState.BROKEN)
        # Repair from broken
        new_state = self.door.update(DoorEvent.REPAIR)
        self.assertEqual(new_state, DoorState.LOCKED)
        self.assertEqual(self.door.current_state, DoorState.LOCKED)

    def test_break_from_unlocked(self):
        self.door.update(DoorEvent.INSERT_KEY)  # UNLOCKED
        new_state = self.door.update(DoorEvent.BREAK)
        self.assertEqual(new_state, DoorState.BROKEN)
        self.assertEqual(self.door.current_state, DoorState.BROKEN)

    def test_force_open_manual(self):
        # Force open from locked
        new_state = self.door.force_open()
        self.assertEqual(new_state, DoorState.UNLOCKED)
        self.assertEqual(self.door.current_state, DoorState.UNLOCKED)
        # Force open from unlocked (no change)
        new_state = self.door.force_open()
        self.assertEqual(new_state, DoorState.UNLOCKED)
        self.assertEqual(self.door.current_state, DoorState.UNLOCKED)

    def test_no_transition_when_event_none(self):
        # No event should keep in locked
        new_state = self.door.update()
        self.assertEqual(new_state, DoorState.LOCKED)

    def test_invalid_state_input_error(self):
        # Attempt to register with mixed state types
        class BadEnum(Enum):
            A = auto()
            B = auto()

        with self.assertRaises(InvalidStateInput):
            with Transition(DoorStateMachine.update) as transition:

                @transition.new((DoorState.LOCKED, BadEnum.A))
                def invalid(
                    self, event: Optional[DoorEvent] = None
                ) -> Optional[DoorState]:
                    return None

    def test_signature_mismatch_error(self):
        # Define a function with wrong signature
        with self.assertRaises(TransitionSignatureError):

            class BadSignatureMachine(
                AbstractStateMachine, init_state=DoorState.LOCKED
            ):
                @Transition.signature
                def update(self, event: Optional[DoorEvent] = None) -> DoorState: ...

                with Transition(update) as transition:

                    @transition.new(DoorState.LOCKED)
                    def bad_transition(
                        self,
                    ) -> Optional[DoorState]:  # missing parameter
                        return None

    def test_add_after_freeze_error(self):
        # Cannot add transitions after context exit
        t = Transition(DoorStateMachine.update)
        with t:

            @t.new(DoorState.LOCKED)
            def dummy(self, event: Optional[DoorEvent] = None) -> Optional[DoorState]:
                return None

        with self.assertRaises(TransitionOutsiteContextError):

            @t.new(DoorState.LOCKED)
            def another(self, event: Optional[DoorEvent] = None) -> Optional[DoorState]:
                return None


class InheritedDoorMachine(DoorStateMachine, init_state=DoorState.UNLOCKED):
    with Transition(DoorStateMachine.update) as Transition:

        @Transition.new(DoorState.UNLOCKED)
        def lock_directly(
            self, event: Optional[DoorEvent] = None
        ) -> Optional[DoorState]:
            # from UNLOCKED, insert key locks
            return DoorState.LOCKED if event is DoorEvent.INSERT_KEY else None


class TestInheritedDoorMachine(unittest.TestCase):
    def setUp(self):
        self.machine = InheritedDoorMachine()

    def test_override_init_state(self):
        self.assertEqual(self.machine.current_state, DoorState.UNLOCKED)

    def test_inherited_and_new_transitions(self):
        # Inherited break transition from UNLOCKED should still work
        new_state = self.machine.update(DoorEvent.BREAK)
        self.assertEqual(new_state, DoorState.BROKEN)
        # Reset
        self.machine.current_state = DoorState.UNLOCKED
        # New lock_directly transition
        new_state = self.machine.update(DoorEvent.INSERT_KEY)
        self.assertEqual(new_state, DoorState.LOCKED)


if __name__ == "__main__":
    unittest.main()

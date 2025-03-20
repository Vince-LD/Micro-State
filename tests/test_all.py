import unittest
from enum import Enum, auto
import inspect
from typing import Literal
from microstate import (
    StateMachine,
    define_transitions,
    overload_signature,
    P,
    StateMachineCompilationError,
)


class EnumTestState(Enum):
    """Example Enum for states."""
    A = auto()
    B = auto()


class ValidStateMachine(StateMachine[EnumTestState, P], start_state=EnumTestState.A):
    """
    A valid state machine with a transition from state A to state B.
    
    This machine starts in state A, and when update() is called while in state A,
    it transitions to state B.
    """
    @overload_signature
    def update(self) -> EnumTestState: 
        ...

    with define_transitions(update) as transition:

        @transition(EnumTestState.A)
        def to_B(self) -> EnumTestState:
            """Transition from state A to state B."""
            return EnumTestState.B


class NoTransitionStateMachine(StateMachine[EnumTestState, P], start_state=EnumTestState.A):
    """
    A state machine with no transitions.
    
    Since no transition is defined, calling update() should leave the state unchanged.
    """
    # No transition is defined
    ...


class ToggleStateMachine(StateMachine[EnumTestState, P], start_state=EnumTestState.A):
    """
    A state machine with toggling transitions.
    
    This machine toggles between state A and state B:
    - When in state A, update() transitions to state B.
    - When in state B, update() transitions back to state A.
    """
    @overload_signature
    def update(self) -> EnumTestState: 
        ...

    with define_transitions(update) as transition:

        @transition(EnumTestState.A)
        def to_B(self) -> EnumTestState:
            """Transition from state A to state B."""
            return EnumTestState.B

        @transition(EnumTestState.B)
        def to_A(self) -> EnumTestState:
            """Transition from state B to state A."""
            return EnumTestState.A


def create_duplicate_transition_class():
    """
    Utility function that creates a state machine class with two transitions
    for the same state. This should raise a compilation error.
    """
    class DuplicateTransitionStateMachine(
        StateMachine[EnumTestState, P], start_state=EnumTestState.A
    ):
        @overload_signature
        def update(self) -> EnumTestState: 
            ...

        with define_transitions(update) as transition:

            @transition(EnumTestState.A)
            def to_B(self) -> EnumTestState:
                return EnumTestState.B

            @transition(EnumTestState.A)
            def to_A(self) -> EnumTestState:
                return EnumTestState.A

    return DuplicateTransitionStateMachine


def create_invalid_signature_class():
    """
    Utility function that creates a state machine class with a transition method
    having an invalid signature. An error is expected because the signature does not match.
    """
    class InvalidSignatureStateMachine(
        StateMachine[EnumTestState, P], start_state=EnumTestState.A
    ):
        @overload_signature
        def update(self) -> EnumTestState: 
            ...

        with define_transitions(update) as transition:
            # The method expects an extra parameter, which differs from the signature of StateMachine.update
            @transition(EnumTestState.A)  # type: ignore -- This is flagged by pyright as an error
            def invalid(self, extra: int) -> EnumTestState:
                return EnumTestState.B

    return InvalidSignatureStateMachine


def create_wrong_return_type_class():
    """
    Utility function that creates a state machine class with a transition method
    that has an incorrect return type. An error is expected because the return type
    does not match the expected state type.
    """
    class WrongReturnTypeStateMachine(
        StateMachine[EnumTestState, P], start_state=EnumTestState.A
    ):
        with define_transitions(StateMachine.update) as transition:
            # Here, the return type is indicated as a Literal that does not correspond to the expected EnumTestState.
            @transition(EnumTestState.A)  # type: ignore -- This is rightfully flagged by pyright as an error
            def wrong_return(self) -> Literal[42]:
                return 42

    return WrongReturnTypeStateMachine


# For testing overload_signature, we define a real function and a function to decorate.
def dummy_real_func(self, x: int) -> EnumTestState:
    """Dummy real function to be wrapped by overload_signature."""
    return EnumTestState.A


def dummy_func_to_decorate(self, x: int) -> EnumTestState:
    """Dummy function that will be decorated by overload_signature."""
    return EnumTestState.A


class TestStateMachineLibrary(unittest.TestCase):
    """Test suite for the state machine library."""

    def test_valid_transition(self):
        """
        Test that a valid transition from state A to state B works correctly.
        
        It verifies:
        - The initial state is A.
        - Calling update() transitions from A to B.
        - The current state is updated to B.
        """
        machine = ValidStateMachine()
        self.assertEqual(machine.current_state, EnumTestState.A)
        new_state = machine.update()
        self.assertEqual(new_state, EnumTestState.B)
        self.assertEqual(machine.current_state, EnumTestState.B)

    def test_no_transition(self):
        """
        Test that a state machine with no defined transitions remains in the same state.
        
        It verifies:
        - The initial state is A.
        - Calling update() returns the same state (A).
        """
        machine = NoTransitionStateMachine()
        self.assertEqual(machine.current_state, EnumTestState.A)
        new_state = machine.update()
        self.assertEqual(new_state, EnumTestState.A)
        self.assertEqual(machine.current_state, EnumTestState.A)

    def test_toggle_state_machine(self):
        """
        Test a state machine that toggles between state A and state B.
        
        It verifies:
        - The machine starts in state A.
        - The first update() call transitions to state B.
        - The second update() call transitions back to state A.
        """
        machine = ToggleStateMachine()
        self.assertEqual(machine.current_state, EnumTestState.A)
        new_state = machine.update()  # Should transition to B.
        self.assertEqual(new_state, EnumTestState.B)
        new_state = machine.update()  # Should transition back to A.
        self.assertEqual(new_state, EnumTestState.A)

    def test_duplicate_transition_error(self):
        """
        Test that defining two transitions for the same state raises an error.
        
        A StateMachineCompilationError is expected when duplicate transitions for the same state are detected.
        """
        with self.assertRaises(StateMachineCompilationError):
            create_duplicate_transition_class()

    def test_invalid_signature_error(self):
        """
        Test that a transition method with an invalid signature raises an error.
        
        The method in the generated class has an extra parameter compared to the expected signature,
        so a StateMachineCompilationError should be raised.
        """
        with self.assertRaises(StateMachineCompilationError):
            create_invalid_signature_class()

    def test_wrong_return_type_error(self):
        """
        Test that a transition method with an incorrect return type annotation raises an error.
        
        A StateMachineCompilationError is expected if the return type of the transition does not match the expected type.
        """
        with self.assertRaises(StateMachineCompilationError):
            create_wrong_return_type_class()

    def test_overload_signature_decorator(self):
        """
        Test that the overload_signature decorator preserves the signature and correctly delegates calls.
        
        It verifies:
        - The decorated function retains the signature of the original function.
        - Calling the decorated function executes the real function (dummy_real_func) as expected.
        """
        decorated = overload_signature(real_func=dummy_real_func)(dummy_func_to_decorate)
        self.assertEqual(
            inspect.signature(decorated),
            inspect.signature(dummy_func_to_decorate),
        )

        # Verify that calling the decorated function executes dummy_real_func.
        class Dummy:
            def dummy_real_func(self, x: int) -> int:
                return x + 1

        dummy = Dummy()
        result = decorated(dummy, 3)
        self.assertEqual(result, EnumTestState.A)


if __name__ == "__main__":
    unittest.main()

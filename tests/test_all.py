import unittest
from enum import Enum
import inspect
from typing import Literal
from microstate import (
    StateMachine,
    define_transitions,
    overload_signature,
    P,
    StateMachineCompilationError,
)

# --- Code de la librairie à tester ---
# (On suppose que le code de la librairie est déjà présent dans le même module.)
#
# Voici les principaux éléments utilisés dans les tests :
# - StateMachine, StateMachineCompilationError, define_transitions, overload_signature
#
# --------------------------------------------------


# Exemple d'Enum pour les états
class EnumTestState(Enum):
    A = "A"
    B = "B"


# Cas valide : une transition de A vers B.
class ValidStateMachine(
    StateMachine[EnumTestState, P], start_state=EnumTestState.A
):  # Nécessaire pour stocker les transitions
    @overload_signature
    def update(self) -> EnumTestState: ...

    with define_transitions(update) as transition:

        @transition(EnumTestState.A)
        def to_B(self) -> EnumTestState:
            return EnumTestState.B


# Cas sans transition : la machine doit rester dans le même état.
class NoTransitionStateMachine(
    StateMachine[EnumTestState, P], start_state=EnumTestState.A
):
    # Aucune transition n'est définie
    ...


# Cas de basculement : deux transitions, de A vers B puis de B vers A.
class ToggleStateMachine(StateMachine[EnumTestState, P], start_state=EnumTestState.A):
    @overload_signature
    def update(self) -> EnumTestState: ...

    with define_transitions(update) as transition:

        @transition(EnumTestState.A)
        def to_B(self) -> EnumTestState:
            return EnumTestState.B

        @transition(EnumTestState.B)
        def to_A(self) -> EnumTestState:
            return EnumTestState.A


# Fonction utilitaire pour générer une classe avec deux transitions pour le même état (erreur attendue)
def create_duplicate_transition_class():
    class DuplicateTransitionStateMachine(
        StateMachine[EnumTestState, P], start_state=EnumTestState.A
    ):
        @overload_signature
        def update(self) -> EnumTestState: ...

        with define_transitions(update) as transition:

            @transition(EnumTestState.A)
            def to_B(self) -> EnumTestState:
                return EnumTestState.B

            @transition(EnumTestState.A)
            def to_A(self) -> EnumTestState:
                return EnumTestState.A

    return DuplicateTransitionStateMachine


# Fonction utilitaire pour générer une classe avec une signature invalide (erreur attendue)
def create_invalid_signature_class():
    class InvalidSignatureStateMachine(
        StateMachine[EnumTestState, P], start_state=EnumTestState.A
    ):
        @overload_signature
        def update(self) -> EnumTestState: ...

        with define_transitions(update) as transition:
            # La méthode attend un paramètre supplémentaire, ce qui diffère de la signature de StateMachine.update
            @transition(EnumTestState.A)
            def invalid(self, extra: int) -> EnumTestState:
                return EnumTestState.B

    return InvalidSignatureStateMachine


# Fonction utilitaire pour générer une classe avec un type de retour incorrect (erreur attendue)
def create_wrong_return_type_class():
    class WrongReturnTypeStateMachine(
        StateMachine[EnumTestState, P], start_state=EnumTestState.A
    ):
        with define_transitions(StateMachine.update) as transition:
            # Ici, on indique un type Literal qui ne correspond pas au type attendu (TestState)
            @transition(EnumTestState.A)
            def wrong_return(self) -> Literal[42]:
                return 42

    return WrongReturnTypeStateMachine


# Pour tester overload_signature, on définit une fonction réelle et une fonction à décorer.
def dummy_real_func(self, x: int) -> EnumTestState:
    return EnumTestState.A


def dummy_func_to_decorate(self, x: int) -> EnumTestState:
    return EnumTestState.A


# --- Suite de tests ---
class TestStateMachineLibrary(unittest.TestCase):
    def test_valid_transition(self):
        machine = ValidStateMachine()
        # Au départ, l'état doit être A
        self.assertEqual(machine.current_state, EnumTestState.A)
        # Après update, la transition A -> B doit s'effectuer
        new_state = machine.update()
        self.assertEqual(new_state, EnumTestState.B)
        self.assertEqual(machine.current_state, EnumTestState.B)

    def test_no_transition(self):
        machine = NoTransitionStateMachine()
        self.assertEqual(machine.current_state, EnumTestState.A)
        # Sans transition, update renvoie le même état
        new_state = machine.update()
        self.assertEqual(new_state, EnumTestState.A)
        self.assertEqual(machine.current_state, EnumTestState.A)

    def test_toggle_state_machine(self):
        machine = ToggleStateMachine()
        self.assertEqual(machine.current_state, EnumTestState.A)
        new_state = machine.update()  # Doit passer à B
        self.assertEqual(new_state, EnumTestState.B)
        new_state = machine.update()  # Doit repasser à A
        self.assertEqual(new_state, EnumTestState.A)

    def test_duplicate_transition_error(self):
        # Une erreur doit être levée lors de la compilation de la machine
        with self.assertRaises(StateMachineCompilationError):
            create_duplicate_transition_class()

    def test_invalid_signature_error(self):
        # Une erreur doit être levée si la signature de la méthode décorée ne correspond pas
        with self.assertRaises(StateMachineCompilationError):
            create_invalid_signature_class()

    def test_wrong_return_type_error(self):
        # Une erreur doit être levée si l'annotation de type de retour est incorrecte
        with self.assertRaises(StateMachineCompilationError):
            create_wrong_return_type_class()

    def test_overload_signature_decorator(self):
        # Décore une fonction avec overload_signature et vérifie que la signature est préservée
        decorated = overload_signature(real_func=dummy_real_func)(
            dummy_func_to_decorate
        )
        self.assertEqual(
            inspect.signature(decorated),
            inspect.signature(dummy_func_to_decorate),
        )

        # Vérifie que l'appel à la fonction décorée exécute bien dummy_real_func.
        # Pour cela, on simule un appel avec un objet dummy.
        class Dummy:
            def dummy_real_func(self, x: int) -> int:
                return x + 1

        dummy = Dummy()
        result = decorated(dummy, 3)
        self.assertEqual(result, EnumTestState.A)


if __name__ == "__main__":
    unittest.main()

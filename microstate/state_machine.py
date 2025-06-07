"""
BSD 3-Clause License

Copyright (c) 2025, Vincent

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import functools
import inspect
import types
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Callable,
    Concatenate,
    Generic,
    Iterable,
    Literal,
    Optional,
    ParamSpec,
    Self,
    Sequence,
    TypeAlias,
    TypeVar,
    get_args,
    get_origin,
    overload,
)

P = ParamSpec("P")
P_bis = ParamSpec("P_bis")
R = TypeVar("R")
StateEnumT = TypeVar("StateEnumT", bound=Enum)
StateEnumT_bis = TypeVar("StateEnumT_bis", bound=Enum)
StateMachineT = TypeVar(
    "StateMachineT", bound="AbstractStateMachine", contravariant=True
)
StateMachineT_bis: TypeAlias = StateMachineT


SpecMethodType: TypeAlias = Callable[Concatenate[StateMachineT, P], StateEnumT]
TransitionMethodType: TypeAlias = Callable[
    Concatenate[StateMachineT, P], Optional[StateEnumT]
]

SignatureOverloadDecoratorType: TypeAlias = Callable[
    [SpecMethodType[StateMachineT, P, StateEnumT]],
    TransitionMethodType[StateMachineT, P, StateEnumT],
]


class BaseStateMachineError(BaseException): ...


class StateMachineCompilationError(BaseStateMachineError): ...


class TransitionSignatureError(StateMachineCompilationError): ...


class TransitionFrozenError(StateMachineCompilationError): ...


class TransitionNotFrozenError(StateMachineCompilationError): ...


class InvalidStateInput(StateMachineCompilationError): ...


TransitionDecoratorType: TypeAlias = Callable[
    [TransitionMethodType[StateMachineT, P, StateEnumT]],
    TransitionMethodType[StateMachineT, P, StateEnumT],
]


class AbstractStateMachine(Generic[StateEnumT, P]):
    _state_type: type[StateEnumT]
    _state_transitions: dict[
        StateEnumT,
        tuple[TransitionMethodType[Self, P, StateEnumT], ...],
    ]
    _init_state: StateEnumT
    _current_state: StateEnumT

    def __init_subclass__(
        cls,
        init_state: Optional[StateEnumT] | None = None,
        inherit_transitions: bool = True,
    ) -> None:
        if init_state is None:
            try:
                init_state = cls._init_state
            except AttributeError:
                raise StateMachineCompilationError(
                    "The starting state was not defined in parent classes. "
                    f"Use `start_state` argument when inheriting from {AbstractStateMachine.__qualname__}"
                )

        cls._state_type = type(init_state)
        cls._init_state = init_state
        cls._current_state = init_state

        if not inherit_transitions or AbstractStateMachine in cls.__bases__:
            print("I WAS OVERRIDEN", cls.__bases__)
            cls._state_transitions = {}
        else:
            cls._state_transitions = cls._state_transitions.copy()

        for attr_name in dir(cls):
            if not isinstance(register := getattr(cls, attr_name), Transitions):
                continue
            for state, funcs in register.get_transitions()[0].items():
                parents_transition = cls._state_transitions.setdefault(state, ())
                if len(parents_transition) == 0:
                    cls._state_transitions[state] = funcs
                    continue
                else:
                    overriden_transitions = tuple(
                        f.__name__ for f in parents_transition
                    )
                    cls._state_transitions[state] = tuple(
                        filter(
                            lambda f: f not in overriden_transitions, parents_transition
                        )
                    ) + tuple(funcs)

    @property
    def current_state(self) -> StateEnumT:
        return self._current_state

    @current_state.setter
    def current_state(self, state: Optional[StateEnumT]):
        self._current_state = state or self._current_state

    def update(self, *args: P.args, **kwargs: P.kwargs) -> StateEnumT:
        for transition_func in self._state_transitions.get(self._current_state, ()):
            new_state = transition_func(self, *args, **kwargs)
            if new_state is not None and new_state != self._current_state:
                self._current_state = new_state
                break
        return self._current_state


class Transitions(Generic[StateMachineT, P, StateEnumT]):
    def __init__(
        self,
        _spec: SpecMethodType[
            StateMachineT, P, StateEnumT
        ] = AbstractStateMachine.update,
    ) -> None:
        self._transitions: dict[
            StateEnumT, list[TransitionMethodType[StateMachineT, P, StateEnumT]]
        ] = {}
        self._frozen_transitions: dict[
            StateEnumT, tuple[TransitionMethodType[StateMachineT, P, StateEnumT], ...]
        ] = {}
        self._manual_transitions: list[
            TransitionMethodType[StateMachineT, ..., StateEnumT]
        ] = []
        self._frozen_manual_transitions: tuple[
            TransitionMethodType[StateMachineT, ..., StateEnumT], ...
        ] = tuple()
        self._spec = _spec
        self._frozen = False

    def new(
        self,
        from_states: Sequence[StateEnumT] | StateEnumT,
    ) -> TransitionDecoratorType[StateMachineT_bis, P, StateEnumT]:
        ref_sig = inspect.signature(self._spec)

        if self._frozen:
            raise TransitionFrozenError(
                "The transitions were already frozen. You cannot add new transitions afterwards."
            )

        if not isinstance(from_states, Iterable):
            from_states = (from_states,)

        if not len(from_states) >= 1:
            raise InvalidStateInput(
                "You must give at least one state to argument `from_states`"
            )

        state_type = type(from_states[0])
        if not all(map(lambda s: isinstance(s, state_type), from_states)):
            raise InvalidStateInput(
                f"All state inputs must be of the same type ({tuple(type(s) for s in state_type)} != {state_type})"
            )

        def inner_register(
            func: TransitionMethodType[StateMachineT_bis, P, StateEnumT],
        ) -> TransitionMethodType[StateMachineT_bis, P, StateEnumT]:
            sig = inspect.signature(func)
            if sig.parameters != ref_sig.parameters:
                raise TransitionSignatureError(
                    f"Method `{func.__qualname__}` does not have the same signature as `{self._spec.__qualname__}`: {sig.parameters} != {ref_sig.parameters}"
                )

            if sig.return_annotation is not state_type and (
                get_origin(sig.return_annotation) is Literal
                and any(
                    (type(r) is not state_type for r in get_args(sig.return_annotation))
                )
            ):
                raise TransitionSignatureError(
                    f"Method `{func.__qualname__}` does not have the same return type as `{self._spec.__qualname__}`: {sig.return_annotation} != {ref_sig.return_annotation}"
                )

            for state in from_states:
                transition_list = self._transitions.setdefault(state, [])
                transition_list.append(func)

            return func

        return inner_register

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> bool | None:
        if exc_value:
            raise exc_value
        self._freeze()
        return None

    def _freeze(
        self,
    ) -> None:
        self._frozen_transitions = {k: tuple(v) for k, v in self._transitions.items()}
        self._frozen_manual_transitions = tuple(self._manual_transitions)
        self._transitions.clear()
        self._manual_transitions.clear()
        self._frozen = True

    def get_transitions(
        self,
    ) -> tuple[
        dict[
            StateEnumT, tuple[TransitionMethodType[StateMachineT, P, StateEnumT], ...]
        ],
        tuple[TransitionMethodType[StateMachineT, ..., StateEnumT], ...],
    ]:
        if not self._frozen:
            raise TransitionNotFrozenError(
                "You cannot access transitions before they are frozen."
            )
        return self._frozen_transitions, self._frozen_manual_transitions

    def manual(
        self,
        func: TransitionMethodType[StateMachineT, P_bis, StateEnumT],
    ) -> TransitionMethodType[StateMachineT, P_bis, StateEnumT]:
        if self._frozen:
            raise TransitionFrozenError(
                "The transitions were already frozen. You cannot add new transitions afterwards."
            )

        @functools.wraps(func)
        def inner_wrapper(
            self: StateMachineT, *args: P_bis.args, **kwargs: P_bis.kwargs
        ) -> StateEnumT:
            result = func(self, *args, **kwargs)
            if result is not None:
                self.current_state = result
            return self.current_state

        self._manual_transitions.append(inner_wrapper)
        return inner_wrapper

    @staticmethod
    @overload
    def define_signature(
        *,
        real_func: SpecMethodType[
            StateMachineT_bis, P_bis, StateEnumT_bis
        ] = AbstractStateMachine.update,
    ) -> TransitionDecoratorType[StateMachineT_bis, P_bis, StateEnumT_bis]: ...

    @staticmethod
    @overload
    def define_signature(
        func: SpecMethodType[StateMachineT_bis, P_bis, StateEnumT_bis],
        /,
        *,
        real_func: SpecMethodType[
            StateMachineT_bis, P_bis, StateEnumT_bis
        ] = AbstractStateMachine.update,
    ) -> SpecMethodType[StateMachineT_bis, P_bis, StateEnumT_bis]: ...

    @staticmethod
    def define_signature(
        func: Optional[SpecMethodType[StateMachineT_bis, P_bis, StateEnumT_bis]] = None,
        /,
        *,
        real_func: SpecMethodType[
            StateMachineT_bis, P_bis, StateEnumT_bis
        ] = AbstractStateMachine.update,
    ) -> (
        SignatureOverloadDecoratorType[StateMachineT_bis, P_bis, StateEnumT_bis]
        | TransitionMethodType[StateMachineT_bis, P_bis, StateEnumT_bis]
    ):
        def inner(
            func: TransitionMethodType[StateMachineT_bis, P_bis, StateEnumT_bis],
        ) -> TransitionMethodType[StateMachineT_bis, P_bis, StateEnumT_bis]:
            if TYPE_CHECKING:
                return func
            else:
                wrapper = functools.wraps(real_func)(real_func)
                wrapper.__signature__ = inspect.signature(func)
                return wrapper

        if func is None:
            return inner

        return inner(func)

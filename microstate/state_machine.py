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
from contextlib import contextmanager
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Callable,
    Concatenate,
    Generator,
    Generic,
    Literal,
    Optional,
    ParamSpec,
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
    cast,
    get_args,
    get_origin,
    overload,
    runtime_checkable,
)


P = ParamSpec("P")
StateEnumT = TypeVar("StateEnumT", bound=Enum)
StateMachineT = TypeVar("StateMachineT", bound="StateMachine")


TransitionMethodType: TypeAlias = Callable[Concatenate[StateMachineT, P], StateEnumT]


@runtime_checkable
class DecoratedTransitionProtocol(Protocol[StateMachineT, P, StateEnumT]):
    _state_tag: StateEnumT

    __call__: TransitionMethodType[StateMachineT, P, StateEnumT]


class BaseStateMachineError(BaseException): ...


class StateMachineCompilationError(BaseStateMachineError): ...


class TransitionContext: ...


class StateMachine(Generic[StateEnumT, P]):
    _state_type: type[StateEnumT]
    _state_transitions: dict[
        StateEnumT,
        DecoratedTransitionProtocol[Self, P, StateEnumT],
    ]
    _start_state: StateEnumT
    _current_state: StateEnumT

    def __init_subclass__(cls, start_state: StateEnumT) -> None:
        super().__init_subclass__()
        cls._state_type = type(start_state)
        cls._start_state = start_state
        cls._current_state = start_state

        cls._state_transitions = {}
        for attr_name in dir(cls):
            if not (
                callable(f := getattr(cls, attr_name))
                and isinstance(f, DecoratedTransitionProtocol)
            ):
                continue

            state_tag = f._state_tag
            f_bis = cls._state_transitions.setdefault(state_tag, f)
            if f_bis is not f:
                raise StateMachineCompilationError(
                    f"There are multiple transitions registered for Enum member '{state_tag}': trying to register '{f.__qualname__}' but '{f_bis.__qualname__}' was already registered."
                )

    @property
    def current_state(self) -> StateEnumT:
        return self._current_state

    @current_state.setter
    def current_state(self, state: StateEnumT):
        self._current_state = state

    def update(self, *args, **kwargs) -> StateEnumT:
        transition_func = self._state_transitions.get(
            self._current_state, lambda *args, **kwargs: self._current_state
        )
        self._current_state = transition_func(self, *args, **kwargs)
        return self._current_state


TransitionDecoratorType: TypeAlias = Callable[
    [TransitionMethodType[StateMachineT, P, StateEnumT]],
    DecoratedTransitionProtocol[StateMachineT, P, StateEnumT],
]


def _register_transition(
    from_state: StateEnumT,
    _spec: TransitionMethodType[StateMachineT, P, StateEnumT],
) -> TransitionDecoratorType[StateMachineT, P, StateEnumT]:
    ref_sig = inspect.signature(_spec)

    def inner_register(
        func: TransitionMethodType[StateMachineT, P, StateEnumT],
    ) -> DecoratedTransitionProtocol[StateMachineT, P, StateEnumT]:
        sig = inspect.signature(func)
        if sig.parameters != ref_sig.parameters:
            raise StateMachineCompilationError(
                f"Method `{func.__qualname__}` does not have the same signature as `{_spec.__qualname__}`: {sig.parameters} != {ref_sig.parameters}"
            )

        if sig.return_annotation is not type(from_state) and (
            get_origin(sig.return_annotation) is Literal
            and any(
                (
                    type(r) is not type(from_state)
                    for r in get_args(sig.return_annotation)
                )
            )
        ):
            raise StateMachineCompilationError(
                f"Method `{func.__qualname__}` does not have the same return type as `{_spec.__qualname__}`: {sig.return_annotation} != {ref_sig.return_annotation}"
            )
        func = cast(DecoratedTransitionProtocol[StateMachineT, P, StateEnumT], func)
        func._state_tag = from_state

        if not isinstance(func, DecoratedTransitionProtocol):
            raise StateMachineCompilationError(
                f"Callable {func.__qualname__} does not conform to {DecoratedTransitionProtocol.__qualname__} interface."
            )
        return func

    return inner_register


@overload
def overload_signature(
    *,
    real_func: TransitionMethodType[StateMachineT, P, StateEnumT] = StateMachine.update,
) -> TransitionDecoratorType[StateMachineT, P, StateEnumT]: ...


@overload
def overload_signature(
    func: TransitionMethodType[StateMachineT, P, StateEnumT],
    /,
    *,
    real_func: TransitionMethodType[StateMachineT, P, StateEnumT] = StateMachine.update,
) -> TransitionMethodType[StateMachineT, P, StateEnumT]: ...


SignatureOverloadDecoratorType: TypeAlias = Callable[
    [TransitionMethodType[StateMachineT, P, StateEnumT]],
    TransitionMethodType[StateMachineT, P, StateEnumT],
]


def overload_signature(
    func: Optional[TransitionMethodType[StateMachineT, P, StateEnumT]] = None,
    /,
    *,
    real_func: TransitionMethodType[StateMachineT, P, StateEnumT] = StateMachine.update,
) -> (
    SignatureOverloadDecoratorType[StateMachineT, P, StateEnumT]
    | TransitionMethodType[StateMachineT, P, StateEnumT]
):
    def inner(
        func: TransitionMethodType[StateMachineT, P, StateEnumT],
    ) -> TransitionMethodType[StateMachineT, P, StateEnumT]:
        if TYPE_CHECKING:
            return func
        else:
            wrapper = functools.wraps(real_func)(real_func)
            wrapper.__signature__ = inspect.signature(func)
            return wrapper

    if func is None:
        return inner

    return inner(func)


@contextmanager
def define_transitions(
    spec_func: TransitionMethodType[StateMachineT, P, StateEnumT],
) -> Generator[
    Callable[
        [StateEnumT],
        TransitionDecoratorType[StateMachineT, P, StateEnumT],
    ],
    None,
    None,
]:
    yield functools.partial(_register_transition, _spec=spec_func)

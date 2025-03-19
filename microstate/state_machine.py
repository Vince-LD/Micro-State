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


StateEnumT = TypeVar("StateEnumT", bound=Enum)
P = ParamSpec("P")
SMT = TypeVar("SMT", bound="StateMachine")


TransitionMethodType: TypeAlias = Callable[Concatenate[SMT, P], StateEnumT]


@runtime_checkable
class DecoratedTransitionProtocol(Protocol[SMT, P, StateEnumT]):
    _state_tag: StateEnumT

    __call__: TransitionMethodType[SMT, P, StateEnumT]


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


def _register_transition(
    from_state: StateEnumT,
    _spec: TransitionMethodType[SMT, P, StateEnumT],
):  # -> Callable[..., TransitionProtocol[P, StateEnumT]]:
    ref_sig = inspect.signature(_spec)

    def inner_register(
        func: Callable[Concatenate[SMT, P], StateEnumT],
    ) -> DecoratedTransitionProtocol[SMT, P, StateEnumT]:
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
        func = cast(DecoratedTransitionProtocol[SMT, P, StateEnumT], func)
        func._state_tag = from_state

        if not isinstance(func, DecoratedTransitionProtocol):
            raise StateMachineCompilationError(
                f"Callable {func.__qualname__} does not conform to {DecoratedTransitionProtocol.__qualname__} interface."
            )
        return func

    return inner_register


TransitionDecoratorType: TypeAlias = Callable[
    [TransitionMethodType[SMT, P, StateEnumT]],
    DecoratedTransitionProtocol[SMT, P, StateEnumT],
]


@overload
def overload_signature(
    *,
    real_func: TransitionMethodType[SMT, P, StateEnumT] = StateMachine.update,
) -> TransitionDecoratorType[SMT, P, StateEnumT]: ...


@overload
def overload_signature(
    func: TransitionMethodType[SMT, P, StateEnumT],
    /,
    *,
    real_func: TransitionMethodType[SMT, P, StateEnumT] = StateMachine.update,
) -> TransitionMethodType[SMT, P, StateEnumT]: ...


SignatureOverloadDecoratorType: TypeAlias = Callable[
    [TransitionMethodType[SMT, P, StateEnumT]],
    TransitionMethodType[SMT, P, StateEnumT],
]


def overload_signature(
    func: Optional[TransitionMethodType[SMT, P, StateEnumT]] = None,
    /,
    *,
    real_func: TransitionMethodType[SMT, P, StateEnumT] = StateMachine.update,
) -> (
    SignatureOverloadDecoratorType[SMT, P, StateEnumT]
    | TransitionMethodType[SMT, P, StateEnumT]
):
    def inner(
        func: TransitionMethodType[SMT, P, StateEnumT],
    ) -> TransitionMethodType[SMT, P, StateEnumT]:
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
    spec_func: TransitionMethodType[SMT, P, StateEnumT],
) -> Generator[
    Callable[
        [StateEnumT],
        TransitionDecoratorType[SMT, P, StateEnumT],
    ],
    None,
    None,
]:
    yield functools.partial(_register_transition, _spec=spec_func)

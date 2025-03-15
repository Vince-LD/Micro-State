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
    ParamSpec,
    Self,
    TypeAlias,
    TypeVar,
    cast,
    get_args,
    get_origin,
)

STATE_TAG = "__tagged_state__"

StateEnumT = TypeVar("StateEnumT", bound=Enum)
StateEnumT_bis = TypeVar("StateEnumT_bis", bound=Enum)
P = ParamSpec("P")
P_bis = ParamSpec("P_bis")
ST = TypeVar("ST", bound="StateMachine", covariant=True)
ST_bis = TypeVar("ST_bis", bound="StateMachine")


TransitionMethodType: TypeAlias = Callable[Concatenate[ST, P], StateEnumT]
TransitionDecoratorType: TypeAlias = Callable[
    [TransitionMethodType[ST, P, StateEnumT]], TransitionMethodType[ST, P, StateEnumT]
]


class BaseStateMachineError(BaseException): ...


class StateMachineCompilationError(BaseStateMachineError): ...


class TransitionContext: ...


class StateMachine(Generic[StateEnumT, P]):
    __state_type__: type[StateEnumT]
    __state_transitions__: dict[
        StateEnumT,
        TransitionMethodType[Self, P, StateEnumT],
    ]
    __start_state__: StateEnumT

    def __init_subclass__(cls, start_state: StateEnumT) -> None:
        print("init subclass")
        super().__init_subclass__()
        cls.__state_type__ = type(start_state)
        cls.__start_state__ = start_state

        cls.__state_transitions__ = cast(
            dict[
                StateEnumT,
                TransitionMethodType[Self, P, StateEnumT],
            ],
            {
                e: f
                for fname in dir(cls)
                if callable(f := getattr(cls, fname))
                and isinstance(e := getattr(f, STATE_TAG, None), cls.__state_type__)
            },
        )
        for attr_name in dir(cls):
            if callable(f := getattr(cls, attr_name)) and isinstance(
                e := getattr(f, STATE_TAG, None), cls.__state_type__
            ):
                f_bis = cls.__state_transitions__.setdefault(
                    e,
                    cast(
                        Callable[
                            Concatenate[Self, P],
                            StateEnumT,
                        ],
                        f,
                    ),
                )
                if f_bis is not f:
                    raise StateMachineCompilationError(
                        f"There are multiple transitions registered for Enum member '{e}': trying to register '{f.__qualname__}' but '{f_bis.__qualname__}' was already registered."
                    )

    def __init__(self) -> None:
        self.state = self.__start_state__

    def update(self, *args, **kwargs) -> StateEnumT:
        transition_func = self.__state_transitions__.get(
            self.state, lambda *args, **kwargs: self.state
        )
        self.state = transition_func(self, *args, **kwargs)
        return self.state


def _register_transition(
    from_state: StateEnumT,
    _spec: TransitionMethodType[ST, P, StateEnumT],
) -> TransitionDecoratorType[ST, P, StateEnumT]:
    ref_sig = inspect.signature(_spec)

    def inner_register(
        func: Callable[Concatenate[ST, P], StateEnumT],
    ) -> Callable[Concatenate[ST, P], StateEnumT]:
        sig = inspect.signature(func)
        if sig.parameters != ref_sig.parameters:
            raise StateMachineCompilationError(
                f"Method `{func.__qualname__}` does not have the same signature as `{ref_sig.__qualname__}`: {sig.parameters} != {ref_sig.parameters}"
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
                f"Method `{func.__qualname__}` does not have the same return type as `{ref_sig.__qualname__}`: {sig.return_annotation} != {ref_sig.return_annotation}"
            )
        setattr(func, STATE_TAG, from_state)
        return func

    return inner_register


def overload_signature(
    real_func: TransitionMethodType[ST, P, StateEnumT] = StateMachine.update,
) -> TransitionDecoratorType[ST_bis, P_bis, StateEnumT_bis]:
    def inner(
        func: TransitionMethodType[ST_bis, P_bis, StateEnumT_bis],
    ) -> TransitionMethodType[ST_bis, P_bis, StateEnumT_bis]:
        if TYPE_CHECKING:
            return func

        else:

            @functools.wraps(real_func)
            def wrapper(*args, **kwargs):
                return real_func(*args, **kwargs)

            wrapper.__signature__ = inspect.signature(func)

            return wrapper

    return inner


@contextmanager
def define_transitions(
    spec_func: TransitionMethodType[ST, P, StateEnumT],
) -> Generator[
    Callable[
        [StateEnumT],
        TransitionDecoratorType[ST, P, StateEnumT],
    ],
    None,
    None,
]:
    yield functools.partial(_register_transition, _spec=spec_func)

from contextlib import contextmanager
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Generator,
    Optional,
    ParamSpec,
    Self,
    TypeVar,
    Generic,
    Literal,
    cast,
    get_origin,
    get_args,
)
from enum import Enum
import functools


StateEnumT = TypeVar("StateEnumT", bound=Enum)
StateEnumT_bis = TypeVar("StateEnumT_bis", bound=Enum)
P = ParamSpec("P")
P_bis = ParamSpec("P_bis")
STATE_TAG = "__state_tagged__"


class BaseStateMachineError(BaseException): ...


class StateMachineCompilationError(BaseStateMachineError): ...


class TransitionContext: ...


class StateMachine(Generic[StateEnumT, P]):
    __state_type__: type[StateEnumT]
    __state_transitions__: dict[
        StateEnumT,
        Callable[
            Concatenate[Self, P],
            StateEnumT,
        ],
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
                Callable[
                    Concatenate[Self, P],
                    StateEnumT,
                ],
            ],
            {
                e: f
                for fname in dir(cls)
                if callable(f := getattr(cls, fname))
                and isinstance(e := getattr(f, STATE_TAG, None), type(start_state))
            },
        )

        update_signature = inspect.signature(cls.update)
        for func in cls.__state_transitions__.values():
            sig = inspect.signature(func)
            if sig.parameters != update_signature.parameters:
                raise StateMachineCompilationError(
                    f"Method `{func.__qualname__}` does not have the same signature as `{cls.update.__qualname__}`: {sig.parameters} != {update_signature.parameters}"
                )

            if sig.return_annotation is not cls.__state_type__ and (
                get_origin(sig.return_annotation) is Literal
                and any(
                    (
                        type(r) is not cls.__state_type__
                        for r in get_args(sig.return_annotation)
                    )
                )
            ):
                raise StateMachineCompilationError(
                    f"Method `{func.__qualname__}` does not have the same return type as `{cls.update.__qualname__}`: {sig.return_annotation} != {update_signature.return_annotation}"
                )

    def __init__(self) -> None:
        self.state = self.__start_state__

    def update(self, *args, **kwargs) -> StateEnumT:
        transition_func = self.__state_transitions__.get(
            self.state, lambda *args, **kwargs: self.state
        )
        self.state = transition_func(self, *args, **kwargs)
        return self.state


ST = TypeVar("ST", bound=StateMachine, covariant=True)
ST_bis = TypeVar("ST_bis", bound=StateMachine)


def _register_transition(
    from_state: StateEnumT,
    _spec: Callable[Concatenate[ST, P], StateEnumT],
) -> Callable[
    [Callable[Concatenate[ST, P], StateEnumT]],
    Callable[Concatenate[ST, P], StateEnumT],
]:
    def inner_register(
        func: Callable[Concatenate[ST, P], StateEnumT],
    ) -> Callable[Concatenate[ST, P], StateEnumT]:
        setattr(func, STATE_TAG, from_state)
        return func

    return inner_register


def fake_signature(
    real_func: Callable[Concatenate[ST, P_bis], StateEnumT] = StateMachine.update,
) -> Callable[
    [Callable[Concatenate[ST_bis, P], StateEnumT_bis]],
    Callable[Concatenate[ST_bis, P], StateEnumT_bis],
]:
    def inner(
        func: Callable[Concatenate[ST_bis, P], StateEnumT_bis],
    ) -> Callable[Concatenate[ST_bis, P], StateEnumT_bis]:
        if TYPE_CHECKING:
            return func

        else:

            @functools.wraps(real_func)
            def wrapper(*args, **kwargs):
                return real_func(*args, **kwargs)

            wrapper.__signature__ = inspect.signature(func)

            return wrapper

    return inner


class TestE(Enum):
    ON = 1
    OFF = 2


@contextmanager
def define_transitions(
    spec_func: Callable[Concatenate[ST, P], StateEnumT],
) -> Generator[
    Callable[
        [StateEnumT],
        Callable[
            [Callable[Concatenate[ST, P], StateEnumT]],
            Callable[Concatenate[ST, P], StateEnumT],
        ],
    ],
    None,
    None,
]:
    yield functools.partial(_register_transition, _spec=spec_func)


class MyStateMachine(StateMachine[TestE, P], start_state=TestE.ON):
    @fake_signature()
    def update(self, a: int, b: int) -> TestE: ...

    with define_transitions(spec_func=update) as new:

        @new(TestE.ON)
        def on_to_off(self, a: int, b: int) -> Literal[TestE.OFF]:
            return TestE.OFF

        @new(TestE.OFF)
        def off_to_on(self, a: int, b: int) -> Literal[TestE.ON]:
            return TestE.ON


m = MyStateMachine()
u = m.update(1, 2)
print(m.update(1, 2))
print(m.update(1, 2))
print(m.update(1, 2))


class OtherStateMachine(StateMachine[TestE, P], start_state=TestE.ON):
    @fake_signature()
    def update(self) -> TestE: ...

    with define_transitions(spec_func=update) as new:

        @new(TestE.ON)
        def on_to_off(self) -> Literal[TestE.OFF]:
            return TestE.OFF

        @new(TestE.OFF)
        def off_to_on(self) -> Literal[TestE.ON]:
            return TestE.ON


m = OtherStateMachine()
u = m.update()

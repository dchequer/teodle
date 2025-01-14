from asyncio import Event
from collections import defaultdict
from functools import cache
from typing import Any, NewType

EventType = NewType('EventType', str)

TYPE_TOTAL_VOTES = EventType('TOTAL_VOTES')
TYPE_CLIP_STATE = EventType('CLIP_STATE')


@cache
def TYPE_USER_VOTE_STATE(username: str) -> EventType:
    return EventType(f'USER_VOTE_STATE_{username}')


@cache
def TYPE_USER_SCORE(username: str) -> EventType:
    return EventType(f'USER_SCORE_{username}')


_subscriptions: dict[EventType, set['Subscription']] = defaultdict(set)
_publish_cache: dict[EventType, Any] = {}


def publish(type: EventType, args: Any = None) -> None:
    _publish_cache[type] = args

    for subscription in _subscriptions[type]:
        subscription.notify(args)


def empty_user_state() -> None:
    for event_type in _publish_cache.keys():
        if event_type.startswith('USER_'):
            publish(event_type, None)


class Subscription:
    type: EventType
    _event: Event
    _args: Any

    def __init__(self, type: EventType) -> None:
        self.type = type
        self._event = Event()

        if self.type in _publish_cache:
            self.notify(_publish_cache[self.type])

    def __enter__(self) -> 'Subscription':
        _subscriptions[self.type].add(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        _subscriptions[self.type].remove(self)

    def notify(self, args: Any) -> None:
        self._args = args
        self._event.set()

    async def wait(self) -> Any:
        await self._event.wait()
        self._event.clear()
        return self._args

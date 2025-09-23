"""
Timer adapter base interface and abstract implementation.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any

from .types import TimerEvent, TimerInfo


class ITimerAdapter(ABC):
    """Interface for timer device adapters."""

    @abstractmethod
    async def start(self) -> None:
        """Start the timer adapter and begin event processing."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the timer adapter and cleanup resources."""
        pass

    @abstractmethod
    async def connect(self, **kwargs) -> None:
        """
        Connect to the timer device.
        
        Args:
            **kwargs: Connection parameters (port, mac_address, etc.)
        """
        pass

    @abstractmethod
    def info(self) -> TimerInfo:
        """Get timer device information."""
        pass

    @property
    @abstractmethod
    def events(self) -> AsyncIterator[TimerEvent]:
        """Async iterator yielding timer events."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if timer is currently connected."""
        pass


class BaseTimerAdapter(ITimerAdapter):
    """
    Base implementation providing common timer adapter functionality.
    """

    def __init__(self, name: str):
        self.name = name
        self._connected = False
        self._running = False
        self._event_queue: asyncio.Queue[TimerEvent] = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []

    @property
    def is_connected(self) -> bool:
        """Check if timer is currently connected."""
        return self._connected

    async def start(self) -> None:
        """Start the adapter."""
        if self._running:
            return
        
        self._running = True
        self._event_queue = asyncio.Queue()

    async def stop(self) -> None:
        """Stop the adapter and cleanup."""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._tasks.clear()

    async def _emit_event(self, event: TimerEvent) -> None:
        """Emit an event to the event queue."""
        if self._running:
            await self._event_queue.put(event)

    @property
    async def events(self) -> AsyncIterator[TimerEvent]:
        """Async iterator yielding timer events."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def _create_task(self, coro) -> asyncio.Task:
        """Create and track an async task."""
        task = asyncio.create_task(coro)
        self._tasks.append(task)
        return task
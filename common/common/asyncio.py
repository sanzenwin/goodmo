import sys
import asyncio
from asyncio.base_events import _format_handle
from asyncio.log import logger

if sys.platform == 'win32':
    from asyncio.windows_events import SelectorEventLoop, DefaultEventLoopPolicy
else:
    from asyncio.unix_events import SelectorEventLoop, DefaultEventLoopPolicy


class StandardSelectorEventLoop(SelectorEventLoop):
    def run_frame(self):
        event_list = self._selector.select(0)
        self._process_events(event_list)
        ntodo = len(self._ready)
        for i in range(ntodo):
            handle = self._ready.popleft()
            if handle._cancelled:
                continue
            if self._debug:
                try:
                    self._current_handle = handle
                    t0 = self.time()
                    handle._run()
                    dt = self.time() - t0
                    if dt >= self.slow_callback_duration:
                        logger.warning('Executing %s took %.3f seconds',
                                       _format_handle(handle), dt)
                finally:
                    self._current_handle = None
            else:
                handle._run()
        handle = None  # Needed to break cycles when an exception occurs.


class StandardEventLoopPolicy(DefaultEventLoopPolicy):
    _loop_factory = StandardSelectorEventLoop


def use_standard_loop():
    asyncio.set_event_loop_policy(StandardEventLoopPolicy())


use_standard_loop()

asyncio_loop = asyncio.get_event_loop()

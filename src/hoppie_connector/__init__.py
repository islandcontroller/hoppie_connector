from .Messages import HoppieMessage, HoppieMessageFactory
from .Responses import ErrorResponse, SuccessResponse, PollSuccessResponse, PingSuccessResponse, PeekSuccessResponse
from .API import HoppieAPI
from datetime import timedelta
from typing import TypeVar
import warnings

class HoppieError(Exception):
    pass
class HoppieWarning(UserWarning):
    pass

class HoppieConnector(object):
    """HoppieConnector(station_name, logon)

    Connector for interacting with Hoppie's ACARS service.
    """

    def __init__(self, station_name: str, logon: str, url: str | None = None):
        """Create a new connector

        Note:
            Station name must be a valid ICAO flight number or 3-letter org code.

        Args:
            station_name (str): Own station name
            logon (str): API logon code
            url (str, optional): API URL. Defaults to None.
        """
        self._f = HoppieMessageFactory(station_name)
        self._api = HoppieAPI(logon, url)

    _T = TypeVar('_T')
    def _connect(self, message: HoppieMessage, type: _T) -> tuple[_T, timedelta]:
        response, delay = self._api.connect(message)
        if isinstance(response, ErrorResponse): 
            raise HoppieError(response.get_reason())
        elif isinstance(response, type):
            return response, delay
        else:
            raise TypeError('Response can not be represented by requested target type')

    def peek(self) -> tuple[list[tuple[int, HoppieMessage]], timedelta]:
        """Peek all messages destined to own station

        Note:
            Own station will not appear as 'online'. Peeked messages will not
            be marked as relayed. Message history is kept on the server for up 
            to 24 hours.

        Returns:
            tuple[list[tuple[int, HoppieMessage]], timedelta]: List of messages (id, content) and reponse delay
        """
        response, delay = self._connect(self._f.create_peek(), PeekSuccessResponse)
        result = []
        for d in response.get_data():
            try:
                result.append((d['id'], self._f.create_from_data(d)))
            except ValueError as e:
                warnings.warn(f"Unable to parse {d}: {e}", HoppieWarning)
        return result, delay

    def poll(self) -> tuple[list[HoppieMessage], timedelta]:
        """Poll for new messages destined to own station and mark them as relayed.

        Note:
            Polling will make the own station name appear as 'online' and mark
            received messages as 'relayed'. Previously relayed messages will 
            not reappear in the next `poll` response.

        Returns:
            tuple[list[HoppieMessage], timedelta]: List of messages and response delay
        """
        response, delay = self._connect(self._f.create_poll(), PollSuccessResponse)
        result = []
        for d in response.get_data():
            try:
                result.append(self._f.create_from_data(d))
            except ValueError as e:
                warnings.warn(f"Unable to parse {d}: {e}", HoppieWarning)
        return result, delay

    def ping(self, stations: list[str] | str | None = None) -> tuple[list[str], timedelta]:
        """Check station online status.

        Note:
            Use `stations='*'` in order to retrieve a list of all currently online stations.
            An empty argument can serve as a connection check to the API server.

        Args:
            stations (list[str] | str | None, optional): List of stations to check. Defaults to None.

        Returns:
            tuple[list[str], timedelta]: List of online stations and response delay
        """
        response, delay = self._connect(self._f.create_ping(stations), PingSuccessResponse)
        return response.get_stations(), delay

    def send_telex(self, to_name: str, message: str) -> timedelta:
        """Send a freetext message to recipient station.

        Note:
            Message length is limited to 220 characters by ACARS specification.

        Args:
            to_name (str): Recipient station name
            message (str): Message content

        Returns:
            timedelta: Response delay
        """
        return self._connect(self._f.create_telex(to_name, message), SuccessResponse)[1]
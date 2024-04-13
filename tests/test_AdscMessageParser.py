from hoppie_connector.Messages import AdscMessageParser, AdscPeriodicContractRequestMessage, AdscPeriodicContractCancellationMessage, AdscPeriodicReportMessage
import unittest

class TestAdscMessageParser(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self._UUT = AdscMessageParser()

    def test_periodic_contract_request(self):
        self.assertIsInstance(self._UUT.from_packet('ATC', 'CALLSIGN', 'REQUEST PERIODIC 120'), AdscPeriodicContractRequestMessage)

    def test_periodic_report(self):
        self.assertIsInstance(self._UUT.from_packet('CALLSIGN', 'ATC', 'REPORT CALLSIGN 011820 -10.0000 10.00000 3000'), AdscPeriodicReportMessage)

    def test_periodic_contract_cancellation(self):
        self.assertIsInstance(self._UUT.from_packet('CALLSIGN', 'ATC', 'REPORT CANCEL'), AdscPeriodicContractCancellationMessage)

    def test_unknown_format(self):
        self.assertRaises(ValueError, lambda: self._UUT.from_packet('ATC', 'CALLSIGN', 'REQUEST EVENT'))

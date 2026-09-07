import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PublicationEvaluation(unittest.TestCase):
    def test_no_private_working_files(self):
        for name in ('research-and-commercial-plan.md','pricing-screenshot.png','github-live.json','consent.json'):
            self.assertFalse(any(p.name==name for p in ROOT.rglob('*') if '.venv' not in p.parts and '.git' not in p.parts))

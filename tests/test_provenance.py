import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ProvenanceEvaluation(unittest.TestCase):
 def test_vendored_sources_match_manifest(self):
  base=ROOT/'contributor_agent/_vendor/dd'
  for record in json.loads((base/'provenance.json').read_text())['files']:
   self.assertEqual(hashlib.sha256((base/record['target']).read_bytes()).hexdigest(),record['local_sha256'])
 def test_policy_references_are_pinned(self):
  for record in json.loads((ROOT/'policies/sources.json').read_text()):
   self.assertEqual(len(record['sha256']),64)
   self.assertEqual(len(record['commit']),40)
   self.assertIn(record['commit'],record['source'])

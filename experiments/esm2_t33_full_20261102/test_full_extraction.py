import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

spec = importlib.util.spec_from_file_location("full", Path(__file__).with_name("run_full_extraction.py"))
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


def fixture(a, b):
    rng = np.random.default_rng(a + 1000 * b)
    x = rng.standard_normal((b-a, f.D)).astype(np.float32)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    return x


class Test(unittest.TestCase):
    def test_sharding_is_complete_without_overlap(self):
        for count in [1, 2, 3, 7, 8, 16, 32, 73]:
            spans = [f.shard_interval(i, count) for i in range(count)]
            self.assertEqual(spans[0][0], 0)
            self.assertEqual(spans[-1][1], f.N)
            self.assertTrue(all(b > a for a,b in spans))
            self.assertTrue(all(spans[i][1] == spans[i+1][0] for i in range(len(spans)-1)))

    def test_invalid_shards(self):
        for i,k in [(-1,1),(3,2),(0,0),(0,f.N+1)]:
            with self.assertRaises(ValueError): f.shard_interval(i,k)

    def test_frozen_anchor_count(self):
        self.assertEqual(len(f.ANCHOR_HASHES), 6)
        self.assertEqual(len(set(f.ANCHOR_HASHES)), 6)
        self.assertEqual(f.MODEL_SHA, "08e4846e537177426273712802403f7ba8261b6c")

    def test_data_rejects_wrong_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "input.json"
            p.write_text('{"test_set": []}')
            with self.assertRaisesRegex(ValueError, "SHA256"): f.read_dataset(p)

    def test_save_verify_block_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            x = fixture(0,3)
            info = f.save_block(p,0,3,x,"cpu")
            manifest = p/'part_00000_00003.json'
            self.assertEqual(info['npy_sha256'],f.sha256(p/'part_00000_00003.npy'))
            verified,y = f.verify_block(manifest, expected_device="cpu")
            self.assertTrue(np.array_equal(x,y))
            with self.assertRaises(FileExistsError): f.save_block(p,0,3,x,"cpu")
            with self.assertRaises(ValueError): f.verify_block(manifest, expected_device="cuda")

    def test_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            f.save_block(p,0,3,fixture(0,3),"cpu")
            npy = p / 'part_00000_00003.npy'
            with open(npy,'ab') as h: h.write(b'BAD')
            with self.assertRaisesRegex(ValueError,"Corrupted"): f.verify_block(p/'part_00000_00003.json')

    def test_assemble_exact_coverage(self):
        with tempfile.TemporaryDirectory() as d,patch.object(f,"N",5):
            p=Path(d)
            f.save_block(p/'part1',0,2,fixture(0,2),'cpu')
            f.save_block(p/'part2',2,5,fixture(2,5),'cpu')
            doc = f.assemble(p,p/'assembled')
            self.assertEqual(doc['rows'],5)
            v=np.load(p/'assembled'/'embeddings_t33.npy',allow_pickle=False)
            self.assertEqual(v.shape,(5,f.D))
            np.testing.assert_array_equal(v,np.vstack([fixture(0,2),fixture(2,5)]))
            self.assertEqual(f.sha256(p/'assembled'/'embeddings_t33.npy'),doc['output_sha256'])
            with self.assertRaises(FileExistsError): f.assemble(p,p/'assembled')

    def test_assembly_gap_detected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(f,"N",5):
            p=Path(d)
            f.save_block(p,0,2,fixture(0,2),'cpu')
            f.save_block(p,3,5,fixture(3,5),'cpu')
            with self.assertRaisesRegex(ValueError,"Missing/overlapping"): f.assemble(p,p/'assembled')

    def test_assembly_duplicate_detected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(f,"N",4):
            p=Path(d)
            f.save_block(p/'part1',0,2,fixture(0,2),'cpu')
            f.save_block(p/'part2',0,2,fixture(0,2),'cpu')
            f.save_block(p/'part3',2,4,fixture(2,4),'cpu')
            with self.assertRaisesRegex(ValueError,"Missing/overlapping"): f.assemble(p,p/'assembled')

    def test_invalid_norms(self):
        with self.assertRaisesRegex(ValueError,'Invalid L2'):
            f.norm_check(np.zeros((1,f.D),dtype=np.float32))
        with self.assertRaisesRegex(ValueError,'finiteness'):
            x = np.ones((1,f.D), dtype=np.float32)
            x[0,0] = np.nan
            f.norm_check(x)

    def test_sha_is_file_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a'
            p.write_bytes(b'abc')
            self.assertEqual(f.sha256(p),hashlib.sha256(b'abc').hexdigest())

    def test_orphan_evidence_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'part_00000_00002.npy').write_bytes(b'orphan')
            with self.assertRaises(FileExistsError): f.save_block(p,0,2,fixture(0,2),'cpu')

if __name__ == '__main__':
    unittest.main()

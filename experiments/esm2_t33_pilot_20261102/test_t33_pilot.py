"""Local CPU-unit checks; do not substitute for actual pretrained-model execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

module_file = Path(__file__).with_name("run_t33_pilot.py")
spec = importlib.util.spec_from_file_location("t33pilot", module_file)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PilotTest(unittest.TestCase):
    def test_sample_contract(self):
        self.assertEqual(len(mod.SAMPLE_INDICES), len(mod.EXPECTED_LENGTHS))
        self.assertEqual(len(set(mod.SAMPLE_INDICES)), 6)
        self.assertEqual(max(mod.EXPECTED_LENGTHS), 995)
        self.assertTrue(all(x > 0 for x in mod.EXPECTED_LENGTHS))

    def test_hash_different(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data.json"
            p.write_text("{}")
            with self.assertRaises(RuntimeError):
                mod.load_sequences(p)

    def test_mask_excludes_special_and_padding(self):
        ids = torch.tensor([0, 3, 4, 2, 1, 1])
        att = torch.tensor([1, 1, 1, 1, 0, 0])
        mask = mod.residue_mask(ids, att, 0, 2, 1)
        self.assertEqual(mask.tolist(), [False, True, True, False, False, False])

    def test_mask_rejects_wrong_shapes(self):
        with self.assertRaises(ValueError):
            mod.residue_mask(torch.zeros((1,3),dtype=torch.long),torch.ones(3),0,2,1)

    def test_pool_residue_only(self):
        hidden = torch.tensor([[100.,0.],[1.,0.],[1.,0.],[0.,100.]])
        mask = torch.tensor([False,True,True,False])
        x = mod.normalized_mean(hidden,mask)
        np.testing.assert_allclose(x,np.array([1,0],dtype=np.float32),atol=1e-7)

    def test_pool_empty_rejected(self):
        with self.assertRaises(ValueError):
            mod.normalized_mean(torch.eye(2),torch.tensor([False,False]))

    def test_pool_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            mod.normalized_mean(torch.tensor([[float("nan"),1.]]), torch.tensor([True]))

    def test_output_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            data = np.ones((6,1280),dtype=np.float32)
            manifest = {"status":"fixture"}
            mod.save_output(data,manifest,root)
            self.assertEqual(mod.digest_file(root/"pilot_embedding.npy"),manifest["embedding_sha256"])
            np.testing.assert_array_equal(np.load(root/"pilot_embedding.npy"),data)
            self.assertEqual(json.loads((root/"pilot_result.json").read_text())["status"],"fixture")
            with self.assertRaises(FileExistsError):
                mod.save_output(data,manifest,root)


if __name__=="__main__":
    unittest.main()

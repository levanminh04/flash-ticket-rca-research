"""Real-process chunk equivalence and checkpoint tests, synthetic inputs only."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W))
from scripts.task_e.rcd_development import CONFIGS,RCDWorker,require_rcd_execution_contract,validate_response
from scripts.task_e.rcd_recovery import job,validate_single
from scripts.task_e.execution import save_json,file_sha

RUN=Path(sys.argv[1]);sys.argv=sys.argv[:1]
CONTRACT=require_rcd_execution_contract(RUN)


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=np.arange(300,dtype=float)%11/11
        cls.values=np.c_[np.r_[base,base+30],np.r_[base,base]]
        cls.record={'case':'synthetic-only','handle':'synthetic-only','values':cls.values,
                    'numeric_sha256':'0'*64,'audit_sha256':'1'*64}
        with RCDWorker(RUN,1) as worker:
            cls.original=worker.exchange({'values':cls.values.tolist(),'configs':CONFIGS},RUN/'original-nine.jsonl')
        validate_response(cls.original,cls.values,CONTRACT)
        with ThreadPoolExecutor(max_workers=3) as pool:
            cls.chunks=list(pool.map(lambda c:job(RUN,cls.record,c,CONTRACT),CONFIGS))

    def test_nine_real_chunks_equal_qualified_batch(self):
        for new,old in zip(self.chunks,self.original['results']):
            self.assertEqual(new['status'],'COMPLETE',new)
            self.assertEqual({k:v for k,v in new['result'].items() if k!='wall_seconds'},
                             {k:v for k,v in old.items() if k!='wall_seconds'})
            for a in new['artifacts']:self.assertEqual(file_sha(a['path']),a['sha256'])

    def test_complete_checkpoint_reused_without_process(self):
        with patch('scripts.task_e.rcd_recovery.subprocess.Popen',side_effect=AssertionError('No rerun')):
            same=job(RUN,self.record,CONFIGS[0],CONTRACT)
        self.assertEqual(same,self.chunks[0])

    def test_single_validator_rejects_identity_or_rank_corruption(self):
        response={**self.original,'results':[self.original['results'][0]]}
        self.assertEqual(validate_single(response,self.record,CONFIGS[0],CONTRACT)['ranks'],['m0'])
        for field,bad in (('input_numeric_sha256','0'*64),('shape',[600,3])):
            changed=copy.deepcopy(response);changed[field]=bad
            with self.assertRaises(ValueError):validate_single(changed,self.record,CONFIGS[0],CONTRACT)
        changed=copy.deepcopy(response);changed['results'][0]['metric_rank_indices']=[1]
        with self.assertRaises(ValueError):validate_single(changed,self.record,CONFIGS[0],CONTRACT)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(RecoveryTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    save_json(RUN/'rcd-recovery-fixture-report.json',{'tests_run':result.testsRun,
        'failures':[str(x) for x in result.failures],'errors':[str(x) for x in result.errors],
        'passed':result.wasSuccessful(),'scope':'synthetic real processes; no corpus predictions',
        'all9_chunk_vs_qualified_batch':True if result.wasSuccessful() else None})
    raise SystemExit(0 if result.wasSuccessful() else 1)

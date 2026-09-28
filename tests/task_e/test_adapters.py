"""Predeclared analytic window/imputation tests, no actual dataset access."""
import json
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.input_adapters import rcd_bundle, integrated_bundle
from scripts.task_e.loader import TRACE_FIELDS, LoaderError


def raw():
    ticks = np.arange(801)
    traces = []
    for t in ticks:
        traces.append(dict(zip(TRACE_FIELDS, ['clock','t'+str(t),'a','a','m','o','',t*1000,t*1000000,1,0])))
    return {'metrics': pd.DataFrame({'time': ticks,'a_cpu': ticks.astype(float),
                                     'a_mem': np.ones(801),'unknown_cpu':ticks}),
            'traces':pd.DataFrame(traces), 'logs':None}


class Adapters(unittest.TestCase):
    def test_raw_seconds_not_binned_and_reference_only_imputation(self):
        r = raw()
        r['metrics'].loc[[101, 400], 'a_cpu'] = np.nan
        b = rcd_bundle(r, 400, ['a'])
        self.assertEqual(b['values'].shape, (600,1))
        expected = np.median(np.delete(np.arange(100,400),1))
        self.assertEqual(b['values'][1,0], expected)
        self.assertEqual(b['values'][300,0], expected)
        self.assertEqual(b['owners'], {'m0':0})
        self.assertEqual(b['audit']['channels']['a_mem']['reason'],'REFERENCE_IQR_NOT_POSITIVE')

    def test_finite_240_gate_not_row_count(self):
        r = raw()
        r['metrics'].loc[np.arange(100,161), 'a_cpu'] = np.nan
        self.assertEqual(rcd_bundle(r,400,['a'])['values'].shape,(600,0))
        r['metrics'].loc[160,'a_cpu']=160.
        self.assertEqual(rcd_bundle(r,400,['a'])['values'].shape,(600,1))

    def test_duplicate_conflict_invalidates_channel(self):
        r=raw()
        copy=r['metrics'].iloc[[110]].copy()
        r['metrics']=pd.concat([r['metrics'],copy])
        self.assertEqual(rcd_bundle(r,400,['a'])['values'].shape,(600,1))
        copy['a_cpu']=999.
        r['metrics']=pd.concat([r['metrics'],copy])
        self.assertEqual(rcd_bundle(r,400,['a'])['values'].shape,(600,0))

    def test_integrated_history_and_past_only_cutoff(self):
        r=raw()
        with self.assertRaises(LoaderError):
            integrated_bundle(r,359)
        a=integrated_bundle(r,400)
        self.assertEqual(a['ref'].shape,(1,12,30))
        self.assertEqual(a['query'].shape,(1,12,6))
        self.assertEqual(a['ref'][0,8,0],44.5)
        self.assertEqual(a['query'][0,8,-1],394.5)
        r['metrics'].loc[r['metrics'].time>=400,'a_cpu']=1e10
        b=integrated_bundle(r,400)
        np.testing.assert_array_equal(a['ref'],b['ref'])
        np.testing.assert_array_equal(a['query'],b['query'])


if __name__=='__main__':
    output=Path(sys.argv[1])
    if not (output/'run-contract.json').is_file():
        raise SystemExit('Contract required')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    (output/'adapter-report.json').write_text(json.dumps({'tests_run':result.testsRun,
        'failures':[(str(t),e) for t,e in result.failures],
        'errors':[(str(t),e) for t,e in result.errors]},indent=2),encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())

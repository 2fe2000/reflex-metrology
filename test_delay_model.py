"""Causality and state-estimation correctness, beyond checking headline scores."""
import copy,itertools,json,unittest
from pathlib import Path
import numpy as np
from delay_model import TimestampedKalman,BayesianRegime
from delay_benchmark import prepare,run
from delayed_runtime import DelayedStream

ROOT=Path(__file__).resolve().parent

class DelayTests(unittest.TestCase):
    def test_portable_delayed_stream_matches_all_locked_replays(self):
        for ds in [1,2]:
            a=json.loads((ROOT/f'models/reflex_delayed_{ds}.json').read_text());d=np.load(ROOT/f'models/replay_{ds}.npz');ref=np.load(ROOT/f'results/v7/predictions_{ds}.npz')
            for delay in [0,5,20]:
                for phase in range(5):
                    out=DelayedStream(a,d['X'],d['y'],d['keys'],delay,phase).advance(len(d['y']))
                    np.testing.assert_allclose([h['prediction'] for h in out['history']],ref[f'delayed_ensemble_d{delay}_p{phase}'],atol=1e-10,rtol=1e-10)
                    self.assertEqual(out['queries'],len(np.arange(phase,len(d['y']),5)))
                    self.assertEqual(out['arrived'],len(np.arange(phase,max(len(d['y'])-delay,phase),5)))

    def test_ensemble_cannot_read_a_label_before_its_arrival(self):
        a=json.loads((ROOT/'models/reflex_delayed_1.json').read_text());d=np.load(ROOT/'models/replay_1.npz');y=d['y'][:50].copy();y[10]+=10000
        first=DelayedStream(a,d['X'][:50],d['y'][:50],d['keys'][:50],20,0).advance(30)
        second=DelayedStream(a,d['X'][:50],y,d['keys'][:50],20,0).advance(30)
        np.testing.assert_array_equal([h['prediction'] for h in first['history']],[h['prediction'] for h in second['history']])
        self.assertIsNone(first['history'][10]['measured'])

    def test_regime_posterior_matches_exhaustive_segmentation(self):
        cfg={'noise_std':.5,'noise_multiplier':1.,'prior_width':4.,'hazard':.1}
        model=BayesianRegime(cfg);values=np.array([.1,.2,1.1,.9]);terms=[]
        R=.25;h=.1
        for resets in itertools.product([False,True],repeat=4):
            starts=[0]+[i for i in range(1,4) if resets[i]];bounds=starts+[4]
            logp=sum(np.log(h if flag else 1-h) for flag in resets)
            for segment,(s,e) in enumerate(zip(bounds[:-1],bounds[1:])):
                variance=4. if resets[s] else R*.01
                obs=values[s:e];C=R*np.eye(e-s)+variance*np.ones((e-s,e-s))
                logp+=-.5*((e-s)*np.log(2*np.pi)+np.linalg.slogdet(C)[1]+obs@np.linalg.solve(C,obs))
                last_mean=float(obs.sum()/(R/variance+len(obs)))
            terms.append((logp,last_mean))
        lw=np.array([a for a,b in terms]);w=np.exp(lw-lw.max());w/=w.sum()
        expected=float(w@np.array([b for a,b in terms]))
        for i,y in enumerate(values):model.observe(np.ones(1),y,i*5)
        self.assertAlmostEqual(model.predict(np.ones(1),20),expected,12)

    def test_regime_memory_bounded_and_extreme_updates_finite(self):
        model=BayesianRegime({'noise_std':.1,'noise_multiplier':1.,'prior_width':4.,'hazard':.01})
        for i in range(300):
            model.observe(np.ones(1),float((i//40)%2)*1000,i*5)
            self.assertLessEqual(len(model.weights),32)
            self.assertTrue(np.isfinite(model.predict(np.ones(1),i*5+20)))
            self.assertAlmostEqual(model.weights.sum(),1.,12)

    def test_damped_filter_matches_explicit_state_space_equations(self):
        cfg=dict(trend=True,prior=1.,q=.03)
        model=TimestampedKalman(cfg,2)
        w=np.zeros(3);P=np.diag([1.,1.,.001]);F=np.array([[1.,0.,1.],[0.,1.,0.],[0.,0.,.95]])
        Q=np.diag([.03,.0003,.0003]);t0=0
        for t,z,y in [(0,np.array([1.,.2]),1.2),(5,np.array([1.,-.5]),.9),(13,np.array([1.,1.]),-.4)]:
            for _ in range(t-t0):w=F@w;P=F@P@F.T+Q
            h=np.r_[z,0.];cross=P@h;den=1+h@cross
            w+=cross/den*(y-h@w);P-=np.outer(cross,cross)/den
            model.observe(z,y,t)
            np.testing.assert_allclose(model.w,w,atol=1e-12)
            np.testing.assert_allclose(model.P,P,atol=1e-12)
            future=w.copy()
            for _ in range(7):future=F@future
            self.assertAlmostEqual(model.predict(z,t+7),h@future,12)
            t0=t

    def pack(self):
        a=json.loads((ROOT/'models/reflex_1.json').read_text());d=np.load(ROOT/'models/replay_1.npz')
        p=prepare((d['X'][:80],d['y'][:80].copy(),d['keys'][:80]),a,{'indices':list(range(4)),'contexts':[]})
        return a,p

    def test_unrequested_labels_cannot_change_predictions(self):
        a,p=self.pack();q=copy.deepcopy(p);q['y'][np.arange(80)%5!=0]+=10000
        for method,cfg in [('ema',{'rate':.2}),('rls',{'dim':0,'prior':1.,'forget':.99}),('timestamped',{'dim':0,'prior':1.,'q':.01,'trend':True}),('bayesian_regime',{'noise_std':.1,'noise_multiplier':1.,'prior_width':4.,'hazard':.01}),('grape',{})]:
            _,first=run(p,a,method,cfg,5,0,True);_,second=run(q,a,method,cfg,5,0,True)
            np.testing.assert_array_equal(first,second)

    def test_future_arrival_and_own_label_cannot_change_earlier_predictions(self):
        a,p=self.pack();q=copy.deepcopy(p);q['y'][10]+=100
        cfg={'dim':0,'prior':1.,'q':.01,'trend':True}
        for delay in [0,5,20]:
            _,first=run(p,a,'timestamped',cfg,delay,0,True);_,second=run(q,a,'timestamped',cfg,delay,0,True)
            boundary=10+max(delay,1)
            np.testing.assert_array_equal(first[:boundary],second[:boundary])
            self.assertNotEqual(first[boundary],second[boundary])

if __name__=='__main__':unittest.main()

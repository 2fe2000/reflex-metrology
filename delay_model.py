"""Timestamped residual estimation. Classical Kalman/RLS building blocks, not a novelty claim.

Models receive only features and timestamped labels that have actually arrived.
The Kalman posterior lives at the newest *sample timestamp*, not arrival time.
"""
import numpy as np


class GlobalEMA:
    def __init__(self, cfg):
        self.rate = cfg['rate']; self.mean = 0.

    def predict(self, z, t):
        return self.mean

    def observe(self, z, residual, t):
        self.mean += self.rate * (residual - self.mean)


class RecursiveResidual:
    def __init__(self, cfg, dimension):
        self.cfg = cfg; self.w = np.zeros(dimension)
        self.P = np.eye(dimension) * cfg['prior']; self.t = 0

    def predict(self, z, t):
        return float(self.w @ z)

    def observe(self, z, residual, t):
        self.P /= self.cfg['forget'] ** max(t-self.t, 0)
        p = self.P @ z; den = 1. + z @ p
        self.w += p / den * (residual - self.w @ z)
        self.P -= np.outer(p, p) / den
        self.P = (self.P + self.P.T) * .5
        self.t = t


class TimestampedKalman:
    """Local level, optional damped slope, and optional feature/context coefficients.

Independent random-walk noise for level/coefficients; damped slope when enabled.
For fixed delays arrivals remain ordered. Filtering at source timestamps plus
forward prediction is sufficient; it avoids pretending stale data is current.
"""
    def __init__(self, cfg, dimension):
        self.cfg = cfg; self.trend = bool(cfg['trend'])
        self.n = dimension + int(self.trend)
        self.w = np.zeros(self.n); self.P = np.eye(self.n) * cfg['prior']
        self.t = 0; self.rho = .95
        self.q = np.full(self.n, cfg['q'] * .01)
        self.q[0] = cfg['q']
        if self.trend:
            self.q[-1] = cfg['q'] * .01
            self.P[-1, -1] = .001

    def vector(self, z):
        return np.r_[z, 0.] if self.trend else z

    def predict(self, z, t):
        h = self.vector(z)
        if self.trend:
            h[-1] = (1-self.rho**max(t-self.t, 0))/(1-self.rho)
        return float(self.w @ h)

    def observe(self, z, residual, t):
        if t < self.t:
            raise ValueError('Out-of-order arrivals require a separate fixed-lag buffer')
        dt = t-self.t
        if self.trend:
            for _ in range(dt):
                self.w[0] += self.w[-1]; self.w[-1] *= self.rho
                self.P[0, :] += self.P[-1, :]
                self.P[:, 0] += self.P[:, -1]
                self.P[-1, :] *= self.rho; self.P[:, -1] *= self.rho
                self.P.flat[::self.n+1] += self.q
        else:
            self.P.flat[::self.n+1] += self.q * dt
        h = self.vector(z); p = self.P @ h; den = float(1. + h @ p)
        innovation = float(residual-self.w @ h)
        self.w += p / den * innovation
        self.P -= np.outer(p, p)/den
        self.P = (self.P+self.P.T)*.5
        self.t = t


def make_model(method, cfg, dimension):
    if method == 'ema': return GlobalEMA(cfg)
    if method == 'rls': return RecursiveResidual(cfg, dimension)
    if method == 'timestamped': return TimestampedKalman(cfg, dimension)
    if method == 'adaptive_timestamped': return AdaptiveTimestampedKalman(cfg, dimension)
    if method == 'reset_ema': return ResetEMA(cfg)
    if method == 'bayesian_regime': return BayesianRegime(cfg)
    raise ValueError(method)


class ResetEMA(GlobalEMA):
    """Strong simple comparator: a noise-normalized change gate plus EWMA."""
    def __init__(self,cfg):
        super().__init__(cfg); self.cfg=cfg; self.sign=0; self.count=0

    def observe(self,z,residual,t):
        error=residual-self.mean; sign=int(np.sign(error))
        if abs(error)>self.cfg['threshold']*self.cfg['noise_std']:
            self.count=self.count+1 if sign==self.sign else 1;self.sign=sign
        else:self.count=0;self.sign=0
        if self.count>=self.cfg['confirm']:
            self.mean+=error;self.count=0
        else:super().observe(z,residual,t)


class AdaptiveTimestampedKalman(TimestampedKalman):
    """Innovation-triggered level reset, using only received timestamped residuals.

    The gate is classical change detection. No new-algorithm claim is made.
    Stale measurements still update the posterior at their source timestamp.
    """
    def __init__(self,cfg,dimension):
        super().__init__(cfg,dimension);self.sign=0;self.count=0;self.resets=0

    def observe(self,z,residual,t):
        error=residual-self.predict(z,t);sign=int(np.sign(error))
        if abs(error)>self.cfg['threshold']*self.cfg['noise_std']:
            self.count=self.count+1 if sign==self.sign else 1;self.sign=sign
        else:self.count=0;self.sign=0
        # First perform the correctly timestamped ordinary filter update.
        super().observe(z,residual,t)
        if self.count>=self.cfg['confirm']:
            self.w[0]+=residual-float(self.vector(z)@self.w)
            if self.trend:self.w[-1]=0.
            self.count=0;self.resets+=1


class BayesianRegime:
    """Conjugate Gaussian regime hypotheses with bounded posterior merging.

    Based on Bayesian online change detection (Adams & MacKay, 2007).
    Moment merging is inspired by recent posterior-merging research (Bagel,
    arXiv:2611.03230), but is NOT a reproduction of Bagel's full algorithm.
    At most 32 hypotheses; merging matches the latent mean/variance moments.
    """
    def __init__(self,cfg):
        self.cfg=cfg;self.R=(cfg['noise_std']*cfg['noise_multiplier'])**2
        self.prior_var=(cfg['noise_std']*cfg['prior_width'])**2
        self.means=np.array([0.]);self.vars=np.array([self.R*.01]);self.weights=np.array([1.])
        self.t=-1;self.change_probability=0.;self.merges=0

    def predict(self,z,t):return float(self.weights@self.means)

    def observe(self,z,residual,t):
        if t<self.t:raise ValueError('Source timestamps must be nondecreasing')
        hazard=self.cfg['hazard'];means=np.r_[self.means,0.];variances=np.r_[self.vars,self.prior_var]
        prior_weights=np.r_[self.weights*(1-hazard),hazard]
        obs_var=variances+self.R
        logw=np.log(np.maximum(prior_weights,1e-300))-.5*(np.log(2*np.pi*obs_var)+(residual-means)**2/obs_var)
        logw-=logw.max();w=np.exp(logw);w/=w.sum()
        self.change_probability=float(w[-1]);gain=variances/obs_var
        self.means=means+gain*(residual-means);self.vars=variances*(1-gain);self.weights=w
        finite_mass=self.weights>1e-250
        self.means=self.means[finite_mass];self.vars=self.vars[finite_mass];self.weights=self.weights[finite_mass]
        self.weights/=self.weights.sum()
        while len(self.weights)>32:
            order=np.argsort(self.means);self.means=self.means[order];self.vars=self.vars[order];self.weights=self.weights[order]
            wa,wb=self.weights[:-1],self.weights[1:];total=wa+wb
            m=(wa*self.means[:-1]+wb*self.means[1:])/total
            v=(wa*(self.vars[:-1]+(self.means[:-1]-m)**2)+wb*(self.vars[1:]+(self.means[1:]-m)**2))/total
            # Weighted KL loss to the moment-matched Gaussian, adjacent means only.
            cost=.5*(total*np.log(v)-wa*np.log(self.vars[:-1])-wb*np.log(self.vars[1:]))
            j=int(np.argmin(cost));self.means[j]=m[j];self.vars[j]=v[j];self.weights[j]=total[j]
            self.means=np.delete(self.means,j+1);self.vars=np.delete(self.vars,j+1);self.weights=np.delete(self.weights,j+1);self.merges+=1
        self.weights/=self.weights.sum();self.t=t


class DelayedEnsemble:
    def __init__(self,artifact,spec,cfg,kalman,regime):
        from portable_runtime import PortableModel
        self.a=artifact;self.spec=spec;self.cfg=cfg;self.kcfg=kalman
        self.grape=PortableModel(artifact)
        dimension=1+kalman.get('dim',0)+(len(spec['contexts']) if kalman.get('context') else 0)
        self.kalman=make_model('timestamped',kalman,dimension);self.regime=make_model('bayesian_regime',regime,1)
        self.weights=np.array([.6,.2,.2]);self.context_map={k:i for i,k in enumerate(spec['contexts'])}

    def z(self,x,key):
        values=[1.];dim=self.kcfg.get('dim',0)
        if dim:values+=list(np.clip(x[np.array(self.spec['indices'][:dim])],-5,5)/np.sqrt(dim))
        if self.kcfg.get('context'):
            c=np.zeros(len(self.context_map))
            if key in self.context_map:c[self.context_map[key]]=.5
            values+=list(c)
        return np.asarray(values)

    def predict(self,x,key,t):
        base=self.grape.base(x)
        experts=np.array([self.grape.predict_scaled(x,key),base+self.kalman.predict(self.z(x,key),t),base+self.regime.predict(np.ones(1),t)])
        return float(self.weights@experts),experts

    def observe(self,x,key,t,y,old_predictions):
        loss=np.minimum(((y-old_predictions)/self.a['residual_std'])**2,25.)
        logw=np.log(np.maximum(self.weights,1e-300))-loss/self.cfg['temperature']
        logw-=logw.max();w=np.exp(logw);w/=w.sum()
        self.weights=(1-self.cfg['share'])*w+self.cfg['share']/3
        residual=y-self.grape.base(x)
        self.grape.update_scaled(x,y,key);self.kalman.observe(self.z(x,key),residual,t);self.regime.observe(np.ones(1),residual,t)

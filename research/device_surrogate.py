"""Pure NumPy posterior prediction for the learned simulator surrogate."""
import numpy as np
class DeviceSurrogate:
 def __init__(self,a):
  self.X=np.asarray(a['training_X']);self.alpha=np.asarray(a['alpha']);self.length=np.asarray(a['length_scale']);self.mean=np.asarray(a['y_mean']);self.std=np.asarray(a['y_std'])
 def predict(self,X):
  X=np.atleast_2d(np.asarray(X,float))
  if X.shape[1]!=3 or not np.isfinite(X).all() or np.any((X<0)|(X>1)):raise ValueError('Requires finite3Dpoints inside normalized design bounds')
  r=np.sqrt(np.sum(((X[:,None,:]-self.X[None,:,:])/self.length)**2,axis=2));z=np.sqrt(5)*r;K=(1+z+z*z/3)*np.exp(-z)
  return (K@self.alpha)*self.std+self.mean

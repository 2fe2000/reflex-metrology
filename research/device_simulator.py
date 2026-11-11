"""1D silicon diode research surrogate source; not a fabrication-qualified device.
Adapted from DEVSIM diode examples, Copyright 2013 DEVSIM LLC, Apache-2.0.
Changes: parametric doping/length, current/conservation return, no output files.
Uses Poisson + drift-diffusion + SRH with the upstream simple silicon physics.
"""
import numpy as np
import devsim as ds
from devsim.python_packages.model_create import CreateNodeModel,CreateSolution
from devsim.python_packages.simple_physics import (SetSiliconParameters,CreateSiliconPotentialOnly,CreateSiliconPotentialOnlyContact,CreateSiliconDriftDiffusion,CreateSiliconDriftDiffusionAtContact,GetContactBiasName)

def simulate(log_na,log_nd,length_um,fine=False):
    ds.reset_devsim();device='diode';region='silicon';mesh='mesh';L=length_um*1e-4;factor=2 if fine else 1
    ds.create_1d_mesh(mesh=mesh)
    ds.add_1d_mesh_line(mesh=mesh,pos=0,ps=L/(100*factor),tag='top')
    ds.add_1d_mesh_line(mesh=mesh,pos=L/2,ps=L/(1000*factor),tag='mid')
    ds.add_1d_mesh_line(mesh=mesh,pos=L,ps=L/(100*factor),tag='bot')
    for name in ['top','bot']:ds.add_1d_contact(mesh=mesh,name=name,tag=name,material='metal')
    ds.add_1d_region(mesh=mesh,material='Si',region=region,tag1='top',tag2='bot');ds.finalize_mesh(mesh=mesh);ds.create_device(mesh=mesh,device=device)
    SetSiliconParameters(device,region,300)
    for name in ['taun','taup']:ds.set_parameter(device=device,region=region,name=name,value=1e-8)
    CreateNodeModel(device,region,'Acceptors',f'{10**log_na:.17g}*step({L/2:.17g}-x)')
    CreateNodeModel(device,region,'Donors',f'{10**log_nd:.17g}*step(x-{L/2:.17g})')
    CreateNodeModel(device,region,'NetDoping','Donors-Acceptors')
    CreateSolution(device,region,'Potential');CreateSiliconPotentialOnly(device,region)
    for contact in ['top','bot']:
        ds.set_parameter(device=device,name=GetContactBiasName(contact),value=0.);CreateSiliconPotentialOnlyContact(device,region,contact)
    ds.solve(type='dc',absolute_error=1.,relative_error=1e-10,maximum_iterations=80)
    for name,initial in [('Electrons','IntrinsicElectrons'),('Holes','IntrinsicHoles')]:
        CreateSolution(device,region,name);ds.set_node_values(device=device,region=region,name=name,init_from=initial)
    CreateSiliconDriftDiffusion(device,region)
    for contact in ['top','bot']:CreateSiliconDriftDiffusionAtContact(device,region,contact)
    ds.solve(type='dc',absolute_error=1e10,relative_error=1e-10,maximum_iterations=80)
    currents=[];balances=[];curve=[]
    for v in np.arange(0,.501,.05):
        ds.set_parameter(device=device,name=GetContactBiasName('top'),value=float(v));ds.solve(type='dc',absolute_error=1e8,relative_error=1e-9,maximum_iterations=80)
        j=[sum(ds.get_contact_current(device=device,contact=c,equation=e) for e in ['ElectronContinuityEquation','HoleContinuityEquation']) for c in ['top','bot']]
        curve.append([float(v),float(abs(j[0]))])
        if any(abs(v-t)<1e-7 for t in [.2,.4,.5]):currents.append(float(abs(j[0])));balances.append(float(abs(sum(j))/max(abs(j[0]),abs(j[1]),1e-30)))
    return {'currents':currents,'log_currents':np.log10(np.maximum(currents,1e-30)).tolist(),'max_current_imbalance':max(balances),'curve':curve,'nodes':len(ds.get_node_model_values(device=device,region=region,name='x'))}
if __name__=='__main__':
 import json,time
 t=time.time();r=simulate(17.3,17.6,.55);r['seconds']=time.time()-t;print('RESULT',json.dumps(r))

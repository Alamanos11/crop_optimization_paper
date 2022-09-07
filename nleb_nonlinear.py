"""
-----------------------  BMP optimization  ---------------------------
April   2021
Price as variable
----------------------------------------------------------------------

"""


import pandas as pd
import numpy as np
import time
import os
from scipy.optimize import minimize,Bounds


os.chdir('/Users/ja4garci/Documents/CropsOntario/pythonResults')


#%% Parameters

parameters = pd.read_excel('../ResultsModel/DataCropsLingo.xlsx',
                           sheet_name='DataParametersCrops',
                           usecols=['Pexp','Nexp','Water','Yield','Cost','Price','Names'])

crops = parameters.Names.tolist()

baseline = pd.read_excel('../AllCropsOntario2016.xlsx',
                         sheet_name='FinalData',
                         usecols=['Geography'] + crops)

subdivisions = baseline.Geography.tolist()


# Baseline [thousand-Ha/yr]
x0 = round(baseline.loc[:,crops],2)
x0 = baseline.loc[:,crops].to_numpy('float64').reshape((len(subdivisions),len(crops))) * 1e-3


yieldCrop = parameters.Yield.to_numpy('float64')     # [Ton/thousand-Ha]
costCrop = parameters.Cost.to_numpy('float64')*1e-3  # [$M/thousand-Ha]
exportP = parameters.Pexp.to_numpy('float64')        # [Ton/thousand-Ha]
exportN = parameters.Nexp.to_numpy('float64')        # [Ton/thousand-Ha]
waterCoef = parameters.Water.to_numpy('float64')     # [thousand-m^3/thousand-Ha]

# Production baseline [Ton/yr]
y0 = x0.sum(0) * yieldCrop

# Units
allowedP = np.matmul(x0.sum(0),exportP)
allowedN = np.matmul(x0.sum(0),exportN)
allowedW = np.matmul(x0.sum(0),waterCoef)

# Price baseline [$M/Ton]
p0 = parameters.Price.to_numpy('float64')*1e-3       # [$M/Ton]

# Available area
area = x0.sum(1)

# Min & Max production
minProd = 0.5
maxProd = 1.5

# Elasticity
elast = -0.2


del parameters,baseline


#%% Auxiliary functions

def extractVars(v):
    global subdivisions,crops
    n = len(subdivisions)*len(crops)
    x = v[0:n].reshape((len(subdivisions),len(crops)))
    y = v[n:n+len(crops)]
    p = v[n+len(crops):]
    return {'x':x,'y':y,'p':p}

def stackVar(x,y,p):
    return np.concatenate((x.flatten(),y,p))

def printTime(x):
    hours = int(x / 3600)
    minutes = int( (x-3600*hours) / 60)
    seconds = x % 60
    print('-------------------------------------------------------------')
    print(f'Processing time: {hours} hour(s), {minutes} minute(s), and {seconds} seconds')
    print('-------------------------------------------------------------')


#%% Model

def objectiveFunction(v):
    global yieldCrop,costCrop
    v = extractVars(v)
    z = v['p'] * yieldCrop - costCrop
    return - np.matmul(v['x'].sum(0),z)

def gradient(v):
    global yieldCrop,costCrop,subdivisions
    v = extractVars(v)
    z1 = v['p'] * yieldCrop - costCrop
    z2 = v['p'] - costCrop / yieldCrop
    z3 = yieldCrop * v['x'].sum(0)
    return - np.concatenate((np.tile(z1,len(subdivisions)),z2,z3)) #np.repeat
    
# Less or equal
def constPexport(v):
    global exportP,allowedP,dP
    v = extractVars(v)
    return (1-dP) * allowedP - np.matmul(v['x'].sum(0),exportP)

def constNexport(v):
    global exportN,allowedN,dN
    v = extractVars(v)
    return (1-dN) * allowedN - np.matmul(v['x'].sum(0),exportN)

def constWaterUse(v):
    global waterCoef,allowedW
    v = extractVars(v)
    return allowedW - np.matmul(v['x'].sum(0),waterCoef).sum()

def availableArea(v):
    global area
    v = extractVars(v)
    return area - v['x'].sum(1)

def minProduction(v):
    global y0,minProd
    v = extractVars(v)
    return v['y'] - minProd * y0

def maxProduction(v):
    global y0,maxProd
    v = extractVars(v)
    return -v['y'] + maxProd * y0

# Equal
def production(v):
    global yieldCrop
    v = extractVars(v)
    return v['y'] - v['x'].sum(0) * yieldCrop

def priceChange(v):
    global elast,p0,y0
    v = extractVars(v)
    return v['p'] - p0 * (1 + (v['y']/y0 - 1)/elast)

# Initial condition
v0 = stackVar(x0,y0,p0)
bounds = Bounds(np.zeros(v0.size),np.inf)


#%% Solution

def runExp(dp,dn):
    global dP,dN
    
    startTime = time.time()
    
    dP = dp
    dN = dn
        
    cons = [{'type':'ineq','fun':constPexport},
            {'type':'ineq','fun':constNexport},
            {'type':'ineq','fun':constWaterUse},
            {'type':'ineq','fun':availableArea},
            {'type':'ineq','fun':minProduction},
            {'type':'ineq','fun':maxProduction},
            {'type':'eq','fun':production},
            {'type':'eq','fun':priceChange}]
    
    sol = minimize(objectiveFunction,
                   v0,
                   #jac=gradient,
                   method='SLSQP',   # 'SLSQP'
                   constraints=cons,
                   bounds=bounds,
                   options={'disp':True})
    
    printTime(round(time.time() - startTime))
    
    if sol.status == 0:
        vopt = extractVars(sol.x)
        print('Objective function:',-sol.fun)
        
        vopt = extractVars(sol.x)
        return vopt['y'],vopt['p']
    return None,None

#%%

dp = 0.1
dn = 0.0

prodOpt, priceOpt = runExp(dp,dn)

if dp < 0.1:
    if dn < 0.1:
        name = 'P0' + str(int(100*dp)) + 'N0' + str(int(100*dn))
    else:
        name = 'P0' + str(int(100*dp)) + 'N' + str(int(100*dn))
else:
    if dn < 0.1:
        name = 'P' + str(int(100*dp)) + 'N0' + str(int(100*dn))
    else:
        name = 'P' + str(int(100*dp)) + 'N' + str(int(100*dn))

# Data frame of production
pd.DataFrame(prodOpt,columns=['Ton_' + name],index=crops).to_csv('Prod_PV_'+name+'.csv')
pd.DataFrame(priceOpt,columns=['MCAD_Ton_' + name],index=crops).to_csv('Price_PV_'+name+'.csv')




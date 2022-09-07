"""
-----------------------  BMP optimization  ---------------------------
April   2021
Price is fixed
----------------------------------------------------------------------

"""

import pandas as pd
import numpy as np
import os
from ortools.linear_solver import pywraplp


os.chdir('/Users/ja4garci/Documents/CropsOntario/pythonResults')


#% Parameters
parameters = pd.read_excel('../ResultsModel/DataCropsLingo.xlsx',
                           sheet_name='DataParametersCrops',
                           usecols=['Pexp','Nexp','Water','Yield','Cost','Price','Names'])
parameters.index = parameters.Names.tolist()
crops = parameters.Names.tolist()

baseline = pd.read_excel('../AllCropsOntario2016.xlsx',
                         sheet_name='FinalData',
                         usecols=['Geography'] + crops)

subdivisions = baseline.Geography.tolist()


# Baseline [thousand-Ha/yr]
x0 = baseline.loc[:,crops].to_numpy().reshape((len(subdivisions),len(crops))) * 1e-3

del baseline

#%% Optimization function
def solveCrop(capP=0.4,capN=0.3,createHaTable=False,waterAvailable=False):
    
    global parameters,crops,subdivisions,x0
    
    # Parameters ----------------------------------------------------------------------------------
    yieldHa = parameters.Yield       # [Ton/thousand-Ha]
    costHa = parameters.Cost*1e-3    # [$M/thousand-Ha]
    costWater = 0                    # [$M/(thousand-m^3 yr)]
    exportPHa = parameters.Pexp      # [Ton/thousand-Ha]
    exportNHa = parameters.Nexp      # [Ton/thousand-Ha]
    waterUseHa = parameters.Water    # [thousand-m^3/thousand-Ha]
    
    # Production baseline [Ton/yr]
    prod = x0.sum(0) * yieldHa
    
    # Allowed emissions or use
    allowed = {'P':np.matmul(x0.sum(0),exportPHa),    # [Ton/yr]
               'N':np.matmul(x0.sum(0),exportNHa),    # [Ton/yr]
               'W':np.matmul(x0.sum(0),waterUseHa)}   # [thousand-m^3/yr]
    
    # Price baseline [$M/Ton]
    price = parameters.Price/1000       # [$M/Ton]
    
    # Available area
    area = x0.sum(1)
    
    # Min & Max production
    minProd = 0.5
    maxProd = 1.5
    
    
    # Optimization model --------------------------------------------------------------------------
    solver = pywraplp.Solver.CreateSolver('GLOP')
    
    # Decision variables
    x = {}      # [Thousand-Ha/yr]
    for s in subdivisions:
        for c in crops:
            x[s,c] = solver.NumVar(0.0,solver.infinity(),f'x[{s},{c}]')
    
    y = {}      # [Ton/yr]
    for c in crops:
        y[c] = solver.NumVar(0.0,solver.infinity(),f'y[{c}]')
    
    if waterAvailable == True:
        w = solver.NumVar(0.0,solver.infinity(),'w')
    else:
        w = solver.NumVar(0.0,0,'w')
    # Objective function
    solver.Maximize(solver.Sum([(price[c]*yieldHa[c] - costHa[c]) * x[s,c] for s in subdivisions
                                                                           for c in crops])
                    + costWater * w)
    
    # Constraints of runoff export and water use
    solver.Add(solver.Sum([exportPHa[c] * x[s,c] for s in subdivisions
                                                 for c in crops]) <= allowed['P'] * (1-capP))
    solver.Add(solver.Sum([exportNHa[c] * x[s,c] for s in subdivisions
                                                 for c in crops]) <= allowed['N'] * (1-capN))
    solver.Add(solver.Sum([waterUseHa[c] * x[s,c] for s in subdivisions
                                                  for c in crops]) <= allowed['W'] + w)
    
    # Area
    for s,i in zip(subdivisions,range(len(subdivisions))):
        solver.Add(solver.Sum([x[s,c] for c in crops]) <= area[i])
    
    # Production
    for c in crops:
        solver.Add(solver.Sum([yieldHa[c] * x[s,c] for s in subdivisions]) <= y[c])
        solver.Add(solver.Sum([yieldHa[c] * x[s,c] for s in subdivisions]) >= y[c])
    
    # Min and max production
    for c in crops:
        solver.Add(solver.Sum([minProd * prod[c]]) <= y[c])
        solver.Add(solver.Sum([maxProd * prod[c]]) >= y[c])
    
    
    
    # Solution ------------------------------------------------------------------------------------
    status = solver.Solve()
    
    if status == solver.OPTIMAL or status == solver.FEASIBLE:
        print('-------------------------------------------')
        print(f'Solution found for reduction {str(int(capP*100))}P%, {str(int(capN*100))}N%')
        print('Additional water:', round(w.solution_value(),3), 'thousand cubic meters')
        print('Total utility:', round(solver.Objective().Value(),3),'Million CAD')
        print('-------------------------------------------\n')
        
        
        # Data frame of solution
        if createHaTable == True:
            optSol = pd.DataFrame(columns=crops,index=subdivisions)
            for s in subdivisions:
                for c in crops:
                    optSol.loc[s,c] = x[s,c].solution_value()
        
        # Data frame of production
        optSolProd = pd.DataFrame(columns=['Prod_Ton'],index=crops)
        for c in crops:
            optSolProd.loc[c,'Prod_Ton'] = y[c].solution_value()
        
    else:
        print('The solver could not solve the problem.')
    
    return optSolProd
#%% Scenarios

dx = 0.02
capP = np.arange(0.0,0.5+dx,dx)
capN = np.arange(0.0,0.5+dx,dx)

# Baseline produnction [Ton/year]
base = x0.sum(0) * parameters.Yield

results = pd.DataFrame(base)
results.rename(columns = {'Yield':'Base'},inplace=True)


for i in capN:
    for j in capP:
        i = round(i,3)
        j = round(j,3)
        if 100*i >= 10:
            if 100*j >= 10:
                name = 'P' + str(100*j)[0:2] + 'N' + str(100*i)[0:2]
            else:
                name = 'P0' + str(100*j)[0:1] + 'N' + str(100*i)[0:2]
        else:
            if 100*j >= 10:
                name = 'P' + str(100*j)[0:2] + 'N0' + str(100*i)[0:1]
            else:
                name = 'P0' + str(100*j)[0:1] + 'N0' + str(100*i)[0:1]
        
        results[name] = solveCrop(j,i,False,False).Prod_Ton


results.to_csv('Prod.csv')

del base,capP,capN,i,j,dx,name
del crops,parameters,subdivisions,x0


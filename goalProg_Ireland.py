"""
---- Goal Programming demo Ireland ----
---------------------------------------

Crops: grass and wheat

Decision variables:
    Ha of land allocated to each crop (grass, wheat) [Ha]
    Livestock - number of animals - cattle (cow)     [Heads]

Constraints:
    1. Maximum sales (based on the quality of the products)
    s1 * grass >= sale1 [kg/year]
    s2 * wheat >= sale2 [kg/year]
    s3 * cow >= sale3   [kg/year]
    
    2. Minimum production or capital costs (for crop and livestock products)
   e.g. fixed budget required for fertilizers,seeds, machinery etc.
  This amount should not exceed the budget allocated or the initial investment
    c1*grass + c2*wheat + c3*cow <= Budget  [$/year]
    
    3. Area
    grass + wheat <= AvailableArea    [Ha]
    
    4. Emissions of P
    e1*grass + e2*wheat + e3*cow <= maxEmissionP   [kg/year]
    
    5. Emissions of GreenHouse Gases (ghg) - here e.g. for Carbon (C)
    ghg1*grass + ghg2*wheat + ghg3*cow <= maxEmissionC  [kg/year]
    
    6. Maximum Organic Fertilizer for crops
    of1 * grass + of2 * wheat = Tof   [kg/year]
    
    7. Minimum Chemical Fertilizer for crops
    cf1 * grass + cf2 * wheat <= MaxChemical  [kg/year]
    
    8. Target production
    yield*grass = grassTarget  [kg/year]
    yield*what = wheatTarget  [kg/year]
    yield*rate*cow = grassTarget  [kg/year]  * see comment below
    
    For cow: assume 1 cow -> 100 kg and 1 cow takes 5 years to grow, then
     yield*rate*cow = [100kg/head]*[1/5years]*[head] = [20 kg/year]
        

Objective:
    Min deviation from environmental and economy targets
    - achieve min deviation for expected sales, costs, organic fert.
    - don't exceed available area, P emissions, C emissions, chemical fert.

Created:    Aug 11, 2021
By:         Jorge A. Garcia

"""

from ortools.linear_solver import pywraplp


# Function to solve model
def solveIrelandModel(weights):
    
    # Parameters (insert the respective data)------------------------
    
    # Average earnings [€/Ha] for crops and [€/Head] for livestock
    sales = {'grass':0.5, 'wheat':0.7, 'cow':1.2}
    
    # Production or capital costs [€/Ha-year] for crops and [€/Head-year] for livestock
    cost = {'grass':0.05, 'wheat':0.17, 'cow':0.6}
    
    # Emissions P [kg/Ha-year] for crops and [kg/Head] for livestock
    emissionP = {'grass':2, 'wheat':5, 'cow':13}
    
    # Emissions C [kg/Ha-year] for crops and [kg/Head] for livestock  (ghg1, ghg2, ghg3)
    emissionC = {'grass':1, 'wheat':2, 'cow':15}
    
    # Organic Fertilizer [kg/Ha-year] for crops and [kg/Head] for livestock 
    of = {'grass':10, 'wheat':15, 'cow':5}
    
    # Chemical Fertilizer [kg/year] for crops and [kg/Head] for livestock 
    cf = {'grass':10, 'wheat':12, 'cow':0}
    
    # Yield [kg/Ha-year] for crops and [kg/head-year] for livestock
    yieldAgro = {'grass':10, 'wheat':12, 'cow':20}
    
    RHS = {
           'TypicalSalesGrass': 2000.0,# [€/year]
           'TypicalSalesWheat': 5000.0,# [€/year]
           'TypicalSalesCow': 15000.0, # [€/year]
           'AvailableArea': 500.0,     # [Ha]
           'Budget': 10000.0,          # [€/year]
           'maxEmissionP': 1000.0,     # [kg/year]
           'maxEmissionC': 1200.0,     # [kg/year]
           'Tof': 100.0,               # [kg/year]
           'MaxChemical': 2000.0,      # [kg/year]
           'TargetGrassProd': 2000.0,  # [kg/year]
           'TargetWheatProd': 2000.0,  # [kg/year]
           'TargetCowProd': 6000.0     # [kg/year]
           }
    
    # Solver ------------------------------------------------
    solver = pywraplp.Solver.CreateSolver('GLOP')
    
    # Decision variables
    grass = solver.NumVar(0, solver.infinity(), 'grass')
    wheat = solver.NumVar(0, solver.infinity(), 'wheat')
    cow =   solver.NumVar(0, solver.infinity(), 'cow')
    
    # Dummy variables
    d_salesGrass_minus = solver.NumVar(0, solver.infinity(), 'd_salesGrass_minus')
    d_salesWheat_minus = solver.NumVar(0, solver.infinity(), 'd_salesWheat_minus')
    d_salesCow_minus =   solver.NumVar(0, solver.infinity(), 'd_salesCow_minus')
    
    d_cost_plus = solver.NumVar(0, solver.infinity(), 'd_cost_plus')
    
    d_emissP_plus = solver.NumVar(0, solver.infinity(), 'd_emissP_plus')
    d_emissC_plus = solver.NumVar(0, solver.infinity(), 'd_emissC_plus')
    
    d_of_minus = solver.NumVar(0, solver.infinity(), 'd_of_minus')
    d_of_plus =  solver.NumVar(0, solver.infinity(), 'd_of_plus')
    
    d_cf_plus =  solver.NumVar(0, solver.infinity(), 'd_cf_plus')
    
    d_grass_plus =  solver.NumVar(0, solver.infinity(), 'd_grass_plus')
    d_grass_minus = solver.NumVar(0, solver.infinity(), 'd_grass_minus')
    
    d_wheat_plus =  solver.NumVar(0, solver.infinity(), 'd_wheat_plus')
    d_wheat_minus = solver.NumVar(0, solver.infinity(), 'd_wheat_minus')
    
    d_cow_plus =  solver.NumVar(0, solver.infinity(), 'd_cow_plus')
    d_cow_minus = solver.NumVar(0, solver.infinity(), 'd_cow_minus')
    
    
    # Constraint 1. Sales [€/year]
    solver.Add( sales['grass']*grass + d_salesGrass_minus >= RHS['TypicalSalesGrass'] )
    solver.Add( sales['wheat']*wheat + d_salesWheat_minus >= RHS['TypicalSalesWheat'] )   
    solver.Add( sales['cow'] * cow   + d_salesCow_minus   >= RHS['TypicalSalesCow'] )
     
    # Constraint 2. Costs [€/year]
    solver.Add( cost['grass']*grass + cost['wheat']*wheat + cost['cow']*cow - d_cost_plus <= RHS['Budget'] )   
    
    # Constraint 3. Area [Ha]. Livestock: 11 cows per 9 Ha -> 0.82 [Ha/head] -> changed to 0.51
    solver.Add( grass + wheat + 0.51*cow <= RHS['AvailableArea'] )
    
    # Constraint 4. Emissions of P [kg/year]
    solver.Add( emissionP['grass']*grass + emissionP['wheat']*wheat + emissionP['cow']*cow - d_emissP_plus <= RHS['maxEmissionP'] )
    
    # Constraint 5. Emissions of C  [kg/year]
    solver.Add( emissionC['grass']*grass + emissionC['wheat']*wheat + emissionC['cow']*cow - d_emissC_plus <= RHS['maxEmissionC'] )
    
    # Constraint 6. Organic Fertilizer [kg/year]
    solver.Add( of['grass']*grass + of['wheat']*wheat - of['cow']*cow + d_of_minus - d_of_plus <= RHS['Tof'] )
    solver.Add( of['grass']*grass + of['wheat']*wheat - of['cow']*cow + d_of_minus - d_of_plus >= RHS['Tof'] )
    
    # Constraint 7. Chemical Fertilizer [kg/year]
    solver.Add( cf['grass']*grass + cf['wheat']*wheat - d_cf_plus <= RHS['MaxChemical'] )
    
    # Constraint 8. Target production
    solver.Add( yieldAgro['grass']*grass + d_grass_minus - d_grass_plus >= RHS['TargetGrassProd'])
    solver.Add( yieldAgro['grass']*grass + d_grass_minus - d_grass_plus <= RHS['TargetGrassProd'])
    
    solver.Add( yieldAgro['wheat']*wheat + d_wheat_minus - d_wheat_plus >= RHS['TargetWheatProd'])
    solver.Add( yieldAgro['wheat']*wheat + d_wheat_minus - d_wheat_plus <= RHS['TargetWheatProd'])
    
    solver.Add( yieldAgro['cow']*cow + d_cow_minus - d_cow_plus >= RHS['TargetCowProd'])
    solver.Add( yieldAgro['cow']*cow + d_cow_minus - d_cow_plus <= RHS['TargetCowProd'])
    
    # Objective function
    solver.Minimize(
        weights['Deficit_GrassSales'] * d_salesGrass_minus + # 1st constraint
        weights['Deficit_WheatSales'] * d_salesWheat_minus + # 1st constraint
        weights['Deficit_CowSales'] * d_salesCow_minus +     # 1st constraint
        weights['Exceed_Cost'] * d_cost_plus + # 2nd constraint
        weights['Exceed_P'] * d_emissP_plus +  # 4th constraint
        weights['Exceed_C'] * d_emissC_plus +  # 5th constraint
        weights['Deficit_OF'] * d_of_minus +   # 6th constraint
        weights['Exceed_OF']  * d_of_plus +    # 6th constraint
        weights['Exceed_CF'] * d_cf_plus +     # 7th constraint
        weights['Deficit_ProdGrass'] * d_grass_minus + # 8th constraint
        weights['Exceed_ProdGrass'] * d_grass_plus +   # 8th constraint
        weights['Deficit_ProdWheat'] * d_wheat_minus + # 8th constraint
        weights['Exceed_ProdWheat'] * d_wheat_plus +   # 8th constraint
        weights['Deficit_ProdCow'] * d_cow_minus +     # 8th constraint
        weights['Exceed_ProdCow'] * d_cow_plus         # 8th constraint
        )           
    
    
    # Solution -----------------------------------------
    status = solver.Solve()
    
    if status == pywraplp.Solver.OPTIMAL:
        print('\n')  # Leaves a row without printing
        print('Optimal solution found:')
        print('Objective value (€/year): {0:.3f}'.format( solver.Objective().Value() ))
        print('-----------------------------')
        print('Grass (Ha) = \t {0:.3f}'.format( grass.solution_value() ))
        print('Wheat (Ha) = \t {0:.3f}'.format( wheat.solution_value() ))
        print('Cow (Heads) = \t {0:.3f}'.format( cow.solution_value() ))
        print('-----------------------------')
        print('Loss in grass sales (€/year): {0:.3f}'.format( d_salesGrass_minus.solution_value() ))
        print('Loss in wheat sales (€/year): {0:.3f}'.format( d_salesWheat_minus.solution_value() ))
        print('Loss in cow sales (€/year): {0:.3f}'.format( d_salesCow_minus.solution_value() ))
        print('Exceedance of costs (€/year): {0:.3f}'.format( d_cost_plus.solution_value() ))
        print('-----------------------------')
        print('Exceedance in emissions of P (kg/year): {0:.3f}'.format( d_emissP_plus.solution_value() ))
        print('Exceedance in emissions of C (kg/year): {0:.3f}'.format( d_emissC_plus.solution_value() ))
        print('-----------------------------')
        print('Exceedance of Organic Fertilizer (kg/year): {0:.3f}'.format( d_of_plus.solution_value() ))
        print('Deficit of Organic Fertilizer (kg/year): {0:.3f}'.format( d_of_minus.solution_value() ))
        print('Exceedance of Chemical Fertilizer (kg/year): {0:.3f}'.format( d_cf_plus.solution_value() ))
        print('-----------------------------')
        print('Exceedance in supply (grass): {0:.3f}'.format( d_grass_plus.solution_value() ))
        print('Deficit in supply (grass): {0:.3f}'.format( d_grass_minus.solution_value() ))
        print('Exceedance in supply (wheat): {0:.3f}'.format( d_wheat_plus.solution_value() ))
        print('Deficit in supply (wheat): {0:.3f}'.format( d_wheat_minus.solution_value() ))
        print('Exceedance in supply (cow): {0:.3f}'.format( d_cow_plus.solution_value() ))
        print('Deficit in supply (cow): {0:.3f}'.format( d_cow_minus.solution_value() ))
        
        opt_sol = {var.name():var.solution_value() for var in solver.variables()}
        opt_sol['Obj_fun'] = solver.Objective().Value()
        return opt_sol
    else:
        print('The problem does not have a feasible solution.')
    return None



if __name__ == '__main__':
    # Penalization of deviations from target values
    weights = {
        'Deficit_GrassSales': 1.0, # €
        'Deficit_WheatSales': 1.0, # €
        'Deficit_CowSales':   1.0, # €
        'Exceed_Cost':        1.0, # €
        'Exceed_P':   0.001, # €/kg
        'Exceed_C':   0.001, # €/kg
        'Exceed_OF':  0.01,  # €/kg
        'Deficit_OF': 0.1,   # €/kg
        'Exceed_CF':  0.001, # €/kg
        'Exceed_ProdGrass':  1.0, # €/kg
        'Deficit_ProdGrass': 1.0, # €/kg
        'Exceed_ProdWheat':  1.0, # €/kg
        'Deficit_ProdWheat': 1.0, # €/kg
        'Exceed_ProdCow':  1.0, # €/kg
        'Deficit_ProdCow': 1.0, # €/kg
        }
    
    # Call function to solve model
    opt_sol = solveIrelandModel(weights)

    

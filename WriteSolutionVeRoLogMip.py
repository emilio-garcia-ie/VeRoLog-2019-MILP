# -*- coding: utf-8 -*-
"""
Created on Fri Apr  9 00:42:29 2021

Purpose
    Create a solution file for the MILP for a given VeRoLog instance. Note that the functions in this file will be called
    from the RunMILPVeRoLog file.

@author: 31640
"""
###########################################################
### imports
import mip as mip
###########################################################
### 
def add_nodes_to_route(t,k_h,var,outgoing_node,route, route_length, home):
    """
    Purpose
        Add nodes to the route by recursively calling this function, the function tries to find the node where the
        outgoing node is travelling to, it will add it to the route and will repeat the same thing for this node, untill
        the route surpasses the total length of the route on the day (function is called in find_truck_route()
        and find_tech_route())
    Input
        t, int: index of day under consideration
        k_h, int: truck or technician under consideration
        var, list: containing the solution of all the mip variables for x or y in the problem        
        outgoing_node, str: node were the truck or technician is departing from
        route, str: (partial) route for truck k or technician h on day t
        route_length, float: length of the route
        home, int: home location of technician or depot in case of trucks
    Output
        route, str: (partial) route for truck k or technician h on day t
    """
    for i in range(len(var[t][k_h])):
        break_second_loop = 0
        for j in range(len(var[t][k_h][i])): #if edge (i,j) was travelled, then j will be the new outgoing node
            if var[t][k_h][i][j].x > 0.99 and var[t][k_h][i][j].name.split("_")[3] == outgoing_node:
                #filter out nodes that have been visited before (unless it's the home location)
                if var[t][k_h][i][j].name.split("_")[4] not in route[len(str(k_h)):] or var[t][k_h][i][j].name.split("_")[4] == str(home):
                    outgoing_node = var[t][k_h][i][j].name.split("_")[4]
                    break_second_loop = 1
                    break
        if break_second_loop == 1:
            break        
              
    route += outgoing_node + " "
    if len(route.split(" ")) < route_length+2: #route length + technician/truck id + home location/depot
        route = add_nodes_to_route(t,k_h,var,outgoing_node,route,route_length,home)
    
    return route
###########################################################
### 
def find_tech_route(t,h,y,tech_home):
    """
    Purpose
        Find the route of technician h on day t, note that the technician will be indexed starting from 1 instead of 0 and that 
        the technicians must start and end each route at home so this is not explicitely mentioned in the solution format
    Input
        t, int: index of day under consideration
        h, int: technician under consideration
        y, list: containing the solution of all the mip variables for y in the problem
        tech_home, int: technicians home location
    Output
        tech_route, str: route for technician h on day t
    """
    outgoing_node = str(tech_home) #start at the home location
    tech_route = str(h+1) + " " #the route start with the technician id (indexing starts at 1 in solution file)
    route_length = mip.xsum(y[t][h][i][j] for i in range(len(y[t][h])) for j in range(len(y[t][h][i]))).x
   # print(t,h,outgoing_node,tech_route,route_length)
    if route_length >= 2:
        tech_route = add_nodes_to_route(t,h,y,outgoing_node,tech_route,route_length,tech_home)
        #remove home location from route, if a feasible solution was found where the technician does travel home before moving to the next customer, the total cost calculated in the algorithm can be different from the cost calculated by the SolutionVerolog2019.py file, because the intermediate visit to home has been skipped such that the maximum number of visits is not exceeded in the solution
        #this is not cosidered a problem because in an optimal route the technician will not visit home before moving to the next customer, since it is highly inefficient
        tech_route = tech_route.replace(str(tech_home)+" ","") 
    else:
        print("Warning, this route makes no sense. Technician: ",h,"Day: ",t)
    
    return tech_route
###########################################################
### 
def find_truck_route(t,k,x):
    """
    Purpose
        Find the route of truck k on day t, note that the truck will be indexed starting from 1 instead of 0 and 
        that the trucks must start and end each route at the depot so this is not explicitely mentioned in the solution format
    Input
        t, int: index of day under consideration
        k, int: truck under consideration
        x, list: containing the solution of all the mip variables for x in the problem
    Output
        truck_route, str: route for truck k on day t
    """
    outgoing_node = str(0) #start at the depot
    truck_route = str(k+1) + " " #the route start with the truck index (indexing starts at 1 in solution file)
    route_length = mip.xsum(x[t][k][i][j] for i in range(len(x[t][k])) for j in range(len(x[t][k][i]))).x
    
    if route_length >= 2:  
        truck_route = add_nodes_to_route(t,k,x,outgoing_node,truck_route,route_length,0)
        truck_route = truck_route[0:len(truck_route)-len(" 0")] #remove depot at the end
    else:
        print("Warning, this route makes no sense. Truck: ",k,"Day: ",t)
    
    return truck_route
###########################################################
### 
def calc_edge_cost(var,t,k_h,i,j,edges_index,cost_edges):
    """
    Purpose,
        Calculate the cost to travel an edge given the variable (x or y) and it's index (t,k or h,i,j)
    Input,
        var, mip.Var: the variable we are looking at (x or y)
        t, int: the index of the day
        k_h, int, the index of the truck (k) or the technician (h)
        i, int: the index of the node we are leaving
        j, int: the index of the node we are entering
        edges_index, dict: indicating the index in cost_edges (values) for each edge (keys)
        cost_edges, list: indicating the cost for each edge
    Output,
        edge_cost, cost to travel over this edge
    """
    var_name = var[t][k_h][i][j].name
    var_name_split = var_name.split('_')
    outgoing_node =  int(var_name_split[3])
    incoming_node = int(var_name_split[4])
    edge_index = edges_index[(outgoing_node,incoming_node)]
    edge_cost = cost_edges[edge_index[0]][edge_index[1]]
    
    return edge_cost
###########################################################
### 
def create_solution_file(file_name,instance,objective_func,c_penalty,x,y,u,v,p,q,DAYS,technicians,trucks,technician_nodes,nodes,edges_index,cost_edges):
    """
    Purpose
        Create a solution file for the optimized model
    Input
        file_name, str: name of the solution file
        instance, name of file of VeRoLog instance
        objective_func, mip.entities.LinExpr: the objective funtion that was optimized
        c_penalty, mip.entities.LinExpr: total penalty cost          
        x, mip.Var: decision variable that indicates if on day t, truck k, drives from node i to j
        y, mip.Var: decision variable that indicates if on day t, technician h, drives from node i to j
        u, mip.Var: decision variable for calculation of the number of trucks used in the problem
        v, mip.Var: decision variable for calculation of the number of truck days in the problem
        p, mip.Var: decision variable for calculation of the number of technicians used in the problem
        q, mip.Var: decision variable for calculation of the number of technician days in the problem
        DAYS, int: number of days in the horizon        
        technicians, list: technicians in the problem
        trucks, list: trucks in the problem        
        technician_nodes, dict: nodes (keys) and coordinates (values) of the technicians
        nodes, dict: nodes (keys) and coordinates (values) of all nodes in the problem        
        edges_index, dict: indicating the index in cost_edges (values) for each edge (keys)
        cost_edges, list: indicating the cost for each edge        
    Output
    """
    file= open(file_name +".txt", 'w')
    file.write('DATASET = VeRoLog solver challenge 2019\n')
    file.write('NAME = ' + instance + '\n')
    
    TruckDistance = int((mip.xsum(x[t][k][i][j] * calc_edge_cost(x,t,k,i,j,edges_index,cost_edges) for t in range(DAYS-1) for k in trucks for i in range(len(x[t][k])) for j in range(len(x[t][k][i])))).x)
    TruckDays = int(mip.xsum(v[t][k] for t in range(DAYS-1) for k in trucks).x) 
    TrucksUsed = int(mip.xsum(u[k] for k in trucks).x)
    TechDistance = int(mip.xsum(y[t][h][i][j] * calc_edge_cost(y,t,h,i,j,edges_index,cost_edges) for t in range(DAYS-1) for h in technicians for i in range(len(y[t][h])) for j in range(len(y[t][h][i]))).x)
    TechDays = int(mip.xsum(q[t][h] for t in range(0,DAYS-1) for h in technicians).x)
    TechsUsed = int(mip.xsum(p[h] for h in technicians).x)
    IdleMachineCost = int(c_penalty.x)
    TotalCost = int(objective_func.x)
    
    file.write('TRUCK_DISTANCE = '+ str(TruckDistance) +'\n')
    file.write('NUMBER_OF_TRUCK_DAYS = '+ str(TruckDays) +'\n')
    file.write('NUMBER_OF_TRUCKS_USED = '+ str(TrucksUsed) +'\n')
    file.write('TECHNICIAN_DISTANCE = '+ str(TechDistance) +'\n')
    file.write('NUMBER_OF_TECHNICIAN_DAYS = '+ str(TechDays) +'\n')
    file.write('NUMBER_OF_TECHNICIANS_USED = '+ str(TechsUsed) +'\n')
    file.write('IDLE_MACHINE_COSTS = '+ str(IdleMachineCost) +'\n')
    file.write('TOTAL_COST = '+ str(TotalCost) +'\n')
    

    #in solution file the day numbering starts at 1
    for t in range(DAYS-1):
        file.write('\n')
        file.write('DAY = '+str(t+1)+'\n')
        file.write('NUMBER_OF_TRUCKS = '+str(int(mip.xsum(v[t][k] for k in trucks).x))+'\n')
        for k in trucks:
            if v[t][k].x > 0.99:
                file.write(find_truck_route(t,k,x)+'\n')
        if t > 0:
            file.write('NUMBER_OF_TECHNICIANS = '+str(int(mip.xsum(q[t-1][h] for h in technicians).x))+'\n')
            for h in technicians:
                if q[t-1][h].x > 0.99:
                    file.write(find_tech_route(t-1,h,y,len(nodes)-len(technician_nodes)+h)+'\n')            
        else:
            file.write('NUMBER_OF_TECHNICIANS = 0'+'\n') #never installation of first day
    file.write('\n')        
    file.write('DAY = '+str(DAYS)+'\n')
    file.write('NUMBER_OF_TRUCKS = 0'+'\n') #never delivery on last day
    file.write('NUMBER_OF_TECHNICIANS = '+ str(int(mip.xsum(q[DAYS-2][h] for h in technicians).x))+'\n')
    for h in technicians:
        if q[DAYS-2][h].x > 0.99:
            file.write(find_tech_route(DAYS-2,h,y,len(nodes)-len(technician_nodes)+h)+'\n')      
    
###########################################################
### main
def main():
    return

if __name__ == '__main__':
    main()
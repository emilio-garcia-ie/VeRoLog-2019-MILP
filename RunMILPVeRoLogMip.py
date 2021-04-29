# -*- coding: utf-8 -*-
"""
Created on Thu Apr  8 23:06:40 2021

Purpose
    Run the MILP for a given VeRoLog instance
    
@author: Bas
"""
###########################################################
### imports
import logging
import math as math
import networkx as nx
import numpy as np
import pandas as pd
import time
import mip as mip
from ReadVeRoLogInstances import * #from local repository
from WriteSolutionVeRoLogMip import * #from local repository
###########################################################
### 
def get_y_for_nodes(y,t,h,outgoing_node,incoming_node):
    """
    Purpose
        Get the y variable given the incoming and outgoing node
    Input
        y, list, containing all the mip variables for y in the problem
        t, int: the index of the day
        h, int: technician under consideration
        outgoing_node, int: node in graph which is move out from
        incoming_node, int: node in graph which is entered
    Output
        y_var
    """
    for i in range(len(y[t][h])):
        for j in range(len(y[t][h][i])):
            if int(y[t][h][i][j].name.split("_")[3]) == outgoing_node and int(y[t][h][i][j].name.split("_")[4]) == incoming_node:
                y_var = y[t][h][i][j]
                return y_var
###########################################################
### 
def ordersize_tkj(x,t,k,j,x_nodes,customer_order_size,machine_size,customer_machine_types):
    """
    Purpose: 
        Returns the expression which is used to calculate the ordersize for customer j on day t in truck k,
        based on binary variable x 
    Input:
        x, mip.Var: decision variable that indicates if on day t, truck k, drives from node i to j
        t, int: day on which the ordersize is calculated
        k, int: truck for which the ordersize is calculated
        j, int: customer_node for which the ordersize is calculated
        customer_order_size, list: order size of each customer
        machine_size, list: machine size of each machine type
        customer_machine_types, list: type of machine the customer ordered
        x_nodes, dict: with the nodes used to the x variable
    Output:
        ordersize_tkj, mip.entities.LinExpr: linear expression which is used to calculate the ordersize 
    """
    ordersize_j = customer_order_size[j-1] * machine_size[customer_machine_types[j-1]]
    ordersize_tkj = ordersize_j * (mip.xsum(x[t][k][n][j-1] for n in x_nodes if n<j) + mip.xsum(x[t][k][n][j] for n in x_nodes if n>j)) 
    return  ordersize_tkj
###########################################################
### 
def cust_tech_variables(y,h,selected_customer,t,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types):
    """
    Purpose
        Create a linear expression of all the nodes that go out of a selected customer on a day for a technician
    Input
        y, mip.Var: decision variable that indicates if on day t, technician h, drives from node i to j     
        h, int: technician under consideration
        selected_customer, int: customer node under consideration
        t, int: the index of the day
        technician_skill_set, list: the skillset of each technician
        technician_nodes, dict: nodes of technicians
        customer_nodes, dict: nodes of customers
        customer_machine_types, list: machine type of each customer order/request 
    Output
        cust_expr, mip.entities.LinExpr: linear expression that sums all nodes that leave the customer node
    """
    g_tech = tech_graph(h,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types)
    if selected_customer in g_tech.nodes:
#        print(h,selected_customer,t,g_tech.nodes)
        cust_expr = mip.xsum(y[t][h][tech_node][i] for tech_node in range(len(g_tech.nodes)) for i in range(len(
                        y[t][h][tech_node])) if int(y[t][h][tech_node][i].name.split('_')[3]) == selected_customer)
    else:
        cust_expr = mip.xsum(i for i in range(2) if 1 == 0) #return empty sum
    return cust_expr
###########################################################
### 
def add_constraints(opt_model,x,y,w,u,v,p,q,z,l,DAYS,technicians,trucks,machines,customers,customer_machine_types,machine_size,customer_order_size,start_delivery_window,end_delivery_window,technician_max_visits,technician_max_distance,technician_skill_set,TRUCK_MAX_DISTANCE,TRUCK_CAPACITY,depot_node,customer_nodes,technician_nodes,nodes,x_nodes,edges_index,cost_edges,LARGE_NUMBER,start):
    """
    Purpose
        Add constraints to the optimization model
    Input
        opt_model, mip.model: model we are optimizing    
        x, mip.Var: decision variable that indicates if on day t, truck k, drives from node i to j
        y, mip.Var: decision variable that indicates if on day t, technician h, drives from node i to j
        w, mip.Var: decision variable indicating if on day t technician h has worked for 5 days in a row
        u, mip.Var: decision variable for calculation of the number of trucks used in the problem
        v, mip.Var: decision variable for calculation of the number of truck days in the problem
        p, mip.Var: decision variable for calculation of the number of technicians used in the problem
        q, mip.Var: decision variable for calculation of the number of technician days in the problem
        z, mip.Var: decision variable for cumulative load on day t, in truck k, delivering to customer j
        l, mip.Var: decision variable for cumulative load on day t, for technician h, installing at customer j
        DAYS, int: number of days in the horizon        
        technicians, list: technicians in the problem        
        trucks, list: trucks in the problem
        machines, list: machines in the problem
        customers, list: customers in the problem
        customer_machine_types, list: machine type of each customer order/request
        machine_size, list: size of each machine
        customer_order_size, list: size of each customer order/request  
        start_delivery_window, list: start of the delivery window for each customer
        end_delivery_window, list: end of the delivery window for each customer
        technician_max_visits, list: maximum number of customers each technician can visit daily
        technician_max_distance, list: maximum distance each technician can drive daily
        technician_skill_set, list: skill set dummy that indicates if a technician can install a machine
        TRUCK_MAX_DISTANCE, int: truck maximum distance
        TRUCK_CAPACITY, int: truck capacity        
        depot_node, dict: node (key) and coordinates (value) of the depot
        customer_nodes, dict: nodes (keys) and coordinates (values) of the customers
        technician_nodes, dict: nodes (keys) and coordinates (values) of the technicians
        nodes, dict: nodes (keys) and coordinates (values) of all nodes in the problem
        x_nodes, dict: nodes (keys) and coordinates (values) related to x variable in the mathematical problem
        edges_index, dict: containing the index in cost_edges (values) for each edge (keys)
        cost_edges, list: containing the cost for each edge       
        LARGE_NUMBER, int: large number used in one of the constraints (set to 1000)
        start, float: start time of algorithm
    Output
        opt_model, mip.model: model we are optimizing
    """
    #Decision variables used for calculation 
    for t in range(DAYS-1):
        for k in trucks:
            for i in range(len(x[t][k])):
                for j in range(len(x[t][k][i])):
                    #u
                    opt_model += u[k] - x[t][k][i][j] >= 0
                    #v
                    opt_model += v[t][k] - x[t][k][i][j] >= 0
        for h in technicians:
            for i in range(len(y[t][h])):
                for j in range(len(y[t][h][i])):
                    #p
                    opt_model += p[h] - y[t][h][i][j] >= 0    
                    #q
                    opt_model += q[t][h] - y[t][h][i][j] >= 0                        
    print("Finished decision variables used for calculation constraints at",time.time()-start)                    
    for t in range(DAYS-1):
        #truck distance
        for k in trucks:
             opt_model += (mip.xsum(x[t][k][i][j] * calc_edge_cost(x,t,k,i,j,edges_index,cost_edges) 
                            for i in range(len(x[t][k])) for j in range(len(x[t][k][i])))) <= TRUCK_MAX_DISTANCE, "truck_dist"    
        for h in technicians:
             #technician distance
             opt_model += (mip.xsum(y[t][h][i][j] * calc_edge_cost(y,t,h,i,j,edges_index,cost_edges) 
                            for i in range(len(y[t][h])) for j in range(len(y[t][h][i])))) <= technician_max_distance[h], "tech_dist"    
             #technician visits
             opt_model += (mip.xsum(y[t][h][i][j] for i in range(len(y[t][h])) for j in range(len(y[t][h][i]))
                    if int(y[t][h][i][j].name.split("_")[4]) in customer_nodes)) <=technician_max_visits[h], "tech_visit"     
    print("Finished truck distance,technician distance and technician visits constraints at",time.time()-start) 
    #customer delivery (trucks)    
    for j in customer_nodes:     
        opt_model += (mip.xsum(x[t][k][i][j-1] for t in range(DAYS-1) for k in trucks for i in x_nodes if i<j) + mip.xsum(x[t][k][i][j] for t in range(DAYS-1) for k in trucks for i in x_nodes if i>j)) == 1 , "cust_delivery"
    print("Finished customer delivery trucks at",time.time()-start)
    #customer delivery (technicians)
    for j in customer_nodes:
        opt_model += mip.xsum(y[t][h][i][n] for t in range(DAYS-1) for h in technicians for i in range(len(y[t][h])) for n in range(len(y[t][h][i])) if int(y[t][h][i][n].name.split('_')[4]) == j) == 1, "tech_delivery"    
    print("Finished customer delivery technicians at",time.time()-start)
    #start delivery window
    for j in customer_nodes:
        opt_model += start_delivery_window[j-1] * (mip.xsum(x[t][k][i][j-1] for t in range(DAYS-1) for k in trucks for i in x_nodes if i<j) + mip.xsum(x[t][k][i][j] for t in range(DAYS-1) for k in trucks for i in x_nodes if i>j)) - (mip.xsum(t*x[t][k][i][j-1] for t in range(DAYS-1) for k in trucks for i in x_nodes if i<j) + mip.xsum(t*x[t][k][i][j] for t in range(DAYS-1) for k in trucks for i in x_nodes if i>j)) <= 0, "start_delivery_window"             
    print("Finished start delivery window at",time.time()-start)
    #end delivery window
    for j in customer_nodes:
        opt_model += (mip.xsum(t*x[t][k][i][j-1] for t in range(DAYS-1) for k in trucks for i in x_nodes if i<j) + mip.xsum(t*x[t][k][i][j] for t in range(DAYS-1) for k in trucks for i in x_nodes if i>j)) - end_delivery_window[j-1] <= 0, "end_delivery_window"    
    print("Finished end delivery window at",time.time()-start)
    #start installation window
    for j in customer_nodes:
        opt_model += ((mip.xsum(t*x[t][k][i][j-1] for t in range(DAYS-1) for k in trucks for i in x_nodes if i<j) + mip.xsum(t*x[t][k][i][j] for t in range(DAYS-1) for k in trucks for i in x_nodes if i>j)) - (mip.xsum((t+1)*tech_cust_variables(y,h,j,t,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types) for t in range(DAYS-1) for h in technicians)) + 1) <= 0, "start_installation_window"
    print("Finished start installation window at",time.time()-start)
    for j in customer_nodes:
        opt_model += (mip.xsum((t+1)*tech_cust_variables(y,h,j,t,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types) for t in range(DAYS-1) for h in technicians)) - (DAYS-1) <= 0, "end_installation_window"    
    print("Finished end installation window at",time.time()-start)
    for t in range(DAYS-1):
        #node enter leave x
        for k in trucks:
            for n in x_nodes:
                opt_model += ((mip.xsum(x[t][k][i][n-1] for i in x_nodes if i<n) + mip.xsum(x[t][k][i][n] for i in x_nodes if i>n)) - 
                (mip.xsum(x[t][k][n][j-1]  for j in x_nodes  if n<j) + mip.xsum(x[t][k][n][j]  for j in x_nodes  if n>j))) == 0, 'node_ent_leave_x'  
        logging.info("Finished node enter and leave x constraints for day {0} at ".format(t) + str(time.time()-start) )
        #node enter leave y
        for h in technicians:
                for n in range(len(y[t][h])):
                    node_n = int(y[t][h][n][0].name.split("_")[3])
                    n_in = (mip.xsum(y[t][h][i][j] for i in range(len(y[t][h])) for j in range(len(y[t][h][i])) if int(y[t][h][i][j].name.split('_')[4]) == node_n))
                    n_out = mip.xsum(y[t][h][n][j] for j in range(len(y[t][h][n])))
                    opt_model += n_in - n_out == 0, "node_ent_leave_tech"    
        logging.info("Finished node enter and leave y constraints for day {0} at ".format(t) + str(time.time()-start) )
    print("Finished node enter and leave constraints at",time.time()-start)
    #truck capacity
    for t in range(DAYS-1):
        for k in trucks:
            for j in customer_nodes:
                opt_model += ordersize_tkj(x,t,k,j,x_nodes,customer_order_size,machine_size
                                           ,customer_machine_types) - z[t][k][j-1] <= 0, "truck_capacity_lower"
                opt_model += z[t][k][j-1] <= TRUCK_CAPACITY, "truck_capacity_upper"  
    print("Finished truck capacity constraints at",time.time()-start)            
    #cumulative load calculation
    for t in range(DAYS-1):
        for k in trucks:                 
            for i in range(len(x[t][k])):
                for j in range(len(x[t][k][i])):
                    var_name = x[t][k][i][j].name
                    var_name_split = var_name.split("_")
                    outgoing_node = int(var_name_split[3])
                    incoming_node = int(var_name_split[4])
                    if (outgoing_node != 0) and (incoming_node != 0) and (outgoing_node != incoming_node):
                        opt_model += z[t][k][incoming_node-1] - z[t][k][outgoing_node-1] - ordersize_tkj(x,t,k,incoming_node,x_nodes
                                        ,customer_order_size,machine_size,
                                        customer_machine_types) + TRUCK_CAPACITY * (1 - x[t][k][i][j]) >= 0, "cumulative_load"                
        logging.info("Finished cumulative truckload calculation for day {0} at ".format(t) + str(time.time()-start) )
        #save the model in case the memory runs out
        try:
            opt_model.write(opt_model.name+".lp")
        except:
            logging.warning("Failed (over)writing the lp model for cumulative truckload calculation for day {0}".format(t))
    print("Finished cumulative truck load constraints at ",time.time()-start)
    #technician capacity
    for t in range(DAYS-1):    
        for h in technicians:
            G_tech_h = tech_graph(h,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types)
            count = 0
            for j in G_tech_h.nodes:
                if j != len(nodes) - len(technician_nodes) + h: #exclude the technician home
                    opt_model += tech_cust_variables(y,h,j,t,technician_skill_set,technician_nodes,
                                              customer_nodes,customer_machine_types) - l[t][h][count] <= 0, "tech_capacity_lower"
                    count+=1
            for j in range(len(l[t][h])):
                opt_model += l[t][h][j] - technician_max_visits[h] <= 0 , "tech_capacity_upper"
    print("Finished technician capacity constraints at",time.time()-start)
    #technician cumulative load calculation
    for t in range(DAYS-1):
        for h in technicians:
            for i in range(len(l[t][h])):
                for j in range(len(l[t][h])):
                    outgoing_node = int(l[t][h][i].name.split("_")[3])
                    incoming_node = int(l[t][h][j].name.split("_")[3])
                    if outgoing_node != incoming_node:
                        opt_model += l[t][h][j] - l[t][h][i] - tech_cust_variables(y,h,incoming_node,t,technician_skill_set,
                                technician_nodes,customer_nodes,customer_machine_types) + technician_max_visits[h] * (1 - get_y_for_nodes(y,
                                t,h,outgoing_node,incoming_node)) >= 0, "tech_cumulative_load"    
        
            logging.info("Finished cumulative technician load constraint for technician {0} on day {1} at ".format(h,t)+str(time.time()-start))
        logging.info("Finished cumulative technician load calculation for day {0} at ".format(t) + str(time.time()-start))
        #save the model in case the memory runs out
        try:
            opt_model.write(opt_model.name+".lp")
        except:
            logging.warning("Failed (over)writing the lp model for cumulative technician load calculation for day {0}".format(t))
    print("Finished cumulative technician load constraints at",time.time()-start)         
    #consecutive working days technicians
    if DAYS > 6:
        for t in range(0,DAYS-6):
            for h in technicians:
                opt_model += 4 + w[t][h] - mip.xsum(q[i][h] for i in range(t,t+5)) >= 0, "set_w_to_1"   
                opt_model += 5*w[t][h] - mip.xsum(q[i][h] for i in range(t,t+5)) <= 0, "set_w_to_0"
                opt_model += w[t][h] - LARGE_NUMBER*(w[t][h]-1) - (q[t+5][h]+1) >= 0, "consecutive_days_t"                
        for t in range(0,DAYS-6-1):
            for h in technicians:
                opt_model += w[t][h] - LARGE_NUMBER*(w[t][h]-1) - (q[t+6][h]+1) >= 0, "consecutive_days_t+1" 
    print("Finished consecutive working days constraints at",time.time()-start)         
    return opt_model
###########################################################
### 
def create_cost_functions(x,y,u,v,p,q,DAYS,technicians,trucks,edges_index,cost_edges,TRUCK_DISTANCE_COST,TRUCK_DAY_COST,TRUCK_COST,TECHNICIAN_DISTANCE_COST,TECHNICIAN_DAY_COST,TECHNICIAN_COST,machine_penalty,customer_order_size,technician_skill_set,technician_nodes,customer_nodes,x_nodes,customer_machine_types,start):
    """
    Purpose
        Create the cost components of the objective function
    Input
        x, mip.Var: decision variable that indicates if on day t, truck k, drives from node i to j
        y, mip.Var: decision variable that indicates if on day t, technician h, drives from node i to j
        u, mip.Var: decision variable for calculation of the number of trucks used in the problem
        v, mip.Var: decision variable for calculation of the number of truck days in the problem
        p, mip.Var: decision variable for calculation of the number of technicians used in the problem
        q, mip.Var: decision variable for calculation of the number of technician days in the problem
        DAYS, int: number of days in the horizon        
        technicians, list: technicians in the problem        
        trucks, list: trucks in the problem
        edges_index, dict: indicating the index in cost_edges (values) for each edge (keys)
        cost_edges, list: indicating the cost for each edge
        TRUCK_DISTANCE_COST, int: truck distance cost
        TRUCK_DAY_COST, int: truck day cost
        TRUCK_COST, int: truck cost
        TECHNICIAN_DISTANCE_COST, int: technician distance cost
        TECHNICIAN_DAY_COST, int: technician day cost
        TECHNICIAN_COST, int: technician cost
        machine_penalty, list: daily penalty for idle machines (delivered but not yet installed)
        customer_order_size, list: size of each customer order/request 
        technician_skill_set, list: the skillset of each technician
        technician_nodes, dict: nodes of technicians
        customer_nodes, dict: nodes of customers
        x_nodes, dict: nodes (keys) and coordinates (values) related to x variable in the mathematical problem
        customer_machine_types, list: machine type of each customer order/request     
        start, float: start time of algorithm
    Output
        c_truck_distance, mip.entities.LinExpr: total truck distance cost
        c_truck, mip.entities.LinExpr: total truck cost
        c_truck_day, mip.entities.LinExpr: total truck day cost
        c_tech_distance, mip.entities.LinExpr: total technician distance cost
        c_tech, mip.entities.LinExpr: total technician cost
        c_tech_day, mip.entities.LinExpr: total technician day cost
        c_penalty, mip.entities.LinExpr: total penalty cost   
    """
    c_truck_distance = TRUCK_DISTANCE_COST * (mip.xsum(x[t][k][i][j] * calc_edge_cost(x,t,k,i,j,edges_index,cost_edges) for t in range(DAYS-1) for k in trucks for i in range(len(x[t][k])) for j in range(len(x[t][k][i]))))
    print("Finished truck distance cost formulation at", time.time()-start)
    c_truck = TRUCK_COST * mip.xsum(u[k] for k in trucks)
    print("Finished truck cost formulation at", time.time()-start)
    c_truck_day = TRUCK_DAY_COST * mip.xsum(v[t][k] for t in range(DAYS-1) for k in trucks) 
    print("Finished truck day cost formulation at", time.time()-start)
    c_tech_distance = TECHNICIAN_DISTANCE_COST * mip.xsum(y[t][h][i][j] * calc_edge_cost(y,t,h,i,j,edges_index,cost_edges) for t in range(DAYS-1) for h in technicians for i in range(len(y[t][h])) for j in range(len(y[t][h][i])))
    print("Finished technician distanc cost formulation at", time.time()-start)
    c_tech = TECHNICIAN_COST * mip.xsum(p[h] for h in technicians) 
    print("Finished technician cost formulation at", time.time()-start)
    c_tech_day = TECHNICIAN_DAY_COST * mip.xsum(q[t][h] for t in range(0,DAYS-1) for h in technicians)
    print("Finished technician day cost formulation at", time.time()-start)
    c_penalty = mip.xsum(machine_penalty[customer_machine_types[j-1]] * customer_order_size[j-1] * ((mip.xsum((t+1)*tech_cust_variables(y,h,j,t,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types) for t in range(DAYS-1) for h in technicians))-(mip.xsum(t*x[t][k][i][j] for t in range(DAYS-1) for k in trucks for i in x_nodes if i > j) + mip.xsum(t*x[t][k][i][j-1] for t in range(DAYS-1) for k in trucks for i in x_nodes if i < j)) - 1) for j in customer_nodes)
    print("Finished penalty cost formulation at", time.time()-start)
    return c_truck_distance,c_truck,c_truck_day,c_tech_distance,c_tech,c_tech_day,c_penalty
###########################################################
### 
def tech_cust_variables(y,h,selected_customer,t,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types):
    """
    Purpose
        Create a linear expression of all the nodes that go into a selected customer on a day for a technician
    Input
        y, mip.Var: decision variable that indicates if on day t, technician h, drives from node i to j    
        h, int: technician under consideration
        selected_customer, int: customer node under consideration
        t, int: the index of the day
        technician_skill_set, list: the skillset of each technician
        technician_nodes, dict: nodes of technicians
        customer_nodes, dict: nodes of customers
        customer_machine_types, list: machine type of each customer order/request
    Output
        tech_cust_expr, mip.entities.LinExpr: linear expression that sums all nodes that go into a customer node
    """
    g_tech = tech_graph(h,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types)
    if selected_customer in g_tech.nodes:
        #print(h,selected_customer,t,g_tech.nodes)
        tech_cust_expr = mip.xsum(y[t][h][tech_node][i] for tech_node in range(len(g_tech.nodes)) for i in range(len(
                            y[t][h][tech_node])) if int(y[t][h][tech_node][i].name.split('_')[4]) == selected_customer)
    else:
        tech_cust_expr = mip.xsum(i for i in range(2) if 1 == 0) #return empty sum
    return tech_cust_expr
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
def create_decisions_variables(opt_model,DAYS,technicians,trucks,x_nodes,technician_skill_set,nodes,technician_nodes,customer_nodes,customer_machine_types,start):
    """
    Purpose
        Create the decision variables of the problem
    Input
        opt_model, mip.model: model we are optimizing
        DAYS, int: number of days in the horizon
        technicians, list: technicians in the problem
        trucks, list: trucks in the problem
        x_nodes, dict: nodes (keys) and coordinates (values) related to x variable in the mathematical problem
        technician_skill_set, list: skill set dummy that indicates if a technician can install a machine
        nodes, dict: nodes (keys) and coordinates (values) of all nodes in the problem
        technician_nodes, dict: nodes (keys) and coordinates (values) of the technicians
        customer_nodes, dict: nodes (keys) and coordinates (values) of the customers
        customer_machine_types, list: machine type of each customer order/request
        start, float: start time of algorithm
    Output
        x, mip.Var: decision variable that indicates if on day t, truck k, drives from node i to j
        y, mip.Var: decision variable that indicates if on day t, technician h, drives from node i to j
        w, mip.Var: decision variable indicating if on day t technician h has worked for 5 days in a row
        u, mip.Var: decision variable for calculation of the number of trucks used in the problem
        v, mip.Var: decision variable for calculation of the number of truck days in the problem
        p, mip.Var: decision variable for calculation of the number of technicians used in the problem
        q, mip.Var: decision variable for calculation of the number of technician days in the problem
        z, mip.Var: decision variable for cumulative load on day t, in truck k, delivering to customer j
        l, mip.Var: decision variable for cumulative load on day t, for technician h, installing at  customer j 
    """
    # Binary
    #no connection between technician homes
    #delivery needs to be fullfilled one day before end of the horizon
    x = [[[[opt_model.add_var(name="x_{0}_{1}_{2}_{3}".format(t,k,i,j),var_type=mip.BINARY) for j in x_nodes if j != i] for i in x_nodes] for k in trucks] for t in range(DAYS-1)]
    print("Finished variable x at", time.time()-start)
    #installation can only start one day later than delivery, also no connection between technician homes and depot
    # the technicians are disconnected from the customer nodes if their skillset does not allow them to install there
    y = [[[]for h in technicians] for t in range(1,DAYS)]
    for t in range(DAYS-1):
        for h in technicians:
            count_h = 0
            G_tech_h = tech_graph(h,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types)
            #note that this will not work if the input file includes a technician that cannot install any of the requests
            for i in G_tech_h.nodes:
                y[t][h].append([])
                for j in G_tech_h.nodes:
                    if i != j:
                        y[t][h][count_h].append(opt_model.add_var(name="y_{0}_{1}_{2}_{3}".format(t+1,h,i,j),var_type=mip.BINARY))
                count_h +=1
    print("Finished variable y at", time.time()-start)            
    #technician can only have worked for the past 5 consecutive days on the 7th day in the horizon
    if DAYS > 6:
        w = [[opt_model.add_var(name="w_{0}_{1}".format(t,h),var_type=mip.BINARY) for h in technicians] for t in range(6,DAYS)]
    else:
        w = []
    print("Finished variable w at", time.time()-start)
    # # Continuous
    u = [opt_model.add_var(name="u_{0}".format(k),lb=0.0) for k in trucks]
    print("Finished variable u at", time.time()-start)    
    v = [[opt_model.add_var(name="v_{0}_{1}".format(t,k),lb=0.0) for k in trucks] for t in range(DAYS-1)]
    print("Finished variable v at", time.time()-start)    
    p = [opt_model.add_var(name="p_{0}".format(h),lb=0.0) for h in technicians]
    print("Finished variable p at", time.time()-start)    
    q = [[opt_model.add_var(name="q_{0}_{1}".format(t,h),lb=0.0) for h in technicians] for t in range(1,DAYS)]
    print("Finished variable q at", time.time()-start)    
    #delivery needs to be fullfilled one day before end of the horizon
    z = [[[opt_model.add_var(name="z_{0}_{1}_{2}".format(t,k,j),lb=0.0) for j in customer_nodes] for k in trucks] for t in range(DAYS-1)]
    print("Finished variable z at", time.time()-start)
    #installation can only start one day later than delivery
    #the load only needs to be calculated for customer nodes that the technician can install
    l = [[[]for h in technicians] for t in range(1,DAYS)]
    for t in range(DAYS-1):
        for h in technicians:
            G_tech_h = tech_graph(h,technician_skill_set,technician_nodes,customer_nodes,customer_machine_types)
            for j in G_tech_h.nodes:
                if j != len(nodes) - len(technician_nodes) + h: #exclude the technician home
                    l[t][h].append(opt_model.add_var(name="l_{0}_{1}_{2}".format(t+1,h,j),lb=0.0)) 
    print("Finished variable l at", time.time()-start)
    return x,y,w,u,v,p,q,z,l
###########################################################
### main
def main():
    #input from user
    #input_file_name = "VSC2019_ORTEC_Example.csv" #must be csv
    input_file_name = "VSC2019_ORTEC_Small_04.csv" #must be csv
    #output_file_name = 'TestSolutionExample'
    output_file_name = 'SolutionInstance_Small_04'
    number_of_trucks = 2
    max_run_time = 36*60*60 #in seconds
    #start of algorithm
    start = time.time()
    logging.basicConfig(filename=input_file_name.strip('.csv')+'_logs', level=logging.INFO,format='%(asctime)s:%(levelname)s:%(message)s')
    opt_model = mip.Model(name=input_file_name.strip('.csv'),solver_name=mip.CBC)   
    DAYS,technicians,trucks,machines,customers,customer_machine_types,machine_size,machine_penalty,customer_order_size,start_delivery_window,end_delivery_window,technician_max_visits,technician_max_distance,technician_skill_set,TRUCK_MAX_DISTANCE,TRUCK_CAPACITY,LARGE_NUMBER,TRUCK_DISTANCE_COST,TRUCK_DAY_COST,TRUCK_COST,TECHNICIAN_DISTANCE_COST,TECHNICIAN_DAY_COST,TECHNICIAN_COST,depot_node,customer_nodes,technician_nodes,nodes,x_nodes,edges_index,cost_edges = read_file(input_file_name,number_of_trucks)
    print("Finished reading data at",time.time()-start)  
    
    #decision variables
    x,y,w,u,v,p,q,z,l = create_decisions_variables(opt_model,DAYS,technicians,trucks,x_nodes,technician_skill_set,nodes,technician_nodes,customer_nodes,customer_machine_types,start)
    print("Finished creating decision variables at",time.time()-start) 
    #create objective function
    c_truck_distance,c_truck,c_truck_day,c_tech_distance,c_tech,c_tech_day,c_penalty = create_cost_functions(x,y,u,v,p,q,DAYS,technicians,trucks,edges_index,cost_edges,TRUCK_DISTANCE_COST,TRUCK_DAY_COST,TRUCK_COST,TECHNICIAN_DISTANCE_COST,TECHNICIAN_DAY_COST,TECHNICIAN_COST,machine_penalty,customer_order_size,technician_skill_set,technician_nodes,customer_nodes,x_nodes,customer_machine_types,start)
    objective_func = c_truck_distance + c_truck + c_truck_day + c_tech_distance + c_tech + c_tech_day + c_penalty
    opt_model.objective = mip.minimize(objective_func)
    print("Finished creating objective function at",time.time()-start)
    try:
        opt_model.write(opt_model.name+".lp")
    except:
        logging.warning("Failed (over)writing the lp model after objective function")
    opt_model = add_constraints(opt_model,x,y,w,u,v,p,q,z,l,DAYS,technicians,trucks,machines,customers,customer_machine_types,machine_size,customer_order_size,start_delivery_window,end_delivery_window,technician_max_visits,technician_max_distance,technician_skill_set,TRUCK_MAX_DISTANCE,TRUCK_CAPACITY,depot_node,customer_nodes,technician_nodes,nodes,x_nodes,edges_index,cost_edges,LARGE_NUMBER,start)
    print("Finished building model, starting optimization at",time.time()-start)
    try:
        opt_model.write(opt_model.name+".lp")
    except:
        logging.warning("Failed (over)writing the lp model before start optimization")
    
    status = opt_model.optimize(max_seconds=max_run_time)
    print("Finished optimization at",time.time()-start)
    
    if opt_model.num_solutions:
        print('Route with total cost %g found' % (opt_model.objective_value))
        instance_name = input_file_name.strip('csv') + 'txt'
        print(instance_name)
        create_solution_file(output_file_name,instance_name,objective_func,c_penalty,x,y,u,v,p,q,DAYS,technicians,trucks,technician_nodes,nodes,edges_index,cost_edges)
        print("Created a solution file at",time.time()-start)
    else: 
        print('No feasible solution was found')
        
        #run the following line in command prompt when in the correct folder path to check if the solution is correct
        #python SolutionVerolog2019.py -i VSC2019_ORTEC_Example.txt -s TestSolutionExample.txt
    if status == mip.OptimizationStatus.OPTIMAL:
        print('optimal solution cost {} found'.format(opt_model.objective_value))
    elif status == mip.OptimizationStatus.FEASIBLE:
        print('sol.cost {} found, best possible: {}'.format(opt_model.objective_value, opt_model.objective_bound))
    elif status == mip.OptimizationStatus.NO_SOLUTION_FOUND:
        print('no feasible solution found, lower bound is: {}'.format(opt_model.objective_bound))
    if status == mip.OptimizationStatus.OPTIMAL or status == mip.OptimizationStatus.FEASIBLE:
        print('solution:')
        for variab in opt_model.vars:
            if abs(variab.x) > 1e-6: # only printing non-zeros
                print('{} : {}'.format(variab.name, variab.x))    
    return

if __name__ == '__main__':
    main()
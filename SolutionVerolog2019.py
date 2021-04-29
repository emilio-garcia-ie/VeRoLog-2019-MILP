#! /usr/bin/env python
import os
import argparse, copy
import xml.etree.ElementTree as ET
from InstanceVerolog2019 import InstanceVerolog2019 as InstanceVerolog2019
import baseParser as base
from collections import OrderedDict
from pprint import pprint as pprint


class SolutionVerolog2019(base.BaseParser):
    parsertype = 'solution'
    
    class LANG:
        class TXT:
            dataset = 'DATASET'
            name = 'NAME'
            
            nrTrucksUsed = 'NUMBER_OF_TRUCKS_USED'
            nrTruckDays = 'NUMBER_OF_TRUCK_DAYS'
            truckDistance = 'TRUCK_DISTANCE'
            nrTechniciansUsed = 'NUMBER_OF_TECHNICIANS_USED'
            nrTechnicianDays = 'NUMBER_OF_TECHNICIAN_DAYS'
            technicianDistance = 'TECHNICIAN_DISTANCE'
            idleMachineCost ='IDLE_MACHINE_COSTS'
            totalCost = 'TOTAL_COST'
            day = 'DAY'
            
            dayNrTrucks = 'NUMBER_OF_TRUCKS'
            dayNrTechnicians = 'NUMBER_OF_TECHNICIANS'
            
            costfields  = { truckDistance:    'TruckDistance',
                            nrTruckDays:      'NrTruckDays',
                            nrTrucksUsed:     'NrTrucksUsed',
                            technicianDistance:'TechnicianDistance',
                            nrTechnicianDays: 'NrTechnicianDays',
                            nrTechniciansUsed:'NrTechniciansUsed',
                            idleMachineCost:  'IdleMachineCost',
                            totalCost:        'Cost',
                            }
            dayfields   = { dayNrTrucks:      'NrTruckRoutes',
                            dayNrTechnicians: 'NrTechnicianRoutes',
                            }
            
  
    class SolutionCost(object):
        def __init__(self):
            self.TruckDistance = None
            self.NrTruckDays = None
            self.NrTrucksUsed = None
            self.TechnicianDistance = None
            self.NrTechnicianDays = None
            self.NrTechniciansUsed = None
            self.IdleMachineCost = None
            self.Cost = None

            self.TruckDistanceCumulative = None
            self.NrTruckDaysCumulative = None
            self.NrTrucksUsedCumulative = None
            self.TechnicianDistanceCumulative = None
            self.NrTechnicianDaysCumulative = None
            self.NrTechniciansUsedCumulative = None
            self.IdleMachineCostCumulative = None
            self.CostCumulative = None            
            
           
        def __str__(self):
            if not self.TruckDistance or not self.NrTruckDays or not self.NrTrucksUsed or not self.TechnicianDistance or not self.NrTechnicianDays or not self.NrTechniciansUsed or not self.IdleMachineCost or not self.Cost:
                return 'TruckDistance: %r\nNrTruckDays: %r\nNrTrucksUsed: %r\nTechnicianDistance: %r\nNrTechnicianDays: %r\nNrTechniciansUsed: %r\nIdleMachineCost: %r\nCost: %r' % (self.TruckDistance, self.NrTruckDays, self.NrTrucksUsed, self.TechnicianDistance, self.NrTechnicianDays,  self.NrTechniciansUsed, self.IdleMachineCost, self.Cost )
            else:
                 return 'TruckDistance: %d\nNrTruckDays: %d\nNrTrucksUsed %d\nTechnicianDistance: %d\nNrTechnicianDays: %d\nNrTechniciansUsed: %d\nIdleMachineCost: %d\nCost: %d' % (self.TruckDistance, self.NrTruckDays, self.NrTrucksUsed, self.TechnicianDistance, self.NrTechnicianDays,  self.NrTechniciansUsed, self.IdleMachineCost, self.Cost )
    
    class TruckRoute(object):
        def __init__(self):
            self.ID = None
            self.Route = []
            self.calcDistance = None

        def __str__(self):
            return '%d %s' % (self.ID, ' '.join(str(x) for x in self.Route))

        
    class TechnicianRoute(object):
        def __init__(self):
            self.ID = None
            self.Route = []
            self.calcDistance = None
            
        def __str__(self):
            return '%d %s' % (self.ID, ' '.join(str(x) for x in self.Route))
          
    class SolutionDay(object):
        def __init__(self, dayNr):
            self.dayNumber = dayNr
            self.NrTruckRoutes = None
            self.TruckRoutes = []
            self.NrTechnicianRoutes = None
            self.TechnicianRoutes = []
        
        def __str__(self):
            strRepr = 'Day: %d' % self.dayNumber
            if self.NrTruckRoutes is not None:
                strRepr += '\nNr Truck Routes: %d' % self.NrTruckRoutes
                for i in range(len(self.TruckRoutes)):
                    strRepr += '\n%s' % ( str(self.TruckRoutes[i]) )              
            if self.NrTechnicianRoutes is not None:
                strRepr += '\nNr Technician Routes: %d' % self.NrTechnicianRoutes
                for i in range(len(self.TechnicianRoutes)):
                    strRepr += '\n%s' % ( str(self.TechnicianRoutes[i]) )        
            return strRepr
   
    def __str__(self):
        strRepr = 'GivenCost: %s\nCalcCost: %s\nDAYS:' % (str(self.givenCost),str(self.calcCost))
        for day in self.Days:
                strRepr += '\n%s\n' % ( str(day) )        
        return strRepr
    
    def __init__(self, inputfile,Instance,filetype=None,continueOnErr=False):
        self.Instance = Instance
        self.Instance.calculateDistances()
        self._doinit(inputfile,filetype,continueOnErr)
        if self.isValid():
            self._calculateSolution()
        
        
    def _initData(self):
        self.Days = []
        self.givenCost = self.SolutionCost()
        self.calcCost = self.SolutionCost()

    def _readTextCost(self, fd, lastLineAssignment = None):
        if not lastLineAssignment:
            lastLineAssignment = self._isAssignment(fd)
       
        field = lastLineAssignment[0]
        member = self.LANG.TXT.costfields.get(field)
        while member:
            value = lastLineAssignment[1]
            value = self._checkInt(field,value)
            self.givenCost.__setattr__(member,value)
            lastLineAssignment = self._isAssignment(fd)
            field = lastLineAssignment[0]
            member = self.LANG.TXT.costfields.get(field)
            

        if lastLineAssignment is None or lastLineAssignment[0] is None or lastLineAssignment[0] == self.LANG.TXT.day:
            return lastLineAssignment
        self._checkError('Unexpected field: %s.' % lastLineAssignment[0], False)
        return lastLineAssignment
    
    def _readDay(self, fd, lastLineAssignment):
        self._checkError('Unexpected string: %s.' % lastLineAssignment[1], lastLineAssignment[0] is not None )
        self._checkError('Unexpected field: %s.' % lastLineAssignment[0],lastLineAssignment[0] == self.LANG.TXT.day)
        newDay = self.SolutionDay(self._checkInt(self.LANG.TXT.day,lastLineAssignment[1]))
        self._checkError('Day number should be positive, found %d.' % (newDay.dayNumber), newDay.dayNumber > 0 )
        self._checkError('Day number should be at most %d, found %d.' % (self.Instance.Days,newDay.dayNumber), newDay.dayNumber <= self.Instance.Days )
        lastDay = self.Days[-1].dayNumber if len(self.Days) > 0 else 0
        self._checkError('Incorrect order of days, found day %d after day %d.' % (newDay.dayNumber, lastDay), newDay.dayNumber > lastDay )
        lastLineAssignment = self._isAssignment(fd)
        
        #read truck routes
        self._checkError('Unexpected field: %s.' % lastLineAssignment[0],lastLineAssignment[0] == self.LANG.TXT.dayNrTrucks)
        newDay.NrTruckRoutes = self._checkInt(self.LANG.TXT.dayNrTrucks,lastLineAssignment[1])
        self._checkError('Nr Trucks used should be non-negative, found %d on day %d.' % (newDay.NrTruckRoutes, newDay.dayNumber), newDay.NrTruckRoutes >= 0 )
        lastLineAssignment = self._isAssignment(fd)

        nrTruckRoutesFound = 0
        while lastLineAssignment is not None and lastLineAssignment[0] is None:
            nrTruckRoutesFound += 1
            line = lastLineAssignment[1]
            routeLine = line.split()
            truckRoute = self.TruckRoute()
            truckRoute.ID = self._checkInt('Truck ID',routeLine[0])
            try:
              truckRoute.Route = [int(x) for x in routeLine[1:]]
              for i in range(len(truckRoute.Route)):
                  if truckRoute.Route[i] < 0:
                      self._checkError('Expected positive integers on the route line (day %d). Found incorrect data: %s.' % (newDay.dayNumber,line),False)
            except:
              self._checkError('Expected integers on the route line (day %d). Found incorrect data: %s.' % (newDay.dayNumber,line),False)
            self._checkError('Route should be at least length 1, found %d (day %d).' % (len(truckRoute.Route),newDay.dayNumber),len(truckRoute.Route)>=1)
            newDay.TruckRoutes.append(truckRoute)
            lastLineAssignment = self._isAssignment(fd)
        self._checkWarning('Expected %d routes (day %d). Found %d.' % (newDay.NrTruckRoutes, newDay.dayNumber, nrTruckRoutesFound), nrTruckRoutesFound == newDay.NrTruckRoutes)

        #read technician routes
        self._checkError('Unexpected field: %s.' % lastLineAssignment[0],lastLineAssignment[0] == self.LANG.TXT.dayNrTechnicians)  
        newDay.NrTechnicianRoutes = self._checkInt(self.LANG.TXT.dayNrTechnicians,lastLineAssignment[1])
        self._checkError('Nr Technicians used should be non-negative, found %d on day %d.' % (newDay.NrTechnicianRoutes, newDay.dayNumber), newDay.NrTechnicianRoutes >= 0 )
        lastLineAssignment = self._isAssignment(fd)

        nrTechRoutesFound = 0
        while lastLineAssignment is not None and lastLineAssignment[0] is None:
            nrTechRoutesFound += 1
            line = lastLineAssignment[1]
            routeLine = line.split()
            techRoute = self.TechnicianRoute()
            techRoute.ID = self._checkInt('Technician ID',routeLine[0])
            try:
                techRoute.Route = [int(x) for x in routeLine[1:]]
                for i in range(len(techRoute.Route)):
                    if techRoute.Route[i] <= 0:
                        self._checkError('Expected strictly positive integers on the route line (day %d). Found incorrect data: %s.' % (newDay.dayNumber,line),False)
            except:
                self._checkError('Expected integers on the route line (day %d). Found incorrect data: %s.' % (newDay.dayNumber,line),False)
            self._checkError('Route should be at least length 1, found %d (day %d).' % (len(techRoute.Route),newDay.dayNumber),len(techRoute.Route)>=1)
            newDay.TechnicianRoutes.append(techRoute)
            lastLineAssignment = self._isAssignment(fd)
        self._checkWarning('Expected %d routes (day %d). Found %d.' % (newDay.NrTechnicianRoutes, newDay.dayNumber, nrTechRoutesFound), nrTechRoutesFound == newDay.NrTechnicianRoutes)

        self.Days.append(newDay)
        return lastLineAssignment

    def _initTXT(self):
        try:
            fd = open(self.inputfile, 'r')
        except:
            self.errorReport.append( 'Solution file %s could not be read.' % self.inputfile )
            return
        
        try:
            with fd:
                self.Dataset = self._checkAssignment(fd,self.LANG.TXT.dataset,'string')
                self.Name = self._checkAssignment(fd,self.LANG.TXT.name,'string')
                
                assignment = self._readTextCost(fd)
                
                while assignment:
                    assignment = self._readDay(fd,assignment)
                

        except self.BaseParseException:
            pass
        except:
            print('Crash during solution reading\nThe following errors were found:')
            print( '\t' + '\n\t'.join(self.errorReport) )
            raise

    def _calculateSolution(self):
        try:
            totalTruckDistance = 0
            dayNumTrucks = 0
            maxNumTrucks = 0
            totalTechnicianDistance = 0
            dayNumTechnicians = 0
            nrOfTechniciansUsed = 0
            idleMachineCost = 0
            totalCost = 0
            TruckDistanceCumulative = [0] * (len(self.Days))
            NrTruckDaysCumulative = [0] * (len(self.Days))
            NrTrucksUsedCumulative = [0] * (len(self.Days))
            TechnicianDistanceCumulative = [0] * (len(self.Days))
            NrTechnicianDaysCumulative = [0] * (len(self.Days))
            NrTechniciansUsedCumulative = [0] * (len(self.Days))
            IdleMachineCostCumulative = [0] * (len(self.Days))
            CostCumulative = [0] * (len(self.Days))             
                        
            techniciansUsed = [ [0 for x in range(len(self.Days))] for y in range(len(self.Instance.Technicians)) ] 
            requestDelivered = [None] * (len(self.Instance.Requests) + 1 )
            requestInstalled  = [None] * (len(self.Instance.Requests) + 1 )
            for day in self.Days:
                # Compute truck routes
                maxNumTrucks = max(maxNumTrucks,len(day.TruckRoutes))
                dayNumTrucks += len(day.TruckRoutes)
                NrTrucksUsedCumulative[day.dayNumber - 1] = maxNumTrucks 
                NrTruckDaysCumulative[day.dayNumber - 1] = dayNumTrucks 
                for i in range(len(day.TruckRoutes)):
                    truck = day.TruckRoutes[i]
                    truckDistance = 0
                    truckLoad = 0
                    lastNode = None
                    for node in truck.Route:                       
                        if node == 0:
                            truckLoad = 0
                        elif node > 0:
                            self._checkError('Unknown request %d (current day %d).' % (node,day.dayNumber), node < len(requestDelivered) )
                            self._checkError('Deliver of request %d is already planned on day %d (current day %d).' % (node, requestDelivered[node] if requestDelivered[node] is not None else 0,day.dayNumber), requestDelivered[node] == None )
                            requestDelivered[node] = day.dayNumber 
                            machineType = self.Instance.Requests[node-1].machineID
                            machineSize = self.Instance.Machines[machineType - 1].size
                            truckLoad += self.Instance.Requests[node-1].amount * machineSize
                            self._checkError('Truckload of truck %d exceeds capacity on day %d' %(truck.ID, day.dayNumber), truckLoad <= self.Instance.TruckCapacity)
                        if lastNode is None:
                            fromCoord = 0 #depot
                            toCoord = 0 if node == 0 else self.Instance.Requests[node-1].customerLocID - 1
                        elif lastNode is not None:
                            fromCoord = 0 if lastNode == 0 else self.Instance.Requests[lastNode-1].customerLocID - 1
                            toCoord = 0 if node == 0 else self.Instance.Requests[node-1].customerLocID - 1
                        truckDistance += self.Instance.calcDistance[fromCoord][toCoord]
                        lastNode = node
                    #From last customer to depot
                    fromCoord = 0 if truck.Route[-1] == 0 else self.Instance.Requests[truck.Route[-1] - 1].customerLocID - 1
                    toCoord = 0
                    truckDistance += self.Instance.calcDistance[fromCoord][toCoord]
                    self._checkError('Distance traveled by truck %d  exceeds maximum allowed distance on day %d (%d > %d)' %(day.TruckRoutes[i].ID, day.dayNumber, truckDistance, self.Instance.TruckMaxDistance), truckDistance <= self.Instance.TruckMaxDistance)
                    totalTruckDistance += truckDistance
                TruckDistanceCumulative[day.dayNumber - 1] = totalTruckDistance
                
                # Compute techinician routes
                dayNumTechnicians += len(day.TechnicianRoutes)
                NrTechnicianDaysCumulative[day.dayNumber - 1] = dayNumTechnicians
                for i in range(len(day.TechnicianRoutes)):
                    technicianDistance = 0
                    technician = self.Instance.Technicians[day.TechnicianRoutes[i].ID - 1]
                    technicianRoute = day.TechnicianRoutes[i]
                    technicianCapabilities = technician.capabilities
                    techniciansUsed[technician.ID-1][day.dayNumber-1] = 1
                    nrOfStops = len(technicianRoute.Route)
                    self._checkError('Number of installations (%d) exceeds maximum allowed number of installations (%d) for technician %d on day %d' %(nrOfStops, technician.maxNrInstallations, day.TechnicianRoutes[i].ID, day.dayNumber), nrOfStops <= self.Instance.Technicians[day.TechnicianRoutes[i].ID - 1].maxNrInstallations)
                    lastNode = None                   
                    for node in technicianRoute.Route:
                        if node > 0:
                            self._checkError('Unknown request %d (current day %d).' % (node,day.dayNumber), node < len(requestInstalled) )
                            self._checkError('Installation of request %d is already planned on day %d (current day %d).' % (node, requestInstalled[node] if requestInstalled[node] is not None else 0,day.dayNumber), requestInstalled[node] == None )
                            self._checkError('Installation of request %d on day %d cannot take place before delivery' %(node, day.dayNumber), requestDelivered[node] < day.dayNumber if requestDelivered[node] is not None else False )
                            requestInstalled[node] = day.dayNumber 
                            machineType = self.Instance.Requests[node-1].machineID
                            self._checkError('Technician %d is not allowed to install request %d (machinetype %d)' %(technicianRoute.ID,  node, self.Instance.Requests[node-1].machineID), technicianCapabilities[machineType-1] == 1)
                        if lastNode is None:
                            fromCoord = technician.locationID - 1 #home location
                            toCoord = 0 if node == 0 else self.Instance.Requests[node-1].customerLocID - 1
                        elif lastNode is not None:
                            fromCoord = 0 if lastNode == 0 else self.Instance.Requests[lastNode-1].customerLocID - 1
                            toCoord = 0 if node == 0 else self.Instance.Requests[node-1].customerLocID - 1
                        technicianDistance += self.Instance.calcDistance[fromCoord][toCoord]
                        lastNode = node
                    #From last customer to home location
                    fromCoord = 0 if technicianRoute.Route[-1] == 0 else self.Instance.Requests[technicianRoute.Route[-1] - 1].customerLocID - 1
                    toCoord = technician.locationID - 1
                    technicianDistance += self.Instance.calcDistance[fromCoord][toCoord]
                    self._checkError('Distance traveled by technician %d exceeds maximum allowed distance on day %d (%d > %d)' %(day.TechnicianRoutes[i].ID, day.dayNumber, technicianDistance, technician.maxDayDistance), technicianDistance <= technician.maxDayDistance)
                    totalTechnicianDistance += technicianDistance
                TechnicianDistanceCumulative[day.dayNumber - 1] = totalTechnicianDistance
                
            #Check if all requests are delivered, within timewindow and installed AFTER delivery and cumputes idle machine cost
            for request in self.Instance.Requests: 
                isDelivered = requestDelivered[request.ID] > 0 if requestDelivered[request.ID] is not None else False
                isInstalled = requestInstalled[request.ID] > 0 if requestInstalled[request.ID] is not None else False 
                if not isDelivered:
                    self._checkError('Request %d has not been delivered' %request.ID, False)
                if isDelivered: 
                    self._checkError('Request %d is not delivered within its time window' %request.ID, (requestDelivered[request.ID] >= request.fromDay) and (requestDelivered[request.ID] <= request.toDay ) )        
                if not isInstalled:
                    self._checkError('Request %d has not been installed' %request.ID, False)    
                if isDelivered and isInstalled:
                    idleMachineCost += (requestInstalled[request.ID] - requestDelivered[request.ID] - 1) * request.amount * self.Instance.Machines[request.machineID - 1].idlePenalty        

            #Check feasibility technician schedule
            for i in range(len(techniciansUsed)):
                technicianSchedule = techniciansUsed[i]
                if sum(technicianSchedule) > 0:
                    nrOfTechniciansUsed +=1
                if len(technicianSchedule) > 5:
                    for j in range(len(technicianSchedule) - 5):
                        if sum(technicianSchedule[j:j+5]) == 5 and sum(technicianSchedule[j:j+7]) > 5:
                            self._checkError('Technician %d has an infeasible workschedule, 2 days off are required after day %d' %(i+1, j+5) , False)
            
            #Compute cumulative costs (technicians used + idle machine costs + total costs)
            for day in self.Days:
                
                if day.dayNumber > 1:
                    IdleMachineCostCumulative[day.dayNumber - 1] += IdleMachineCostCumulative[day.dayNumber - 2]   
                for request in self.Instance.Requests:
                    if requestDelivered[request.ID] < day.dayNumber and requestInstalled[request.ID] > day.dayNumber:
                        IdleMachineCostCumulative[day.dayNumber - 1] += request.amount * self.Instance.Machines[request.machineID - 1].idlePenalty        
                
                for i in range(len(techniciansUsed)):
                    #if sum(techniciansUsed[day.dayNumber - 1][0:i]) > 0:
                    if sum(techniciansUsed[i - 1][0:day.dayNumber]) > 0:   
                        NrTechniciansUsedCumulative[day.dayNumber - 1] += 1
                CostCumulative[day.dayNumber - 1] = TruckDistanceCumulative [day.dayNumber - 1] * self.Instance.TruckDistanceCost \
                        + NrTruckDaysCumulative[day.dayNumber - 1] * self.Instance.TruckDayCost \
                        + NrTrucksUsedCumulative[day.dayNumber - 1] * self.Instance.TruckCost \
                        + TechnicianDistanceCumulative[day.dayNumber - 1] * self.Instance.TechnicianDistanceCost \
                        + NrTechnicianDaysCumulative[day.dayNumber - 1] * self.Instance.TechnicianDayCost \
                        + NrTechniciansUsedCumulative[day.dayNumber - 1] * self.Instance.TechnicianCost \
                        + IdleMachineCostCumulative[day.dayNumber - 1]       
            
            totalCost = totalTruckDistance * self.Instance.TruckDistanceCost \
                        + dayNumTrucks * self.Instance.TruckDayCost \
                        + maxNumTrucks * self.Instance.TruckCost \
                        + totalTechnicianDistance * self.Instance.TechnicianDistanceCost \
                        + dayNumTechnicians * self.Instance.TechnicianDayCost \
                        + nrOfTechniciansUsed * self.Instance.TechnicianCost \
                        + idleMachineCost
                        
            self.calcCost.TruckDistance = totalTruckDistance
            self.calcCost.NrTruckDays = dayNumTrucks
            self.calcCost.NrTrucksUsed = maxNumTrucks
            self.calcCost.TechnicianDistance = totalTechnicianDistance
            self.calcCost.NrTechnicianDays = dayNumTechnicians
            self.calcCost.NrTechniciansUsed = nrOfTechniciansUsed
            self.calcCost.IdleMachineCost = idleMachineCost
            self.calcCost.Cost = totalCost
            
            self.calcCost.TruckDistanceCumulative = TruckDistanceCumulative
            self.calcCost.NrTruckDaysCumulative = NrTruckDaysCumulative
            self.calcCost.NrTrucksUsedCumulative = NrTrucksUsedCumulative
            self.calcCost.TechnicianDistanceCumulative = TechnicianDistanceCumulative
            self.calcCost.NrTechnicianDaysCumulative = NrTechnicianDaysCumulative
            self.calcCost.NrTechniciansUsedCumulative = NrTechniciansUsedCumulative
            self.calcCost.IdleMachineCostCumulative = IdleMachineCostCumulative
            self.calcCost.CostCumulative = CostCumulative
        
        except self.BaseParseException:
            pass
        except:
            print('Crash during solution calculation\nThe following errors were found:')
            print( '\t' + '\n\t'.join(self.errorReport) )
            raise
        

    def isValid(self):
        return not self.errorReport
    
    def areGivenValuesValid(self):
        result = True
        try:
            result = result and self._checkWarning('Incorrect truck distance (given value: %d. Calculated value: %d).' % (self.givenCost.TruckDistance if self.givenCost.TruckDistance is not None else 0, self.calcCost.TruckDistance), self.givenCost.TruckDistance is None or self.givenCost.TruckDistance == self.calcCost.TruckDistance )
            result = result and self._checkWarning('Incorrect number of truck days (given value: %d. Calculated value: %d).' % (self.givenCost.NrTruckDays if self.givenCost.NrTruckDays is not None else 0,self.calcCost.NrTruckDays), self.givenCost.NrTruckDays is None or self.givenCost.NrTruckDays == self.calcCost.NrTruckDays )
            result = result and self._checkWarning('Incorrect number of trucks used (given value: %d. Calculated value: %d).' % (self.givenCost.NrTrucksUsed if self.givenCost.NrTrucksUsed is not None else 0,self.calcCost.NrTrucksUsed), self.givenCost.NrTrucksUsed is None or self.givenCost.NrTrucksUsed == self.calcCost.NrTrucksUsed )
            result = result and self._checkWarning('Incorrect technician distance (given value: %d. Calculated value: %d).' % (self.givenCost.TechnicianDistance if self.givenCost.TechnicianDistance is not None else 0,self.calcCost.TechnicianDistance), self.givenCost.TechnicianDistance is None or self.givenCost.TechnicianDistance == self.calcCost.TechnicianDistance )
            result = result and self._checkWarning('Incorrect number of technician days (given value: %d. Calculated value: %d).' % (self.givenCost.NrTechnicianDays if self.givenCost.NrTechnicianDays is not None else 0,self.calcCost.NrTechnicianDays), self.givenCost.NrTechnicianDays is None or self.givenCost.NrTechnicianDays == self.calcCost.NrTechnicianDays )
            result = result and self._checkWarning('Incorrect number of technician used (given value: %d. Calculated value: %d).' % (self.givenCost.NrTechniciansUsed if self.givenCost.NrTechniciansUsed is not None else 0,self.calcCost.NrTechniciansUsed), self.givenCost.NrTechniciansUsed is None or self.givenCost.NrTechniciansUsed == self.calcCost.NrTechniciansUsed )
            result = result and self._checkWarning('Incorrect idle machine cost (given value: %d. Calculated value: %d).' % (self.givenCost.IdleMachineCost if self.givenCost.IdleMachineCost is not None else 0,self.calcCost.IdleMachineCost), self.givenCost.IdleMachineCost is None or self.givenCost.IdleMachineCost == self.calcCost.IdleMachineCost )
            result = result and self._checkWarning('Incorrect total cost (given value: %d. Calculated value: %d).' % (self.givenCost.Cost if self.givenCost.Cost is not None else 0,self.calcCost.Cost), self.givenCost.Cost is None or self.givenCost.Cost == self.calcCost.Cost )
            
        except self.BaseParseException as E:
            return (False, E.message if E.message is not None else '')
        except:
            print('Crash during solution validation\nThe following errors were found:')
            print( '\t' + '\n\t'.join(self.errorReport) )
            raise
        
        return (result, '')
                                

def DoWork(args):
    instance = args.instance
    if not instance:
        if args.solution.endswith('.sol.txt'):
            instance = args.solution[:-7] + 'txt'
            print('No instance file specified, trying: %s ' % instance)
        else:
            print('No instance file specified and unable to determine one based on the solution file')
            return
    
    Instance = InstanceVerolog2019(instance,args.itype)
    if not Instance.isValid():
        print('File %s is an invalid instance file\nIt contains the following errors:' % instance)
        print( '\t' + '\n\t'.join(Instance.errorReport) )
        return
    Solution = SolutionVerolog2019(args.solution,Instance,args.type,args.continueOnError)   
    if Solution.isValid():
        print('Solution %s is a valid solution' % args.solution)
        if not args.skipExtraDataCheck:
            res = Solution.areGivenValuesValid()
            if res[0]:
                print('The given solution information is correct')
            else:
                print(res[1])
        print('\t' + '\n\t'.join(str(Solution.calcCost).split('\n')))
        if args.outputFile:
            Solution.writeSolution(args.outputFile,args.writeExtra)
        if len(Solution.warningReport) > 0:
            print('There were warnings:')
            print( '\t' + '\n\t'.join(Solution.warningReport) )
    else:
        print('File %s is an invalid solution file\nIt contains the following errors:' % args.solution)
        print( '\t' + '\n\t'.join(Solution.errorReport) )
        if len(Solution.warningReport) > 0:
            print('There were also warnings:')
            print( '\t' + '\n\t'.join(Solution.warningReport) )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read and checks solution file.')
    parser.add_argument('--solution', '-s', metavar='SOLUTION_FILE', required=True,
                        help='The solution file')
    parser.add_argument('--instance', '-i', metavar='INSTANCE_FILE',
                        help='The instance file')
    parser.add_argument('--type', '-t', choices=['txt', 'xml'],
                        help='Solution file type')
    parser.add_argument('--itype', choices=['txt', 'xml'],
                        help='instance file type')
    parser.add_argument('--outputFile', '-o', metavar='NEW_SOLUTION_FILE',
                        help='Write the solution to this file')
    parser.add_argument('--writeExtra', '-e', action='store_true',
                        help='Write the extra data in the outputfile')
    parser.add_argument('--skipExtraDataCheck', '-S', action='store_true',
                        help='Skip extra data check')
    parser.add_argument('--continueOnError', '-C', action='store_true',
                        help='Try to continue after the first error in the solution. This may result in a crash (found errors are reported). Note: Any error after the first may be a result of a previous error')
    args = parser.parse_args()
    
    if args.writeExtra and not args.outputFile:
        parser.error('--writeExtra can only be given when --outputFile is also given')

    DoWork(args)
             
    
 
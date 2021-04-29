#! /usr/bin/env python

import argparse
import math
import baseParser as base

class InstanceVerolog2019(base.BaseParser):
    parsertype = 'instance'
    
    class LANG:
        class TXT:
            dataset = 'DATASET'
            distance = 'DISTANCE'
            name = 'NAME'
            days = 'DAYS'
            truckCapacity = 'TRUCK_CAPACITY'
            truckMaxDistance = 'TRUCK_MAX_DISTANCE'
            truckDistanceCost = 'TRUCK_DISTANCE_COST'
            truckDayCost = 'TRUCK_DAY_COST'
            truckCost = 'TRUCK_COST'
            technicianDistanceCost = 'TECHNICIAN_DISTANCE_COST'
            technicianDayCost = 'TECHNICIAN_DAY_COST'
            technicianCost = 'TECHNICIAN_COST'
            machines = 'MACHINES'
            locations = 'LOCATIONS'
            requests = 'REQUESTS'
            technicians = 'TECHNICIANS'
    
    class Machine(object):
        def __init__(self,ID,size,idlePenalty):
            self.ID = ID
            self.size = size
            self.idlePenalty = idlePenalty

        def __repr__(self):
            return '%d %d %d' % (self.ID,self.size,self.idlePenalty)
    
    class Request(object):
        def __init__(self,ID,customerLocID,fromDay,toDay,machineID,amount):
            self.ID = ID
            self.customerLocID = customerLocID
            self.fromDay = fromDay
            self.toDay = toDay
            self.machineID = machineID
            self.amount = amount

        def __repr__(self):
            return '%d %d %d %d %d %d' % (self.ID,self.customerLocID,self.fromDay,self.toDay,self.machineID,self.amount)
    
    class Location(object):
        def __init__(self,ID,X,Y):
            self.ID = ID
            self.X = X
            self.Y = Y

        def __repr__(self):
            return '%d %d %d' % (self.ID,self.X,self.Y)
          
    class Technician(object):
        def __init__(self,ID,locationID,maxDayDistance, maxNrInstallations, capabilities):
            self.ID = ID
            self.locationID = locationID
            self.maxDayDistance = maxDayDistance
            self.maxNrInstallations = maxNrInstallations
            self.capabilities = capabilities

        def __repr__(self):
            return '%d %d %d %d %s' % (self.ID,self.locationID,self.maxDayDistance,self.maxNrInstallations, ' '.join(str(x) for x in self.capabilities))
    
    def __init__(self, inputfile=None,filetype=None,continueOnErr=False):
        if inputfile is not None:
            self._doinit(inputfile,filetype,continueOnErr)
        else:
            self._initData()
        
    def _initData(self):
        self.Machines = []
        self.Requests = []
        self.Locations = []
        self.Technicians = []
        self.ReadDistance = None
        self.calcDistance = None
    
    def _initTXT(self):
        try:
            fd = open(self.inputfile, 'r')
        except:
            self.errorReport.append( 'Instance file %s could not be read.' % self.inputfile )
            return

        try:
            with fd:
                self.Dataset = self._checkAssignment(fd,self.LANG.TXT.dataset,'string')
                self.Name = self._checkAssignment(fd,self.LANG.TXT.name,'string')
                
                self.Days = self._checkInt( 'Days', self._checkAssignment(fd,self.LANG.TXT.days) )
                self.TruckCapacity = self._checkInt( 'Truck Capacity', self._checkAssignment(fd,self.LANG.TXT.truckCapacity) )
                self.TruckMaxDistance = self._checkInt( 'Truck Max trip distance', self._checkAssignment(fd,self.LANG.TXT.truckMaxDistance) )
                
                self.TruckDistanceCost = self._checkInt( 'Truck Distance Cost', self._checkAssignment(fd,self.LANG.TXT.truckDistanceCost) )                
                self.TruckDayCost = self._checkInt( 'Truck Day Cost', self._checkAssignment(fd,self.LANG.TXT.truckDayCost) )
                self.TruckCost = self._checkInt( 'Truck Cost', self._checkAssignment(fd,self.LANG.TXT.truckCost) )
                self.TechnicianDistanceCost = self._checkInt( 'Technician Distance Cost', self._checkAssignment(fd,self.LANG.TXT.technicianDistanceCost) )                
                self.TechnicianDayCost = self._checkInt( 'Technician Day Cost', self._checkAssignment(fd,self.LANG.TXT.technicianDayCost) )
                self.TechnicianCost = self._checkInt( 'Technician Cost', self._checkAssignment(fd,self.LANG.TXT.technicianCost) )
                
                nrMachineTypes = self._checkInt("Number of machines", self._checkAssignment(fd,self.LANG.TXT.machines))
                for i in range(nrMachineTypes):
                    line = self._getNextLine(fd)
                    MachineLine = line.split()
                    self._checkError("Expected three integers on a machine line. Found: '%s'." % line,
                                     len(MachineLine) == 3)
                    machineID = self._checkInt('Machine ID', MachineLine[0] )
                    size = self._checkInt('Machine size', MachineLine[1], 'for machine %d ' % machineID )
                    idlePenalty = self._checkInt('Machine idle penalty', MachineLine[2], 'for machine %d ' % machineID )
                    self.Machines.append( self.Machine(machineID,size,idlePenalty) )
                    self._checkError('The indexing of the Machines is incorrect at Machine nr. %d.' % machineID, machineID == len(self.Machines) )
                    
                nrLocations = self._checkInt("Number of locations", self._checkAssignment(fd,self.LANG.TXT.locations))
                for i in range(nrLocations):
                    line = self._getNextLine(fd)
                    LocationLine = line.split()
                    self._checkError("Expected three integers on a coordinate line. Found: '%s'." % line,
                                    len(LocationLine) == 3)
                    locID = self._checkInt('Coordinate ID', LocationLine[0] )
                    X = self._checkInt('Coordinate X', LocationLine[1], 'for Location %d ' % locID )
                    Y = self._checkInt('Coordinate Y', LocationLine[2], 'for Location %d ' % locID )
                    self.Locations.append( self.Location(locID,X,Y) )
                    self._checkError('The indexing of the Locations is incorrect at Location nr. %d.' % locID, locID == len(self.Locations) )
 
                nrRequests = self._checkInt("Number of requests", self._checkAssignment(fd,self.LANG.TXT.requests))
                for i in range(nrRequests):
                    line = self._getNextLine(fd)
                    RequestLine = line.split()
                    self._checkError("Expected six integers on a request line. Found: '%s'." % line,
                                    len(RequestLine) == 6)
                    requestID = self._checkInt('Request ID', RequestLine[0] )
                    customerLocID = self._checkInt('Customer Location ID', RequestLine[1], 'for Request %d ' % requestID )
                    self._checkError('Customer Location ID %d for request %d is larger than the number of locations (%d)' % (customerLocID, requestID, nrLocations), 0 < customerLocID <= nrLocations )
                    fromDay = self._checkInt('Request from-day', RequestLine[2], 'for Request %d ' % requestID )
                    self._checkError('Request from-day %d is larger than the horizon (%d) for request %d' % (fromDay, self.Days, requestID), 0 < fromDay <= self.Days )
                    toDay = self._checkInt('Request to-day', RequestLine[3], 'for Request %d ' % requestID )
                    self._checkError('Request to-day %d is larger than the horizon (%d) for request %d' % (toDay, self.Days, requestID), 0 < toDay <= self.Days )
                    self._checkError('Request to-day %d is smaller than Request from-day (%d) for request %d' % (toDay, fromDay, requestID), 0 < fromDay <= toDay )

                    machineID = self._checkInt('Request Machine ID', RequestLine[4], 'for Request %d ' % requestID )
                    self._checkError('Request Machine ID %d is larger than the number of machines (%d) for request %d' % (machineID, nrMachineTypes, requestID), 0 < machineID <= nrMachineTypes )
                    amount = self._checkInt('Requested amount', RequestLine[5], 'for Request %d ' % requestID )
                    self._checkError('Requested amount is not strict positive (%d) for request %d' % (amount, requestID), 0 < amount )
                    self.Requests.append( self.Request(requestID,customerLocID,fromDay,toDay,machineID,amount) )
                    self._checkError('The indexing of the Requests is incorrect at Request nr. %d.' % requestID, requestID == len(self.Requests) )
 
                nrTechnicians = self._checkInt("Number of technicians", self._checkAssignment(fd,self.LANG.TXT.technicians))
                for i in range(nrTechnicians):
                    line = self._getNextLine(fd)
                    TechnicianLine = line.split()
                    self._checkError("Expected %d integers on a technician line. Found: '%s'." % (4 + nrMachineTypes, line),
                                    len(TechnicianLine) == 4 + nrMachineTypes )
                    technicianID = self._checkInt('Technician ID', TechnicianLine[0] )
                    locID = self._checkInt('Technician Location ID', TechnicianLine[1], 'for Technician %d ' % technicianID )
                    self._checkError('Technician Location ID %d is larger than the number of locations (%d) for technician %d' % (locID, nrLocations, technicianID), 0 < locID <= nrLocations )
                    
                    maxDayDistance = self._checkInt('Max Day Distance', TechnicianLine[2], 'for Technician %d ' % technicianID )
                    self._checkError('Max Day Distance is not strict positive (%d) for Technician %d' % (maxDayDistance, technicianID), 0 < maxDayDistance )
                    maxNrInstallations = self._checkInt('Max Nr Installations', TechnicianLine[3], 'for Technician %d ' % technicianID )
                    self._checkError('Max Nr Installations is not strict positive (%d) for Technician %d' % (maxNrInstallations, technicianID), 0 < maxNrInstallations )

                    try:
                        capabilities = [int(x) for x in TechnicianLine[4:]]
                    except ValueError as err:
                        self._checkError('Error reading technician capabilities for technician %d, expecting integers on line: %s' % (technicianID,line), False)

                    self._checkError('Technician capabilities should be zero or one for technician %d on line: %s' % (technicianID,line), all([ (x==0 or x==1) for x in capabilities]))
                    self.Technicians.append( self.Technician(technicianID,locID,maxDayDistance,maxNrInstallations,capabilities) )
        except:
            print('Crash during Verolog2019 instance reading\nThe following errors were found:')
            print( '\t' + '\n\t'.join(self.errorReport) )
            raise
               
    def calculateDistances(self):
        if not self.isValid() or self.calcDistance is not None:
            return
        numLocs = len(self.Locations)
        self.calcDistance = [[0 for x in range(numLocs)] for x in range(numLocs)]
        for i in range(numLocs): 
            cI = self.Locations[i]
            for j in range(i,numLocs):
                cJ = self.Locations[j]
                dist = math.ceil( math.sqrt( pow(cI.X-cJ.X,2) + pow(cI.Y-cJ.Y,2) ) )
                self.calcDistance[i][j] = self.calcDistance[j][i] = int(dist)
                
    def isValid(self):
        return not hasattr(self, 'errorReport') or not self.errorReport
        
    def areDistancesValid(self):
        if self.ReadDistance is None:
            return (True,'Distances are not given.')
        self.calculateDistances()
        if self.ReadDistance != self.calcDistance:
            numLocs = len(self.Locations)
            for i in range(numLocs): 
                for j in range(numLocs):
                    if self.ReadDistance[i][j] != self.calcDistance[i][j]:
                        return (False,'Incorrect Distances. First difference is at location %d,%d: %d should be %d' % (i,j,self.ReadDistance[i][j],self.calcDistance[i][j])  )
        return (True,'The given distances are correct')
        
    def writeInstance(self,filename,writeMatrix):
        res = self._writeInstanceTXT(filename,writeMatrix)
        if res[0]:
            print('Instance file written to %s' % filename)
        else:
            print('Error writing output file %s: %s' % (filename,res[1]))

    def _writeInstanceTXT(self,filename,writeMatrix):
        try:
            fd = open(filename,  mode='w')
        except:
            return (False, 'Could not write to file.')
        
        with fd:
            self._writeAssignment(fd,self.LANG.TXT.dataset,self.Dataset)
            self._writeAssignment(fd,self.LANG.TXT.name,self.Name)
            fd.write('\n')
            self._writeAssignment(fd,self.LANG.TXT.days,self.Days)
            self._writeAssignment(fd,self.LANG.TXT.truckCapacity,self.TruckCapacity)
            self._writeAssignment(fd,self.LANG.TXT.truckMaxDistance,self.TruckMaxDistance)
            fd.write('\n')
            self._writeAssignment(fd,self.LANG.TXT.truckDistanceCost,self.TruckDistanceCost)
            self._writeAssignment(fd,self.LANG.TXT.truckDayCost,self.TruckDayCost)
            self._writeAssignment(fd,self.LANG.TXT.truckCost,self.TruckCost)
            self._writeAssignment(fd,self.LANG.TXT.technicianDistanceCost,self.TechnicianDistanceCost)
            self._writeAssignment(fd,self.LANG.TXT.technicianDayCost,self.TechnicianDayCost)
            self._writeAssignment(fd,self.LANG.TXT.technicianCost,self.TechnicianCost)
            fd.write('\n')
            
            self._writeAssignment(fd,self.LANG.TXT.machines,len(self.Machines))
            for i in range(len(self.Machines)):
                fd.write('%s\n' % str(self.Machines[i]) )
            fd.write('\n')
            
            self._writeAssignment(fd,self.LANG.TXT.locations,len(self.Locations))
            for i in range(len(self.Locations)):
                fd.write('%s\n' % str(self.Locations[i]) )
            fd.write('\n')
            
            self._writeAssignment(fd,self.LANG.TXT.requests,len(self.Requests))
            for i in range(len(self.Requests)):
                fd.write('%s\n' % str(self.Requests[i]) )
            fd.write('\n')
            
            self._writeAssignment(fd,self.LANG.TXT.technicians,len(self.Technicians))
            for i in range(len(self.Technicians)):
                fd.write('%s\n' % str(self.Technicians[i]) )
            fd.write('\n')
            
            if writeMatrix:
                self.calculateDistances()
                fd.write(self.LANG.TXT.distance + '\n')
                for distLine in self.calcDistance:
                    fd.write('\t'.join(str(d) for d in distLine) + '\n')
                fd.write('\n')
            
        return (True, '')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read and checks Verolog2019 instance file.')
    parser.add_argument('--instance', '-i', metavar='INSTANCE_FILE', required=True,
                        help='The instance file')
    parser.add_argument('--type', '-t', choices=['txt'],
                        help='Instance file type')
    parser.add_argument('--skipDistanceCheck', '-S', action='store_true',
                        help='Skip check on given distances')
    parser.add_argument('--outputFile', '-o', metavar='NEW_INSTANCE_FILE',
                        help='Write the instance to this file')
    parser.add_argument('--writeMatrix', '-m', action='store_true',
                        help='Write the matrix in the outputfile')
    parser.add_argument('--continueOnError', '-C', action='store_true',
                        help='Try to continue after the first error in the solution. This may result in a crash (found errors are reported). Note: Any error after the first may be a result of a previous error')
    args = parser.parse_args()
    
    if args.writeMatrix and not args.outputFile:
        parser.error('--writeMatrix can only be given when --outputFile is also given')
    
    Instance = InstanceVerolog2019(args.instance,args.type,args.continueOnError)
    if Instance.isValid():
        print('Instance %s is a valid Verolog2019 instance' % args.instance)
        if not args.skipDistanceCheck:
            res = Instance.areDistancesValid()
            print(res[1])
        if args.outputFile:
            Instance.writeInstance(args.outputFile,args.writeMatrix)
        if len(Instance.warningReport) > 0:
            print('There were warnings:')
            print( '\t' + '\n\t'.join(Instance.warningReport) )
    else:
        print('File %s is an invalid Verolog2019 instance file\nIt contains the following errors:' % args.instance)
        print( '\t' + '\n\t'.join(Instance.errorReport) )
        if len(Instance.warningReport) > 0:
            print('There were also warnings:')
            print( '\t' + '\n\t'.join(Instance.warningReport) )


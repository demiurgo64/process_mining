import csv
import copy
import itertools as it
import numpy as np
import datetime

class ACO(object):
    def __init__(self, ant_cant:int, generation:int, alpha:float,
                 beta:float, rho:float, q:int):
        self.Q=q
        self.rho=rho
        self.beta=beta
        self.alpha=alpha
        self.ant_cant= ant_cant
        self.generation = generation

class Log(object):
    def __init__(self, path:str):
        self.path=path
        self.log, self.activity  = self.log_import()
        self.start, self.end = self.StartEnd()
        
    def log_import(self):
    
        log = dict()
        activity= dict()
        counter=0
        with open(self.path, 'r') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';',quotechar='"')
            for row in spamreader:
                caseid = row[0]
                task = row[1]
                user = row[2]
                timestamp = datetime.datetime.strptime(row[3], '%Y/%m/%d %H:%M:%S.%f')
                if caseid not in log:
                    log[caseid] = []
                event = (task, user, timestamp)
                log[caseid].append(event)
                if task not in activity.keys():
                    activity[task]=counter
                    counter+=1
        for case in log.keys():
            log[case].sort(key=lambda x:x[2])
        
        return log, activity
    
    def trace(self):
        order=dict()
        for caseid in self.log:
             if caseid not in order:
                    order[caseid] = [x[0] for x in self.log[caseid]]
        return order
                
    def StartEnd(self):
        initial=[x[0] for x in self.trace().values()]
        start=dict()
        for i in initial:
            if i not in start:
                start[i]=0
            start[i]+=1
        
        final=[x[-1] for x in self.trace().values()]
        end=dict()
        for i in final:
            if i not in end:
                end[i]=0
            end[i]+=1
        return start, end
    def direct(self):
        F = dict()
        for caseid in self.log:
            for i in range(0, len(self.log[caseid])-1):
                ai = self.log[caseid][i][0]
                aj = self.log[caseid][i+1][0]
                if ai not in F:
                    F[ai] = dict()
                if aj not in F[ai]:
                    F[ai][aj] = 0
                F[ai][aj] += 1
        return F
    
    def getStartEnd(self):
        stAct = [k for k,v in self.activity.items() if v==0]
        F=self.direct()
        enAct = list(set(self.activity.keys())-set(F.keys()))
        return stAct, enAct
    
    def getDist(self):
        F=self.direct()
        dist=dict()
        for ai in sorted(F.keys()):
            if ai not in F.keys():
                dist[ai]=dict()
            total=sum(F[ai].values())
            for aj in sorted(F[ai].keys()):
                if ai not in dist:
                    dist[ai]=dict()
                dist[ai][aj]=F[ai][aj]/total
        return dist
    
    def getRoute(self, combinations=100):
        F=self.direct()
        route=dict()
        for ai in F.keys():
            if ai not in route:
                route[ai]=list()
            count= len(F[ai].keys())
            for i in range(1,min(combinations,count+1)):
                route[ai].extend(list(it.combinations(list(F[ai].keys()),i)))
        return route
    
    def getInfo(self, acumulate=False):
        route=self.getRoute(3)
        F=self.direct()
        prob=dict()
        count=dict()
        for fromAct in route.keys():
            count[fromAct]={('dir',toAct):F[fromAct][toAct[0]] for toAct in route[fromAct] if len(toAct)==1}
            count[fromAct].update({('and',toAct):sum([F[fromAct][item] for item in toAct])*log.splitTask(fromAct, toAct, F) for toAct in route[fromAct] if len(toAct)>1})
            count[fromAct].update({('or',toAct):sum([F[fromAct][item] for item in toAct])*(1-log.splitTask(fromAct, toAct, F)) for toAct in route[fromAct] if len(toAct)>1})
        for fromAct in count.keys():
            total=sum(count[fromAct].values())
            prob[fromAct]={toAct:count[fromAct][toAct]/total for toAct in count[fromAct].keys()}
        
        if acumulate:
            for fromAct in prob.keys():
                acum=0
                for key, value in prob[fromAct].items():
                    acum+=value
                    prob[fromAct][key]=acum
        return prob
    
    def splitTask(self, fromAct, toAct:tuple, F:dict):
        tasks=list()
        for act in toAct:
            tasks.append(F[fromAct][act])
        coeff=np.std(tasks)/np.mean(tasks)
        if coeff>0.8:
            relation=0.2
        else:
            relation=min(1-coeff,0.8)
        return relation
   
class AntColony(object):
    def __init__(self, dist:dict, route:dict, startAct:dict, endAct:dict):
        self.heuristic = copy.deepcopy(dist)
        self.route = copy.deepcopy(route)
        self.phero = self.startPheromone()
        self.start = copy.deepcopy(startAct)
        self.end = copy.deepcopy(endAct)
        
    def startPheromone(self, value=0.5):
        pheromone=copy.deepcopy(self.heuristic)
        for fromAct in pheromone.keys():
            pheromone[fromAct]={key:value for key, old in pheromone[fromAct].items()}
        return pheromone
    def updatePheromone(self, ants, accu:list, rho=0.01, tau=0.01):
        phero=self.phero
        for key in phero.keys(): #reduce pheromone
            for subkey, value in phero[key].items():
                new_val=value-rho
                if new_val <0.05: new_val=0.05
                phero[key][subkey]=new_val
        g_perc=[x*tau for x in accu]#pheromone to add per ant
        for index, ant in enumerate(ants):
            for key, value in ant.items():
                phero[key][value]=phero[key][value]+g_perc[index]
        self.phero = phero
        
    def probability(self):
        matriz=copy.deepcopy(self.heuristic)
        phero=self.phero
        heuristic=self.heuristic
        for fromAct in matriz.keys():
            for toAct in matriz[fromAct].keys():
                matriz[fromAct][toAct]=phero[fromAct][toAct] * heuristic[fromAct][toAct]
            total=sum(matriz[fromAct].values())
            matriz[fromAct]={key:value/total for key, value in matriz[fromAct].items()}
        for fromAct in matriz.keys(): #Acumulate probability
            acum=0
            for key, value in matriz[fromAct].items():
                acum+=value
                matriz[fromAct][key]=acum
        return matriz
    
    def createSolutions(self, quantity=1):
        ants=[None]*quantity
        actInit=list(self.start.keys())
        actEnd=list(self.end.keys())
        prob=self.probability()
        
        for ant in range(quantity):
            graph=dict()
            if len(actInit)>1:
                ind=np.random.randint(len(actInit))
            else:
                ind=0
            step=actInit[ind] #Choose start task
            #graph['/start/']=('dir',(step,)) #temporaly this support and/or split initial
            random=np.random.random()
            for key, value in prob[step].items():
                if random<=value:
                    graph[step]=key
                    step=key
                    break

            #rest of activities
            for act in step[1]:
                if act in prob.keys():
                    tupla=self.chooseAct(act, prob[act])
                    if act not in graph.keys():
                        graph[act]=tupla
            
#            #create connection to final task
#            temporal=dict()
#            for tasks in graph.values():
#                for act in tasks[1]:
#                    if act in actEnd:
#                        if act not in graph.values():
#                            temporal[act]=('dir',('/end/',))
#            #Add temporal to graph
#            for key, value in temporal.items():
#                graph[key]=value
            
            #Check not-end task
            temporal=dict() #to save pairs key, value
            for tasks in graph.values():
                for act in tasks[1]:
                    if act not in graph.keys():
                        if act not in actEnd:
                            if act !='/end/':
                                temporal[act]=self.chooseAct(act, prob[act])
            #Add temporal to graph
            for key, value in temporal.items():
                graph[key]=value
                            
            
            ants[ant]=graph
        return ants
    
    def chooseAct(self, act:str, subprob:dict):
        random=np.random.random()
        for key, value in subprob.items():
            if random<=value:
                tupla=key
        return tupla

def accuracity(ant:dict, traces:list, endTask):
    result=list()
    for trace in traces:
        complete=True
        for index, element in enumerate(trace):
            if index+1 < len(trace):
                if element in ant.keys():
                    kind, tasks =ant[element] #Split kind of relation and activity
                    complete=complete and check(kind, tasks, index, trace)
            else:
                if trace[-1] not in endTask.keys():
                    complete=False
        result.append(complete)
        complete=True
    return sum(result)/len(result)

def check(kind, tasks, pos, trace):
    result=False
    if kind=='dir':
        if trace[pos+1]==tasks: result=True
    if kind=='and':
        ind=len(tasks)
        if pos+1+ind<len(trace):
            subtrace=trace[pos+1:pos+ind+1]
            mask=[act in subtrace for act in tasks]
            if sum(mask)==len(mask): result=True
    if kind=='or':
        ind=len(tasks)
        limit=min(pos+ind+1,len(trace))
        if pos+1<len(trace):
            subtrace=trace[pos+1:limit]
            mask=[act in subtrace for act in tasks]
            if (sum(mask)>0)and (sum(mask)<len(mask)): result=True
    return result
    
log=Log('hospital.csv')
activities=log.getStartEnd()
F=log.direct()
route=log.getRoute()
prob=log.getInfo()
final={key: value for key, value in log.end.items() if value/sum(log.end.values())>0.01}
colonia=AntColony(prob, route, log.start, final)
phero=colonia.phero
matriz=colonia.probability()
#ants=colonia.createSolutions(100)
antTest={'NEW':('or',('DELETE', 'CHANGE DIAGN', 'FIN')), 
         'FIN':('dir',('RELEASE')), 
         'RELEASE':('or',('CODE NOK','CODE OK')),
         'CODE NOK':('dir',('BILLED',)),
         'CODE OK':('or',('BILLED','STORNO')),
         'STORNO':('dir',('REJECT',)),
         'REJECT':('dir',('REOPEN',)),
         'REOPEN':('dir',('DELETE')),
         'CHANGED DIAGN':('dir',('FIN',)),
         }
trazas=list(log.trace().values())
print(accuracity(antTest, trazas, final))
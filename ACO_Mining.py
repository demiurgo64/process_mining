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
                timestamp = datetime.datetime.strptime(row[3], '%Y/%m/%d %H:%M:%S.%f')#'%Y/%m/%d %H:%M:%S.%f' '%d/%m/%y %H:%M'
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
    
    def direct1(self, prob=0.005):
        size=len(self.log)
        F = self.direct()
        F1={key:{subkey:value for subkey, value in F[key].items() if (F[key][subkey]/size)>prob} for key in F.keys()}
        toDel=[key for key in F1.keys() if len(F1[key])<1]
        for key in toDel:
            del F1[key]
        return F1
    
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
        F=self.direct1()
        route=dict()
        for ai in F.keys():
            if ai not in route:
                route[ai]=list()
            count= len(F[ai].keys())
            for i in range(1,min(combinations,count+1)):
                route[ai].extend(list(it.combinations(list(F[ai].keys()),i)))
        return route
    
#    def filterRoute(self, endtask, combinations=100):
#        route = self.getRoute(combinations)
#        routeKeys = list(route.keys())
#        for toAct, fromAct in route.items():
#            for comb in from fromAct:
#                for act in comb:
#                    None
#        
#        return route
    
    def getInfo(self, acumulate=False, combinations=100):
        route=self.getRoute(combinations)
        F=self.direct1()
        prob=dict()
        count=dict()
        for fromAct in route.keys():
            count[fromAct]={('dir',toAct):F[fromAct][toAct[0]] for toAct in route[fromAct] if len(toAct)==1}
            #count[fromAct].update({('and',toAct):sum([F[fromAct][item] for item in toAct])*self.splitTask(fromAct, toAct, F) for toAct in route[fromAct] if len(toAct)>1})
            #count[fromAct].update({('or',toAct):sum([F[fromAct][item] for item in toAct])*(1-self.splitTask(fromAct, toAct, F)) for toAct in route[fromAct] if len(toAct)>1})
            count[fromAct].update({('and',toAct):sum([F[fromAct][item]/(len(toAct)) for item in toAct])*self.splitTask(fromAct, toAct, F) for toAct in route[fromAct] if len(toAct)>1})
            count[fromAct].update({('or',toAct):sum([F[fromAct][item]/(len(toAct)) for item in toAct])*(1-self.splitTask(fromAct, toAct, F)) for toAct in route[fromAct] if len(toAct)>1})
        for fromAct in count.keys():
            total=1#sum(count[fromAct].values())
            prob[fromAct]={toAct:count[fromAct][toAct]/total for toAct in count[fromAct].keys() if count[fromAct][toAct]>0}
        
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
        if coeff>0.3:
            relation=0
        else:
            relation=1-coeff
        return relation
   
class AntColony(object):
    def __init__(self, dist:dict, route:dict, startAct:dict, endAct:dict):
        self.heuristic = copy.deepcopy(dist)
        #self.route = copy.deepcopy(route)
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
        # for key in phero.keys(): #reduce pheromone
        #     for subkey, value in phero[key].items():
        #         new_val=value*(1-rho)
        #         phero[key][subkey]=new_val
        g_perc=[x*tau for x in accu]#pheromone to add per ant
        for index, ant in enumerate(ants):
            for key, value in ant.items():
                phero[key][value]=phero[key][value]*(1-rho)+g_perc[index]
        self.phero = phero

    def localUpdatepheromone(self, ants, sigma:float, initial:float):
        phero=self.phero
        # for key in phero.keys(): #reduce pheromone
        #     for subkey, value in phero[key].items():
        #         phero[key][subkey]=value*(1-sigma)+sigma*initial
        for ant in ants:
            for key, value in ant.items():
                phero[key][value]=phero[key][value]*(1-sigma)+sigma*initial
        self.phero = phero

    def probability(self, alpha=1, beta=1, acumulate=True):#1,1
        matriz=copy.deepcopy(self.heuristic)
        phero=self.phero
        heuristic=self.heuristic
        for fromAct in matriz.keys():
            for toAct in matriz[fromAct].keys():
                matriz[fromAct][toAct]=(phero[fromAct][toAct]**alpha) * (heuristic[fromAct][toAct]**beta)
            total=sum(matriz[fromAct].values())
            matriz[fromAct]={key:value/total for key, value in matriz[fromAct].items()}
        if acumulate:
            for fromAct in matriz.keys(): #Acumulate probability
                acum=0
                for key, value in matriz[fromAct].items():
                    acum+=value
                    matriz[fromAct][key]=acum
        return matriz
    
    def createSolutions(self, start:list, final:list, alpha=1, beta=1, quantity=1):
        ants=[None]*quantity
        actInit=start #list(self.start.keys())
        actEnd= final #list(self.end.keys())
        prob=self.probability(alpha, beta)
        prob2=self.probability(beta=2, acumulate=False)
        for ant in range(quantity):
            graph=dict()
            if len(actInit)>1:
                ind=np.random.randint(len(actInit))
            else:
                ind=0
            step=actInit[ind] #Choose start task
            random=np.random.random()
            for key, value in prob[step].items():
                if random<=value:
                    graph[step]=key
                    step=key
                    break
            
            #rest of activities
            for act in step[1]:
                if act in prob.keys():
                    tupla=self.chooseAct(act, prob[act], prob2[act])
                    if act not in graph.keys():
                        graph[act]=tupla
            
            allconected=False
            while(not allconected):#            
                #Check not-end task
                temporal=dict() #to save pairs key, value
                count=0
                for tasks in graph.values():
                    for act in tasks[1]:
                        if act not in graph.keys():
                            if act in prob.keys():
                            #if act not in actEnd:
                                temporal[act]=self.chooseAct(act, prob[act], prob2[act])
                                count+=1
                            elif act not in actEnd:
                                print("violation {}".format(act))
                #Add temporal to graph
                for key, value in temporal.items():
                    graph[key]=value
                if count==0:
                    allconected=True
                            
            
            ants[ant]=graph
        return ants
    
    def chooseAct(self, act:str, subprob:dict, subprob2:dict, limit=0.05):
        random=np.random.random(size=2)
        if random[0]>limit:
            for key, value in subprob.items():
                if random[1]<=value:
                    tupla=key
        else:
            lista=list(subprob.keys())
            ind=np.random.randint(len(lista))
            tupla=lista[ind]
            tupla=max(subprob2, key=subprob2.get)
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
                    if not complete: break
                else:
                    if element not in endTask.keys():
                        complete=False
            else:
                if trace[-1] not in endTask.keys():
                    complete=False
        result.append(complete)
        complete=True
    return sum(result)/len(result)

def check(kind, tasks, pos, trace):
    result=False
    if kind=='dir':
        if trace[pos+1]==tasks[0]: result=True
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

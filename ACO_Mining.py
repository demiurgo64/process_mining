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
        
    #def _update_feromone(self):
        
    #def solve(self):

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
    
    def getRoute(self):
        F=self.direct()
        route=dict()
        for ai in F.keys():
            if ai not in route:
                route[ai]=list()
            count= len(F[ai].keys())
            for i in range(1,count+1):
                route[ai].extend(list(it.combinations(list(F[ai].keys()),i)))
        return route
    
    def getInfo(self, acumulate=False):
        route=self.getRoute()
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
    
    def updatePheromone(self, ants, accu:list, route:dict, rho=0.01, tau=0.01):
        phero=self.phero
        for i in phero.keys(): #evaporation
            phero[i]=[x-rho for x in phero[i]]
        sol=ants[0]#Route
        rel=ants[1]#kind of route
        g_perc=[x*tau for x in accu]
        for i in range(len(sol)):#new pheromone
            for key in sol[i].keys():
                value=sol[i][key]
                j=0
                for item in value:
                    if(len(item)>1):
                        type_split=rel[i][key][j]
                        j+=1
                        if type_split==1: #And
                            phero[key][2]+=g_perc[i]
                        else: #or
                            phero[key][3]+=g_perc[i]
                    else:
                        pos=[list(x) for x in route[key]].index(item)
                        phero[key][pos]+=g_perc[i]
        self.phero=phero
        
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
            graph['/start/']=('dir',(step,)) #temporaly this support and/or split initial
            random=np.random.random()
            for key, value in prob[step].items():
                if random<=value:
                    graph[step]=key
                    step=key
                    break

            #rest of activities
            for act in step[1]:
                if act in prob.keys():
                    tupla=self.chooseAct(act, prob[act], graph)
                    if act not in graph.keys():
                        graph[act]=tupla
#                    for key, value in prob[act].items():
#                        random=np.random.random()
#                        if random<=value:
#                            if act not in graph.keys():
#                                graph[act]=key
            
            #Check not end task
            for tasks in graph.values():
                for act in tasks[1]:
                    if act not in graph.keys():
                        if act not in actEnd:
                            None
            #check if reach end's task
            if act in graph.keys():
                None
                            
            
            ants[ant]=graph
        return ants
    
    def chooseAct(self, act:str, subprob:dict, graph:dict):
        random=np.random.random()
        for key, value in subprob.items():
            if random<=value:
                tupla=key
        return tupla
    
    def createSolution(self, quantity):
        ants=[None]*quantity
        ant2=[None]*quantity
        actSE=self.start
        route=self.route #Get path
        relation=self.relation
        prob=self.probability() #Get prob per route
        for p in range(quantity):
            graph=dict()
            rel=dict()
            ant=['a']#Routine for first element
            step=ant[-1]
            for j in ant:
                step=j
                for i in step:
                    if i not in actSE[1]:
                        random=self.choose(prob[i])
                        part=route[i][random]
                        rel_ind=relation[i][random]
                        if i not in graph.keys():
                            graph[i]=list()
                            rel[i]=list()
                        new=[str(x) for x in part]
                        if new not in  graph[i]:
                            graph[i].append(new)
                            rel[i].append(rel_ind)
                            ant.append(part)
            ants[p]=graph
            ant2[p]=rel
        return ants, ant2
     #Create que tipo de relación es           
    
    def choose(self, lista:list):
        """Get a random index form acumulative list.
        
        Args:
            param1 (list): list of probabilities
        Returns:
            int: Position choose element."""
        num=np.random.rand()
        for i in lista:
            if i>num:
                ind=lista.index(i)
                break            
        return ind

def accuracity(ant, rel, log):
    count=0
    
    for trace in list(log.trace().values()):
        complete=True
        for index, element in enumerate(trace): #check element-by-element in trace
            if element in ant.keys(): #Check if element exist in ant
                for i in ant[element]:
                    ind=ant[element].index(i)
                    if(rel[element][ind]<2):#Direct & and
                        for j in i:
                            #print("(%s,%s - %s )" % (element, j, check(element, j, trace)))
                            complete = complete and check(element, j, trace)
                    else:#Or
                        #print("(%s,%s - %s )" % (element, i, check_or(index, i, trace)))
                        complete = complete and check_or(index,i,trace)
            else:
                complete = complete and element in log.getStartEnd()[1]
        #print(complete)
    
    
        #Check if was good fitness    
        if complete == True:
            count+=1
    per=count/len(log.trace().values())
    return per

def check(first, second, lista:list):
    result=False
    if first in lista and second in lista:
        result=lista.index(first)<lista.index(second)
    return result

def check_or(index,split:list, lista:list):
    result=False
    for item in split:
        if index+3 <= len(lista):
            result=(lista[index+1] in split)|(lista[index+2] in split) #is posible Xor o or activities
        elif index+2<=len(lista):
            result=lista[index+1] in split
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
ants=colonia.createSolutions(10)
#    for i in range(len(sol)):
#        accu.append(accuracity(sol[i],rel[i],log))
#    colonia.updatePheromone([sol, rel], accu, route)
#print(colonia.phero)
#trazas=list(log.trace().values())

#for i in range(len(sol)):
#    print(accuracity(sol[i],rel[i],log))
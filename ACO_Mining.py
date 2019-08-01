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
                timestamp = datetime.datetime.strptime(row[3], '%d/%m/%y %H:%M')
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
    
    def getInfo(self):
        route=copy.deepcopy(self.getRoute())
        F=copy.deepcopy(self.direct())
        prob=dict()
        for ai in route.keys():
            if ai not in prob.keys():
                prob[ai]=[0]*len(route[ai])
            for i in range(len(route[ai])):
                acts=route[ai][i]
                for j in range(len(acts)):
                    fkey=acts[j]
                    prob[ai][i]+=F[ai][fkey]
        for ai in prob.keys():
            total=sum(prob[ai])
            for i in range(len(prob[ai])):
                if (len(route[ai][i])==1):
                    prob[ai][i]=prob[ai][i]/total
                else:
                    lista=route[ai][i]
                    value=prob[ai][i]/total
                    prob[ai][i]=[x * value for x in self.splitTask(F, lista, ai)]
        return prob
    
    def splitTask(self, F:dict, act:list, a:str):
        prob=[0]*2
        if(act[0] in F.keys() and act[1] in F.keys() and act[0] in F[act[1]].keys() and act[1] in F[act[0]].keys()):
            num=F[act[0]][act[1]]+F[act[1]][act[0]]
        else:
            num=0
        den=F[a][act[0]]+F[a][act[1]]+1
        prob[0]=num/den #And probabilitiy
        prob[1]=1-prob[0] #or probability
        return prob
    
    def getInfoAcum(self):
        prob=self.getInfo()
        for ai in prob.keys():
            acum=0
            for i in range(len(prob[ai])):
                if (isinstance(prob[ai][i], list)):
                    split=list()
                    for j in prob[ai][i]:
                        acum+=j
                        split.append(acum)
                    prob[ai][i]=split
                else:
                    acum+=prob[ai][i]
                    prob[ai][i]=acum
        return prob
    
    def convertList(self, dic:dict):
        for ai in dic.keys():
            i=0
            while(i<len(dic[ai])):
            #for i in range(len(dic[ai])):
                if(isinstance(dic[ai][i],list)):
                    for j in range(len(dic[ai][i])):
                        dic[ai].insert(i+j+1, dic[ai][i][j])
                    del dic[ai][i]
                i+=1
        return dic
    
    def convertRoute(self, dic:dict):#revisar
        dic=copy.deepcopy(dic)
        relation=copy.deepcopy(dic)
        for key, value in dic.items():
            if(len(value)>1):
                count=0
                for i in value:
                    if (len(i)==1):
                        count+=1
                par=len(dic[key][count:])
                dic[key].extend(dic[key][count:])
                relation[key]=[0]*count
                relation[key].extend([1]*par)
                relation[key].extend([2]*par)
            else:
                relation[key]=[0]
        return dic, relation
class AntColony(object):
    def __init__(self, dist:dict, route:dict, relation:dict, startAct:list, endAct:list):
        self.heuristic = dict(dist.copy())
        self.route = copy.deepcopy(route)
        self.relation = copy.deepcopy(relation)
        self.phero = self.startPheromone()
        self.start = startAct
        self.end = endAct
        
    def startPheromone(self, value=0.5):
        pheromone=copy.deepcopy(self.heuristic)
        for ai in pheromone.keys():
            for i in range(len(pheromone[ai])):
                if (isinstance(pheromone[ai][i], list)):
                    split=list()
                    for j in pheromone[ai][i]:
                        split.append(value)
                    pheromone[ai][i]=split
                else:
                    pheromone[ai][i]=value
        return pheromone
    
    def probability(self):
        matriz=copy.deepcopy(self.heuristic)
        suma=copy.deepcopy(self.heuristic)
        for ai in self.heuristic.keys():
            suma[ai]=0
            for i in range(len(self.heuristic[ai])):
                suma[ai]+=self.heuristic[ai][i]*self.phero[ai][i]
        for ai in self.heuristic.keys():
            prev=0
            for i in range(len(self.heuristic[ai])):
                matriz[ai][i]=self.heuristic[ai][i]*self.phero[ai][i]/suma[ai]+prev
                prev=matriz[ai][i]
        return matriz
    
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
        #trace=list(log.trace().values())[1]#Check trace
        complete=True
        for element in trace: #check element-by-element in trace
            if element in ant.keys(): #Check if element exist in ant
                for i in ant[element]:
                    ind=ant[element].index(i)
                    if(rel[element][ind]<2):#Direct & and
                        for j in i:
                            print("(%s,%s - %s )" % (element, j, check(element, j, trace)))
                            complete = complete and check(element, j, trace)
                    else:#Or
                        print("(%s,%s - %s )" % (element, i, check_or(element, i, trace)))
                        complete = complete and check_or(element,i,trace)
            else:
                complete = complete and element in log.getStartEnd()[1]
        print(complete)
    
    
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

def check_or(first,split:list, lista:list):
    result=False
    result=not(all(elem in split for elem in lista))
    if result:
        for i in split:
            if first in lista and i in lista:
                result=lista.index(first)<lista.index(i)
    return result
log=Log('log_base.csv')
activities=log.getStartEnd()
F=log.direct()
route=log.getRoute()
prob=log.getInfo()
heuristic=log.convertList(log.getInfoAcum())
convertido, relation=log.convertRoute(route)
colonia=AntColony(heuristic,convertido, relation, activities, activities[1])
AntProb=colonia.probability()
phero=colonia.startPheromone(0.5)
#colonia.choose(AntProb['b'])
sol, rel=colonia.createSolution(20)

best=[{
      'a':[['b']],
      'b':[['c','d']],
      'd':[['g','e']],
      'e':[['f']],
      'f':[['h','g']],
      'g':[['h','e']]
      },{    
      'a':[0],
      'b':[2],
      'd':[2],
      'e':[0],
      'f':[2],
      'g':[2]
      }]
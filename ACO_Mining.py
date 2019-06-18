import csv
import copy
import itertools as it
import numpy as np

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
                timestamp = row[3]
                if caseid not in log:
                    log[caseid] = []
                event = (task, user, timestamp)
                log[caseid].append(event)
                if task not in activity.keys():
                    activity[task]=counter
                    counter+=1
        
        return log, activity
    
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
        for ai in sorted(F.keys()):
            if ai not in route:
                route[ai]=list()
            count= len(F[ai].keys())
            for i in range(1,count+1):
                route[ai].extend(list(it.combinations(list(F[ai].keys()),i)))
        return route
    
    def getInfo(self):
        route=self.getRoute()
        F=self.direct()
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
    
    def convertRoute(self, dic:dict):
        for ai in dic.keys():
            for i in range(len(dic[ai])):
                if(len(dic[ai][i])>1):
                    dic[ai].insert(i+1,dic[ai][i])
                    dic[ai].insert(i+2,dic[ai][i])
                    del dic[ai][i]
        return dic
class AntColony(object):
    def __init__(self, dist:dict, route:dict, startAct:list, endAct:list):
        self.heuristic = dict(dist.copy())
        self.route = route.copy()
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
        actSE=self.start
        route=self.route #Get path
        prob=self.probability() #Get prob per route
        for p in range(quantity):
            ant=['a']
            #ant.append(lista[self.choose(lista)])
            complete=False
            while(complete==False):
                step=ant[-1]
                for i in step:
                    if i not in actSE[1]:
                        run=[''.join(x) if len(x)==1 else list(x) for x in route[i]]
                        part=route[i][self.choose(prob[i])]
                        ant.append(part)
                    else:
                        complete=True
                if len(ant)>=4:
                    complete= True
            ants[p]=ant
        return ants
                
    
    def choose(self, lista:list):
        """Get a random index form acumulative list.
        
        Args:
            param1 (list): list of probabilities
        Returns:
            int: Position choose element."""
        num=np.random.rand()
        for i in lista:
            print('value of list = %s' % str(i))
            if i>num:
                ind=lista.index(i)
                break            
        return ind



log=Log('log_base.csv')
activities=log.getStartEnd()
F=log.direct()
route=log.getRoute()
prob=log.getInfo()
heuristic=log.convertList(log.getInfoAcum())
convertido=log.convertRoute(log.convertRoute(route))
colonia=AntColony(heuristic,route, activities, activities[1])
AntProb=colonia.probability()
phero=colonia.startPheromone(0.5)
#colonia.choose(AntProb['b'])
colonia.createSolution(2)
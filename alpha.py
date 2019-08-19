import itertools
import copy
import pygraphviz as pgv
import csv
def log_import(file):
    log = dict()
    activity= dict()
    counter=0
    with open(file, 'r') as csvfile:
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

def log_print(log):
    for caseid in log:
        for (task, user, timestamp) in log[caseid]:
                print (caseid, task, user, timestamp)
                
def direct(log):
    F = dict()
    for caseid in log:
        for i in range(0, len(log[caseid])-1):
            ai = log[caseid][i][0]
            aj = log[caseid][i+1][0]
            if ai not in F:
                F[ai] = dict()
            if aj not in F[ai]:
                F[ai][aj] = 0
            F[ai][aj] += 1
    return F

def causality(F):
    C=dict()
    for ai in sorted(F.keys()):
        if ai in F.keys():                
            for aj in sorted(F[ai].keys()):
                if ai not in C:
                    C[ai]=dict()
                C[ai][aj]=1
    return C

def parallel(F):
    P=dict()
    for ai in sorted(F.keys()):
        if ai in F.keys():
            for aj in sorted(F[ai].keys()):
                if aj in F.keys():
                    if aj in F[ai].keys() and ai in F[aj].keys():
                        if ai not in P:
                            P[ai]=dict()
                        P[ai][aj]=1
    return P

def choice(F, activity):
    CH=dict()
    for ai in sorted(activity.keys()):
        for aj in sorted(activity.keys()):
            if ai not in F.keys(): #Valida el caso a1#a1 sii a1 no esta
                if ai not in CH.keys():
                    CH[ai]=dict()
                CH[ai][ai]=1
            elif aj not in F[ai].keys(): #valida la relacion a!>b
                if aj not in F.keys(): #Valida b exista dict
                    if ai not in CH.keys():
                        CH[ai]=dict.keys()
                    CH[ai][aj]=1
                elif ai not in F[aj].keys():
                    if ai not in CH.keys():
                        CH[ai]=dict()
                    CH[ai][aj]=1                   
    return CH

def start_end(log):
    st=dict()
    et=dict()
    for caseid in sorted(log.keys()):
        log[caseid].sort(key = lambda event: event[-1])
        ai= log[caseid][0][0]
        af= log[caseid][-1][0]
        if ai not in st:
            st[ai]=0
        st[ai]+=1            
        if af not in et:
            et[af]=0
        et[af]+=1
    return st, et

def get_X(activity, C, CH):
    X=set()
    trace=set()
    for i in range(len(activity.keys())-1):
        for s in itertools.combinations(activity.keys(),i+1):
            trace.add(s)
    for i in trace:
        for j in trace:
            if check(i,j,C,CH):
                X.add((i,j))            
    return X

def check(trace1, trace2, C, CH):
    testA=check_CH(trace1,CH)
    testB=check_CH(trace2,CH)
    if testA and testB:
        return check_C(trace1, trace2, C)
    return False

def check_CH(trace, CH):
    for i in trace:
        for j in trace:
            if j not in CH[i] or i not in CH[j]:
                return False
    return True

def check_C(trace1, trace2, C):
    for i in trace1:
        if i not in C.keys():
            return False
        for j in trace2:
            if j not in C[i].keys():
                return False
    return True

def get_Y(X):
    Y=copy.deepcopy(X)#evaluar los subset no sean subconjuntos de otros
    for i in X:
        A=i[0];
        B=i[1];
        for j in X:
            if set(A).issubset(j[0]) and set(B).issubset(j[1]):
                if i != j:
                    Y.discard(i)
    return Y

def plot_petri(st,et,Y,name):
    p = pgv.AGraph(strict=False, directed=True)
    p.graph_attr['rankdir'] = 'LR'
    p.node_attr['shape'] = 'box'
    for item in Y:
        for i in item[0]:
            p.add_edge(i,str(item))
            p.add_node(i, shape='box')
            p.add_node(str(item), shape='circle', label='')
        for i in item[1]:
            p.add_edge(str(item), i)
            p.add_node(i, shape='box')
    p.add_node('inicio')
    p.add_node('fin')
    for i in st:
        p.add_edge('inicio',i)
    for i in et:
        p.add_edge(i,'fin')
    p.draw(name[:-4]+'.png', prog='dot')

def test(file):
    log, activity=log_import(file)
    F=direct(log)
    C=causality(F)
    P=parallel(F)
    CH=choice(F,activity)
    st, et=start_end(log)
    X=get_X(activity,C,CH)
    Y=get_Y(X)
    plot_petri(st,et,Y,file)
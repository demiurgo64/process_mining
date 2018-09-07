import pygraphviz as pgv
import numpy as np

def dependency_matrix(M, LL, LD, MC):
    size=M.shape[0]
    DM=np.zeros((size,size))
    DLL=np.zeros((size,size))
    DLD=np.zeros((size,size))
    for i in range(size):
        for j in range(size):
            DM[j,i]=(M[i,j]-M[j,i])/(M[i,j]+M[j,i]+1) # Direct follow matrix
            if i==j:
                DM[j,i]=M[i,j]/(M[i,j]+1) #Short loop one-length
            DLL[j,i]=(LL[i,j]+LL[j,i])/(LL[i,j]+LL[j,i]+1) #Short loop two-length
            DLD[j,i]=(LD[i,j]/MC[i]) #Long distance dependency
    return DM, DLL, DLD

def causal_matrix(M):
    size=M.shape[0]
    CM=np.zeros(size,size,size)
    for k in range(0,size-1):
        for i in range(0, size-1):
            for j in range(0,size-1):
                CM[k,j,i]=(M[i,j]+M[j,i])/(M[k,i]+M[k,j]+1) #And or Or activities
    return CM

def frecuency(log,act):
    size=len(act)
    MC=np.zeros(size)
    M=np.zeros((size,size)) 
    LL=np.zeros((size,size))
    LD=np.zeros((size,size))
    trace=list()
    for caseid in log:
        trace.clear()
        for i in range(0, len(log[caseid])-1):
            ai = log[caseid][i][0]
            aj = log[caseid][i+1][0]
            MC[act[ai]]+=1
            if i == len(log[caseid])-2:
                MC[act[aj]]+=1
            M[act[aj],act[ai]]+=1
            if i<=len(log[caseid])-3:
                if ai==log[caseid][i+2][0]:
                    LL[act[ai],act[aj]]+=1
            trace.append(ai)
        num=1
        for i in trace:
            for jn in range(num, len(trace)-1):
                j=trace[jn]
                LD[act[i],act[j]]+=1
            num+=1
    return M, LL, LD, MC

def graphic_flow(DM, act, name):
    p = pgv.AGraph(strict=False, directed=True)
    p.graph_attr['rankdir'] = 'LR'
    p.node_attr['shape'] = 'box'
    p.add_node('inicio')
    p.add_node('fin')
    for i in range(0, DM.shape[0]):#i equal from Create connection with best value
        to=np.argmax(DM[i,:])
        p.add_edge(list(act.keys())[list(act.values()).index(i)], \
                   list(act.keys())[list(act.values()).index(to)])
        p.add_node(list(act.keys())[list(act.values()).index(i)], shape='box')
        p.add_node(list(act.keys())[list(act.values()).index(i)], shape='box')
        if np.all(DM[:,i]<=0):
            p.add_edge('inicio',list(act.keys())[list(act.values()).index(i)])
        if np.all(DM[i,:]<=0):
            p.add_edge(list(act.keys())[list(act.values()).index(i)], 'fin')
    p.draw(name[:-4]+'.png', prog='dot')


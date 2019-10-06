import pygraphviz as pgv

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
    
def flow(graph:dict, name:str):
    p = pgv.AGraph(strict=False, directed=True)
    p.graph_attr['rankdir'] = 'LR'
    p.node_attr['shape'] = 'box'
    for key, value in graph.items():
        p.add_node(key)
        for act in value[1]:
            p.add_node(act)
            p.add_edge(key, act)
    p.draw(name+'.png', prog='dot')

from ACO_Mining import *
import time
log=Log('hospital.csv')
#log=Log('log_base.csv')
activities=log.getStartEnd()
F=log.direct1()
route=log.getRoute(combinations=4)
heuristic=log.getInfo(combinations=4)
final={key: value for key, value in log.end.items() if value/sum(log.end.values())>0.01}
colonia=AntColony(heuristic, route, log.start, final)
trazas=list(log.trace().values())


alpha=[0.8, 1,1.2]
beta=[0.8, 1, 1.2]
tau=[0.1, 0.2, 0.3]
init=[0.1, 0.9]
sigma=[0.01, 0.001]
m=[10]


def run(alpha_i, beta_i, rho_i, tau_i, init_i, sigma_i, m_i):
    np.random.seed(30)#47
    startPhero=init_i
    colonia.phero=colonia.startPheromone(init_i)
    itera=50
    Nant=m_i
    best=0
    bestAnt=None
    Ants=list()
    initial=list(colonia.start.keys())
    endTasks=list(final.keys())
    startTime=time.process_time()
    for i in range(itera):
        for j in range(Nant):
            ants=colonia.createSolutions(initial, endTasks, alpha=alpha_i, beta=beta_i)
            result=list()
            for ant in ants:
                value=accuracity(ant, trazas, final)
                result.append(value)
                colonia.localUpdatepheromone([ant], sigma=0.01, initial=startPhero)#001
            Ants.append(ant)
        if max(result)>best:
            ind=result.index(max(result))
            best=result[ind]
            bestAnt=Ants[ind]
        if i%3==0:
            colonia.updatePheromone([bestAnt], [best], rho=rho_i, tau=tau_i)
        else:
            ind=result.index(max(result))
            colonia.updatePheromone([Ants[ind]], [result[ind]], rho=rho_i, tau=tau_i)
    
    endTime=time.process_time()
    lista=[alpha_i, beta_i, rho_i, tau_i, init_i, sigma_i, m_i, endTime-startTime, best, bestAnt]
    with open('result.csv', mode='a') as resultados:
        resultados_writter = csv.writer(resultados, delimiter=';')
        resultados_writter.writerow(lista)
    
    print('--------------------------------------')
    print(endTime-startTime)
    print('Mejor valor obtenido {}'.format(best)) 
 
        
        

for m_i in m:
    for alpha_i in alpha:
        for beta_i in beta:
            for tau_i in tau:
                for init_i in init:
                    for sigma_i in sigma:
                        run(alpha_i, beta_i, tau_i, tau_i, init_i, sigma_i, m_i)

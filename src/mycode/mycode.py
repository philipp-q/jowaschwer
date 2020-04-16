import tequila as tq
import numpy

# myscript.py needs to have this function
# this will be what orquestra executes
def run(*args, **kwargs):
    
    H = tq.QubitHamiltonian.init_from_string(string=Hstring)
    
    # in case you want to diagonalize brut force (works here since its a small system)
    eigenValues, eigenVectors = numpy.linalg.eigh(H.to_matrix())
    true_wfn = tq.QubitWaveFunction.from_array(eigenVectors[:,0])
    print("True Ground State Energy = ", eigenValues[0])
    print("True Ground State Wfn    = ", true_wfn)
    print("--------------------------\n")
    
    # An example of how to build a circuit and optimize itL Should be replaced by an ansatz that actually can solve the thing
    # thats now the 4-layer circuit Hannah said
    for i in range(4):
        U = tq.gates.Ry(angle=("a",i), target=0)
        U += tq.gates.Ry(angle=("b",i), target=1)
        U += tq.gates.Ry(angle=("c",i), target=2)
        U += tq.gates.Ry(angle=("d",i), target=3)
        U += tq.gates.Z(target=0, control=1)
        U += tq.gates.Z(target=1, control=2)
        U += tq.gates.Z(target=2, control=3)
    
    print("Circuit Ansatz is:")
    tq.draw(U)
    
    # build an objective/expectationvalue
    E = tq.ExpectationValue(H=H, U=U) # this would be the energy, for compression you need a different one
    
    ## simulate the wavefunction or the full expectationvalue for a given set of parameters/variables
    # Just to play around, not necessary
    #variables = {"a": 1.0, "b": 2.0, "c": 3.0, "d": 4.0} # just a random example, need to update for all variables now
    #wfn = tq.simulate(U, variables=variables)
    #energy = tq.simulate(E, variables=variables)
    #print("Test ansatz for variables: ", variables)
    #print("wfn    = ", wfn)
    #print("energy = ", energy)
    
    # optimize the current ansatz
    result = tq.optimizer_scipy.minimize(E, method="bfgs")
    
    # print the results and do some analysis
    print("\n------------------------")
    print("final energy: ", result.energy)
    print("final angles:\n", result.angles)
    wfn = tq.simulate(U, variables=result.angles) # wavefunction from the ansatz with optimized angles
    print("final wfn: ", )
    print("fidelity with true groundstate: ", numpy.abs(wfn.inner(true_wfn))**2)
    
    results = {"energy": result.energy, "opt_result":result}
    return result

Hstring ="""(-0.05464328026292111+0j) [] +
(-0.03612215216611762+0j) [X0] +
(0.007745843479504796+0j) [X0 X1] +
(0.020367458151550725+0j) [X0 X1 X2] +
(-0.018808202704690864+0j) [X0 X1 X2 X3] +
(-0.004622309468383025+0j) [X0 X1 X2 Z3] +
(-0.004594041204536627+0j) [X0 X1 Y2 Y3] +
(-0.03224619245886413+0j) [X0 X1 Z2] +
(0.011078986873101928+0j) [X0 X1 Z2 X3] +
(0.0029269735342627766+0j) [X0 X1 Z2 Z3] +
(0.006086156148015766+0j) [X0 X1 X3] +
(0.00963076884670983+0j) [X0 X1 Z3] +
(0.015164019915180365+0j) [X0 Y1 X2 Y3] +
(0.03224516234350878+0j) [X0 Y1 Y2] +
(-0.030075598279075563+0j) [X0 Y1 Y2 X3] +
(-0.0029220092389672706+0j) [X0 Y1 Y2 Z3] +
(0.009677449643777694+0j) [X0 Y1 Z2 Y3] +
(-0.0037939254733839233+0j) [X0 Y1 Y3] +
(0.01871671605585788+0j) [X0 Z1] +
(0.022233977805426308+0j) [X0 Z1 X2] +
(-0.009654121056965554+0j) [X0 Z1 X2 X3] +
(0.012047804697635887+0j) [X0 Z1 X2 Z3] +
(-0.021103465908406713+0j) [X0 Z1 Y2 Y3] +
(0.017315121425959226+0j) [X0 Z1 Z2] +
(-0.0338530307119166+0j) [X0 Z1 Z2 X3] +
(-0.012518021844434828+0j) [X0 Z1 Z2 Z3] +
(0.00883846669059664+0j) [X0 Z1 X3] +
(0.0008608650264746805+0j) [X0 Z1 Z3] +
(-0.010027616842073197+0j) [X0 X2] +
(-0.0032198356341980555+0j) [X0 X2 X3] +
(-0.012804860668112096+0j) [X0 X2 Z3] +
(0.009243783567722465+0j) [X0 Y2 Y3] +
(-0.005397506891011183+0j) [X0 Z2] +
(0.015007766455123521+0j) [X0 Z2 X3] +
(0.021165609117109598+0j) [X0 Z2 Z3] +
(0.013175317627257183+0j) [X0 X3] +
(-0.0054228473685851005+0j) [X0 Z3] +
(0.0053924938716080366+0j) [Y0 X1 X2 Y3] +
(-0.01670437590131352+0j) [Y0 X1 Y2] +
(0.015737752772868964+0j) [Y0 X1 Y2 X3] +
(0.013100213450022742+0j) [Y0 X1 Y2 Z3] +
(-0.0028710260455741213+0j) [Y0 X1 Z2 Y3] +
(-0.0013245899572199335+0j) [Y0 X1 Y3] +
(-0.0033940728899871076+0j) [Y0 Y1] +
(0.0020577439080072426+0j) [Y0 Y1 X2] +
(-0.004612753422315559+0j) [Y0 Y1 X2 X3] +
(-0.008634385715449498+0j) [Y0 Y1 X2 Z3] +
(0.011847917889693029+0j) [Y0 Y1 Y2 Y3] +
(-0.01067720351487838+0j) [Y0 Y1 Z2] +
(0.030028765520755115+0j) [Y0 Y1 Z2 X3] +
(0.008569577714545345+0j) [Y0 Y1 Z2 Z3] +
(-0.019513967298769152+0j) [Y0 Y1 X3] +
(-0.003025128331033952+0j) [Y0 Y1 Z3] +
(0.002869899410708089+0j) [Y0 Z1 X2 Y3] +
(0.013619017817843334+0j) [Y0 Z1 Y2] +
(-0.018622218511598603+0j) [Y0 Z1 Y2 X3] +
(-0.008789983840204506+0j) [Y0 Z1 Y2 Z3] +
(0.01608300915106067+0j) [Y0 Z1 Z2 Y3] +
(-0.009901067319119472+0j) [Y0 Z1 Y3] +
(0.005607484664318001+0j) [Y0 X2 Y3] +
(-0.011525154843691524+0j) [Y0 Y2] +
(0.014138756048420607+0j) [Y0 Y2 X3] +
(0.014902042792056336+0j) [Y0 Y2 Z3] +
(-0.0030274230730280346+0j) [Y0 Z2 Y3] +
(-0.0028174892829690313+0j) [Y0 Y3] +
(-0.009569376426081319+0j) [Z0] +
(0.02505602786355032+0j) [Z0 X1] +
(-0.002816638768832116+0j) [Z0 X1 X2] +
(0.008512792246082153+0j) [Z0 X1 X2 X3] +
(0.019096050595398695+0j) [Z0 X1 X2 Z3] +
(-0.009785583377682337+0j) [Z0 X1 Y2 Y3] +
(-0.016837834258841045+0j) [Z0 X1 Z2] +
(-0.0028262082771420846+0j) [Z0 X1 Z2 X3] +
(-0.0049266909027929845+0j) [Z0 X1 Z2 Z3] +
(-0.001972121269953078+0j) [Z0 X1 X3] +
(-0.0005541798580819249+0j) [Z0 X1 Z3] +
(0.007127105196336308+0j) [Z0 Y1 X2 Y3] +
(0.004530749548537081+0j) [Z0 Y1 Y2] +
(0.003593137218311999+0j) [Z0 Y1 Y2 X3] +
(0.009392402281021908+0j) [Z0 Y1 Y2 Z3] +
(-0.0113103280246576+0j) [Z0 Y1 Z2 Y3] +
(0.012048104529648045+0j) [Z0 Y1 Y3] +
(0.014223635553094098+0j) [Z0 Z1] +
(0.017714550361759878+0j) [Z0 Z1 X2] +
(-0.008102905523380187+0j) [Z0 Z1 X2 X3] +
(0.00013018108362979443+0j) [Z0 Z1 X2 Z3] +
(-0.00017379220443200917+0j) [Z0 Z1 Y2 Y3] +
(0.001830211530045156+0j) [Z0 Z1 Z2] +
(0.010185015541188+0j) [Z0 Z1 Z2 X3] +
(0.002006764115379636+0j) [Z0 Z1 Z2 Z3] +
(-0.019531039480124503+0j) [Z0 Z1 X3] +
(-0.0015860252331301881+0j) [Z0 Z1 Z3] +
(-0.029847487960520957+0j) [Z0 X2] +
(0.017029840834927704+0j) [Z0 X2 X3] +
(0.009558259066827793+0j) [Z0 X2 Z3] +
(0.0003973052832248849+0j) [Z0 Y2 Y3] +
(0.0002787831999546806+0j) [Z0 Z2] +
(0.005877501755546171+0j) [Z0 Z2 X3] +
(0.007300989413876149+0j) [Z0 Z2 Z3] +
(-0.0007006042999753654+0j) [Z0 X3] +
(-0.012329294479121834+0j) [Z0 Z3] +
(0.0016379603381920323+0j) [X1] +
(0.027750090607270798+0j) [X1 X2] +
(-0.017018102120470256+0j) [X1 X2 X3] +
(-0.004716283495971816+0j) [X1 X2 Z3] +
(-0.008881297186148766+0j) [X1 Y2 Y3] +
(-0.023144877971068237+0j) [X1 Z2] +
(0.004883230828813822+0j) [X1 Z2 X3] +
(-0.008206901361187319+0j) [X1 Z2 Z3] +
(0.009677822765995683+0j) [X1 X3] +
(0.02092257800719527+0j) [X1 Z3] +
(0.018155607940764824+0j) [Y1 X2 Y3] +
(0.029099409915102945+0j) [Y1 Y2] +
(-0.020417546068991106+0j) [Y1 Y2 X3] +
(0.0032910536892268873+0j) [Y1 Y2 Z3] +
(0.0012079662975533786+0j) [Y1 Z2 Y3] +
(0.002466710169468431+0j) [Y1 Y3] +
(0.02075604243926646+0j) [Z1] +
(0.029272289868540444+0j) [Z1 X2] +
(-0.01577631260633405+0j) [Z1 X2 X3] +
(0.00872796551849902+0j) [Z1 X2 Z3] +
(-0.016066270619490775+0j) [Z1 Y2 Y3] +
(0.016575847973424096+0j) [Z1 Z2] +
(-0.0211683399367871+0j) [Z1 Z2 X3] +
(-0.009442821618527967+0j) [Z1 Z2 Z3] +
(-0.002888098226929484+0j) [Z1 X3] +
(0.00030310480400382397+0j) [Z1 Z3] +
(-0.012773887515918292+0j) [X2] +
(0.00019369169282781136+0j) [X2 X3] +
(-0.016960161443043336+0j) [X2 Z3] +
(0.008392195293335748+0j) [Y2 Y3] +
(0.008591351383900566+0j) [Z2] +
(0.013162563155263995+0j) [Z2 X3] +
(0.013632150169624399+0j) [Z2 Z3] +
(0.016118362305797117+0j) [X3] +
(0.0016557416878873815+0j) [Z3]"""

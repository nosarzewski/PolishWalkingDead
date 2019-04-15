from zombie_epidemy import *

# load data
with open("./map_utils/map_values.out", "rb") as mv, open("./map_utils/map_colored.out", "rb") as mc:
    map_colors = np.load(mc)
    map_values = np.load(mv)

# alfa - probability of a zombie being killed by a human
# beta - probability of a zombie infecting encountered human
# gamma - probabilty of a human being eaten by a zombie
# CHI - number of iterations which each zombie can survive without eating a human

# setup analysis information
N_VALUES = 1
ALFA = 0.9
# ALFA_FROM  = 0.5
# ALFA_TO    = 0.99
BETA = 0.2
# BETA_FROM  = 0.1
# BETA_TO    = 0.4
# GAMMA cannot be lower than BETA
GAMMA = 0.6
# GAMMA_FROM = 0.2
# GAMMA_TO   = 0.8
CHI = 10
# CHI_FROM  = 10
# CHI_TO    = 1000
# results=[]

# run simulation
for i in range(1):
    poland = country(ALFA, BETA, GAMMA, CHI, map_values, map_colors)
    res = poland.run()
    name = "a%sb%sg%sp%ssym%s.csv" % (ALFA, BETA, GAMMA, CHI, i)
    res.to_csv(name)

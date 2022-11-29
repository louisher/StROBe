import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


strobeDir = os.path.dirname(os.path.realpath(__file__)) # get path where this file is (StROBe path)
sys.path.append(os.path.join(strobeDir, 'Corpus'))

import Corpus.feeder as fee
import Corpus.residential as res

os.chdir(os.path.join(strobeDir, 'Corpus')) # make Corpus the current directory

# Create and simulate a single household, with given type of members, and given year
family = res.Household("Example household", members=['FTE','FTE', "School", "School"])
family.simulate(year=2020, ndays=365)

family.__dict__ # list all elements of family for inspection

print(family.members)

# Define variables to calculate metabolic heat gains. Since only thermal comfort is studied, only sensible heat is calculated (no latent heat is considered here).
# Values taken from ASHRAE Handbook - Fundamentals (2009), body surface of 1.8 m^2 is assumed
# seated (quiet)=60 (35%), standing (relaxed)=70 (35%), walking (slow)=115 (10%), cooking=95-115 (10%), housecleaning=115-200 (10%)
QMetActivePerA = 80
QMetSleepPerA = 40
# based on https://doi.org/10.1016/j.dib.2017.10.036 ! For U12, no occupancy is generated, so it is not taken into account for metabolic heat gains
A = {'U12': 0.9, 'School': 1.68, 'Unemployed': 1.8, 'PTE': 1.8, 'FTE': 1.8, 'Retired': 1.8}

Occ_profiles = np.array(family.occ)
nb_mem = Occ_profiles.shape[0] #aantal members
nb_val = Occ_profiles.shape[1] #aantal datapunten (voor occupancy profiles is dit om de 10min)
radFra = 0.5


QConMet_day = np.zeros((nb_mem, nb_val))
QRadMet_day = np.zeros((nb_mem, nb_val))
QConMet_night = np.zeros((nb_mem, nb_val))
QRadMet_night = np.zeros((nb_mem, nb_val))

for member in range(0,len(family.members)):
    QConMet_day[member, :] = ((Occ_profiles[member, :] == 1) *
                              QMetActivePerA * A[family.members[member]] * (1 - radFra))
    QRadMet_day[member, :] = ((Occ_profiles[member, :] == 1) *
                              QMetActivePerA * A[family.members[member]] * (radFra))
    QConMet_night[member, :] = ((Occ_profiles[member, :] == 2) *
                              QMetSleepPerA * A[family.members[member]] * (1 - radFra))
    QRadMet_night[member, :] = ((Occ_profiles[member, :] == 2) *
                                QMetSleepPerA * A[family.members[member]] * (radFra))

#take the sum of all members in one profile
QConMet_day = sum(QConMet_day)
QRadMet_day = sum(QRadMet_day)
QConMet_night = sum(QConMet_night)
QRadMet_night = sum(QRadMet_night)

prefix = "House3_"  # prefix to put in front of text files
names = ["QCon", "QRad", "Tset", "QConMet_day", "QConMet_night", "QRadMet_day", "QRadMet_night"]
Results_name = [prefix + names[i] + ".txt" for i in range(0, len(names))]
Results_name_opt = [prefix + names[i] + "Opt" + ".txt" for i in range(0, len(names))]

Results = [family.QCon, family.QRad, family.sh_day, QConMet_day, QConMet_night, QRadMet_day, QRadMet_night]

os.chdir(os.path.join(strobeDir, 'Profiles')) # make Profiles the current directory$


for res in range(0,len(Results_name)):
    if len(Results[res]) == 525601:
    #omzetten van Qcon en Qrad van tijdstap van 1min naar tijdstap van 10min
        Results[res] = 0.1*np.add.reduceat(Results[res], np.arange(0, len(Results[res]), 10))

    time_step = 600
    time = np.arange(0,3600*24*365 + time_step,time_step)
    combo = np.stack((time,Results[res]),axis=1)
    np.savetxt(Results_name[res], combo, delimiter='\t', fmt='%f')

    line = "double data("+ str(len(Results[res]))+",2)"

    with open(Results_name[res],'r+') as file:
        file_data = file.read()
        file.seek(0,0)
        file.write("#1"+ "\n")
        file.write(line+ '\n' + file_data)

time_step_opt = 900  #control interval of 15min
time_opt = np.arange(0, 3600*24*365+time_step_opt, time_step_opt)
Results_opt = np.array([np.zeros(35041) for i in range(0, len(Results))])

for res in range(0, len(Results)):
    #first element is taken directly, other values are averaged
    Results_opt[res][0] = Results[res][0]
    for i in range(1, len(Results_opt[res])):
        k = i-1
        Results_opt[res][i] = (1/3)*Results[res][(k + k//2 + 1 - (k%2))+1] + (2/3)*Results[res][(k + (k//2) + (k%2))+1]



    combo = np.stack((time_opt, Results_opt[res]), axis=1)
    np.savetxt(Results_name_opt[res], combo, delimiter='\t', fmt='%f')

    line = "double data(" + str(len(Results_opt[res])) + ",2)"

    with open(Results_name_opt[res], 'r+') as file:
            file_data = file.read()
            file.seek(0, 0)
            file.write("#1" + "\n")
            file.write(line + '\n' + file_data)

# for res in range(0, len(Results_name_opt)):
#     Results_opt[res] = (1/6)*np.add.reduceat(Results[res], np.arange(0, len(Results_opt[res]), 6))
#
#     combo = np.stack((time_opt, Results_opt[res]), axis=1)
#     np.savetxt(Results_name_opt[res], combo, delimiter='\t', fmt='%f')
#
#     line = "double data(" + str(len(Results[res])) + ",2)"
#
#     with open(Results_name_opt[res], 'r+') as file:
#         file_data = file.read()
#         file.seek(0, 0)
#         file.write("#1" + "\n")
#         file.write(line + '\n' + file_data)


#
# ## Strobe profielen voor optimalisatie --> control interval of 1h
#
# time_step_opt = 3600  # number of seconds in control interval
# time_opt = np.arange(0, 3600*24*365 + time_step_opt, time_step_opt)
#
# Results_opt = Results  # must be decleared here otherwise timestep of Qrad en Qcon is still 1 minute
#
# for res in range(0, len(Results_name_opt)):
#     Results_opt[res] = (1/6)*np.add.reduceat(Results[res], np.arange(0, len(Results_opt[res]), 6))
#
#     combo = np.stack((time_opt, Results_opt[res]), axis=1)
#     np.savetxt(Results_name_opt[res], combo, delimiter='\t', fmt='%f')
#
#     line = "double data(" + str(len(Results[res])) + ",2)"
#
#     with open(Results_name_opt[res], 'r+') as file:
#         file_data = file.read()
#         file.seek(0, 0)
#         file.write("#1" + "\n")
#         file.write(line + '\n' + file_data)




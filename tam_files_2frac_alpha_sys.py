from shutil import copyfile
import os
from random import random as rand
import numpy as np
import pandas as pd
from subprocess import call
import time
import datetime

def anisotropic_parameters(dn1,dt1,alpha1, dn2,dt2,alpha2):
    return "lh= '0 (base)' ls= 65536 lac= 0.000000 las= 0.000000 laa= 0.000000 lab=0.000000 tf=0.000000 tg=0.000000 tf1={:.6f} tf2={:.6f} tf3=0.000000 tdn1={:.6f} tdn2={:.6f} tdn3=0.000000 tdt1={:.6f} tdt2={:.6f} tdt3=0.000000 tfb=2\n".format(alpha1,alpha2,dn1,dn2,dt1,dt2)

def copy_files(dir):
    # tgr, tgr.cr0, tgr.cr2 files
    for word in ['Gath']:
        for form in ['tgr','tgr.cr0','tgr.cr2']:
            str = 'model+{0}NP.{1}'.format(word,form)
            file = os.path.join(dir,str)
            temp_file = os.path.join(cwd,str)
            copyfile(temp_file, file)
            os.remove(temp_file)

    # SEGY files
    for ch in ['C','X','Z']:
        str = 'model+GathNP-{}.sgy'.format(ch)
        file = os.path.join(dir,str)
        temp_file = os.path.join(cwd,str)
        copyfile(temp_file, file)
        os.remove(temp_file)

    # the rest of the files
    #file = os.path.join(dir,'model+GathNP-Z.sgy.cr0')
    #copyfile(os.path.join(cwd,'model+GathNP-Z.sgy.cr0'), file)
    file = os.path.join(dir,'model+WaveNP-1.tgr')
    copyfile(os.path.join(cwd,'model+WaveNP-1.tgr'), file)
    os.remove(os.path.join(cwd,'model+WaveNP-1.tgr'))

print('Enter the number of generated models:', end=' ')
N = int(input())
print('Enter the first model number:',end=' ')
K = int(input())

start_time = datetime.datetime.now()

cwd = os.getcwd()
pattern = os.path.join(cwd,'pattern\\pattern2.tam')
runtask_original = os.path.join(cwd,'runtask_original2.ini')
runtask = os.path.join(cwd,'runtask.ini')
copyfile(runtask_original, runtask)
data = np.empty([6]) # массив, в к-м будут храниться данные по всем моделям

######################################
# добавить чтение data из файла .csv #
######################################

for i in range(K,N+1):
    dir = os.path.join(cwd,"model_"+str(i))
    if not os.path.exists(dir):
        os.mkdir(dir)
    #model = os.path.join(dir,'model1.tam')
    model = os.path.join(cwd,'model1.tam')
    copyfile(pattern, model)

    # записываем случайные параметры в файл
    f = open(model, 'r')    # pass an appropriate path of the required file
    lines = f.readlines()
    n = 46
    # dn, dt generation from Bakulin Grechka Tsvankin article "Estimation of fracture parameters from reflection seismic data -- Part I"
    Vs = 2750
    Vp = 5000
    g = (Vs**2)/(Vp**2)
    
    e1 = 0.1*rand()
    dn1 = 4*e1/(3*g*(1-g))
    if dn1 < 0.1:
        dt1 = 16*0.1*rand()/(3*(3-2*g))
    else:
        dt1 = 16*e1/(3*(3-2*g))
    alpha1 = 15.0*rand()

    e2 = 0.1*rand()
    dn2 = 4*e2/(3*g*(1-g))
    if dn2 < 0.1:
        dt2 = 16*0.1*rand()/(3*(3-2*g))
    else:
        dt2 = 16*e2/(3*(3-2*g))
    alpha2 = (alpha1 - 90) + (20.0*rand() - 10)
    if alpha2 < -90.0:
        alpha2 = 180 - abs(alpha2)
    
    lines[n-1] = anisotropic_parameters(dn1,dt1,alpha1, dn2,dt2,alpha2)    # n is the line number you want to edit; subtract 1 as indexing of list starts from 0
    f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.
    f = open(model, 'w')
    f.writelines(lines)
    # do the remaining operations on the file
    f.close()

    copyfile(model, os.path.join(dir,'model1.tam'))

    frac_params = np.array([dn1,dt1,alpha1,dn2,dt2,alpha2])
    data = np.vstack((data,frac_params)) # записываем осреднённые параметры в массив

    """
    # указываем путь к tam-файлу в runtask.ini:
    f = open(runtask, 'r')    # pass an appropriate path of the required file
    lines_runtask = f.readlines()
    #for line in lines_runtask:
    #    print(line)
    n = 4
    #"Model Name=model_" + str(i) + "\\model.tam\n"
    lines_runtask[n-1] = "Model Name=model.tam\n"   # n is the line number you want to edit; subtract 1 as indexing of list starts from 0
    f.close()   # close the file and reopen in write mode to enable writing to file; you can also open in append mode and use "seek", but you will have some unwanted old data if the new data is shorter in length.
    #for line in lines_runtask:
    #    print(line)
    f = open(runtask, 'w')
    f.writelines(lines_runtask)
    # do the remaining operations on the file
    f.close()
    """

    # запускаем вычислительный модуль
    log_file = open(os.path.join(dir,'log.txt'),'w')
    call([os.path.join(cwd,"Tesseral2D_Win64.exe")], universal_newlines=True, stdout=log_file)
    log_file.close()

    # копируем выходные файлы в папку соответствующей модели
    copy_files(dir)
    # удаляем model1.tam (на всякий пожарный)
    os.remove(os.path.join(cwd,'model1.tam'))


# записываем параметры в csv-файл
df = pd.DataFrame(data[1:])
df.to_csv(str(cwd) + '\\frac_params_2frac_alpha_sys.csv',index=None, header=['dn1','dt1','alpha1','dn2','dt2','alpha2'])

# прошедшее время
sec = (datetime.datetime.now() - start_time).total_seconds()
print(sec,'sec')
print('Time elapsed:',int(sec/60),'min',sec%60,'sec')



import numpy as np

def delta(age,bp=1000):
    return (np.exp(-age/8033)*np.exp(-bp/8267)-1)*1000

def fm(age,bp=1000):
    return np.exp(-age/8033)

age = 5000
bp = 5000
agvediff = 40
deltadelta = (delta(age,bp=bp) - delta(age+agvediff,bp=bp))/delta(age,bp=bp)
deltafm = (fm(age) - fm(age+agvediff))/fm(age)*1000
print(deltadelta)
print(deltafm)
age = 200
bp = 200
deltadelta = (delta(age,bp=bp) - delta(age+agvediff,bp=bp))/delta(age,bp=bp)
deltafm = (fm(age) - fm(age+agvediff))/fm(age)*1000

print(deltadelta)
print(deltafm)

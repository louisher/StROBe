import numpy as np
A = np.array([1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0])
C = np.zeros(3)
C[0] = A[1]
print(C)
B = np.split(A,3)

for k in range(0,8):
    print(k + (k//2) + (k%2))
import numpy as np
import matplotlib.pyplot as plt

def Weighted_Jacobi(v, f, n, niter, omega):
    v2 = v.copy()
    a = 0.5 * omega
    b = 1.0 - omega
    c = a    
    d = a
    for iter in range(0, niter):
        for i in range(1, n):
            v2[i] = a * v[i-1] + b * v[i] + c * v[i+1] + d * f[i]
        v = v2.copy()
    return v
    
def CalcResidual(v, f, n):
    v2 = v.copy()
    a = -1.0
    b = 2.0
    c = -1.0
    for i in range(1, n):
        av = a * v[i-1] +  b * v[i] + c * v[i+1]
        v2[i] = f[i] - av
    return v2
    
def Restrict(rh, nc):
    r2h = np.zeros( nc + 1 )
    for i in range(1, nc):
        r2h[i] = rh[2*i]
    return r2h

def Interpolate(e2h, nc):
    eh = np.zeros( 2*nc + 1 )
    for i in range(1, nc):
        eh[2*i] = e2h[i]
        eh[2*i+1] = 0.5 * ( e2h[i] + e2h[i+1] )
    return eh
    
def Correct(vh, eh, n):
    vh_new = np.zeros( n + 1 )
    for i in range(1, n):
        vh_new[i] = vh[i] + eh[i]
    return vh_new
    
def VectorNorm(vh, n): 
    return np.max(np.abs(vh))
    
def IsCoarseGrid(level, nCoarse):
    return level == nCoarse
    
def VCycle(vh, fh, n, level, nCoarse, omega):
    nIter1 = 3
    nIter2 = 3
    vh  = Weighted_Jacobi(vh, fh, n, nIter1, omega)
    if not IsCoarseGrid( level, nCoarse ):
        vh  = Weighted_Jacobi(vh, fh, n, nIter2, omega)
        rh  = CalcResidual(vh, fh, n)
        f2h = Restrict( rh, int(n/2) )
        v2h = np.zeros( int(n/2) + 1 )
        v2h = VCycle( v2h, f2h, int(n/2), level + 1, nCoarse, omega )
        eh  = Interpolate( v2h, int(n/2) )
        vh  = Correct(vh, eh, n)
    
    vh  = Weighted_Jacobi(vh, fh, n, nIter2, omega)
    return vh
    
def GetFmgError( n, rr, nLevel, nCoarse, omega, vIter ):
    m1 = int( np.power(2,nLevel) )
    nc = int( n / m1 )
    exh = np.zeros( nc + 1 )
    for i in range(0, nLevel+1):
        kLevel = nLevel - i
        km = int( np.power(2,kLevel) )
        kPoint = int(n/km)
        
        if i != 0:
            exh = Interpolate( exh, int(kPoint/2) )
            
        for it in range(0, vIter):
            exh = VCycle( exh, rr[kLevel], kPoint, kLevel, nCoarse, omega )

    return exh
    
def CalcResidualList(vh, fh, n, nLevel):
    rr = []
    rh  = CalcResidual(vh, fh, n)
    rr.append( rh )
    m = n
    for i in range(0, nLevel):
        m = int(m/2)
        r2h = Restrict( rh, m )
        rr.append( r2h )
        rh = r2h.copy()
    return rr

def FMG_VCycle_Recursive(vh, fh, n, nLevel, nCoarse, omega, vIter):
    resList = CalcResidualList(vh, fh, n, nLevel)
    
    eh = GetFmgError( n, resList, nLevel, nCoarse, omega, vIter )
    vh = Correct(vh, eh, n)
    return vh

def basic_visual_setup(ax):    
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')
    ax.set_xlabel("X")
    ax.set_ylabel("Y",rotation='horizontal')
    ax.xaxis.set_label_coords(1.02, 0.02)
    ax.yaxis.set_label_coords(0.0, 1.0)
    ax.set_ylim(-1.0, 1.0)
    return


n = 64
m = int(n/2)
dx = 1.0 / n
h = dx

fh = np.zeros( n + 1 )

x = np.zeros( n + 1 )
y = np.zeros( n + 1 )

for i in range(0, n+1):
    x[i] = i * h
    y16m = np.sin( i * 16 * np.pi / n )
    y40m = np.sin( i * 40 * np.pi / n )
    y[i] = 0.5 * ( y16m + y40m )
    
omega = 2.0/3.0

vh = y.copy()

nCycle = 1000

res = np.zeros( nCycle + 1 )
res[0] = VectorNorm( vh, n )

nLevel = 4
nCoarse = nLevel
vIter = 1

for iCycle in range(0, nCycle):
    vh = FMG_VCycle_Recursive(vh, fh, n, nLevel, nCoarse, omega, vIter)
    res[iCycle+1] = VectorNorm( vh, n )
    
    
print("res=\n",res)

fig = plt.figure('OneFLOW-CFD Solver Full Multigrid V-Cycle Scheme', figsize=(8, 6), dpi=100)

ax = fig.add_subplot(1,3,1)
basic_visual_setup( ax )
mycolor  = 'blue'
mymarker = 'none'
mylabel  = 'initial field'
ax.plot(x,y,color='black',linewidth=1,marker=mymarker,markerfacecolor='none',label=mylabel)

ax = fig.add_subplot(1,3,2)
basic_visual_setup( ax )

mycolor  = 'blue'
mymarker = 'o'
mylabel  = 'coarse grid'
ax.plot(x,y,color='black',linewidth=1,linestyle='dotted',marker='none',markerfacecolor='none',label=mylabel)
ax.plot(x,vh,color=mycolor,linewidth=2,marker='none',markerfacecolor='none',label=mylabel)

ax = fig.add_subplot(1,3,3)
ii = np.linspace(0, nCycle, nCycle + 1)
ax.set_yscale("log", base=10)
ax.plot(ii,res,color='black',linewidth=2,linestyle='solid',marker='none',markerfacecolor='none',label='res')

fig.tight_layout()
plt.show()

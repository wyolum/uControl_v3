from uControl import *
from pylab import *
import util

def load(fn):
    data = pickle.load(open(fn))
    return data['hirate']

def plot_hirate(hirate):
    times = hirate[:,0]
    gage = hirate[:,1]
    flow = hirate[:,2]
    ax = pylab.subplot(211)
    ylabel('Gage mmHG')
    pylab.plot(times, gage)
    pylab.subplot(212)
    xlabel('Time sec.')
    ylabel('Flow')
    pylab.plot(times, flow)

if __name__ == '__main__':
    import sys
    usage = 'python plot_uc.py [ucontrol.pkl]'
    if len(sys.argv) > 1:
        fn = sys.argv[1]
        hirate = load(fn)
        plot_hirate(hirate)
        show()
    else:
        raise Exception(usage)
    

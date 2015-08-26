from uControl import *
import util

hirate = pickle.load(open("hirate.pkl"))

pylab.plot(hirate[:,2])
pylab.show()

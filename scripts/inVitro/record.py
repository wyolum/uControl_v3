from uControl import *
import util

def test():
    print 'here we go'
    uc = uControl()
    try:
        print 'uc.cuff_pressure', uc.cuff_pressure
        uc.record(True)
        start = time.time()
        print "recording..."
        try:
            while 1:
                print 'uc.cuff_pressure', uc.cuff_pressure
                serial_interact()
        except KeyboardInterrupt:
            pass
        uc.record(False)
        
        print 'len(uc.hirate)', len(uc.hirate)
        hirate = array(uc.hirate)
        if len(uc.hirate) > 0:
            pfn = 'hirate.pkl'
            pickle.dump(hirate, open(pfn, 'w'))
            print 'wrote', pfn
        print 'done'
    finally:
        # uc.deflate(50)
        send_cmd(pump_rate=False, valve=True)
        time.sleep(2)
        send_cmd(pump_rate=False, valve=False, interval=0)



if __name__ == '__main__':
    test()

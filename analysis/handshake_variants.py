import serial, time
from crccheck.crc import CrcX25
def crc(d): return (CrcX25.calc(d)&0xffff).to_bytes(2,'little')
base=b"\x26\x00\x00\x25\xa7\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00"
frameA=base+crc(base)+b"\x7e"
frameB=b"\x7e"+frameA
variants=[('A dtr0 rts0',frameA,False,False),('B lead7e dtr0 rts0',frameB,False,False),('C dtr1 rts1',frameA,True,True),('D lead7e dtr1 rts1',frameB,True,True)]
for name,frame,dtr,rts in variants:
    try:
        p=serial.Serial('COM8',9600,timeout=1)
        p.dtr=dtr; p.rts=rts
        p.reset_input_buffer()
        p.write(frame); p.flush()
        resp=p.read(256)
        print(name,'TX',frame.hex(),'RX',resp.hex(),'MATCH',b"\x7e\x26\x00\x00\x25\xa7" in resp)
        p.close()
    except Exception as e:
        print(name,'ERR',e)
    time.sleep(0.5)

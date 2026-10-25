import serial, time
from crccheck.crc import CrcX25
def crc(d): return (CrcX25.calc(d)&0xffff).to_bytes(2,'little')
base=b"\x26\x00\x00\x25\xa7\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00"
frameA=base+crc(base)+b"\x7e"
frameB=b"\x7e"+frameA
for port in ['COM5','COM8']:
  for name,frame,dtr,rts in [('A',frameA,False,False),('B',frameB,False,False),('C',frameA,True,True),('D',frameB,True,True)]:
    try:
      p=serial.Serial(port,9600,timeout=1); p.dtr=dtr; p.rts=rts; p.reset_input_buffer()
      p.write(frame); p.flush(); resp=p.read(256); p.close()
      print(port,name,'RX',resp.hex(),'MATCH',b"\x7e\x26\x00\x00\x25\xa7" in resp)
    except Exception as e: print(port,name,'ERR',e)
    time.sleep(0.3)

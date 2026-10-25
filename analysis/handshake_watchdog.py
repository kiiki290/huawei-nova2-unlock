import os, threading, time, serial
from crccheck.crc import CrcX25
def watch(): os._exit(3)
threading.Timer(6, watch).start()
def crc(d): return (CrcX25.calc(d)&0xffff).to_bytes(2,'little')
port=os.environ.get('TESTCOM','COM8')
base=b"\x26\x00\x00\x25\xa7\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00"
frame=base+crc(base)+b"\x7e"
print('opening',port,flush=True)
p=serial.Serial(port,9600,timeout=0.8)
print('opened',flush=True)
p.reset_input_buffer(); p.write(frame); p.flush(); time.sleep(0.3)
resp=p.read(128)
print('RX',resp.hex(),'MATCH',b"\x7e\x26\x00\x00\x25\xa7" in resp,flush=True)
p.close()

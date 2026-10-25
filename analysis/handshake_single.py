import serial, time
from crccheck.crc import CrcX25
def crc(d): return (CrcX25.calc(d)&0xffff).to_bytes(2,'little')
base=b"\x26\x00\x00\x25\xa7\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00"
frameA=base+crc(base)+b"\x7e"
for port in ['COM8','COM5']:
  try:
    p=serial.Serial(port,9600,timeout=0.5)
    p.reset_input_buffer()
    p.write(frameA); p.flush()
    time.sleep(0.3)
    resp=p.read(64)
    print(port,'RX',resp.hex(),'MATCH',b"\x7e\x26\x00\x00\x25\xa7" in resp)
    p.close()
  except Exception as e:
    print(port,'ERR',type(e).__name__,str(e)[:200])

import serial, time
from crccheck.crc import CrcX25
def crc(d): return (CrcX25.calc(d)&0xffff).to_bytes(2,'little')
port='COM8'
try:
    p=serial.Serial(port,9600,timeout=2)
except Exception as e:
    print('OPEN ERR',e); raise SystemExit
cmd=b"\x26\x00\x00\x25\xa7\x00\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00"
frame=cmd+crc(cmd)+b"\x7e"
print('TX',frame.hex())
p.write(frame); p.flush()
time.sleep(0.5)
resp=p.read(256)
print('RX',resp.hex())
print('HANDSHAKE OK' if b"\x7e\x26\x00\x00\x25\xa7" in resp else 'HANDSHAKE NO MATCH')
p.close()

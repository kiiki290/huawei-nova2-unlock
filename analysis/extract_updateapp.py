import zipfile, os, time
z=zipfile.ZipFile(r'tools/firmware/update-377.zip')
out=r'tools/firmware/377/UPDATE.APP'
os.makedirs(os.path.dirname(out), exist_ok=True)
with z.open('UPDATE.APP') as src, open(out,'wb') as dst:
    total=0; last=time.time()
    while True:
        b=src.read(8*1024*1024)
        if not b: break
        dst.write(b); total+=len(b)
        if time.time()-last>2:
            print(f'{total/1e9:.2f} GB'); last=time.time()
print('DONE', total)

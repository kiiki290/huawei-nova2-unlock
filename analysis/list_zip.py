import zipfile
p=r'tools/firmware/update-377.zip'
z=zipfile.ZipFile(p)
for i in z.infolist():
    print(f"{i.filename}\t{i.file_size}")

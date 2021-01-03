from astropy.io import fits
import os
import json

root = "C:/Users/ole/OneDrive/Desktop/Jufo/Daten"
folders = ["/20200116/", "/20201207/reduced/", "/20201208/Azimut_h23°(Airmass=2,5)_reduced/", "/20201208/Azimut_h45°(Airmass=1,5)_reduced/", 
           "/20201208/Azimut_h76°(Airmass=1,03)_reduced/", "/20201216/h_reduced/"]

files = {}

for i in folders:
    for file in os.listdir(root+i):
        if file.lower().endswith(".fits") or file.lower().endswith(".fit") and "NO-Guiding" in file:
            f = fits.open(root+i+file)
            head = f[0].header
            try:
                rdec = head["OBJCTDEC"]
                deg, min, sec = map(float, rdec.split(" "))
                declination = deg + min / 60 + sec / 3600
                files[root+i+file] = (declination)
            except KeyError:
                continue

with open(root+"/filedecs.json", "w") as f:
    json.dump(files, f)

print(sorted(files.values()))
print(*[(i, files[i]) for i in files if 70 < files[i]], sep="\n")
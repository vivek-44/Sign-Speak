import h5py

try:
    f = h5py.File("models/ISLResNet50V2.h5", "r")
    print("VALID HDF5 FILE")
    f.close()
except Exception as e:
    print("NOT A VALID HDF5 FILE")
    print(e)

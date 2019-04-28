import pydicom
import glob
import os
import numpy as np
import sys
import nibabel as nib
import operator


# Sort DCMs with attribution: Instance Number
def sortDCM(dcm_files):
    datadic = {}
    for (i, file) in enumerate(dcm_files):
        ds = pydicom.dcmread(file)
        order = ds.InstanceNumber
        datadic[file] = order
    sortDic = sorted(datadic.items(), key=operator.itemgetter(1))
    dcm_files = []
    for i in sortDic:
        dcm_files.append(i[0])
    return dcm_files


# data shape:  (number, resolution, resolution)
def ReadData(dcm_folder):
    files = sorted(glob.glob(os.path.join(dcm_folder, "*.dcm")))
    dcm_files = sortDCM(files)
    datas=[]
    for (i, dcm) in enumerate(dcm_files):
        ds = pydicom.dcmread(dcm)
        data = ds.pixel_array
        datas.append(data)
    data = np.array(datas)
    return data



def d2n(dcm_folder, sliceNum, nifti, meta_folder):
    dcm_files = sorted(glob.glob(os.path.join(dcm_folder, "*.dcm")))
    for(i, file) in enumerate(dcm_files):
        fileName = os.path.split(file)[1]
        if not os.path.exists(meta_folder):
            os.makedirs(meta_folder)
        ds = pydicom.dcmread(file)
        empty = bytes(0)
        ds.PixelData = empty
        ds.Rows = 0
        ds.Columns = 0
        path = os.path.join(meta_folder, fileName)
        ds.save_as(path)

    resolution = 512
    data = ReadData(dcm_folder)
    output = nifti
    factor = sliceNum / resolution
    affine = np.eye(4)
    affine[1][1] = factor
    affine[2][2] = factor
    img = nib.Nifti1Image(data, affine)
    nib.save(img, output)




def n2d(nifti, slicesNum, empty_dcm, dcm_folder):
    files = sorted(glob.glob(os.path.join(empty_dcm, "*.dcm")))
    img = nib.load(nifti)
    datas = img.get_data()
    subs = np.vsplit(datas, slicesNum)
    dcm_files = sortDCM(files)

    for (i, file) in enumerate(dcm_files):
        if not os.path.exists(dcm_folder):
            os.makedirs(dcm_folder)

        resolution = 512
        fileName = os.path.split(file)[1]
        output = os.path.join(dcm_folder, fileName)
        slice = subs[i]
        pixel_array = np.reshape(slice, (resolution, resolution))

        ds = pydicom.dcmread(file)
        ds.PixelData = pixel_array.tobytes()
        ds.Rows = resolution
        ds.Columns = resolution
        ds.save_as(output)



def Edm(input, empty_Name):
    if(os.path.isfile(input)):
        file = input
    else:
        files = sorted(glob.glob(os.path.join(input, "*.dcm")))
        file = sortDCM(files)[0]
    ds = pydicom.dcmread(file)
    empty = bytes(0)
    ds.PixelData = empty
    ds.Rows = 0
    ds.Columns = 0
    ds.save_as(empty_Name)




def m2d(file, empty_dcm, dcm_folder):
    mgz = nib.load(file)
    factor_x, factor_y, factor_z = mgz.shape
    datas = mgz.get_data()
    subs = np.vsplit(datas, factor_x)
    fileNames = ["IMG%04d.dcm" %x for x in range(1, factor_x+1)]

    for i in range(factor_x):
        pixel_array = np.reshape(subs[i], (factor_y, factor_z))
        pixels = pixel_array.astype("int16")
        ds = pydicom.dcmread(empty_dcm)
        pixels = pixels.tobytes()
        ds.PixelData = pixels
        ds.Rows = factor_y
        ds.Columns = factor_z
        name = fileNames[i]
        if not os.path.exists(dcm_folder):
            os.makedirs(dcm_folder)
        path = os.path.join(dcm_folder, name)
        ds.save_as(path)





if __name__ == "__main__":
    command = str(input("==> Enter: d2n, n2d, edm, m2d or exit? "))
    while(command != "exit"):
        if(command == "d2n"):
            dcm_folder = str(input("=> Enter DICOM Folder Name <input>: "))
            sliceNum = int(input("=> Enter slices number of DCM: "))
            nifit = str(input("=> Enter Nifti Name <output> (example.nii): "))
            meta = str(input("=> Enter Meta Folder Name <output>: "))
            d2n(dcm_folder, sliceNum,  nifit, meta)

        elif(command == "n2d"):
            nifit = str(input("=> Enter Nifti Name <input> (example.nii): "))
            sliceNum = int(input("=> Enter slices number of DCM: "))
            meta = str(input("=> Enter Empty DICOM Folder Name <input>: "))
            dcm_folder = str(input("=> Enter DICOM Folder Name <output>: "))
            n2d(nifit, sliceNum, meta, dcm_folder)

        elif(command == "edm"):
            file = str(input("=> Enter file/folder Name <input> : "))
            name = str(input("=> Enter Empty DCM Name <output> (example.dcm): "))
            Edm(file, name)
        elif(command == "m2d"):
            mgz = str(input("=> Enter MGZ Name <input>: "))
            empty_dcm = str(input("=> Enter Empty DICOM Name <input>: "))
            dcm_folder = str(input("=> Enter DICOM Folder Name <output>: "))
            m2d(mgz, empty_dcm, dcm_folder)

        else:
            print(">>> Error: Invalid input. Try again.")

        print("==> What you want? d2n/n2d/edm/m2d or exit?")
        command = input()

    sys.exit()

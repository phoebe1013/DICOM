import pydicom
import glob
import os
import numpy as np
import sys
import nibabel as nib
import operator



# python WriteNifti.py SUBJ03 200 Meta myNifti.nii

def ReadData(dcm_folder):
    files = sorted(glob.glob(os.path.join(dcm_folder, "*.dcm")))
    datadic = {}
    for (i, file) in enumerate(files):
        ds = pydicom.dcmread(file)
        order = ds.InstanceNumber
        datadic[file] = order
    sortDic = sorted(datadic.items(), key=operator.itemgetter(1))
    dcm_files = []
    for i in sortDic:
        dcm_files.append(i[0])

    datas=[]
    for (i, dcm) in enumerate(dcm_files):
        ds = pydicom.dcmread(dcm)
        data = ds.pixel_array
        datas.append(data)

    data = np.array(datas)              # shape:  (200, 512, 512)
    return data




def writeMetaData(dcm_folder, meta_folder):
    dcm_files = sorted(glob.glob(os.path.join(dcm_folder, "*.dcm")))
    for(i, file) in enumerate(dcm_files):
        fileName = os.path.split(file)[1]
        if not os.path.exists(meta_folder):
            os.makedirs(meta_folder)

        ds = pydicom.dcmread(file)
        empty = bytes(0)  # byte -> 0
        ds.PixelData = empty
        ds.Rows = 0
        ds.Columns = 0
        path = os.path.join(meta_folder, fileName)
        ds.save_as(path)

writeMetaData(str(sys.argv[1]), str(sys.argv[3]))




# Nifti_Name have to be nifit.nii or nifti.nii.gz
def writeNifti(dcm_folder, sliceNum, nifti):
    data = ReadData(dcm_folder)
    output = nifti
    factor = 512 / sliceNum  # resolution / numSlices
    affine = np.eye(4)
    affine[1][1] = 1 / factor
    affine[2][2] = 1 / factor
    img = nib.Nifti1Image(data, affine)
    nib.save(img, output)

writeNifti(str(sys.argv[1]), int(sys.argv[2]), str(sys.argv[4]))
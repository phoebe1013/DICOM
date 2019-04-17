import pydicom
import glob
import os
import numpy as np
import sys
import nibabel as nib
import operator



# python WriteDCM.py myNifti.nii Meta 200 Origins

def loadNifti(nifti, meta_folder, sliceNumber, outputDirectory):
    files = sorted(glob.glob(os.path.join(meta_folder, "*.dcm")))
    img = nib.load(nifti)
    datas = img.get_data()
    subs = np.vsplit(datas, sliceNumber)

    datadic = {}
    for (i, file) in enumerate(files):
        ds = pydicom.dcmread(file)
        order = ds.InstanceNumber
        datadic[file] = order
    sortDic = sorted(datadic.items(), key=operator.itemgetter(1))
    dcm_files = []
    for i in sortDic:
        dcm_files.append(i[0])

    for (i, file) in enumerate(dcm_files):
        if not os.path.exists(outputDirectory):
            os.makedirs(outputDirectory)

        fileName = os.path.split(file)[1]
        output = os.path.join(outputDirectory, fileName)
        slice = subs[i]                                 # <class 'numpy.core.memmap.memmap'>    shape  (1, 512, 512)
        pixel_array = np.reshape(slice, (512, 512))

        ds = pydicom.dcmread(file)
        ds.PixelData = pixel_array.tobytes()
        ds.Rows = 512
        ds.Columns = 512
        ds.save_as(output)

loadNifti(str(sys.argv[1]), str(sys.argv[2]), int(sys.argv[3]), str(sys.argv[4]))





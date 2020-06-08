import pydicom
from pydicom.dataset import Dataset, FileDataset
import glob
import os
import numpy as np
import sys
import nibabel as nib
import operator
import datetime
import time




def sortDCM(dcm_files):
    """
    Sort dicom slices with attribution: Instance Number.
    :param dcm_files: dicom slices that need to be sorted
    :return: sorted dicom slices
    """

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




def ReadData(dcm_folder):
    """
    Read all pixel data of dicom slices from a folder.
    :param dcm_folder: dicom folder name
    :return: 3-D array pixel data with shape (number, resolution, resolution)
    """

    files = sorted(glob.glob(os.path.join(dcm_folder, "*.dcm")))
    dcm_files = sortDCM(files)
    datas=[]
    for (i, dcm) in enumerate(dcm_files):
        ds = pydicom.dcmread(dcm)
        slice = ds.pixel_array
        data = np.transpose(slice)
        datas.append(data)
    result = np.array(datas)
    return result




def d2n_lossless(dcm_folder, nifti, meta_folder):
    """
    Convert dicom files to nifti format, empty pixel data of original dicom slices and save them to meta_folder.
    :param dcm_folder: dicom folder name
    :param nifti: nifti file name
    :param meta_folder: the meta data folder name
    """

    dcm_files = sorted(glob.glob(os.path.join(dcm_folder, "*.dcm")))
    for(i, file) in enumerate(dcm_files):
        fileName = os.path.split(file)[1]
        ds = pydicom.dcmread(file)
        sliceThickness = ds.SliceThickness      # for nifti's Affine
        PixelSpacing = ds.PixelSpacing          # for nifti's Affine
        empty = bytes(0)
        ds.PixelData = empty
        ds.Rows = 0
        ds.Columns = 0
        if not os.path.exists(meta_folder):
            os.makedirs(meta_folder)
        path = os.path.join(meta_folder, fileName)
        ds.save_as(path)

    data = ReadData(dcm_folder)
    output = nifti
    affine = np.eye(4)
    affine[0][0] = sliceThickness
    affine[1][1] = PixelSpacing[0]
    affine[2][2] = PixelSpacing[1]
    img = nib.Nifti1Image(data, affine)
    nib.save(img, output)




def n2d_lossless(nifti, empty_dcm, dcm_folder):
    """
    Convert nifti file to dicom files. Read nifti pixel data and write it in empty dicom slices.
    :param nifti: nifti file name
    :param empty_dcm: the meta data folder
    :param dcm_folder: dicom slices folder
    """

    files = sorted(glob.glob(os.path.join(empty_dcm, "*.dcm")))
    img = nib.load(nifti)
    datas = img.get_data()
    Affine = img.affine
    dcm_files = sortDCM(files)

    for (i, file) in enumerate(dcm_files):
        if not os.path.exists(dcm_folder):
            os.makedirs(dcm_folder)

        fileName = os.path.split(file)[1]
        output = os.path.join(dcm_folder, fileName)
        slice = datas[i, :, :]
        data = np.transpose(slice)
        rows = data.shape[0]
        cols = data.shape[1]
        pixel_array = np.reshape(data, (rows, cols))

        ds = pydicom.dcmread(file)              # Write pixel data to dicom
        ds.PixelData = pixel_array.tobytes()
        ds.Rows = rows
        ds.Columns = cols
        ds.SliceThickness = Affine[0][0]
        ds.PixelSpacing = [Affine[1][1], Affine[2][2]]
        ds.SeriesDescription = "_n2d"
        ds.save_as(output)





def Edm(input, empty_Name):
    """
    Read single DICOM file, write the meta data to a new dicom file as template for m2d_lossless().
    If input is a DICOM folder, then only use the first DICOM file.
    :param input: a single dicom slice or a folder
    :param empty_Name: the empty dicom name
    """
    start = time.time()
    if(os.path.isfile(input)):
        file = input
    else:
        files = sorted(glob.glob(os.path.join(input, "*.dcm")))
        file = sortDCM(files)[0]

    dataSet = pydicom.dcmread(file)

    fileName = "Edm.dcm"
    file_meta = Dataset()

    # add file meta data
    file_meta.MediaStorageSOPClassUID = dataSet.file_meta.MediaStorageSOPClassUID

    file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
    file_meta.FileMetaInformationVersion = dataSet.file_meta.FileMetaInformationVersion
    file_meta.MediaStorageSOPInstanceUID = dataSet.file_meta.MediaStorageSOPInstanceUID
    file_meta.ImplementationClassUID = dataSet.file_meta.ImplementationClassUID
    file_meta.ImplementationVersionName = dataSet.file_meta.ImplementationVersionName
    ds = FileDataset(fileName, {},
                     file_meta=file_meta, preamble=b"\0" * 128)

    # add meta data
    ds.ImageType = dataSet.ImageType
    ds.SOPClassUID = dataSet.SOPClassUID
    ds.SOPInstanceUID = dataSet.SOPInstanceUID
    ds.StudyDate = dataSet.StudyDate
    ds.StudyTime = dataSet.StudyTime
    ds.AccessionNumber = dataSet.AccessionNumber
    ds.Manufacturer = dataSet.Manufacturer
    ds.StudyDescription = dataSet.StudyDescription
    ds.SeriesDescription = dataSet.SeriesDescription
    ds.ManufacturerModelName = dataSet.ManufacturerModelName
    ds.PatientName = dataSet.PatientName
    ds.PatientID = dataSet.PatientID
    ds.PatientBirthDate = dataSet.PatientBirthDate
    ds.PatientSex = dataSet.PatientSex
    ds.SliceThickness = dataSet.SliceThickness
    ds.PatientPosition = dataSet.PatientPosition
    ds.StudyInstanceUID = dataSet.StudyInstanceUID
    ds.SeriesInstanceUID = dataSet.SeriesInstanceUID
    ds.StudyID = dataSet.StudyID
    ds.SeriesNumber = dataSet.SeriesNumber
    ds.InstanceNumber = "1"
    ds.ImagePositionPatient = dataSet.ImagePositionPatient
    ds.ImageOrientationPatient = dataSet.ImageOrientationPatient
    ds.FrameOfReferenceUID = dataSet.FrameOfReferenceUID
    ds.PositionReferenceIndicator = dataSet.PositionReferenceIndicator
    ds.PositionReferenceIndicator = "SN"
    ds.SamplesPerPixel = dataSet.SamplesPerPixel
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 0
    ds.Columns = 0
    ds.PixelSpacing = dataSet.PixelSpacing
    ds.BitsAllocated = dataSet.BitsAllocated
    ds.BitsStored = dataSet.BitsStored
    ds.HighBit = dataSet.HighBit
    ds.PixelRepresentation = dataSet.PixelRepresentation
    ds.PixelData = bytes(0)
    ds.save_as(empty_Name)

    print("Cost time (seconds): " , (time.time() - start))




def n2d_edm(nifti, meta_file, dcm_folder):
    """
    Convert nifit file to dicom slices with an template dicom file.
    :param nifti: nifti file name
    :param meta_file: the template file
    :param dcm_folder: the result dicom folder name
    """
    niftiData = nib.load(nifti)
    affine = niftiData.affine
    p = affine[:, 3][0:3]             # for ImagePositionPatient
    position = [round(p[0] * -1, 3), round(p[1] * -1, 3), round(p[2], 3)]
    factor_x, factor_y, factor_z = niftiData.shape
    datas = niftiData.get_data()         # (166, 256, 256)
    fileNames = ["IMG%04d.dcm" % x for x in range(1, factor_x + 1)]
    sopNums = ["%03d" % x for x in range(1, factor_x + 1)]

    for i in range(factor_x):
        ds = pydicom.dcmread(meta_file)
        pixel_array = np.transpose(datas[i, :, :])
        ds.PixelData = pixel_array.tobytes()
        ds.Rows = factor_y
        ds.Columns = factor_z
        ds.PixelSpacing = [1, 1]

        last_index = ds.SOPInstanceUID.rindex(".")
        prefix = ds.SOPInstanceUID[: last_index + 1]
        ds.SOPInstanceUID = prefix + sopNums[i]                        # change SOP Instance UID
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID     # change Media Storage SOP Instance UID
        ds.InstanceNumber = i + 1                                       # change Instance Number
        ds.SeriesDescription = "_m2d_edm"

        # change ImagePositionPatient & ImageOrientationPatient
        ds.ImageOrientationPatient = [affine[0][0] * -1, affine[1][0] * -1, affine[2][0], affine[0][1] * -1,
                                      affine[1][1] * -1, affine[2][1]]
        ds.ImagePositionPatient = [position[0], round(position[1] - i, 3), position[2]]

        if not os.path.exists(dcm_folder):
            os.makedirs(dcm_folder)
        path = os.path.join(dcm_folder, fileNames[i])
        ds.save_as(path)




def m2d_lossless(file, empty_dcm, dcm_folder):
    """
    Read pixel data of the mgz file then write it to empty dicom file from Edm.
    :param file: mgz file name
    :param empty_dcm: meta data folder name
    :param dcm_folder: dicom slices folder
    """

    start = time.time()
    mgzData = nib.load(file)
    affine = mgzData.affine
    p = affine[:, 3][0:3]             # for ImagePositionPatient
    position = [round(p[0] * -1, 3), round(p[1] * -1, 3), round(p[2], 3)]
    factor_x, factor_y, factor_z = mgzData.shape
    datas = mgzData.get_data()
    fileNames = ["IMG%04d.dcm" % x for x in range(1, factor_x + 1)]
    sopNums = ["%03d" % x for x in range(1, factor_x + 1)]

    for i in range(factor_x):
        ds = pydicom.dcmread(empty_dcm)
        pixel_array = np.transpose(datas[:, :, i])  # axis = 2
        pixels = pixel_array.astype("int16")
        ds.PixelData = pixels.tobytes()
        ds.Rows = factor_y
        ds.Columns = factor_z
        ds.PixelSpacing = [1, 1]

        last_index = ds.SOPInstanceUID.rindex(".")
        prefix = ds.SOPInstanceUID[: last_index + 1]
        ds.SOPInstanceUID = prefix + sopNums[i]                        # change SOP Instance UID
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID     # change Media Storage SOP Instance UID
        ds.InstanceNumber = i + 1                                       # change Instance Number
        ds.SeriesDescription = "_m2d_lossless"

        # change ImagePositionPatient & ImageOrientationPatient
        ds.ImageOrientationPatient = [affine[0][0] * -1, affine[1][0] * -1, affine[2][0], affine[0][1] * -1,
                                      affine[1][1] * -1, affine[2][1]]
        ds.ImagePositionPatient = [position[0], round(position[1] - i, 3), position[2]]

        if not os.path.exists(dcm_folder):
            os.makedirs(dcm_folder)
        path = os.path.join(dcm_folder, fileNames[i])
        ds.save_as(path)

    print("Cost time (seconds): " , (time.time() - start))




def newDCM(meta_file, shape):
    """
    Create a new dicom file as template for m2d.
    This dicom file has no pixel data. Pixel data will be filled in m2d method.
    :param meta_file: provide meta data
    :param shape: mgz data shape
    :return: the dataset of dicom file, which could be filled pixel data from mgz file
    """

    fileName = "template.dcm"
    prefix = "1.2.826.0.1.3680043.10.271."
    suffix = str(datetime.datetime.today())[:10].replace('-', '') + str(time.time()).replace('.', '')


    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"  # Standard SOP CLasses: MR Image Storage
    ds = FileDataset(fileName, {},
                     file_meta=file_meta, preamble=b"\0" * 128)
    ds.SeriesInstanceUID = prefix + suffix  # change Series Instance UID

    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.4"            # Standard SOP CLasses: MR Image Storage
    ds.ImageType = ['ORIGINAL', 'PRIMARY', 'OTHER']
    ds.PatientPosition = "HFS"
    ds.Manufacturer =  "GE MEDICAL SYSTEMS"
    ds.ManufacturerModelName = "SIGNA EXCITE"
    ds.PositionReferenceIndicator = "SN"
    ds.SliceThickness = 1

    # Set the transfer syntax
    ds.is_little_endian = True
    ds.is_implicit_VR = True
    ds.PixelData = bytes(0)
    ds.Rows = shape[0]
    ds.Columns = shape[1]
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.SeriesDescription = "_m2d"
    ds.PixelSpacing = [1, 1]
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian

    with open(meta_file) as f:
        for line in f:
            index = line.rindex(":")
            key = line[: index].replace(' ', '').lower()
            value = line[index + 1:].strip()
            if (key == "studydate"):
                ds.StudyDate = value
            if (key == "seriesdate"):
                ds.SeriesDate = value
            if (key == "patientbirthdate"):
                ds.PatientBirthDate = value
            if (key == "studytime"):
                ds.StudyTime = value
            if (key == "accessionnumber"):
                ds.AccessionNumber = value
            if (key == "studydescription"):
                ds.StudyDescription = value
            if (key == "seriesdescription"):
                ds.SeriesDescription = value
            if (key == "patientname"):
                ds.PatientName = value
            if (key == "patientid"):
                ds.PatientID = value
            if (key == "seriesnumber"):
                ds.SeriesNumber = value
            if (key == "patientsex"):
                ds.PatientSex = value;

    return ds




def m2d(mgz, meta_file, dcm_folder):
    """
    Read pixel data of the mgz file then write it to an new dicom.
    Meanwhile, write the meta data provided by user to the dicom.
    :param mgz: mgz file name
    :param meta_file: meta data folder name
    :param dcm_folder: dicom slices folder
    """

    start = time.time()
    mgzData = nib.load(mgz)
    affine = mgzData.affine
    shape = mgzData.shape
    p = affine[:, 3][0:3]  # for ImagePositionPatient
    position = [round(p[0] * -1, 3), round(p[1] * -1, 3), round(p[2], 3)]
    prefix = "1.2.826.0.1.3680043.10.271."
    factor_x, factor_y, factor_z = mgzData.shape
    datas = mgzData.get_data()
    fileNames = ["IMG%04d.dcm" % x for x in range(1, factor_x + 1)]
    sopNums = ["%03d" % x for x in range(1, factor_x + 1)]

    ds = newDCM(meta_file, shape)
    for i in range(factor_x):
        pixel_array = np.transpose(datas[:, :, i])  # axis = 2
        pixels = pixel_array.astype("int16")
        ds.PixelData = pixels.tobytes()
        ds.Rows = factor_y
        ds.Columns = factor_z
        ds.PixelSpacing = [1, 1]
        ds.SOPInstanceUID = prefix + sopNums[i]                        # change SOP Instance UID
        ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID     # change Media Storage SOP Instance UID
        ds.InstanceNumber = i + 1  # change Instance Number

        # change ImagePositionPatient & ImageOrientationPatient
        ds.ImageOrientationPatient = [affine[0][0] * -1, affine[1][0] * -1, affine[2][0], affine[0][1] * -1,
                                      affine[1][1] * -1, affine[2][1]]
        ds.ImagePositionPatient = [position[0], round(position[1] - i, 3), position[2]]

        if not os.path.exists(dcm_folder):
            os.makedirs(dcm_folder)
        path = os.path.join(dcm_folder, fileNames[i])
        ds.save_as(path)

    print("Cost time (seconds): ", (time.time() - start))



def checkArgs():
    """
    Print prompts and check if inputs are valid.
    :return: return "exit" if this is included in users' input, otherwise, return String command.
    """
    print("\n===> Enter the Function Number and Parameters:")
    print(" => 1. d2n_lossless(dcm_folder, nifti, meta_folder)")
    print(" => 2. n2d_lossless(nifti, empty_dcm, dcm_folder)")
    print(" => 3. n2d_edm(nifti, meta_file, dcm_folder)")
    print(" => 4. n2d(nifti, meta_file, dcm_folder)")   #TODO
    print(" => 5. m2d_lossless(file, empty_dcm, dcm_folder)")
    print(" => 6. m2d(mgz, meta_file, dcm_folder)")
    command = str(input())
    if "exit" in command:
        return "exit"
    return command



def execute(commands):
    """
    Execute functions according to the commands if commands are valid.
    :param commands: Commands provided from user.
    """
    commands = [x.strip() for x in commands.split()]
    funNum = int(commands[0])
    argNum = len(commands[1:])
    # print('func:{}, argNum:{}:{}'.format(functionNum, argNum, command[1:]))
    if (argNum != 3):
        return

    if (funNum == 1):
        d2n_lossless(commands[1], commands[2], commands[3])
    elif (funNum == 2):
        n2d_lossless(commands[1], commands[2], commands[3])
    elif (funNum == 3):
        n2d_edm(commands[1], commands[2], commands[3])
    elif (funNum == 4):
        print("TODO: n2d(nifti, meta_file, dcm_folder)!")
    elif (funNum == 5):
        m2d_lossless(commands[1], commands[2], commands[3])
    else:
        m2d(commands[1], commands[2], commands[3])


if __name__ == "__main__":
    commands = checkArgs()
    while (commands != "exit"):
        execute(commands)
        commands = checkArgs()
    sys.exit()

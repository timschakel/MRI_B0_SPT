#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 08:11:06 2023

@author: tschakel
"""

from wad_qc.module import pyWADinput
from wad_qc.modulelibs import wadwrapper_lib
import pydicom
import matplotlib.pyplot as plt

### Helper functions
def getValue(ds, label):
    """Return the value of a pydicom DataElement in Dataset identified by label.

    ds: pydicom Dataset
    label: dicom identifier, in either pydicom Tag object, string or tuple form.
    """
    if isinstance(label, str):
        try:
            # Assume form "0x0008,0x1030"
            tag = pydicom.tag.Tag(label.split(','))
        except ValueError:
            try:
                # Assume form "SeriesDescription"
                tag = ds.data_element(label).tag
            except (AttributeError, KeyError):
                # `label` string doesn't represent an element of the DataSet
                return None
    else:
        # Assume label is of form (0x0008,0x1030) or is a pydicom Tag object.
        tag = pydicom.tag.Tag(label)

    try:
        return str(ds[tag].value)
    except KeyError:
        # Tag doesn't exist in the DataSet
        return None
    
def isFiltered(ds, filters):
    """Return True if the Dataset `ds` complies to the `filters`,
    otherwise return False.
    """
    for tag, value in filters.items():
        if not str(getValue(ds, tag)) == str(value):
            # Convert both values to string before comparison. Reason is that
            # pydicom can return 'str', 'int' or 'dicom.valuerep' types of data.
            # Similarly, the user (or XML) supplied value can be of any type.
            return False
    return True

def applyFilters(series_filelist, filters):
    """Apply `filters` to the `series_filelist` and return the filtered list.

    First, convert `filters` from an ElementTree Element to a dictionary
    Next, create a new list in the same shape as `series_filelist`, but only
    include filenames for which isFiltered returns True.
    Only include sublists (i.e., series) which are non empty.
    """
    # Turn ElementTree element attributes and text into filters
    #filter_dict = {element.attrib["name"]: element.text for element in filters}
    filter_dict = filters

    filtered_series_filelist = []
    # For each series in the series_filelist (or, study):
    for instance_filelist in series_filelist:
        # Filter filenames within each series
        filtered_instance_filelist = [fn for fn in instance_filelist
                                      if isFiltered(
                pydicom.read_file(fn, stop_before_pixels=True), filter_dict)]
        # Only add the series which are not empty
        if filtered_instance_filelist:
            filtered_series_filelist.append(filtered_instance_filelist)

    return filtered_series_filelist


if __name__ == "__main__":
    data, results, config = pyWADinput()
    
    # Log which series are found
    data_series = data.getAllSeries()
    print("The following series are found:")
    for item in data_series:
        print(item[0]["SeriesDescription"].value+" with "+str(len(item))+" instances")
        
    for name,action in config['actions'].items():
        if name == 'acqdatetime':
            filters = action["filters"]
            datetime_series = data.getInstanceByTags(filters["datetime_filter"])
            dt = wadwrapper_lib.acqdatetime_series(datetime_series[0])
            results.addDateTime('AcquisitionDateTime', dt) 
            
        elif name == 'showimages':
            filters = action["filters"]
            
            # load the data, 4 sets
            data_shim_R = applyFilters(data.series_filelist,filters['shim_R'])
            if len(data_shim_R[0]) < 1:
                print(">>> SHIM REAL not found <<<")
            else:
                dcmInfile_shim_R,pixeldata_shim_R,dicomMode = wadwrapper_lib.prepareInput(data_shim_R[0],headers_only=False)
                
            data_shim_P = applyFilters(data.series_filelist,filters['shim_P'])
            if len(data_shim_P[0]) < 1:
                print(">>> SHIM PHASE not found <<<")
            else:
                dcmInfile_shim_P,pixeldata_shim_P,dicomMode = wadwrapper_lib.prepareInput(data_shim_P[0],headers_only=False)
           
            data_shimmagnet_R = applyFilters(data.series_filelist,filters['shimmagnet_R'])
            if len(data_shim_R[0]) < 1:
                print(">>> SHIM MAGNET REAL not found <<<")
            else:
                dcmInfile_shimmagnet_R,pixeldata_shimmagnet_R,dicomMode = wadwrapper_lib.prepareInput(data_shimmagnet_R[0],headers_only=False)
           
            data_shimmagnet_P = applyFilters(data.series_filelist,filters['shimmagnet_P'])
            if len(data_shim_R[0]) < 1:
                print(">>> SHIM MAGNET PHASE not found <<<")
            else:
                dcmInfile_shimmagnet_P,pixeldata_shimmagnet_P,dicomMode = wadwrapper_lib.prepareInput(data_shimmagnet_P[0],headers_only=False)
           
            # Create plots
            figtitle = 'B0 SPT '+str(dcmInfile_shim_R.info.PatientName)+' '+dcmInfile_shim_R.info.SeriesDescription+' '+dcmInfile_shim_R.info.StudyDate+' '+dcmInfile_shim_R.info.StudyTime
            fig, axs = plt.subplots(2,3,figsize=(12,6))
            fig.suptitle(figtitle)
                        
            axs[0,0].imshow(pixeldata_shim_R[1,:,:],cmap='gray')
            axs[0,0].set_title('Real slice 2')
            axs[0,0].axis('off')
            
            axs[0,1].imshow(pixeldata_shim_R[2,:,:],cmap='gray')
            axs[0,1].set_title('Real slice 3')
            axs[0,1].axis('off')
            
            axs[0,2].imshow(pixeldata_shim_R[3,:,:],cmap='gray')
            axs[0,2].set_title('Real slice 4')
            axs[0,2].axis('off')
            
            axs[1,0].imshow(pixeldata_shim_P[1,:,:],cmap='gray')
            axs[1,0].set_title('Phase slice 2')
            axs[1,0].axis('off')
            
            axs[1,1].imshow(pixeldata_shim_P[2,:,:],cmap='gray')
            axs[1,1].set_title('Phase slice 3')
            axs[1,1].axis('off')
            
            axs[1,2].imshow(pixeldata_shim_P[3,:,:],cmap='gray')
            axs[1,2].set_title('Phase slice 4')
            axs[1,2].axis('off')
            
            filename_shim = 'B0_SPT_'+str(dcmInfile_shim_R.info.PatientName)+'_'+dcmInfile_shim_R.info.SeriesDescription+'.png'
            fig.savefig(filename_shim,dpi=150)
            
            
            # Create plots
            figtitle = 'B0 SPT '+str(dcmInfile_shimmagnet_R.info.PatientName)+' '+dcmInfile_shimmagnet_R.info.SeriesDescription+' '+dcmInfile_shimmagnet_R.info.StudyDate+' '+dcmInfile_shimmagnet_R.info.StudyTime
            fig, axs = plt.subplots(2,3,figsize=(12,6))
            fig.suptitle(figtitle)
                        
            axs[0,0].imshow(pixeldata_shimmagnet_R[1,:,:],cmap='gray')
            axs[0,0].set_title('Real slice 2')
            axs[0,0].axis('off')
            
            axs[0,1].imshow(pixeldata_shimmagnet_R[2,:,:],cmap='gray')
            axs[0,1].set_title('Real slice 3')
            axs[0,1].axis('off')
            
            axs[0,2].imshow(pixeldata_shimmagnet_R[3,:,:],cmap='gray')
            axs[0,2].set_title('Real slice 4')
            axs[0,2].axis('off')
            
            axs[1,0].imshow(pixeldata_shimmagnet_P[1,:,:],cmap='gray')
            axs[1,0].set_title('Phase slice 2')
            axs[1,0].axis('off')
            
            axs[1,1].imshow(pixeldata_shimmagnet_P[2,:,:],cmap='gray')
            axs[1,1].set_title('Phase slice 3')
            axs[1,1].axis('off')
            
            axs[1,2].imshow(pixeldata_shimmagnet_P[3,:,:],cmap='gray')
            axs[1,2].set_title('Phase slice 4')
            axs[1,2].axis('off')
            
            filename_shimmagnet = 'B0_SPT_'+str(dcmInfile_shimmagnet_R.info.PatientName)+'_'+dcmInfile_shimmagnet_R.info.SeriesDescription+'.png'
            fig.savefig(filename_shimmagnet,dpi=150)
            
            results.addObject("B0_SPT_SHIM_figure", filename_shim)
            results.addObject("B0_SPT_SHIM_MAGNET_figure", filename_shimmagnet)
            
            
    
    results.write()
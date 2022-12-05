# Distribution Ready: 11/17/2022
# Step 2: IF YOU HAVE NOT RUN MYFUNCTIONS.PY YET GO BACK AND RUN THAT FIRST, THIS IS THE SECOND STEP IN THE NAT
# CAP PROCESS
# This code sets up one geodatabase for each Local Authority District (LAD), clips and copies in the input files for
# OSMM,
# LAD boundary, and either CROME (formerly used LCM) and PHI or Phase 1 habitat (HLU).
# Can be applied either to Oxfordshire or the other LADs in the Arc. The basic format of this code is to call from a
# previously set up folder which holds a previously set up File Geodatabase (gdb) called 'Data.gdb'.
# REQUIRED: shapefile in the Data.gdb which has all LADs that are required in the analysis
# REQUIRED: an input of LADs which the user is interested in. These can be changed in the 'LADs_Inlcuded' list to not
# process more data than necessary.
# -----------------------------------------------------------------------------------------------------------------

import time
import arcpy
import os
import MyFunctions

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True         # Overwrites files
arcpy.env.qualifiedFieldNames = False    # Joined fields will be exported without the join table name
arcpy.env.XYTolerance = "0.001 Meters"

#Step 2
# Choose a dataset
data_source = "HLU"


Step 3
# This code will first create a folder structure that it can call from, you will need to go in and put the LAD gdb and
# the HLU the data in the data gdb and call it "LADs_Input" and "HLU" respectively
repository = r"E:\Zach\2022\test"
os.makedirs(repository)
data = os.path.join(repository, "Data")
os.makedirs(data)
LAD_folder = os.path.join(data, 'LADs_Output')
os.makedirs(LAD_folder)
arcpy.management.CreateFileGDB(data, 'Data.gdb')
data_gdb = os.path.join(data, "Data.gdb")
LADs_Input = os.path.join(data_gdb, "LADs_Input")
filemap = input('write DONE once you have input the feature class of LADS labeled LADs_Input into the data.gdb')
if filemap == 'DONE':
    print('FILE MAP LAD SET')
else:
    input('write DONE once you have input the feature class of LADS labeled LADs_Input into the data.gdb')
counties_included = ["Oxfordshire"]  # This is for doing whole county in one go
LADs_included = ["Cherwell", "Oxford", "South Oxfordshire", "Vale of White Horse", "West Oxfordshire"]   # This is for doing separate LADs
LAD_name_field = "desc_"
County_field = "county"

# set to the highest branch of the OSMM folder before the geodatabases
tile_folder = r"E:\Zach\2022_OSMM\topo"

# set the name os the feature classes within the OSMM files
fc_name = "topographicarea"

# set an output space
OSMM_out_gdb = r"E:\Zach\2022"
# make a gdb in that folder
arcpy.management.CreateFileGDB(OSMM_out_gdb, 'OSMM')
OSMM_out_gdb = os.path.join(OSMM_out_gdb, 'OSMM.gdb')

# set the output name of osmm merge results
new_fc = "OSMM"
OSMM_fc = new_fc
OSMM_fc_prep = os.path.join(data_gdb, new_fc)

#choose settings for the OSMM split
collate_tiles = True
merge_tiles = True
' Split into LADs OR trim to county boundary'

if collate_tiles:
    arcpy.env.workspace = tile_folder
    folders = arcpy.ListFiles()
    print(folders)
    print(OSMM_out_gdb)
    i = 0
    for folder in folders:
        print(folder)
        arcpy.env.workspace = os.path.join(tile_folder, folder)
        i = i + 1
        clean_name = os.path.splitext(folder)[0]
        out_fc = os.path.join(OSMM_out_gdb, "OSMM_tile_" + clean_name)
        print(out_fc)
        print("    Copying to " + out_fc)
        arcpy.CopyFeatures_management(fc_name, out_fc)
        
if merge_tiles:
    print ("Merging tiles")
    arcpy.env.workspace = OSMM_out_gdb
    in_fcs = arcpy.ListFeatureClasses()
    arcpy.Merge_management(in_fcs, OSMM_fc_prep)
    print(''.join(["## Finished merge on : ", time.ctime()]))

print(''.join(["## Finished on : ", time.ctime()]))        

if data_source == "CROME_PHI":
    CROME_Data = os.path.join(data_gdb, 'CROME')
    LAD_name_field = "_desc"
    County_field = "county"
    PHI = "PHI"
    PHI_hab_field = "Main_habit"

elif data_source == "HLU":
    HLU_data = os.path.join(data_gdb, "HLU")
    HLUfilemap = input('write DONE once you have input the HLU into the newly built data.gdb folder')
    if HLUfilemap == 'DONE':
        print('HLU FILEMAP DONE')
    else:
        HLUfilemap = input('write DONE once you have input the HLU Data into the newly built data.gdb folder')
    # Updated for new version of OSMM
    LAD_name_field = "desc_"
    County_field = "county"

elif data_source == "NP_Wales":
    CROME_data = os.path.join(data_gdb, "Crome")
    Walesfilemap = input('write DONE once you have input the WALES CROME Data into the newly built data.gdb folder')
    if Walesfilemap == 'DONE':
        print('HLU FILEMAP DONE')
    else:
        Walesfilemap = input('write DONE once you have input the WALES CROME Data into the newly built data.gdb folder')
    PHI = 'NRW_SensitiveHabitats'
    PHI_hab_field = 'Habitat_2'
   
#step 4 - select all necessary preparations for each dataset, the comments will determine which are necessary

LAD_names = []

# Which stages of the code do we want to run? Depends on method - also can be useful for debugging or updates.
if method == "CROME_PHI":
    prep_PHI = True
    setup_PHI = True
    setup_HLU = False    # Always false for the LCM_PHI method
    setup_LCM = False    # False if LCM not being used (default)
elif method == "HLU":
    prep_PHI = False     # Always false for the HLU method
    setup_LCM = False    # Always false for the HLU method
    setup_PHI = False    # Always false for the HLU method
    setup_HLU = True
else:
    print("ERROR: Invalid region")
    exit()

setup_LAD_gdbs = True
create_gdb = True
setup_OSMM = True
clip_OSMM = False
setup_boundary = True

arcpy.env.workspace = data_gdb

if prep_PHI:
    print ("Preparing PHI datasets")
    # main PHI dataset
    arcpy.Dissolve_management(PHI, "PHI_diss_over10m2", PHI_hab_field, multi_part="SINGLE_PART")
    MyFunctions.delete_by_size("PHI_diss_over10m2", 10)
    # Copy habitat into a new field called 'PHI' (for neatness)
    MyFunctions.check_and_add_field("PHI_diss_over10m2", "PHI", "TEXT", 100)
    arcpy.CalculateField_management("PHI_diss_over10m2", "PHI", "!" + PHI_hab_field + "!", "PYTHON_9.3")
    arcpy.DeleteField_management("PHI_diss_over10m2", PHI_hab_field)
    # Wood pasture and parkland with scattered trees
    arcpy.Dissolve_management("WoodPastureAndParkland", "WPP_diss_over10m2", "PRIHABTXT", multi_part="SINGLE_PART")
    MyFunctions.delete_by_size("WPP_diss_over10m2", 10)
    # Copy 'Main_habit' into a new field called 'WPP' (for neatness)
    MyFunctions.check_and_add_field("WPP_diss_over10m2", "WPP", "TEXT", 100)
    arcpy.CalculateField_management("WPP_diss_over10m2", "WPP", "!PRIHABTXT!", "PYTHON_9.3")
    arcpy.DeleteField_management("WPP_diss_over10m2", "PRIHABTXT")
    # Open mosaic habitats on previously developed land
    arcpy.Dissolve_management("OMHD", "OMHD_diss_over10m2", "PRIHABTXT", multi_part="SINGLE_PART")
    MyFunctions.delete_by_size("OMHD_diss_over10m2", 10)
    # Copy 'Main_habit' into a new field called 'OMHD' (for neatness)
    MyFunctions.check_and_add_field("OMHD_diss_over10m2", "OMHD", "TEXT", 100)
    arcpy.CalculateField_management("OMHD_diss_over10m2", "OMHD", "!PRIHABTXT!", "PYTHON_9.3")
    arcpy.DeleteField_management("OMHD_diss_over10m2", "PRIHABTXT")
    # Union
    print("Unioning the three PHI datasets")
    arcpy.Union_analysis(["PHI_diss_over10m2", "WPP_diss_over10m2", "OMHD_diss_over10m2"], "PHI_union", "NO_FID")

    print ("Copying WPP or OMHD to blank PHI fields")
    # Fill in "PHI" field where it is blank, with WPP or OMHD (OMHD takes priority as WPP can cover large mixed areas indiscriminately)
    # This bit not tested since rewrite...
    expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%') AND (OMHD IS NOT NULL AND OMHD <> '')"
    MyFunctions.select_and_copy("PHI_union", "PHI", expression, "!OMHD!")
    expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%') AND (WPP IS NOT NULL AND WPP <> '')"
    MyFunctions.select_and_copy("PHI_union", "PHI", expression, "!WPP!")

if setup_LAD_gdbs:
    LADs = arcpy.SearchCursor(LAD_Input)
    for LAD in LADs:
        LAD_full_name = LAD.getValue(LAD_name_field)
        LAD_county = LAD.getValue(County_field)
        # if LAD_county in counties_included:          # This can be used if there is a county field and we want to select all LADs for a county
        if LAD_full_name in LADs_included:             # Or if listing each LAD separately
            LAD_name = LAD_full_name.replace(" ", "")
            LAD_names.append(LAD_name)

            # Set up a new geodatabase for each LAD, copy clipped OSMM, copy boundary, and clip HLU or PHI to the boundaries
            print ("Setting up " + LAD_full_name)

            if create_gdb:
                print ("  Creating new geodatabase for " + LAD_name)
                arcpy.CreateFileGDB_management(LAD_folder, LAD_name)

            LAD_gdb = os.path.join(LAD_folder, LAD_name + ".gdb")

            if setup_boundary:
                print ("  Creating boundary for " + LAD_name)
                arcpy.MakeFeatureLayer_management(LAD_table, "LAD_lyr")
                arcpy.SelectLayerByAttribute_management("LAD_lyr", where_clause= LAD_name_field + " = '" + LAD_full_name + "'")
                arcpy.CopyFeatures_management("LAD_lyr", os.path.join(LAD_gdb, "boundary"))
                arcpy.Delete_management("LAD_lyr")

            boundary = os.path.join(LAD_gdb, "boundary")

            if setup_OSMM:
                out_fc = os.path.join(LAD_gdb, "OSMM")
                if clip_OSMM:
                    print ("  Clipping OSMM to LAD boundary")
                    arcpy.MakeFeatureLayer_management("OSMM", "OSMM_lyr")
                    arcpy.SelectLayerByLocation_management("OSMM_lyr", "INTERSECT", boundary)  # To save time select all the intersecting features first
                    arcpy.Clip_analysis("OSMM_lyr", boundary, out_fc)
                    MyFunctions.check_and_repair(out_fc)
                else:    # If OSMM has already been clipped to a feature class called OSMM_LADname (which should be in the current folder)
                    print("  Copying OSMM for " + LAD_name + " to new geodatabase")
                    arcpy.CopyFeatures_management("OSMM_" + LAD_name, out_fc)

            if setup_PHI:
                print ("  Clipping PHI to LAD boundary")
                out_file = os.path.join(LAD_gdb, "PHI")
                arcpy.Clip_analysis("PHI_union", boundary, out_file)
                MyFunctions.check_and_repair(out_file)

            if setup_HLU:
                print ("  Clipping HLU to LAD boundary")
                out_file = os.path.join(LAD_gdb, "HLU")
                arcpy.Clip_analysis(HLU_data, boundary, out_file)
                MyFunctions.check_and_repair(out_file)

            print(''.join(["## Finished setting up " + LAD_name + " gdb on : ", time.ctime()]))

exit()

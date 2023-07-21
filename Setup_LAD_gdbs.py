# Distribution Ready: 10/31/2022
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
# -----------------------------------------------------------------------------------------------------------

import time
import arcpy
import os
import MyFunctions

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True         # Overwrites files
arcpy.env.qualifiedFieldNames = False    # Joined fields will be exported without the join table name
arcpy.env.XYTolerance = "0.001 Meters"

# step 2
data_source = "CROME_PHI"
#data_source = 'HLU'

Build_Structure = False

repository = r"Z:\NatCap_OS_v2"
data = os.path.join(repository, "Data")
LAD_folder = os.path.join(data, 'LADs_Output')
data_gdb = os.path.join(repository, "Data.gdb")
LADs_Input = os.path.join(data_gdb, "LADs_Input")
Inputs = os.path.join(data, "Input_Shapefiles.gdb")
CROME_Folder = os.path.join(data, 'CROME')
All_Lads = os.path.join(data, "Complete_Lads", "All_Lads")
tile_folder = r"Z:\OSMM"
fc_name = "Topgraphicarea"

OSMM_out_gdb = repository
# make a gdb in that folder

OSMM_out_gdb = os.path.join(OSMM_out_gdb, 'OSMM.gdb')

# set the output name of osmm merge results
new_fc = "OSMM"
OSMM_fc = new_fc
OSMM_fc_prep = os.path.join(data_gdb, new_fc)

if Build_Structure:
    repository = r"Z:\NatCap_OS_v2"
    os.makedirs(repository)
    data = os.path.join(repository, "Data")
    os.makedirs(data)
    LAD_folder = os.path.join(data, 'LADs_Output')
    os.makedirs(LAD_folder)
    arcpy.CreateFileGDB_management(repository, 'Data.gdb', "CURRENT")
    data_gdb = os.path.join(repository, "Data.gdb")
    LADs_Input = os.path.join(data_gdb, "LADs_Input")
    Inputs = os.path.join(data, "Input_Shapefiles.gdb")
    CROME_Folder = os.path.join(data, 'CROME')
    filemap = input(
        "If you have one shapefile of lads, write 'DONE' once you have input the feature class of LADS labeled "
        "LADs_Input into the data.gdb. If you are inputting shapefiles to create minimum bounding geometries "
        "type 'INPUT':")
    if filemap == 'DONE':
        print('FILE MAP LAD SET')
    elif filemap == 'INPUT':
        arcpy.CreateFileGDB_management(data, 'Input_Shapefiles.gdb', "CURRENT")
        map2 = input('Copy all shapefiles to the input folder, Now type "DONE"')
        if map2 == 'DONE':
            print('All set, good luck !')
        else:
            input('Copy all selecting shapefiles to the input folder, then type "DONE"')
    else:
        input('write DONE once you have input the feature class of LADS labeled LADs_Input into the data.gdb')
    # set to the highest branch of the OSMM folder before the geodatabases
    tile_folder = r"Z:\OSMM"

    # set the name os the feature classes within the OSMM files
    fc_name = "Topgraphicarea"

    # set an output space
    OSMM_out_gdb = repository
    # make a gdb in that folder
    arcpy.CreateFileGDB_management(OSMM_out_gdb, "OSMM.gdb")
    # arcpy.management.CreateFileGDB(OSMM_out_gdb, 'OSMM')
    # set the gdb path
    OSMM_out_gdb = os.path.join(OSMM_out_gdb, 'OSMM.gdb')

    # set the output name of osmm merge results
    new_fc = "OSMM"
    OSMM_fc = new_fc
    OSMM_fc_prep = os.path.join(data_gdb, new_fc)

collate_tiles = True #first time run through with OSMM data
merge_tiles = True #first time run through with OSMM data


if collate_tiles:
    arcpy.env.workspace = tile_folder
    folders = arcpy.ListFiles()
    i = 0
    for folder in folders:
        print("Folder " + folder)
        arcpy.env.workspace = os.path.join(tile_folder, folder)
        subfolders = arcpy.ListFiles("mastermap*")
        for subfolder in subfolders: #no subfolders in the hierarchy
            print ("  Subfolder " + subfolder)
            arcpy.env.workspace = os.path.join(tile_folder, folder, subfolder)
            in_gdb_list = arcpy.ListFiles("*.gdb")
            if in_gdb_list:  # Check if the list is not empty
                in_gdb = in_gdb_list[0]
                in_gdb = in_gdb_list[0]
                print("    gdb " + in_gdb)
                arcpy.env.workspace \
                    = in_gdb
                i = i + 1
                out_fc = os.path.join(OSMM_out_gdb, "OSMM_tile_" + folder)
                print("    Copying to " + out_fc)
                arcpy.CopyFeatures_management(fc_name, out_fc)
            else:
                print("No geodatabase files found in the workspace.")


if merge_tiles:
    print("Merging tiles")
    arcpy.env.workspace = OSMM_out_gdb
    in_fcs = arcpy.ListFeatureClasses()
    arcpy.Merge_management(in_fcs, OSMM_fc_prep)
    print(''.join(["## Finished merge on : ", time.ctime()]))

print(''.join(["## Finished on : ", time.ctime()]))

if data_source == "CROME_PHI":
    CROME_Data = os.path.join(data_gdb, 'CROME')
    LAD_name_field = "lad20nm"
    County_field = "county"
    PHI = "PHI"
    PHI_hab_field = "mainhabs"
    CROME_data = os.path.join(data_gdb, "CROME")
    filemap = input(
        'write DONE once you have input the CROME and PHI Data into the newly built data.gdb folder, '
        'rename the CROME to be called "CROME". If there is more than one county involved type MULTI and '
        'follow further instructions')
    if filemap == 'DONE':
        print('CROME FILEMAP DONE')
    elif filemap == 'MULTI':
        os.makedirs(CROME_Folder)
        multi_Crome = True
        map2 = input("Download all necessary CROME data from link in readme and put in the CROME folder. "
                     "You can check the LADsInput file that was created if you're unsure which counties you will need. "
                      "Type DONE when set")
        if filemap == 'DONE':
            print("Goodluck !")
    else:
        filemap = input('write DONE once you have input the CROME Data into the newly built data.gdb folder')

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

#step 4 - select all necessary preparations for each dataset, the comments will determine which are necessary
LAD_names = []

# Which stages of the code do we want to run? Depends on data_source - also can be useful for debugging or updates.
if data_source == "CROME_PHI":
    prep_PHI = False
    setup_PHI = False
    clip_CROME = False
    setup_HLU = False

elif data_source == "HLU":
    prep_PHI = False     # Always false for the HLU data_source
    setup_PHI = False    # Always false for the HLU data_source
    setup_HLU = True
else:
    print("ERROR: Invalid region")
    exit()

setup_boundary = False # True if you are taking from a LAD lyr
setup_LAD_gdbs = True # always True
setup_minimum_bounding_geom = False # True if we are using non - LAD shapefiles
create_gdb = False
setup_OSMM = True
clip_OSMM = True



if setup_LAD_gdbs:
    arcpy.env.workspace = Inputs
    Inputs_list = arcpy.ListFeatureClasses()
    for LAD in Inputs_list:
        LAD_name = LAD.replace('.shp', '')
        print(LAD_name)
        # LAD_full_name = LAD.getValue(LAD_name_field)
        # LAD_county = LAD.getValue(County_field)
        # if LAD_county in counties_included:          # This can be used if there is a county field and we want to select all LADs for a county             # Or if listing each LAD separately
        LAD_name = LAD_name.replace(" ", "")
        LAD_names.append(LAD_name)

        # Set up a new geodatabase for each LAD, copy clipped OSMM, copy boundary, and clip HLU or PHI to the boundaries
        print("Setting up " + LAD_name)

        if create_gdb:
            print("  Creating new geodatabase for " + LAD_name)
            arcpy.CreateFileGDB_management(LAD_folder, LAD_name)

            LAD_gdb = os.path.join(LAD_folder, LAD_name + ".gdb")
            arcpy.env.workspace = LAD_gdb

        if setup_boundary:
            LAD_gdb = os.path.join(LAD_folder, LAD_name + ".gdb")
            arcpy.env.workspace = LAD_gdb
            print("  Creating boundary for " + LAD_name)
            arcpy.MakeFeatureLayer_management(LADs_Input, "LAD_lyr")
            arcpy.SelectLayerByAttribute_management("LAD_lyr",
                                                    where_clause=LAD_name_field + " = '" + LAD_full_name + "'")
            arcpy.CopyFeatures_management("LAD_lyr", os.path.join(LAD_gdb, "boundary"))
            arcpy.Delete_management("LAD_lyr")

        if setup_minimum_bounding_geom:
            LAD_gdb = os.path.join(LAD_folder, LAD_name + ".gdb")
            arcpy.env.workspace = LAD_gdb
            LAD = os.path.join(Inputs, LAD)
            print(" Creating a minimum bounding geometry for " + LAD_name)
            arcpy.MakeFeatureLayer_management(LAD, "MBG_lyr")
            print("Number of features in MBG layer: {}".format(arcpy.GetCount_management("MBG_lyr")))
            arcpy.MinimumBoundingGeometry_management("MBG_lyr", "boundary_mbg", geometry_type='CONVEX_HULL',
                                                     group_option='ALL')
            print("Number of features in Bounding Geometry: {}".format(arcpy.GetCount_management("boundary_mbg")))
            arcpy.CopyFeatures_management("boundary_mbg", "boundary")
            arcpy.Delete_management("MBG_lyr")
            arcpy.Delete_management("boundary_mbg")

        LAD_gdb = os.path.join(LAD_folder, LAD_name + ".gdb")
        boundary = os.path.join(LAD_gdb, "boundary")

        if setup_OSMM:
            out_fc = os.path.join(LAD_gdb, "OSMM")
            if clip_OSMM:
                print("  Clipping OSMM to LAD boundary")
                OSMM = os.path.join(data_gdb, 'OSMM')
                arcpy.MakeFeatureLayer_management(OSMM, "OSMM_lyr")
                arcpy.SelectLayerByLocation_management("OSMM_lyr", "INTERSECT",
                                                       boundary)  # To save time select all the intersecting features first
                arcpy.Clip_analysis("OSMM_lyr", boundary, out_fc)
                MyFunctions.check_and_repair(out_fc)
            else:  # If OSMM has already been clipped to a feature class called OSMM_LADname (which should be in the current folder)
                print("  Copying OSMM for " + LAD_name + " to new geodatabase")
                arcpy.CopyFeatures_management("OSMM_" + LAD_name, out_fc)

        if setup_PHI:
            PHI_List = ["Priority_Habitat_Inventory_England_1", "Priority_Habitat_Inventory_England_2"]
            LAD_gdb = os.path.join(LAD_folder, LAD_name + ".gdb")
            arcpy.env.workspace = data_gdb
            boundary = os.path.join(LAD_gdb, "boundary")
            # arcpy.MakeFeatureLayer_management(boundary, "boundary")
            for i in PHI_List:
                print("Checking correct PHI Layer")
                arcpy.MakeFeatureLayer_management(i, "PHI_v1")
                arcpy.SelectLayerByLocation_management("PHI_v1", "INTERSECT", boundary)
                numrows = arcpy.GetCount_management("PHI_v1")
                numrows = int(numrows.getOutput(0))
                print(numrows)
                if numrows == 0:
                    print("No features selected, moving to other PHI set")
                    continue
                else:
                    print("  Clipping PHI to LAD boundary")
                    out_file = os.path.join(LAD_gdb, "PHI")
                    MyFunctions.check_and_repair("PHI_v1")
                    arcpy.Clip_analysis("PHI_v1", boundary, out_file)
                    MyFunctions.check_and_repair(out_file)

            WPP = os.path.join(data_gdb, "WPP")
            print("  Clipping WPP to LAD boundary")
            out_file = os.path.join(LAD_gdb, "WPP")
            arcpy.Clip_analysis(WPP, boundary, out_file)
            MyFunctions.check_and_repair(out_file)
            OMHD = os.path.join(data_gdb, "OMHD")
            print("  Clipping OMHD to LAD boundary")
            out_file = os.path.join(LAD_gdb, "OMHD")
            arcpy.Clip_analysis(OMHD, boundary, out_file)
            MyFunctions.check_and_repair(out_file)

        if prep_PHI:
            arcpy.env.workspace = LAD_gdb
            print("Preparing PHI datasets")
            # main PHI dataset
            # arcpy.MakeFeatureLayer_management(PHI, "PHI")
            # MyFunctions.check_and_repair("PHI_1")
            print('Dissolving PHI')
            arcpy.Dissolve_management("PHI", "PHI_diss_over10m2", PHI_hab_field, multi_part="SINGLE_PART")
            MyFunctions.delete_by_size("PHI_diss_over10m2", 10)
            # Copy habitat into a new field called 'PHI' (for neatness)
            print('Adding Field')
            MyFunctions.check_and_add_field("PHI_diss_over10m2", "PHI", "TEXT", 100)
            arcpy.CalculateField_management("PHI_diss_over10m2", "PHI", "!" + PHI_hab_field + "!", "PYTHON_9.3")
            arcpy.DeleteField_management("PHI_diss_over10m2", PHI_hab_field)
            # Wood pasture and parkland with scattered trees
            print('Dissolving on habitat')
            arcpy.Dissolve_management("WPP", "WPP_diss_over10m2", "prihabtxt",
                                      multi_part="SINGLE_PART")
            MyFunctions.delete_by_size("WPP_diss_over10m2", 10)
            # Copy 'Main_habit' into a new field called 'WPP' (for neatness)
            MyFunctions.check_and_add_field("WPP_diss_over10m2", "WPP", "TEXT", 100)
            arcpy.CalculateField_management("WPP_diss_over10m2", "WPP", "!prihabtxt!", "PYTHON_9.3")
            arcpy.DeleteField_management("WPP_diss_over10m2", "prihabtxt")
            # Open mosaic habitats on previously developed land
            arcpy.Dissolve_management("OMHD", "OMHD_diss_over10m2", "prihabtxt", multi_part="SINGLE_PART")
            MyFunctions.delete_by_size("OMHD_diss_over10m2", 10)
            # Copy 'Main_habit' into a new field called 'OMHD' (for neatness)
            MyFunctions.check_and_add_field("OMHD_diss_over10m2", "OMHD", "TEXT", 100)
            arcpy.CalculateField_management("OMHD_diss_over10m2", "OMHD", "!prihabtxt!", "PYTHON_9.3")
            arcpy.DeleteField_management("OMHD_diss_over10m2", "prihabtxt")
            # Union
            print("Unioning the three PHI datasets")
            arcpy.Union_analysis(["PHI_diss_over10m2", "WPP_diss_over10m2", "OMHD_diss_over10m2"], "PHI_union",
                                 "NO_FID")

            print("Copying WPP or OMHD to blank PHI fields")
            # Fill in "PHI" field where it is blank, with WPP or OMHD (OMHD takes priority as WPP can cover large mixed areas indiscriminately)
            # This bit not tested since rewrite...
            expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%') AND (OMHD IS NOT NULL AND OMHD <> '')"
            MyFunctions.select_and_copy("PHI_union", "PHI", expression, "!OMHD!")
            expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%') AND (WPP IS NOT NULL AND WPP <> '')"
            expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%') AND (WPP IS NOT NULL AND WPP <> '')"
            MyFunctions.select_and_copy("PHI_union", "PHI", expression, "!WPP!")

        if setup_HLU:
            print("  Clipping HLU to LAD boundary")
            out_file = os.path.join(LAD_gdb, "HLU")
            arcpy.Clip_analysis(HLU_data, boundary, out_file)
            MyFunctions.check_and_repair(out_file)

        if clip_CROME:
            if multi_Crome == True:
                arcpy.env.workspace = CROME_Folder
                CromeList = arcpy.ListFeatureClasses('*.shp')
                print(CromeList)
                cromelist2 = []
                c = 0
                for i in CromeList:
                    arcpy.env.workspace = LAD_gdb
                    print("Checking CROME intersection for " + i)
                    crome = os.path.join(CROME_Folder, i)
                    arcpy.MakeFeatureLayer_management(crome, "CROME_v1")
                    arcpy.SelectLayerByLocation_management("CROME_v1", "INTERSECT", boundary)
                    numrows = arcpy.GetCount_management("CROME_v1")
                    numrows = int(numrows.getOutput(0))

                    print(numrows)
                    if numrows == 0:
                        print("No features selected, moving to next CROME layer")
                        continue
                    else:
                        c = c + 1
                        print("  Clipping CROME to LAD boundary")
                        n = str(c)
                        out_file = os.path.join(LAD_gdb, "crome_" + n)
                        arcpy.Clip_analysis("CROME_v1", boundary, out_file)
                        MyFunctions.check_and_repair(out_file)
                        cromelist2.append("crome_" + n)
                if c > 1:
                    print('Merging multiple CROME selections from same layer into crome file')
                    arcpy.Merge_management(cromelist2, 'CROME')
                    print("Deleting Extra CROME layers")
                    for x in cromelist2:
                        arcpy.Delete_management(x)

                else:
                    arcpy.CopyFeatures_management('crome_1', 'CROME')
                    arcpy.Delete_management('crome_1')

            else:
                arcpy.env.workspace = data_gdb
                outfile = os.path,join(LAD_gdb, 'CROME')
                print('Clipping CROME to boundary')
                arcpy.Clip_analysis('CROME', boundary, out_file)

            print(''.join(["## Finished setting up " + LAD_name + " gdb on : ", time.ctime()]))

exit()

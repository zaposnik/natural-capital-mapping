# Pre-processes OSMM and HLU (Phase 1 habitat) layers prior to calling 'Merge_into_Base_Map.py'.
# -----------------------------------
# Code by Martin Besnier and Alison Smith (Environmental Change Institute, University of Oxford)
# This code is a research tool and has not been rigorously tested for wider use.
# ------------------------------------------------------------------------------
# Optional initial step to clip input files to the exact boundary shape.
# If this step is used, input files must be named HLU_in and OSMM_in, and boundary file
# Oxfordshire should be included in the gdb. Otherwise they should be HLU and OSMM
# ------------------------------------------------------------------------------------------------------------
# BEFORE RUNNING THIS SCRIPT
# Geometries should be repaired
# The HLU dataset should also be checked for spelling errors in Phase 1 Habitat names
# Inconsistencies in capitalisation do not need to fixed as the script can cope with them
# Any phase 1 habitats which are set as 'Unknown' or 'Unidentified' should be assigned
# categories based on the S41 habitat column  or via aerial photo interpretation
# ----------------------------------------------------------------------------------------------------------

import time
import arcpy
import MyFunctions
import os

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files
arcpy.env.XYTolerance = "0.001 Meters"

# Set parameters and workspace here
# ---------------------------------

# Set Repository equal to the file in which
Repository = r"C:\Users\zposn\Documents\NBSI\test\Oxon_County\Data\LADs_Output"

LADs = os.listdir(LADs)

#this needs to be worked on this doesn't looop iteratively this loops seperately there is a way to integrate just need to have another proper think
for LAD in LADs:
    print('Beginning work on ' + LAD)
    gdb = os.path.join(Repository, LAD)
    arcpy.env.workspace = gdb
    gdb_name = LAD
    OSMM = "OSMM"
    HLU = "HLU"
    boundary = "boundary"
    needed_fields = ["fid", "theme", "descriptivegroup", "descriptiveterm", "make", "OSMM_hab"]    # Updated for Fall 2022 version of OSMM
    HLU_Needed = ["PolyID", "Phase1Hab", "S41Habitat", "S41Hab2", "Siteref", "Copyright", "Version"] #updated for Fall 2022 version of HLU
    
    # What stages of the code do we want to run? Useful for debugging or updates

    clip_HLU = False
    clip_OSMM = False
    delete_not_needed_fields_OSMM = True
    delete_not_needed_fields_HLU = True
    delete_OSMM_overlaps = True
    delete_and_erase_HLU = True
    elim_HLU_slivers = True
    check = True
    # Main code
    # ----------
    print(''.join(["## Started analysing ", gdb_name, " on : ", time.ctime()]))
    # Optional step: clip input files. Or this could be done before.
    # Input feature classes must be suffixed with "_in" in order to clip
    if clip_HLU:
        print("Clipping " + HLU)
        arcpy.Clip_analysis(HLU + "_in", boundary, HLU)
        print("## Finished clipping " + HLU + "on : " + time.ctime())
    if clip_OSMM:
        print("Clipping " + OSMM)
        arcpy.Clip_analysis(OSMM + "_in", boundary, OSMM)
        print(''.join(["## Finished clipping OSMM on : ", time.ctime()]))
    # Optional step: delete not needed fields
    if delete_not_needed_fields_OSMM:
        print("Deleting un-necessary fields")
        MyFunctions.delete_fields("OSMM", OSMM_Needed, "OSMM_delfields")
        OSMM = "OSMM_delfields"
    if delete_not_needed_fields_HLU:
        MyFunctions.delete_fields("HLU", HLU_Needed, "HLU_delfields")
        HLU = "HLU_delfields"

    if delete_OSMM_overlaps:
        ###  Deleting overlapping "landform" features in OSMM
        print("   Deleting overlapping 'Landform' and 'Pylon' from OSMM")
        arcpy.CopyFeatures_management(OSMM, "OSMM_noLandform")
        arcpy.MakeFeatureLayer_management("OSMM_noLandform", "OSMM_layer")
        expression = "DescriptiveGroup LIKE '%Landform%' OR DescriptiveTerm IN ('Cliff','Slope','Pylon')"
        arcpy.SelectLayerByAttribute_management("OSMM_layer", where_clause=expression)
        arcpy.DeleteFeatures_management("OSMM_layer")
        arcpy.Delete_management("OSMM_layer")
        print("   Finished deleting overlapping 'Landform' and 'Pylon' from OSMM")
    
    if delete_and_erase_HLU:
        # Delete HLU water features as we prefer to use OSMM
        print("   Deleting HLU water")
        arcpy.CopyFeatures_management(HLU, "HLU_noWater")
        arcpy.MakeFeatureLayer_management("HLU_noWater", "HLU_layer")
        arcpy.SelectLayerByAttribute_management("HLU_layer", where_clause="PHASE1HAB LIKE '%ater%'")
        arcpy.DeleteFeatures_management("HLU_layer")
        arcpy.Delete_management("HLU_layer")
        print("   Finished deleting HLU water")

        # Delete HLU built up or unknown polygons as they do not add any useful information, unless S41 habitat is present
        # (change by Alison 21 Oct 2022, not yet tested)
        print("   Deleting HLU built-up or unknown areas")
        arcpy.MakeFeatureLayer_management("HLU_noWater", "HLU_layer2")
        expression = "(PHASE1HAB LIKE '%uilt-up%' or PHASE1HAB IN ['Unknown','Unidentified','']) AND S41Habitat NOT IN ['none','not assessed yet','',' ']"
        arcpy.SelectLayerByAttribute_management("HLU_layer2", where_clause=expression)
        arcpy.DeleteFeatures_management("HLU_layer2")
        arcpy.Delete_management("HLU_layer2")
        print("   Finished deleting HLU built-up or unknown areas")

        ###  Erasing OSMM buildings, roads and paths from HLU
        print("   Erasing OSMM buildings, roads and paths from HLU")
        arcpy.MakeFeatureLayer_management("OSMM_noLandform", "OSMM_layer2")
        # Alison: removed deletion of 'Roadside' as it was removing semi-natural grass verges. Manmade pavements will be removed anyway.
        arcpy.SelectLayerByAttribute_management("OSMM_layer2", where_clause="Make = 'Manmade' OR DescriptiveTerm = 'Track' OR Theme = 'Water'")
        arcpy.Erase_analysis("HLU_noWater", "OSMM_layer2", "HLU_Manerase")
        arcpy.Delete_management("OSMM_layer2")

        ##  Correcting HLU overlaps and sliver gaps because the original data contains many overlapping features.
        print("   Correcting HLU overlaps")

        # Arcpy crashes on the instruction below: it seems you cannot union a layer with itself and keep gaps?
        # Do this manually instead and then restart
        try:
            arcpy.Union_analysis([["HLU_Manerase",1]], "HLU_Manerase_union", "ALL", 0, "NO_GAPS")
        except:
            print("Please do a manual union of HLU_Manerase with itself, keeping gaps. This crashed in Arcpy")
            exit()

    if elim_HLU_slivers:
        # Eliminate and then delete slivers (just deleting creates gaps).
        arcpy.MultipartToSinglepart_management("HLU_Manerase_union", "HLU_Manerase_union_sp")
        print("   Eliminating HLU slivers")
        arcpy.MakeFeatureLayer_management("HLU_Manerase_union_sp", "HLU_elim_layer")
        arcpy.SelectLayerByAttribute_management("HLU_elim_layer", where_clause="(Shape_Area <1)")
        arcpy.Eliminate_management("HLU_elim_layer", "HLU_Manerase_union_sp_elim")

        print("   Deleting remaining standalone slivers")
        arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim", "HLU_Manerase_union_sp_elim_del")
        arcpy.MakeFeatureLayer_management("HLU_Manerase_union_sp_elim_del", "HLU_del_layer")
        arcpy.SelectLayerByAttribute_management("HLU_del_layer", where_clause="Shape_Area < 1")
        arcpy.DeleteFeatures_management("HLU_del_layer")

        print("   Deleting larger gaps")
        arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim_del", "HLU_Manerase_union_sp_elim_del2")
        arcpy.MakeFeatureLayer_management("HLU_Manerase_union_sp_elim_del2", "HLU_del_gap_layer")
        arcpy.SelectLayerByAttribute_management("HLU_del_gap_layer", where_clause="(FID_HLU_Manerase=-1)")
        arcpy.DeleteFeatures_management("HLU_del_gap_layer")

        print("   Deleting identical HLU polygons")
        arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim_del2", "HLU_Manerase_union_sp_elim_delid")
        arcpy.DeleteIdentical_management("HLU_Manerase_union_sp_elim_delid", ["Shape"])

    if check:
        arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim_delid", "HLU_preprocessed")
        MyFunctions.check_and_repair("HLU_preprocessed")
    

print(''.join(["## Completed on : ", time.ctime()]))

exit()

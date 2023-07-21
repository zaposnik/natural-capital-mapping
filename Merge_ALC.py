# Merge Agricultural Land Class with the land dataset
# Pre-process ALC by dissolving on ALC grade and then unioning with itself with no gaps and 1m tolerance
# to remove sliver gaps
# ---------------------------------------------------
import time, arcpy
import os
import  MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# Choice of method that has been used to generate the input files - this determines location and names of input files
method = "CROME_PHI"
# method = "HLU"

if method == "HLU":
    data = r'Z:\NatCap_v2\Data.gdb'
    base_map_name = "OSMM_HLU_CR"
    out_name = "OSMM_HLU_CR_ALC"
    ALC_data = r'Z:\NatCap_OS\Provisional_Agricultural_Land_Classification_(ALC)_(England)\ALC_Grades__Provisional____ADAS___Defra.shp'
elif method == "CROME_PHI":
    data = r'Z:\NatCap_OS_v2\Data.gdb'
    base_map_name = "OSMM_CROME_PHI"
    out_name = "OSMM_CR_PHI_ALC"
    ALC_data = r'Z:\NatCap_OS\Provisional_Agricultural_Land_Classification_(ALC)_(England)\ALC_Grades__Provisional____ADAS___Defra.shp'

prep_ALC = True

arcpy.env.workspace = data
if prep_ALC:
    print('Dissolving ALC by Grade')
    arcpy.Dissolve_management(ALC_data, "ALC_data_prepped", dissolve_field="ALC_GRADE", multi_part="MULTI_PART")
    ALC_data = os.path.join(data, 'ALC_data_prepped')
    print('Unioning to itself')
    arcpy.Union_analysis(ALC_data, "ALC_Union", cluster_tolerance=1, gaps='NO_GAPS')
    ALC_data = os.path.join(data, 'ALC_Union')

i = 0
repository = r"Z:\NatCap_OS_v2\Data\LADs_Output"
LADs = os.listdir(repository)
for LAD in LADs:
    gdb = os.path.join(repository, LAD)
    arcpy.env.workspace = gdb
    i = i+1
    # Need to define base map here otherwise it keeps repeating the first gdb base map
    base_map = os.path.join(gdb, base_map_name)

    numrows = arcpy.GetCount_management(base_map)
    print ("Processing " + LAD + ". No. " + str(i) + " out of " + str(len(LADs)) + ". " +
           base_map_name + " has " + str(numrows) + " rows.")

    print("    Selecting intensive agriculture polygons from land cover layer")
    arcpy.CopyFeatures_management(base_map_name, "noFarmland")
    arcpy.MakeFeatureLayer_management("noFarmland", "farmland_layer")
    expression = "(Interpreted_habitat LIKE 'Arable%' OR Interpreted_habitat = 'Agricultural land' "
    expression = expression + "OR Interpreted_habitat LIKE 'Improved%' OR Interpreted_habitat LIKE '%rchard%')"
    arcpy.SelectLayerByAttribute_management("farmland_layer", where_clause=expression)

    print("    Running Identity")
    out_file = os.path.join(folder, gdb, out_name)
    arcpy.Identity_analysis ("farmland_layer", ALC_data, out_file, "NO_FID")

    print("    Creating no_farmland layer")
    arcpy.DeleteFeatures_management("farmland_layer")

    print("    Appending")
    arcpy.Append_management("noFarmland", out_file, "NO_TEST")

    MyFunctions.check_and_repair((out_file))

    # Temporary correction
    print "Doing corrections for tidal habitats"
    MyFunctions.select_and_copy(out_file, "Interpreted_habitat", "Interpreted_habitat = 'Coastal saltmarsh'", "'Saltmarsh'")
    MyFunctions.select_and_copy(out_file, "Interpreted_habitat", "Interpreted_habitat = 'Saline lagoons'", "'Coastal lagoons'")
    MyFunctions.select_and_copy(out_file, "Interpreted_habitat", "Interpreted_habitat = 'Maritime cliff and slope'", "'Coastal rock'")
    expression = "(descriptiveterm IS NULL OR descriptiveterm = '') AND descriptivegroup LIKE '%Tidal Water%'"
    MyFunctions.select_and_copy(out_file, "Interpreted_habitat", expression, "'Saltwater'")
    expression = "descriptiveterm LIKE 'Foreshore%' AND descriptivegroup LIKE '%Tidal Water%'"
    MyFunctions.select_and_copy(out_file, "Interpreted_habitat", expression, "'Intertidal sediment'")

exit()

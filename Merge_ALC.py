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

# region = "Arc"
# region = "Oxon"
region = "NP"
# Choice of method that has been used to generate the input files - this determines location and names of input files
method = "CROME_PHI"
# method = "HLU"

if region == "Oxon" and method == "HLU":
    base_map_name = "OSMM_HLU_CR"
    out_name = "OSMM_HLU_CR_ALC"
    ALC_data = r"E:\Zach\2022\test\Data\Data.gdb\ALC_Union"
elif method == "CROME_PHI":
    if region == "Arc":
        folder = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData"
    elif region == "NP":
        folder = r"M:\urban_development_natural_capital\LADs"
    else:
        print "Invalid region"
        exit()
    arcpy.env.workspace = folder
    base_map_name = "OSMM_CROME_PHI"
    # base_map_name = "LERC"
    out_name = "OSMM_CR_PHI_ALC"
    # out_name = "LERC_ALC"
    if region == "Arc":
        gdbs = []
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        #gdbs.append(os.path.join(folder, "AylesburyVale.gdb"))
        #gdbs.append(os.path.join(folder, "Chiltern.gdb"))
        ALC_data = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Data.gdb\ALC_diss_union"
    elif region == "NP":
        gdbs = []
        # Remember Leeds is missing cos already done
        # LADs = ["Allerdale", "Barnsley", "Barrow-in-Furness", "Blackburn with Darwen", "Blackpool", "Bolton", "Bradford",
        #         "Burnley", "Bury", "Calderdale",  "Carlisle", "Cheshire East", "Cheshire West and Chester", "Chorley",
        #         "Copeland", "County Durham", "Craven", "Darlington", "Doncaster", "East Riding of Yorkshire",  "Eden",
        #         "Fylde", "Gateshead", "Halton", "Hambleton", "Harrogate",  "Hartlepool", "Hyndburn",
        #         "Kirklees", "Knowsley", "Lancaster", "Liverpool", "Manchester", "Middlesbrough", "Newcastle upon Tyne",
        #         "North East Lincolnshire", "North Lincolnshire", "Northumberland", "North Tyneside", "Oldham", "Pendle", "Preston",
        #         "Redcar and Cleveland",  "Ribble Valley", "Richmondshire", "Rochdale", "Rossendale", "Rotherham",  "Ryedale",
        #         "Salford", "Scarborough", "Sefton", "Selby", "Sheffield", "South Lakeland", "South Ribble",
        #         "South Tyneside", "St Helens", "Stockport",  "Stockton-on-Tees", "Sunderland", "Tameside", "Trafford",
        #         "Wakefield", "Warrington", "West Lancashire", "Wigan",  "Wirral", "Wyre", "York"]
        LADs = ["Copeland"]
        for LAD in LADs:
            LAD_name = LAD.replace(" ", "")
            gdbs.append(os.path.join(folder, LAD_name + ".gdb"))
        # gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        #gdbs.append(os.path.join(folder, "AylesburyVale.gdb"))
        ALC_data = r"M:\urban_development_natural_capital\Data.gdb\ALC_NP_diss_sp_union"
    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(folder, LAD))
        ALC_data = os.path.join(folder, "ALC_Union.shp")

i = 0
Repository = r"E:\Zach\2022\test\Data\LADs_Output"
LADs = os.listdir(Repository)
for LAD in LADs:
    gdb = os.path.join(Repository, LAD)
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

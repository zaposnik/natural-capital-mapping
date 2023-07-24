#
# Unions individual designations files, reading file details from an input table (DesignationFiles)
# Caution: there are hard-coded details within the code relating to the Green Belt dataset because it has an extra
# processing step to remove internal slivers and also it is chosen as a starting point for the Union.
#-------------------------------------------------------------------------------------------------------------------------------

import time, os, arcpy

import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files
arcpy.env.XYTolerance = "0.001 Meters"

# region = "Arc"
# region = "Oxon"


in_folder = r'Z:\NatCap_OS_v2'
Union_gdb = r"Z:\NatCap_OS_v2\Union_Designations.gdb"
habitat_field = True

# Note: could read in actual field lengths from the info table (or find them in a loop), but I have checked them separately
# to determine optimum values as some do not need to be so long.
desc_len = 254
desc_field = True
start_len = 40    # Green Belt name
name_len = 150
hab_len = 80

In_gdb_name = "DesignationInputs.gdb"
In_gdb = os.path.join(in_folder, In_gdb_name)
InfoTable = os.path.join(In_gdb, "DesignationFiles")

# Which stages of the code do we want to run? Useful for debugging or updates.
prep_NT_land = False #run on the first time
sort_info_table = False
copy_to_new_fc = True
clip_inputs = True
dissolve = True
union_GB = True
Setup_union_file = False
union_files = True

repository = r"Z:\NatCap_OS_v2\Data\LADs_Output"
LADs = os.listdir(repository)

if prep_NT_land:
    print('Prepping the National Trust Layers')
    arcpy.env.workspace = In_gdb
    NT_shplist = ['NT_Land_Always_Open', 'NT_Land_Limited_Access']
    for NT in NT_shplist:
        if NT == 'NT_Land_Always_Open':
            Descr = "National Trust Open Access"
        else:
            Descr = "National Trust Limited Access"
        MyFunctions.check_and_add_field(NT, 'NT_Descr', "TEXT", 250)
        arcpy.CalculateField_management(NT, "NT_Descr","'" + Descr + "'", "PYTHON_9.3")
    print('Merging NT Layers')
    arcpy.Merge_management(NT_shplist, "NT_Land")
    for NT in NT_shplist:
        arcpy.Delete_management(NT)

for LAD in LADs:
    LAD_Name = LAD.replace('.gdb', '')
    gdb = os.path.join(repository, LAD)
    arcpy.env.workspace = gdb


    if sort_info_table:
        # Sort the table in order of 'UnionOrder', so that the first table to union is at the top, and TableOrder (order for the fields)
        # BUG - the code may complain that the table already exists even though overwrite is on. So sort the table beforehand instead.
        arcpy.Sort_management(InfoTable, InfoTable + "_TableSort", [["TableOrder", "ASCENDING"]])
        arcpy.Sort_management(InfoTable, InfoTable + "_UnionSort", [["UnionOrder", "ASCENDING"]])

    arcpy.env.workspace = In_gdb

    # Loop through all the input files and find the name, habitat and designation fields
    cursor = arcpy.SearchCursor(InfoTable + "_UnionSort")

    unionInFiles = []

    for row in cursor:
        arcpy.env.workspace = In_gdb

        ShortName = row.getValue("ShortName")
        NewFile = ShortName + "_input"
        new_name = ShortName + '_name'
        hab_name = ShortName + "_hab"
        desc_name = ShortName + "_desc"

        print("Processing " + ShortName)
        DesFile= row.getValue("Filename")
        NameField = row.getValue("NameField")
        print("  Name field " + NameField)

        if copy_to_new_fcs:
            arcpy.env.workspace = In_gdb
            boundary = os.path.join(gdb, 'boundary')
            out_fc = os.path.join(gdb, NewFile)
            if clip_inputs:
                arcpy.Clip_analysis(DesFile, boundary, out_fc)
            else:
                arcpy.CopyFeatures_management(DesFile, out_fc)


            NumCount = arcpy.GetCount_management(out_fc)
            NumCount = int(NumCount.getOutput(0))
            if NumCount > 0:
                arcpy.env.workspace = gdb

                fields = []
                if NameField:
                    MyFunctions.check_and_add_field(NewFile, new_name, "TEXT", name_len)
                    # If the two names differ only in case, the check_and_add_field function will have already copied the data across and
                    # deleted the old field, so skip the calcuate field step
                    if NameField.lower() != new_name.lower():
                        arcpy.CalculateField_management(NewFile, new_name, "!" + NameField + "!", "PYTHON_9.3")
                    fields.append(new_name)

                if desc_field:
                    DescField = row.getValue("DescField")
                    if DescField:
                        print("  Desc field " + DescField)
                        MyFunctions.check_and_add_field(NewFile, desc_name, "TEXT", desc_len)
                        if DescField.lower() != desc_name.lower():
                            expression = "!" + DescField + "![:" + str(desc_len - 1) + "]"
                            arcpy.CalculateField_management(NewFile, desc_name, expression, "PYTHON_9.3")
                        fields.append(desc_name)

                if habitat_field:
                    HabField = row.getValue("HabField")
                    if HabField:
                        print("  Hab field " + HabField)
                        MyFunctions.check_and_add_field(NewFile, hab_name, "TEXT", hab_len)
                        if HabField.lower() != hab_name.lower():
                            arcpy.CalculateField_management(NewFile, hab_name, "!" + HabField + "!", "PYTHON_9.3")
                        fields.append(hab_name)

                # Delete all the fields that are not needed
                MyFunctions.delete_fields(NewFile, fields, "")

                # Dissolve each input file based on name, habitat and description
                if dissolve:
                    print("Dissolving...")
                    arcpy.Dissolve_management(NewFile, NewFile + "_diss", fields, multi_part="SINGLE_PART")
                    MyFunctions.check_and_repair(NewFile + "_diss")

                if ShortName == "GB":
                    if union_GB:
                    # Special treatment for green belt - union with no gaps and tolerance 10m then delete gaps to remove internal slivers
                    # First check if there is already a field called FID_GB_input_diss from an earlier step, and delete if there is
                        if ("FID_GB_input_diss") in arcpy.ListFields("GB_input_diss"):
                            arcpy.DeleteField_management("GB_input_diss", "FID_GB_input_diss")
                        print('projecting to British national grid')
                        output_coordinate_system = arcpy.SpatialReference(27700)
                        arcpy.Project_management("GB_input_diss", "GB_input_diss_pr", output_coordinate_system)
                        print('Deleting Old GB layer')
                        arcpy.Delete_management("GB_input_diss")
                        print('Making New GB layer')
                        arcpy.CopyFeatures_management("GB_input_diss_pr", "GB_input_diss")
                        arcpy.Delete_management('GB_input_diss_pr')
                        print('unioning to itself')
                        arcpy.Union_analysis([["GB_input_diss", 1]], ("GB_input_diss_union"), "ALL", 10, "NO_GAPS")
                        arcpy.MakeFeatureLayer_management(("GB_input_diss_union"), "gap_lyr")
                        arcpy.SelectLayerByAttribute_management("gap_lyr", where_clause="FID_GB_input_diss = -1")
                        arcpy.DeleteFeatures_management("gap_lyr")
                        arcpy.Delete_management("gap_lyr")
                    unionInFiles.append(NewFile + "_diss_union")
                else:
                    unionInFiles.append(NewFile + "_diss")

            else:
                continue
        
    if Setup_union_file:
        print("Setting up union file")
        # Add new fields to first dataset to be unioned.  Use Green Belt because that is the most accurate
        # Note: set the field length to accommodate the longest input, otherwise truncation characters cause
        # problems with 'calculate field' later on
        starting_file = "GB_input_diss_union"
        # First add the overall type, name, description and habitat fields
        MyFunctions.check_and_add_field(starting_file, "Type", "TEXT", start_len)
        MyFunctions.check_and_add_field(starting_file, "Name", "TEXT", name_len)
        if desc_field:
            MyFunctions.check_and_add_field(starting_file, "Description", "TEXT", desc_len)
        if habitat_field:
            MyFunctions.check_and_add_field(starting_file, "Habitat", "TEXT", hab_len)

        # Add the Green Belt fields
        MyFunctions.check_and_add_field(starting_file, "GreenBelt", "SHORT", 0)

        # Move Green Belt name field to after the other fields, for tidiness, by copying to a temporary field first and then deleting
        MyFunctions.check_and_add_field(starting_file, "GB_name_temp", "TEXT", start_len)
        arcpy.CalculateField_management(starting_file, "GB_name_temp", "!GB_name!", "PYTHON_9.3")
        arcpy.DeleteField_management(starting_file, "GB_name")
        MyFunctions.check_and_add_field(starting_file, "GB_name", "TEXT", name_len)
        arcpy.CalculateField_management(starting_file, "GB_name", "!GB_name_temp!", "PYTHON_9.3")
        arcpy.DeleteField_management(starting_file, "GB_name_temp")

    # Note: tried creating correct fields in starting dataset first, then merging before unioning in order to get tidy field order
    # and avoid duplicate fields. But this did not work as it created duplicate shapes instead of combining attributes for each polygon.
    # So revert to unioning, then correct field order afterwards if necessary (as fields can get out of order for no reason).
    # For some reason this did not work when I tried doing it as a standalone stage so I ended up doing it in ArcMap. Maybe workspace
    # was wrong, so i have put it before this step to see if it helps in future
    arcpy.env.workspace = gdb
    if union_files:
        print("Unioning: \n" + '\n'.join(unionInFiles))
        Desig_union = "Desig_union"
        print("Unioning List")
        arcpy.Union_analysis(unionInFiles, Desig_union, "ALL", 0.1, "NO_GAPS")

    # Now copy the fields for the other designation types into the right order
    # arcpy.env.workspace = Union_gdb   # moved above
    print ('Making Search Cursor')
    cursor = arcpy.SearchCursor(os.path.join(In_gdb, "DesignationFiles_TableSort"))

    for row in cursor:
        ShortName = row.getValue("ShortName")
        print(ShortName)
        checklist = ShortName + "_input_diss"


        def check_string_in_list(checklist, unionInFiles):
            if checklist in unionInFiles:
                if ShortName != "GB":
                    print("Tidying field order for " + ShortName)
                    MedName = row.getValue("NewName")
                    MyFunctions.check_and_add_field(Desig_union, MedName, "SHORT", 0)

                    new_name = ShortName + '_name'
                    MyFunctions.check_and_add_field(Desig_union, new_name + "_temp", "TEXT", name_len)
                    arcpy.CalculateField_management(Desig_union, new_name + "_temp", "!" + new_name + "!", "PYTHON_9.3")
                    arcpy.DeleteField_management(Desig_union, new_name)
                    arcpy.AddField_management(Desig_union, new_name, "TEXT", name_len)
                    arcpy.CalculateField_management(Desig_union, new_name, "!" + new_name + "_temp!", "PYTHON_9.3")
                    arcpy.DeleteField_management(Desig_union, new_name + "_temp")

                    if desc_field:
                        DescField = row.getValue("DescField")
                        if DescField:
                            desc_name = ShortName + "_desc"
                            MyFunctions.check_and_add_field(Desig_union, desc_name + "_temp", "TEXT", desc_len)
                            # Truncate the description field at the correct length (minus 1) because some fields have truncation error characters
                            # which cause CalculateField to crash (specifically, LGS in Oxon)
                            expression = "!" + desc_name + "![:" + str(desc_len - 1) + "]"
                            arcpy.CalculateField_management(Desig_union, desc_name + "_temp", expression, "PYTHON_9.3")
                            arcpy.DeleteField_management(Desig_union, desc_name)
                            arcpy.AddField_management(Desig_union, desc_name, "TEXT", desc_len)
                            arcpy.CalculateField_management(Desig_union, desc_name, "!" + desc_name + "_temp!",
                                                            "PYTHON_9.3")
                            arcpy.DeleteField_management(Desig_union, desc_name + "_temp")

                    if habitat_field:
                        HabField = row.getValue("HabField")
                        if HabField:
                            hab_name = ShortName + "_hab"
                            MyFunctions.check_and_add_field(Desig_union, hab_name + "_temp", "TEXT", hab_len)
                            arcpy.CalculateField_management(Desig_union, hab_name + "_temp", "!" + hab_name + "!",
                                                            "PYTHON_9.3")
                            arcpy.DeleteField_management(Desig_union, hab_name)
                            arcpy.AddField_management(Desig_union, hab_name, "TEXT", hab_len)
                            arcpy.CalculateField_management(Desig_union, hab_name, "!" + hab_name + "_temp!",
                                                            "PYTHON_9.3")
                            arcpy.DeleteField_management(Desig_union, hab_name + "_temp")
            else:
                    print('This designation layer not present in your boundary, moving to next layer')

    MyFunctions.check_and_add_field(Desig_union, "NumDesig", "SHORT", 0)
    #print('Copying Designated Union to LAD')
    #outlayer = os.path.join(gdb, 'Desig_union')
    #arcpy.management.CopyFeatures(Desig_union, outlayer)

    print("Completed. Now run Process_Designations.py to clean the data and fill in designation fields")

exit()

#
#     # Relict code for setting fields to be not visible, as this works in ArcMap, i.e.
#     # only the visible fields are transferred to the union output, but does not work in python
#     layer_name =  ShortName + "_layer"
#     arcpy.MakeFeatureLayer_management(DesFile, layer_name)
#     print("Selecting fields from " + layer_name)
#     # List of fields to select
#     fieldsToSelect = [NameField, HabField, DescField]
#     print("Fields to select: ", fieldsToSelect)
#     Create a describe object
#     desc = arcpy.Describe(layer_name)
#     if desc.dataType == "FeatureLayer":
#
#         # Create a fieldinfo object
#         field_info = desc.fieldInfo
#
#         # Use the count property to iterate through all the fields
#         for index in range(0, field_info.count):
# #            field_info.setVisible(index, "HIDDEN")
#             if field_info.getFieldName(index) not in fieldsToSelect:
#                 field_info.setVisible(index, "HIDDEN")
#             print("{0}".format(field_info.getFieldName(index)) + " {0}".format(field_info.getVisible(index)))

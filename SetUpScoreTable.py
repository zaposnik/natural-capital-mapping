#
# Sets up the table of natural capital scores
# Three starting files are needed:
# 1. Base map of habitats
# 2. Table of Agricultural Land Class multipliers "ALC_multipliers" with grade in "ALC_grade"
# 3. Matrix of scores for each habitat: "Matrix"
# Option to merge all LADs into a single file at the end
#----------------------------------------------------------------------------------------------

import time, arcpy, os
import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files
arcpy.env.qualifiedFieldNames = False

# region = "Arc"
region = "Oxon"
# Choice of method that has been used to generate the input files - this determines location and names of input files
# method = "CROME_PHI"
method = "HLU"

LERC_LWS = False

Repository = r"Z:\NatCap_OS_v2\Data\LADs_Output"
LADs = os.listdir(Repository)

if method == "HLU":
    Base_map = "OSMM_HLU_CR_ALC_Desig_GS_PA"
    hab_field = "Interpreted_habitat"
    Matrix = r"E:\Zach\2022\test\Data\Matrix.csv"
    ALC_multipliers = r"E:\Zach\2022\test\Data\ALC_multipliers.dbf"
    nature_fields = "!SAC! + !RSPB! + !SSSI! + !NNR! + !LNR! + !LWS! + !Prop_LWS! + !AncientWood! + !RdVergeNR!"
    culture_fields = "!LGS! + !MillenGn! + !DoorstepGn! + !NT! + !CountryPk! + !GreenBelt! + !AONB! + !SchMon! + !WHS! + !HistPkGdn!"
    education_fields = nature_fields + " + !LGS! +  !CountryPk! + !NT! + !SchMon! + !WHS! + !HistPkGdn!"
    all_des_fields = ["SAC", "RSPB", "SSSI", "NNR", "LNR", "LWS", "Prop_LWS", "AncientWood", "RdVergeNR",
                      "LGS", "MillenGn", "DoorstepGn", "NT", "CountryPk", "GreenBelt", "AONB", "SchMon", "WHS", "HistPkGdn"]

elif "CROME_PHI":
    Matrix = r"E:\Zach\2022\test\Data\Matrix.csv"
    del_fields = ["OBJECTID_1", "FID_ALC_di", "Shape_Leng", "ORIG_FID", "Base_Area", "Base_Relationship", "ORIG_FID_1",
                          "Desig_OBJID","Desig_Area", "Base_Relationship_1", "Desig_OBJID_1", "BaseID_GS", "FID_Natural_features",
                          "FID_Public_access_erase_sp", "ORIG_FID_12"]

    Base_map = "OSMM_CR_PHI_ALC_Desig_GS_PA"


    hab_field = "Interpreted_habitat"
    nature_list = ['SAC', 'SPA', 'Ramsar', 'IBA', 'RSPB', 'SSI', 'NNR', 'LNR', 'AW']
    culture_list = ['MillenGn', 'DoorstepGn', 'NT', 'CountryPk', 'GreenBelt', 'AONB','SchMon', 'WHS','HistPkGdn']
    education_list = ['SAC', 'SPA', 'Ramsar', 'IBA', 'RSPB', 'SSI', 'NNR', 'LNR', 'AW','CountryPk', 'NT','SchMon','WHS','HistPkGdn']
    all_des_list = ["SAC", "SPA", "Ramsar", "IBA", "RSPB", "SSSI", "NNR", "LNR", "AW",
                      "MillenGn", "DoorstepGn", "NT", "CountryPk", "GreenBelt", "AONB", "SchMon", "WHS", "HistPkGdn"]

    ALC_multipliers = r"E:\Zach\2022\test\Data\ALC_multipliers.dbf"
    #nature_fields = "!SAC! + !SPA! + !Ramsar! + !IBA! + !RSPB! + !SSSI! + !NNR! + !LNR! + !AncientWood!"
    #culture_fields = "!MillenGn! + !DoorstepGn! + !NT! + !CountryPk! + !GreenBelt! + !AONB! + !SchMon! + !WHS! + !HistPkGdn!"
    #education_fields = nature_fields + " + !CountryPk! + !NT! + !SchMon! + !WHS! + !HistPkGdn!"
    all_des_fields = ["SAC", "SPA", "Ramsar", "IBA", "RSPB", "SSSI", "NNR", "LNR", "AncientWood",
                      "MillenGn", "DoorstepGn", "NT", "CountryPk", "GreenBelt", "AONB", "SchMon", "WHS", "HistPkGdn"]


historic_data = True
null_to_zero = False    # Only needed if any rows containing designations have some NULL values - should not happen normally
# Special case: set to true for Arc LERC data because LWS is coded as a separate field


# Multiplier for aesthetic value if area is in an AONB
AONB_multiplier = 1.1
Max_des_mult = 1.2
Max_food_mult = 2.4

# Which stages of the script do we want to run? (Useful for debugging or for updating only certain scores)
# Temporary correction
correct_habitats = False

tidy_fields = False
join_tables = True
food_scores = True
aesthetic_scores = True
other_cultural = True
public_access_multiplier = True
calc_averages = True
calc_max = True



for LAD in LADs:
    gdb = os.path.join(Repository, LAD)
    area_tag = os.path.splitext(LAD)[0]
    arcpy.env.workspace = gdb
    numrows = arcpy.GetCount_management(Base_map)
    print (''.join(["### Started processing ", LAD, " on ", time.ctime(), ": ", str(numrows), " rows"]))

    if tidy_fields:
        print("Deleting surplus fields ")
        arcpy.DeleteField_management(Base_map, del_fields)

    print ("Area is " + area_tag)
    NatCap_scores = "NatCap_" + area_tag.replace("-", "")

    if correct_habitats:

        data_gdb = r"E:\Zach\2022\test\Data\PublicAccess"
        AccessTable_name = "AccessMult_tble.csv"
        AccessTable = os.path.join(data_gdb, "AccessMult_tble.csv")


        print("Correcting OMHD where there is a greenspace designation")
        print("Allotments")
        expression = "Interpreted_habitat_temp = 'Open mosaic habitats' AND GreenSpace = 'Allotments Or Community Growing Spaces'"
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp", expression,"'Allotments, city farm, community garden'")
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp", expression,"'Allotments, city farm, community garden'")
        print("Sport and play")
        expression = "Interpreted_habitat_temp = 'Open mosaic habitats'"
        expression = expression + " AND GreenSpace IN ('Playing Field', 'Other Sports Facility', 'Play Space', 'Tennis Court','Bowling Green')"
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp", expression,"'Natural sports facility, recreation ground or playground'")
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp", expression,"'Natural sports facility, recreation ground or playground'")
        print("Churchyards")
        expression = "Interpreted_habitat_temp = 'Open mosaic habitats' AND (GreenSpace = 'Cemetery' OR GreenSpace = 'Religious Grounds')"
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp", expression,"'Cemeteries and churchyards'")
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp", expression,"'Cemeteries and churchyards'")
        print("Golf")
        expression = "Interpreted_habitat_temp = 'Open mosaic habitats' AND GreenSpace = 'Golf Course'"
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp", expression,"'Golf course'")
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp", expression,"'Golf course'")
        print("Amenity")
        expression = "Interpreted_habitat_temp = 'Open mosaic habitats' AND GreenSpace IN ('Amenity - Residential Or Business', 'Public Park Or Garden')"
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp", expression,"'Amenity grassland'")
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp", expression,"'Amenity grassland'")

        print("Correcting Public Access for new greenspace rows")
        # Green spaces (from OS green space and OS open green space) - correct for Rail in OSGS Amenity residential
        # Exclude National Trust as that has better information on access, so we don't want to overwrite it
        # Also exclude arable land (added 4/10/2020 at end of EA work) otherwise incorrect OSGS 'Amenity' over-rides habitat type
        arcpy.MakeFeatureLayer_management("OSMM_CR_PHI_ALC_Desig_GS_PA", "sel_lyr4")
        expression = " Interpreted_habitat_temp NOT IN ('Arable', 'Arable and scattered trees', 'Arable fields, horticulture and temporary grass') "
        expression = expression + "AND GreenSpace IS NOT NULL AND GreenSpace <> '' "
        expression = expression + "AND descriptivegroup NOT LIKE '%Rail%' AND (NT IS NULL OR NT = 0)"
        arcpy.SelectLayerByAttribute_management("sel_lyr4", where_clause=expression)
        NumCount = arcpy.GetCount_management("sel_lyr4")
        NumCount = int(NumCount.getOutput(0))
        if NumCount > 0:
            arcpy.CalculateField_management("sel_lyr4", "PAType", "!GreenSpace!", "PYTHON_9.3")
            arcpy.CalculateField_management("sel_lyr4", "PADescription", "!GreenSpace!", "PYTHON_9.3")
            arcpy.AddJoin_management("sel_lyr4", "PADescription", AccessTable, "Description", "KEEP_ALL")
            arcpy.CalculateField_management("sel_lyr4", "Source", "'GreenSpace'", "PYTHON_9.3")
            arcpy.CalculateField_management("sel_lyr4", "AccessType", "!" + AccessTable_name + ".AccessType!", "PYTHON_9.3")
            arcpy.CalculateField_management("sel_lyr4", "AccessMult", "!" + AccessTable_name + ".AccessMult!", "PYTHON_9.3")
            arcpy.RemoveJoin_management("sel_lyr4", AccessTable_name)
        arcpy.Delete_management("sel_lyr4")

        # Correction for school grounds from OSGS because playing fields were omitted (this will omit non-urban schools not in OSGS)
        print("      Interpreting schools")
        arcpy.MakeFeatureLayer_management("OSMM_CR_PHI_ALC_Desig_GS_PA", "school_lyr")
        arcpy.SelectLayerByAttribute_management("school_lyr", where_clause="OSGS_priFunc = 'School Grounds'")
        NumCount = arcpy.GetCount_management("school_lyr")
        NumCount = int(NumCount.getOutput(0))
        if NumCount > 0:
            arcpy.CalculateField_management("school_lyr", "PAType", "'School Grounds'", "PYTHON_9.3")
            arcpy.CalculateField_management("school_lyr", "PADescription", "'School Grounds'", "PYTHON_9.3")
            arcpy.AddJoin_management("school_lyr", "PADescription", AccessTable, "Description", "KEEP_ALL")
            arcpy.CalculateField_management("school_lyr", "Source", "'OSGS'", "PYTHON_9.3")
            arcpy.CalculateField_management("school_lyr", "AccessType", "!" + AccessTable_name + ".AccessType!", "PYTHON_9.3")
            arcpy.CalculateField_management("school_lyr", "AccessMult", "!" + AccessTable_name + ".AccessMult!", "PYTHON_9.3")
            arcpy.RemoveJoin_management("school_lyr", AccessTable_name)
        arcpy.Delete_management("school_lyr")

        print("Correcting OMHD for sealed surfaces")
        expression = "Interpreted_habitat_temp = 'Open mosaic habitats' AND Interpreted_habitat = 'Sealed surface'"
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp", expression,"'Sealed surface'")
        MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp", expression,"'Sealed surface'")

        # print "Correcting natural land within PHI woodland (should be rides)"
        # Decided not to do this because sometimes PHI is correct
        # expression = "PHI = 'Deciduous woodland' AND Interpreted_habitat_temp = 'Woodland: broadleaved, semi-natural' AND OSMM_hab = 'Natural surface'"
        # MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp", expression,"'Natural surface'")
        # MyFunctions.select_and_copy("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp", expression,"'Natural surface'")

        print("Copying new hab field across")
        arcpy.CalculateField_management("OSMM_CR_PHI_ALC_Desig_GS", "Interpreted_habitat", "!Interpreted_habitat_temp!", "Python_9.3")
        arcpy.CalculateField_management("OSMM_CR_PHI_ALC_Desig_GS_PA", "Interpreted_habitat", "!Interpreted_habitat_temp!", "Python_9.3")
        print("Deleting surplus fields from GS layer")
        MyFunctions.tidy_fields("OSMM_CR_PHI_ALC_Desig_GS", True, ["fid"])
        print("Deleting temp habitat field")
        arcpy.DeleteField_management("OSMM_CR_PHI_ALC_Desig_GS","Interpreted_habitat_temp")
        arcpy.DeleteField_management("OSMM_CR_PHI_ALC_Desig_GS_PA","Interpreted_habitat_temp")

    # Join base map to scores
    # -----------------------
    if join_tables:
        # Join table to matrix of scores
        print("Joining matrix")
        arcpy.MakeFeatureLayer_management(Base_map, "join_layer")
        arcpy.AddJoin_management("join_layer", hab_field, Matrix, "Habitat")

        # Join table to ALC multipliers
        print("Joining ALC multipliers")
        arcpy.AddJoin_management("join_layer", "ALC_grade", ALC_multipliers, "ALC_grade")

        # Export to new table
        print ("Creating output dataset " + NatCap_scores)
        arcpy.CopyFeatures_management("join_layer", NatCap_scores)
        arcpy.Delete_management("join_layer")

        # If no historic data, add a dummy field for the Scheduled Monument flag which is expected for the
        # cultural multipliers. Should probably delete this later as well.
        if historic_data == False:
            MyFunctions.check_and_add_field(NatCap_scores,"SchMon","Short", 0)
            arcpy.CalculateField_management(NatCap_scores,"SchMon",0,"Python_9.3")

    # Food: apply ALC multiplier
    # --------------------------
    if food_scores:
        # Add new field and copy over basic food score (this is the default for habitats not used for intensive food production)
        print("Setting up food multiplier field")
        MyFunctions.check_and_add_field(NatCap_scores,"FoodxALC", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores,"FoodxALC","!Food!", "PYTHON_9.3")

        # Select intensive food production habitats and multiply food score by ALC multiplier (ignore 'Arable field margins')
        print("Multiplying by ALC multiplier")
        expression = "(" + hab_field + " = 'Arable' OR " + hab_field + " LIKE 'Arable and%' " \
                     "OR " + hab_field + " LIKE 'Cultivated%' OR " + hab_field + " LIKE 'Improved grass%' " \
                     "OR " + hab_field + " LIKE 'Agric%' OR " + hab_field + " ='Orchard') AND ALC_mult IS NOT NULL"
        arcpy.MakeFeatureLayer_management(NatCap_scores, "Intensive_farmland")
        arcpy.SelectLayerByAttribute_management("Intensive_farmland", where_clause=expression)
        arcpy.CalculateField_management("Intensive_farmland", "FoodxALC", "!Food! * !ALC_mult!", "PYTHON_9.3")
        arcpy.Delete_management("Intensive_farmland")

        # Add new field and calculate normalised food score
        print("Calculating normalised food score")
        MyFunctions.check_and_add_field(NatCap_scores,"Food_ALC_norm","Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Food_ALC_norm", "!FoodxALC!  / " + str(Max_food_mult), "PYTHON_9.3")

    # Aesthetic value: apply AONB multiplier
    #--------------------------------------
    if aesthetic_scores:
        field_names = [field.name for field in arcpy.ListFields(NatCap_scores)]
        if 'AONB' in field_names:
            # Add new field and populate with aesthetic value score (default for habitats not in AONB)
            print("Setting up new field for adjusted aesthetic value")
            MyFunctions.check_and_add_field(NatCap_scores, "Aesthetic_AONB", "Float", 0)
            arcpy.CalculateField_management(NatCap_scores, "Aesthetic_AONB", "!Aesthetic!", "PYTHON_9.3")

            # Select AONB areas and multiply aesthetic value score by AONB multiplier

            print("Multiplying by AONB multiplier")
            arcpy.MakeFeatureLayer_management(NatCap_scores, "AONB_layer")
            arcpy.SelectLayerByAttribute_management("AONB_layer", where_clause="AONB = 1")
            arcpy.CalculateField_management("AONB_layer", "Aesthetic_AONB", "!Aesthetic! * " + str(AONB_multiplier),
                                            "PYTHON_9.3")
            arcpy.Delete_management("AONB_layer")

            # Add new field and calculate normalised aesthetic value score
            print("Calculating normalised aesthetic score")
            MyFunctions.check_and_add_field(NatCap_scores, "Aesthetic_norm", "Float", 0)
            arcpy.CalculateField_management(NatCap_scores, "Aesthetic_norm",
                                            "!Aesthetic_AONB! / " + str(AONB_multiplier), "PYTHON_9.3")



    # Education, Interaction with Nature and Sense of Place: apply multiplier based on number of designations
    # -------------------------------------------------------------------------------------------------------
    if other_cultural:

        nature_fields = "!"
        t = 0
        new_nature_list = []
        print('creating the nature fields list')
        field_names = [field.name for field in arcpy.ListFields(NatCap_scores)]
        for i, field_name in enumerate(nature_list):
            if field_name in field_names:
                t = t + 1
                print(t)
                if t > 1:
                    nature_fields += "! + !"
                nature_fields += "'{}'".format(field_name)

                new_nature_list.append(field_name)

        nature_fields += "!"
        nature_fields = nature_fields.replace("'", "")
        print(nature_fields)
        # Add new fields and populate with number of nature and cultural designations
        # Replace null values with zeros - not usually needed as all rows containing designations should not contain nulls

        culture_fields = "!"
        new_culture_list = []
        print('Creating the new culture list')
        field_names = [field.name for field in arcpy.ListFields(NatCap_scores)]
        t = 0
        for i, field_name in enumerate(culture_list):
            if field_name in field_names:
                t = t + 1
                print(t)
                if t > 1:
                    culture_fields += "! + !"
                culture_fields += "'{}'".format(field_name)

                new_culture_list.append(field_name)

        culture_fields += "!"
        culture_fields = culture_fields.replace("'", "")
        print(culture_fields)

        education_fields = "!"
        new_education_list = []
        print('Creating the new education list')
        field_names = [field.name for field in arcpy.ListFields(NatCap_scores)]
        t = 0
        for i, field_name in enumerate(education_list):
            if field_name in field_names:
                t = t + 1
                print(t)
                if t > 1:
                    education_fields += "! + !"
                education_fields += "'{}'".format(field_name)

                new_education_list.append(field_name)

        education_fields += "!"
        education_fields = education_fields.replace("'", "")
        print(education_fields)


        if null_to_zero:
            print ("Replacing nulls with zeros in designation indices, before adding")
            for des_field in all_des_fields:
                MyFunctions.select_and_copy(NatCap_scores, des_field, des_field + " IS NULL", 0)
        print("Adding nature, cultural and education designation fields")
        MyFunctions.check_and_add_field(NatCap_scores, "NatureDesig", "SHORT", 0)
        if nature_fields == '!!':
            print('nature fields empty')
        else:
            arcpy.CalculateField_management(NatCap_scores, "NatureDesig", nature_fields, "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "CultureDesig", "SHORT", 0)
        if culture_fields == '!!':
            print('culture fields empty')
        else:
            arcpy.CalculateField_management(NatCap_scores, "CultureDesig", culture_fields, "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "EdDesig", "SHORT", 0)
        if education_fields == '!!':
            print('education fields empty')
        else:
            arcpy.CalculateField_management(NatCap_scores, "EdDesig", education_fields, "PYTHON_9.3")

        # Add new fields and populate with adjusted scores
        print("Setting up new fields for adjusted education, interaction with nature and sense of place values")
        MyFunctions.check_and_add_field(NatCap_scores, "Education_desig", "Float", 0)
        MyFunctions.check_and_add_field(NatCap_scores, "Nature_desig", "Float", 0)
        MyFunctions.check_and_add_field(NatCap_scores, "Sense_desig", "Float", 0)

        # Special case for LERC LWS - add extra designation if proportion of polygon overlapping LWS site is >0.5
        if LERC_LWS:
            print("Setting up LWS designation score for LERC data")
            MyFunctions.select_and_copy(NatCap_scores, "NatureDesig", "NatureDesig IS NULL", 0)
            MyFunctions.select_and_copy(NatCap_scores, "EdDesig", "EdDesig IS NULL", 0)
            MyFunctions.select_and_copy(NatCap_scores, "NatureDesig","LWS_p >= 0.5", "!NatureDesig! + 1")
            MyFunctions.select_and_copy(NatCap_scores, "EdDesig","LWS_p >= 0.5", "!EdDesig! + 1")

        codeblock = """
def DesMult(NatureDesig, CultureDesig, EdDesig, ScheduledMonument, Habitat, GreenSpace, Score, Service):
    # GreenSpace currently not used (see notes for reasons) but could be in future
    if Service == "SensePlace":
        if NatureDesig is None or NatureDesig == 0:
            if CultureDesig is None or CultureDesig == 0:
                NumDesig = 0
            else:
                NumDesig = CultureDesig
        elif CultureDesig is None or CultureDesig == 0:
            NumDesig = NatureDesig
        else:
            NumDesig = NatureDesig + CultureDesig
    elif Service == "Nature":
        NumDesig = NatureDesig
    elif Service == "Education":
        NumDesig = EdDesig
    else:
        return Score

    if NumDesig is None or NumDesig == 0:
        NewScore = Score / 1.2
    elif NumDesig == 1:
        NewScore = 1.1 * Score / 1.2
    elif NumDesig == 2:
        NewScore = 1.15 * Score / 1.2
    elif NumDesig >=3:
        NewScore = 1.2 * Score / 1.2
    else:
        NewScore = Score

    # Minimum score of 7/10 for scheduled monuments unless arable (min score 3) or sealed surface (Score =0)
    if Service == "SensePlace" or Service == "Education":
        if ScheduledMonument == 1 and Score > 0:
            if Habitat == "Arable":
                if NewScore <3:
                    NewScore = 3
            elif NewScore <7:
                NewScore = 7
 
    return NewScore
"""
        print("Calculating education field")
        expression = 'DesMult(!NatureDesig!, !CultureDesig!, !EdDesig!, !SchMon!, !Interpreted_habitat!, !GreenSpace!, !Education!, ' \
                     '"Education" )'
        arcpy.CalculateField_management(NatCap_scores, "Education_desig", expression, "PYTHON_9.3", codeblock)
        print("Calculating nature field")
        expression = 'DesMult( !NatureDesig! , !CultureDesig!, !EdDesig!, !SchMon!, !Interpreted_habitat!, !GreenSpace!, !Nature!, "Nature" )'
        arcpy.CalculateField_management(NatCap_scores,"Nature_desig", expression, "PYTHON_9.3", codeblock)
        print("Calculating sense of place field")
        expression = 'DesMult(!NatureDesig!, !CultureDesig!, !EdDesig!, !SchMon!, !Interpreted_habitat!, !GreenSpace!, !SensePlace!, ' \
                     '"SensePlace")'
        arcpy.CalculateField_management(NatCap_scores, "Sense_desig", expression, "PYTHON_9.3", codeblock)

    if public_access_multiplier:
        # Add field and multiply by access indicator
        print ("Calculating recreation field with public access multiplier")
        MyFunctions.check_and_add_field(NatCap_scores, "Rec_access", "FLOAT", 0)
        arcpy.CalculateField_management(NatCap_scores, "Rec_access", "!Recreation! * !AccessMult!", "PYTHON_9.3")
        # Set all habitats within path buffers to an absolute score of 7.5 out of 10 (unless sealed surface)
        MyFunctions.select_and_copy(NatCap_scores, "Rec_access", "AccessType = 'Path' AND Recreation > 0", 7.5)
        # Replace null values with zeros (needed later for calculating scenario impact)
        MyFunctions.select_and_copy(NatCap_scores, "Rec_access", "Rec_access IS NULL", 0)

    if calc_averages:
        print("Calculating averages")
        MyFunctions.check_and_add_field(NatCap_scores, "AvSoilWatReg", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "AvSoilWatReg",
                                        '(!Flood! + !Erosion! + !WaterQual!)/3', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "AvCAQCoolNs", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "AvCAQCoolNs",
                                        '(!Carbon! + !AirQuality! + !Cooling! + !Noise!)/4', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av7Reg", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av7Reg",
                                        '((!AvSoilWatReg! * 3) + (!AvCAQCoolNs! * 4))/7', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "AvPollPest", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "AvPollPest",
                                        '(!Pollination! + !PestControl!)/2', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av9Reg", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av9Reg",
                                        '((!Av7Reg! * 7) + (!AvPollPest! * 2))/ 9', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "AvCultNoRec", "Float", 0)
        if 'AONB' in field_names:
            arcpy.CalculateField_management(NatCap_scores, "AvCultNoRec",
                                        '(!Aesthetic_norm! + !Education_desig! + !Nature_desig! + !Sense_desig!)/4', "PYTHON_9.3")
        else:
            arcpy.CalculateField_management(NatCap_scores, "AvCultNoRec",
                                        '(!Education_desig! + !Nature_desig! + !Sense_desig!)/4', "PYTHON_9.3")


        MyFunctions.check_and_add_field(NatCap_scores, "Av5Cult", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av5Cult", '(!Rec_access! + (!AvCultNoRec! * 4))/5', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av14RegCult", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av14RegCult",
                                        '((!Av9Reg! * 9) + (!Av5Cult!) * 5)/14', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av15WSRegCult", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av15WSRegCult",
                                        '((!Av14RegCult! * 14)+ !WaterProv!)/15', "PYTHON_9.3")

    if calc_max:
        print("Calculating maximum scores")
        MyFunctions.check_and_add_field(NatCap_scores, "MaxRegCult", "FLOAT", 0)
        if 'AONB' in field_names:
            arcpy.CalculateField_management(NatCap_scores, "MaxRegCult",
                                        'max(!Flood!, !Erosion!, !WaterQual!, !Carbon!, !AirQuality!, !Cooling!, !Noise!, '
                                        '!Pollination!, !PestControl!, !Aesthetic_norm!, !Education_desig!, !Nature_desig!,'
                                        ' !Sense_desig!, !Rec_access!)', "PYTHON_9.3")
        else:
            arcpy.CalculateField_management(NatCap_scores, "MaxRegCult",
                                            'max(!Flood!, !Erosion!, !WaterQual!, !Carbon!, !AirQuality!, !Cooling!, !Noise!, '
                                            '!Pollination!, !PestControl!, !Education_desig!, !Nature_desig!,'
                                            ' !Sense_desig!, !Rec_access!)', "PYTHON_9.3")



        MyFunctions.check_and_add_field(NatCap_scores, "MaxWSRegCult", "Float", 0)
        if 'AONB' in field_names:
            arcpy.CalculateField_management(NatCap_scores, "MaxWSRegCult",
                                        'max(!WaterProv!, !Flood!, !Erosion!, !WaterQual!, !Carbon!, !AirQuality!, !Cooling!, !Noise!, '
                                        '!Pollination!, !PestControl!, !Aesthetic_norm!, !Education_desig!, !Nature_desig!,'
                                        ' !Sense_desig!, !Rec_access!)', "PYTHON_9.3")
        else:
            arcpy.CalculateField_management(NatCap_scores, "MaxWSRegCult",
                                            'max(!WaterProv!, !Flood!, !Erosion!, !WaterQual!, !Carbon!, !AirQuality!, !Cooling!, !Noise!, '
                                            '!Pollination!, !PestControl!, !Education_desig!, !Nature_desig!,'
                                            ' !Sense_desig!, !Rec_access!)', "PYTHON_9.3")

        # MaxRegCultFood is the max of all regulating and cultural services or food production
        MyFunctions.check_and_add_field(NatCap_scores, "MaxRegCultFood", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "MaxRegCultFood", 'max(!Food_ALC_norm!, !MaxRegCult!)', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "MaxWSRegCultFood", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "MaxWSRegCultFood", 'max(!WaterProv!, !MaxRegCultFood!)', "PYTHON_9.3")

    print("## Completed " + LAD + " on " +  time.ctime())

exit()

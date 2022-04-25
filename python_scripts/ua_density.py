#-------------------------------------------------------------------------------
# Name:        Transport infrastructure area UA
#
# Purpose:     The purpose of this script is to assess transport infrastructure (ti) of a city/FUA based on Urban Atlas (UA) 2018 land use/land cover data.
#              It calculates two indicators, ti_percentage (how many % of area is covered by ti) and ti_per_capita (how many m2 of ti per one inhabitant).
#
# Author:      Adam Tóth
#
# This script is a part of bachelor thesis "Possibilities of calculation characteristics of the transport network of states and cities"
# supervisor: doc. Ing. Zdena Dobešová, Ph.D.
# Department of Geoinformatics, Faculty of Science, Palacký University in Olomouc, Czech republic
#
# Created:     24.01.2022
#-------------------------------------------------------------------------------

# import library arcpy and allow overwriting features with the same name
import arcpy
arcpy.env.overwriteOutput = True

def main():
    arcpy.AddMessage("The script has started!")

    # getting inputs from parameters in tool's interface
    data = arcpy.GetParameterAsText(0)
    area = arcpy.GetParameterAsText(1)
    hex_or_own = arcpy.GetParameterAsText(2)
    size = arcpy.GetParameterAsText(3)
    own_layer = arcpy.GetParameterAsText(4)
    workspace = arcpy.GetParameterAsText(5)
    cor_sys_string = arcpy.GetParameterAsText(11)

    area_name = area[(area.rfind(chr(92))+1):]

    # ti_types is a list of 5 boolean-type strings which tell whether the respective type of ti should be included in the calculation or not
    # ftroads: 4, oroads: 5, rails: 6, ports: 7, airports: 8 (positions in the ti_types list are 0, 1, 2, 3, 4, respectively)
    ti_types = []
    for i in range(6,11):
        ti_types.append(arcpy.GetParameterAsText(i))

    # checking input data, if it is a polygon layer, if it has a field 'Pop2018' of Integer type,
    # if it has a field 'code_2018' of String type and if it contains at least one ti feature
    desc = arcpy.Describe(data)
    fields = arcpy.ListFields(data)
    check_d = 0

    if desc.shapeType == "Polygon":
        for i in fields:
            if (i.name == 'code_2018') and (i.type == 'String'):
                with arcpy.da.SearchCursor(data, i.name) as cursor:
                    for row in cursor:
                        if (int(row[0]) > 12209) and (int(row[0]) < 12401):
                            check_d += 1
                            break
            if (i.name == 'Pop2018') and (i.type == 'Integer'):
                check_d += 1

    # check of output layer: if user selected that they want to use their own layer, it has to be provided in "own_layer"
    # if user wanted to use hexagon grid, the size of hexagon has to be provided in "size"
    if hex_or_own == "true":
        if own_layer != "":
            check_d += 1
    else:
        if size != "":
            check_d += 1

    # if it doesn't meet the requirements, script is ended
    if check_d < 3:
        del data, area, size, workspace, cor_sys_string, desc, fields, i, cursor, row, check_d, ti_types, area_name, hex_or_own, own_layer
        arcpy.AddError("Your data is not suitable for this script.")
    else:
        arcpy.AddMessage("Your data layer is OK.")

        # if the workspace is geodatabase, the result will be feature class in gdb,
        # if the workspace is folder, the result will be shapefile in that folder, but first,
        # "working.gdb" is created in the folder and from this geodatabase, the result will be exported as a shapefile into the folder
        leng = len(workspace)
        ending = workspace[(leng-4):leng]
        if ending != ".gdb":
            arcpy.management.CreateFileGDB(workspace, "working.gdb")
            workspace = workspace + chr(92) + "working.gdb"

        # setting of workspace in environments
        arcpy.env.workspace = workspace

        # checking and setting the main coordinate system and projecting data into it
        data_spref = arcpy.Describe(data).spatialReference
        area_spref = arcpy.Describe(area).spatialReference
        if hex_or_own == "true":
            own_layer_spref = arcpy.Describe(own_layer).spatialReference

        # if user selected projected coordinate system with meter as its unit, it is set as the main coordinate system
        if (cor_sys_string[:6] == "PROJCS") and ('UNIT["Meter",1.0]' in cor_sys_string):
            cor_sys = arcpy.SpatialReference()
            cor_sys.loadFromString(cor_sys_string)
            arcpy.AddMessage(f"You selected this projected coordinate system for the output: {cor_sys.name}")
        # if user selected geographic coordinate system or projected coordinate system with different unit than meter or they selected nothing,
        # this is the order of setting the main coordinate system:
        # the coordinate system of their own output layer, the coordinate system of UA data, the system of area, WGS84 Web Mercator (Auxiliary Sphere)
        else:
            if hex_or_own == "true":
                if (own_layer_spref.type == "Projected") and (own_layer_spref.linearUnitName == "Meter"):
                    cor_sys = own_layer_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of your output layer {cor_sys.name} will be used.")
                elif (data_spref.type == "Projected") and (data_spref.linearUnitName == "Meter"):
                    cor_sys = data_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of UA layer {cor_sys.name} will be used.")
                elif (area_spref.type == "Projected") and (area_spref.linearUnitName == "Meter"):
                    cor_sys = area_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of area layer {cor_sys.name} will be used.")
                else:
                    cor_sys = arcpy.SpatialReference(3857)
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system and systems of input layers weren't appropriate, so {cor_sys.name} coordinate system will be used.")
            elif (data_spref.type == "Projected") and (data_spref.linearUnitName == "Meter"):
                cor_sys = data_spref
                arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of UA layer {cor_sys.name} will be used.")
            elif (area_spref.type == "Projected") and (area_spref.linearUnitName == "Meter"):
                cor_sys = area_spref
                arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of area layer {cor_sys.name} will be used.")
            else:
                cor_sys = arcpy.SpatialReference(3857)
                arcpy.AddMessage(f"You didn't select any appropriate coordinate system and systems of input layers weren't appropriate, so {cor_sys.name} coordinate system will be used.")

        # if coordinate systems of data is different from the main coordinate system, it is reprojected into that coordinate system
        if data_spref.factoryCode != cor_sys.factoryCode:
            arcpy.management.Project(data, "reprj_data", cor_sys)
            data = workspace + chr(92) + "reprj_data"
            arcpy.AddMessage(f"Data layer was reprojected from {data_spref.factoryCode} to {cor_sys.factoryCode}")

        # if coordinate systems of area is different from the main coordinate system, it is reprojected into that coordinate system
        if area_spref.factoryCode != cor_sys.factoryCode:
            arcpy.management.Project(area, "reprj_area", cor_sys)
            area = workspace + chr(92) + "reprj_area"
            arcpy.AddMessage(f"Area layer was reprojected from {area_spref.factoryCode} to {cor_sys.factoryCode}")

        # control of output polygon layer which user selected
        check_a = 0
        if hex_or_own == "true":
            # reprojection into the main coordinate system if necessary
            if own_layer_spref.factoryCode != cor_sys.factoryCode:
                arcpy.management.Project(own_layer, "reprj_own_layer", cor_sys)
                own_layer = workspace + chr(92) + "reprj_own_layer"
                arcpy.AddMessage(f"Your output layer was reprojected from {own_layer_spref.factoryCode} to {cor_sys.factoryCode}")
            del own_layer_spref
            # control whether the area layer and the output polygon layer overlap
            control_selection = arcpy.management.SelectLayerByLocation(own_layer, "INTERSECT", area)
            if int(control_selection[2]) == 0:
                control_selection = arcpy.management.SelectLayerByAttribute(own_layer, "CLEAR_SELECTION")
                arcpy.AddError("Your output layer and area layer don't overlap.")
            elif int(control_selection[2]) > 0:
                control_selection = arcpy.management.SelectLayerByAttribute(own_layer, "CLEAR_SELECTION")
                # control whether the data and the output polygon layer overlap
                control_selection = arcpy.management.SelectLayerByLocation(data, "INTERSECT", own_layer)
                if int(control_selection[2]) > 0:
                    control_selection = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
                    check_a += 1
                    arcpy.AddMessage("Your chosen polygon layer for the output is OK.")
                else:
                    arcpy.AddError("Your chosen polygon layer for the output and data layer don't overlap.")
            else:
                arcpy.AddError("Your chosen polygon layer for the output and area layer don't overlap.")
        else:
            check_a += 1

        # control of area layer, whether it is a polygon layer and if it overlaps with UA data
        desc = arcpy.Describe(area)
        control_selection = arcpy.management.SelectLayerByLocation(data, "INTERSECT", area)

        if desc.shapeType == "Polygon":
            if int(control_selection[2]) == 0:
                arcpy.AddError("Your data and area layers don't overlap.")
            # if it meets the requirements, UA data is clipped by area and population inside polygons is recalculated based on the area:
            # copy of UA data is created, into this copied layer new field "area_orig" is added, the area of polygons is loaded there,
            # then the copied layer is clipped by area, into this clipped layer new field "P_2018_orig" is added and
            # new population inside polygons is calculated as the original population divided by original area of polygons multiplied by current area of polygons
            elif int(control_selection[2]) > 0:
                check_a += 1
                arcpy.management.CopyFeatures(control_selection, "data_copy")
                arcpy.management.AddField("data_copy", "area_orig", "DOUBLE")
                arcpy.management.CalculateField("data_copy", "area_orig", '!geom_Area!')
                arcpy.analysis.Clip("data_copy", area, "clipped_data")
                arcpy.management.AddField("clipped_data", "P_2018_orig", "DOUBLE")
                arcpy.management.CalculateField("clipped_data", "P_2018_orig", '(!Pop2018!/!area_orig!)*!geom_Area!')
                data = workspace + chr(92) + "clipped_data"
                arcpy.AddMessage("Your area layer is OK, data clipped by area.")
        else:
            arcpy.AddError("Your area layer is not of polygon shape type.")

        control_selection = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")

        # if it doesn't meet the requirements, script is ended
        if check_a < 2:
            del data, area, size, workspace, cor_sys_string, desc, fields, i, cursor, row, control_selection, check_d, check_a, leng, ending
            del ti_types, area_name, data_spref, area_spref, cor_sys, hex_or_own, own_layer
        else:
            # if user selected their own output layer, it is clipped by area layer, this clipped layer is called "hex_gr"
            if hex_or_own == "true":
                arcpy.analysis.Clip(own_layer, area, "hex_gr")
                arcpy.AddMessage("Your chosen polygon layer for the output was clipped")
            # otherwise hexagon grid is generated and clipped by area layer, this clipped layer is called "hex_gr"
            else:
                # if user selects the areal unit "Unknown", it will be used as Square Kilometers
                if size[len(size)-7:len(size)] == "Unknown":
                    size = size.replace("Unknown", "SquareKilometers")
                    arcpy.AddMessage("You selected 'Unknown' as the areal unit, therefore 'Square Kilometers' will be used")

                arcpy.management.GenerateTessellation("hex_grid", area, "HEXAGON", size)
                arcpy.AddMessage("Hexagon grid generated")
                arcpy.analysis.Clip("hex_grid", area, "hex_gr")
                arcpy.AddMessage("Clipped")

            # adding geometry attribute (area) of polygons to UA data, then intersecting it, adding new field for population and calculating it proportionally to area
            # and finally dissolving all polygons in one polygon/hexagon and summing the population in one polygon/hexagon
            arcpy.management.AddGeometryAttributes(data, "AREA", "", "SQUARE_METERS")
            arcpy.analysis.Intersect([data, "hex_gr"], "data_isect", "ALL")
            arcpy.management.AddField("data_isect", "new_pop2018_ua", "DOUBLE")
            arcpy.management.CalculateField("data_isect", "new_pop2018_ua", '(!P_2018_orig!/!POLY_AREA!)*!geom_Area!')
            arcpy.management.Dissolve("data_isect", "data_isect_diss", "FID_hex_gr", [["new_pop2018_ua","SUM"]])
            arcpy.AddMessage("Population in each hexagon calculated from 2018 estimate")

            # ti  selected, in UA data there are 5 categories of ti: 12210, 12220, 12230, 12300, 12400
            # (Fast transit roads and associated land, Other roads and associated land, Railways and associated land, Port areas, Airports)
            # at first, all categories are selected, that's the default in tool's interface
            selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code_2018 = '12210' Or code_2018 = '12220' Or code_2018 = '12230' Or code_2018 = '12300' Or code_2018 = '12400'")
            s = 5
            # and then if certain category is unselected (it is 'false' or ''), it is removed from the default selection
            if ti_types[0] != 'true':
                selected_features = arcpy.management.SelectLayerByAttribute(data, "REMOVE_FROM_SELECTION", "code_2018 = '12210'")
                s -= 1
            if ti_types[1] != 'true':
                selected_features = arcpy.management.SelectLayerByAttribute(data, "REMOVE_FROM_SELECTION", "code_2018 = '12220'")
                s -= 1
            if ti_types[2] != 'true':
                selected_features = arcpy.management.SelectLayerByAttribute(data, "REMOVE_FROM_SELECTION", "code_2018 = '12230'")
                s -= 1
            if ti_types[3] != 'true':
                selected_features = arcpy.management.SelectLayerByAttribute(data, "REMOVE_FROM_SELECTION", "code_2018 = '12300'")
                s -= 1
            if ti_types[4] != 'true':
                selected_features = arcpy.management.SelectLayerByAttribute(data, "REMOVE_FROM_SELECTION", "code_2018 = '12400'")
                s -= 1
            # if user accidentally unselected all 5 categories, all 5 will be selected and included in calculation
            if s == 0:
                selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code_2018 = '12210' Or code_2018 = '12220' Or code_2018 = '12230' Or code_2018 = '12300' Or code_2018 = '12400'")

            # export of selected ti into a new layer
            arcpy.conversion.FeatureClassToFeatureClass(selected_features, workspace, "tport_istructure")
            selected_features = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
            arcpy.AddMessage("Transport infrastructure selected and exported into a new layer")

            # intersecting (cutting) ti by "hex_gr"
            arcpy.analysis.Intersect(["tport_istructure", "hex_gr"], "ti_isect", "ONLY_FID")
            arcpy.AddMessage("Transport infrastructure intersected by hexagons")

            # dissolving (merging, aggregating) ti in the same hexagon, so there will be only one ti feature for each hexagon
            arcpy.management.Dissolve("ti_isect", "ti_isect_diss", "FID_hex_gr")
            arcpy.AddMessage("Dissolved")

            # joining ti area and population to "hex_gr"
            arcpy.management.JoinField("hex_gr", "OBJECTID", "data_isect_diss", "FID_hex_gr", ["SUM_new_pop2018_ua"])
            arcpy.management.AddField("ti_isect_diss", "ti_area", "DOUBLE")
            arcpy.management.CalculateField("ti_isect_diss", "ti_area", '!Shape_Area!')
            arcpy.management.JoinField("hex_gr", "OBJECTID", "ti_isect_diss", "FID_hex_gr", ["ti_area"])
            arcpy.AddMessage("Join of fields successful.")

            # creating new fields "tia_percentage" and "tia_per_capita", where the indicators will be calculated
            arcpy.management.AddFields("hex_gr", [["tia_percentage", "DOUBLE"], ["tia_per_capita", "DOUBLE"]])
            arcpy.AddMessage("New fields added")

            # calculation of new fields:
            # "ti_percentage" is the percentage which ti area covers
            # "tia_per_capita" is ti area in square meters per 1 inhabitant
            arcpy.management.CalculateField("hex_gr", "tia_percentage", '!ti_area!/!Shape_Area!*100')
            arcpy.management.CalculateField("hex_gr", "tia_per_capita", '!ti_area!/!SUM_new_pop2018_ua!')
            arcpy.AddMessage("Indicators calculated")

            # "siz_uni" is a list that looks like this: ["your", "_output"] in case the output layer is provided by user,
            if hex_or_own == "true":
                siz_uni = ["your", "_output"]
            # or it can look like this : ["50", "km"] in case the hexagon grid is generated and used as the output layer
            else:
                siz_uni = size.split()
                if siz_uni[1] == "SquareKilometers":
                    siz_uni[1] = "km"
                elif siz_uni[1] == "Hectares":
                    siz_uni[1] = "ha"
                elif siz_uni[1] == "Ares":
                    siz_uni[1] = "a"
                elif siz_uni[1] == "SquareMeters":
                    siz_uni[1] = "m"
                elif siz_uni[1] == "SquareDecimeters":
                    siz_uni[1] = "dm"
                elif siz_uni[1] == "SquareCentimeters":
                    siz_uni[1] = "cm"
                elif siz_uni[1] == "SquareMillimeters":
                    siz_uni[1] = "mm"
                elif siz_uni[1] == "SquareMiles":
                    siz_uni[1] = "mi"
                elif siz_uni[1] == "Acres":
                    siz_uni[1] = "ac"
                elif siz_uni[1] == "SquareYards":
                    siz_uni[1] = "y"
                elif siz_uni[1] == "SquareFeet":
                    siz_uni[1] = "ft"
                elif siz_uni[1] == "SquareInches":
                    siz_uni[1] = "in"
                elif siz_uni[1] == "Unknown":
                    siz_uni[1] = "km"

            # "area_ending" can contain the name of FUA/UrbanCore in case the area layer has the name from UA Boundary/UrbanCore layer
            if "main." and "_UA2018_" in area_name:
                area_ending = area_name[area_name.find("_"):]
                area_ending = area_ending.replace("_UA2018", "")
            if "main_" and "_UA2018_" in area_name:
                area_name = area_name[6:]
                area_ending = area_name[area_name.find("_"):]
                area_ending = area_ending.replace("_UA2018", "")
            else:
                area_ending = ""

            # "v" is version
            v = 0
            # if in the workspace is already a different layer with the same name, version number will be added
            if ending == ".gdb":
                try:
                    arcpy.management.Rename("hex_gr", "ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                except:
                    v += 1
                    # while some other layer with the same name exists in the geodatabase, the version number would increase by 1
                    while arcpy.Exists("ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v)):
                        v += 1
                    arcpy.management.Rename("hex_gr", "ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))
                if v > 0:
                    arcpy.AddMessage("Name of the output: " + "ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))
                else:
                    arcpy.AddMessage("Name of the output: " + "ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending)

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["data_copy", "clipped_data", "data_isect", "data_isect_diss", "ti_isect", "ti_isect_diss", "tport_istructure"])
            else:
                # renaming the output layer: when exporting to shapefile, the version number is added automatically if some other layer with the same name is in the output folder
                arcpy.management.Rename("hex_gr", "ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                arcpy.conversion.FeatureClassToShapefile("ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending, workspace[:(workspace.rfind(chr(92)))])

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["data_copy", "clipped_data", "data_isect", "data_isect_diss", "ti_isect", "ti_isect_diss", "tport_istructure"])
                arcpy.env.workspace = workspace[:(workspace.rfind(chr(92)))]

                # deleting the "working.gdb"
                arcpy.management.Delete("working.gdb")
                arcpy.AddMessage("Name of the output: " + "ti_ua" + "_" + siz_uni[0] + siz_uni[1] + area_ending + ".shp")

            # deleting variables
            del data, area, size, workspace, cor_sys_string, desc, fields, i, cursor, row, control_selection, check_d, check_a, leng, ending
            del ti_types, area_name, data_spref, area_spref, cor_sys, selected_features, siz_uni, s, area_ending, v, hex_or_own, own_layer
            arcpy.AddMessage("Trash deleted")

            # finish! :D
            arcpy.AddMessage("The script has succesfully ended! Your result is ready :)")

if __name__ == '__main__':
    main()

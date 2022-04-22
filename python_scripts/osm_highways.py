#-------------------------------------------------------------------------------
# Name:        Highways OSM
#
# Purpose:     The purpose of this script is to assess highways of chosen area based on roads data from OpenStreetMap (OSM).
#              It calculates two indicators, hway_percentage (how many % of roads are highways) and hway_density (length of highways in km per 1 km2 of area).
#
# Author:      Adam Tóth
#
# This script is a part of bachelor thesis "Possibilities of calculation characteristics of the transport network of states and cities"
# supervisor: doc. Ing. Zdena Dobešová, Ph.D.
# Department of Geoinformatics, Faculty of Science, Palacký University in Olomouc, Czech republic
#
# Created:     03.03.2022
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
    cor_sys_string = arcpy.GetParameterAsText(6)

    area_name = area[(area.rfind(chr(92))+1):]

    # checking OSM roads layer, if it is a line layer, if it has a field 'code' of Short/Long type
    # and if it contains at least one highway
    desc = arcpy.Describe(data)
    fields = arcpy.ListFields(data)
    check_d = 0

    if desc.shapeType == "Polyline":
        for i in fields:
            if (i.name == 'code') and ((i.type == 'SmallInteger') or (i.type == 'Integer')):
                with arcpy.da.SearchCursor(data, i.name) as cursor:
                    for row in cursor:
                        if (row[0] > 5110) and (row[0] < 5113):
                            check_d += 1
                            arcpy.AddMessage("Your data layer is OK.")
                            break
                break

    # check of output layer: if user selected that they want to use their own layer, it has to be provided in "own_layer"
    # if user wanted to use hexagon grid, the size of hexagon has to be provided in "size"
    if hex_or_own == "true":
        if own_layer != "":
            check_d += 1
    else:
        if size != "":
            check_d += 1

    # if it doesn't meet the requirements, script is ended
    if check_d < 2:
        del data, area, size, workspace, cor_sys_string, desc, fields, i, cursor, row, check_d, area_name, hex_or_own, own_layer
        arcpy.AddError("Your data and/or settings for output are not suitable for this script.")
    else:
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
        # the coordinate system of their own output layer, the coordinate system of OSM roads, the system of area, WGS84 Web Mercator (Auxiliary Sphere)
        else:
            if hex_or_own == "true":
                if (own_layer_spref.type == "Projected") and (own_layer_spref.linearUnitName == "Meter"):
                    cor_sys = own_layer_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of your output layer {cor_sys.name} will be used.")
                elif (data_spref.type == "Projected") and (data_spref.linearUnitName == "Meter"):
                    cor_sys = data_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of OSM layer {cor_sys.name} will be used.")
                elif (area_spref.type == "Projected") and (area_spref.linearUnitName == "Meter"):
                    cor_sys = area_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of area layer {cor_sys.name} will be used.")
                else:
                    cor_sys = arcpy.SpatialReference(3857)
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system and systems of input layers weren't appropriate, so {cor_sys.name} coordinate system will be used.")
            elif (data_spref.type == "Projected") and (data_spref.linearUnitName == "Meter"):
                cor_sys = data_spref
                arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of OSM layer {cor_sys.name} will be used.")
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

        # control of area layer, whether it is a polygon layer and if it overlaps with OSM roads
        desc = arcpy.Describe(area)
        control_selection = arcpy.management.SelectLayerByLocation(data, "INTERSECT", area)

        if desc.shapeType == "Polygon":
            if int(control_selection[2]) == 0:
                control_selection = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
                arcpy.AddError("Your data and area layers don't overlap.")
            # if it meets the requirements, OSM roads are clipped by area
            elif int(control_selection[2]) > 0:
                control_selection = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
                check_a += 1
                arcpy.analysis.Clip(data, area, "clipped_data")
                data = workspace + chr(92) + "clipped_data"
                arcpy.AddMessage("Your area layer is OK, data clipped by area.")
        else:
            arcpy.AddError("Your area layer is not of polygon shape type.")

        # if it doesn't meet the requirements, script is ended
        if check_a < 2:
            del data, area, size, workspace, cor_sys_string, desc, fields, i, cursor, row, control_selection, check_d, check_a, leng, ending
            del area_name, data_spref, area_spref, cor_sys, hex_or_own, own_layer
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
                arcpy.AddMessage("Hexagonal grid generated")
                arcpy.analysis.Clip("hex_grid", area, "hex_gr")
                arcpy.AddMessage("Clipped")

            # selection of highways, there are 2 categories in OSM which are considered as highways: 5111 (motorways), 5112 (trunks)
            # export of selected features into a new layer
            selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code = 5111 Or code = 5112")
            arcpy.conversion.FeatureClassToFeatureClass(selected_features, workspace, "highways")
            selected_features = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
            arcpy.AddMessage("Highways selected and exported into a new layer")

            # selection of roads: major roads (5111-5115), minor roads (5121-5124), major road links (5131-5135) and export to a new layer
            selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code >= 5111 And code <= 5135")
            arcpy.conversion.FeatureClassToFeatureClass(selected_features, workspace, "roads")
            selected_features = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
            arcpy.AddMessage("Roads selected and exported into a new layer")

            # intersecting (cutting) highways and roads by "hex_gr"
            arcpy.analysis.Intersect(["highways", "hex_gr"], "hways_isect", "ONLY_FID")
            arcpy.analysis.Intersect(["roads", "hex_gr"], "roads_isect", "ONLY_FID")
            arcpy.AddMessage("Highways and roads intersected by hexagons")

            # dissolving (merging, aggregating) highways and roads in the same hexagon, so there will be only one feature for each hexagon
            arcpy.management.Dissolve("hways_isect", "hways_isect_diss", "FID_hex_gr")
            arcpy.management.Dissolve("roads_isect", "roads_isect_diss", "FID_hex_gr")
            arcpy.AddMessage("Dissolved")

            # joining highways and roads lengths to by "hex_gr"
            arcpy.management.AddField("hways_isect_diss", "hway_length", "DOUBLE")
            arcpy.management.CalculateField("hways_isect_diss", "hway_length", '!Shape_Length!')
            arcpy.management.AddField("roads_isect_diss", "road_length", "DOUBLE")
            arcpy.management.CalculateField("roads_isect_diss", "road_length", '!Shape_Length!')
            arcpy.management.JoinField("hex_gr", "OBJECTID", "hways_isect_diss", "FID_hex_gr", ["hway_length"])
            arcpy.management.JoinField("hex_gr", "OBJECTID", "roads_isect_diss", "FID_hex_gr", ["road_length"])
            arcpy.AddMessage("Join successful")

            # creating new fields "hway_percentage" and "hway_density", where the indicators will be calculated
            arcpy.management.AddFields("hex_gr", [["hway_percentage", "DOUBLE"], ["hway_density", "DOUBLE"]])
            arcpy.AddMessage("New fields added")

            # calculation of new fields:
            # hway_percentage is the percentage of highways length from the roads length (highways length divided by roads length multiplied by 100)
            # hway_density is the highways length in km per 1 square km of area
            arcpy.management.CalculateField("hex_gr", "hway_percentage", '!hway_length!/!road_length!*100')
            arcpy.management.CalculateField("hex_gr", "hway_density", '(!hway_length!/1000)/(!Shape_Area!/1000000)')
            arcpy.AddMessage("Indicators 'highway ratio' and 'highway density' calculated")

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
                    arcpy.management.Rename("hex_gr", "highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                except:
                    v += 1
                    # while some other layer with the same name exists in the geodatabase, the version number would increase by 1
                    while arcpy.Exists("highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v)):
                        v += 1
                    arcpy.management.Rename("hex_gr", "highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))

                if v > 0:
                    arcpy.AddMessage("Name of the output: " + "highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))
                else:
                    arcpy.AddMessage("Name of the output: " + "highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending)

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["clipped_data", "hways_isect", "hways_isect_diss", "highways", "roads_isect_diss", "roads_isect", "roads"])
            else:
                # renaming the output layer: when exporting to shapefile, the version number is added automatically if some other layer with the same name is in the output folder
                arcpy.management.Rename("hex_gr", "highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                arcpy.conversion.FeatureClassToShapefile("highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending, workspace[:(workspace.rfind(chr(92)))])

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["clipped_data", "hways_isect", "hways_isect_diss", "highways", "roads_isect_diss", "roads_isect", "roads"])
                arcpy.env.workspace = workspace[:(workspace.rfind(chr(92)))]

                # deleting the "working.gdb"
                arcpy.management.Delete("working.gdb")
                arcpy.AddMessage("Name of the output: " + "highways_osm" + "_" + siz_uni[0] + siz_uni[1] + area_ending + ".shp")

            # deleting variables
            del selected_features, area, data, size, siz_uni, workspace, ending, leng, area_ending, v, data_spref, area_spref, cor_sys, cor_sys_string, desc
            del fields, i, cursor, control_selection, row, check_d, check_a, area_name, hex_or_own, own_layer
            arcpy.AddMessage("Trash deleted")

            # finish! :D
            arcpy.AddMessage("The script has succesfully ended! Your result is ready :)")

if __name__ == '__main__':
    main()

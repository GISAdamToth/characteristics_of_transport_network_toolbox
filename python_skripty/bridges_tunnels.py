#-------------------------------------------------------------------------------
# Name:        Bridges Tunnels OSM
#
# Purpose:     The purpose of this script is to assess OpenStreetMap (OSM) road/railway network of chosen area based on the bridges and tunnels ratio.
#              It calculates three indicators:
#              rd/rlw_density (roads/railways length in km per 1 km2 of area),
#              br_rd/rlw_ratio (bridges length in m per 1 km of roads/railways),
#              tu_rd/rlw_ratio (tunnels length in m per 1 km of roads/railways).
#
# Author:      Adam Tóth
#
# This script is a part of bachelor thesis "Possibilities of calculation characteristics of the transport network of states and cities"
# supervisor: doc. Ing. Zdena Dobešová, Ph.D.
# Department of Geoinformatics, Faculty of Science, Palacký University in Olomouc, Czech republic
#
# Created:     23.03.2022
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

    # checking OSM layer, if it is a line layer, if it has a field 'code' of Short/Long type,
    # if it contains at least one road or railway and if it contains fields 'bridge' and 'tunnel'
    desc = arcpy.Describe(data)
    fields = arcpy.ListFields(data)
    check_d = 0
    # variable "rd_or_rlw" contains "rd" if the input layer are roads and "rlw" if the input layer are railways
    rd_or_rlw = ""

    if desc.shapeType == "Polyline":
        for i in fields:
            if (i.name == 'code') and ((i.type == 'SmallInteger') or (i.type == 'Integer')):
                with arcpy.da.SearchCursor(data, i.name) as cursor:
                    for row in cursor:
                        if (row[0] > 5110) and (row[0] < 5136):
                            check_d += 1
                            rd_or_rlw = "rd"
                            break
                with arcpy.da.SearchCursor(data, i.name) as cursor:
                    for row in cursor:
                        if (row[0] == 6101) or (row[0] == 6102):
                            check_d += 1
                            rd_or_rlw = "rlw"
                            break
            if (i.name == 'bridge') and (i.type == 'String'):
                check_d += 1
            if (i.name == 'tunnel') and (i.type == 'String'):
                check_d += 1

    # if both roads and railways are in the input layer, both are included
    if check_d == 4:
        rd_or_rlw = "rd_rlw"

    # check of output layer: if user selected that they want to use their own layer, it has to be provided in "own_layer"
    # if user wanted to use hexagon grid, the size of hexagon has to be provided in "size"
    if hex_or_own == "true":
        if own_layer != "":
            check_d += 1
    else:
        if size != "":
            check_d += 1

    # if it doesn't meet the requirements, script is ended
    if check_d < 4:
        del data, area, size, workspace, cor_sys_string, desc, fields, i, cursor, row, check_d, area_name, rd_or_rlw, hex_or_own, own_layer
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
        # the coordinate system of their own output layer, the coordinate system of OSM layer, the system of area, WGS84 Web Mercator (Auxiliary Sphere)
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

        arcpy.env.outputCoordinateSystem = cor_sys

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

        # control of area layer, whether it is a polygon layer and if it overlaps with OSM layer
        desc = arcpy.Describe(area)
        control_selection = arcpy.management.SelectLayerByLocation(data, "INTERSECT", area)

        if desc.shapeType == "Polygon":
            if int(control_selection[2]) == 0:
                control_selection = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
                arcpy.AddError("Your data and area layers don't overlap.")
            # if it meets the requirements, OSM layer is clipped by area
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
            del area_name, data_spref, area_spref, cor_sys, rd_or_rlw, hex_or_own, own_layer
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

            # selection of roads: major roads (5111-5115), minor roads (5121-5124), major road links (5131-5135)
            if rd_or_rlw == "rd":
                selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code > 5110 And code < 5136")
            # selection of railways: rails (6101) light rails (6102)
            elif rd_or_rlw == "rlw":
                selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code > 6100 And code < 6103")
            # selection of both roads and railways in case both are in a layer
            if rd_or_rlw == "rd_rlw":
                selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "(code > 5110 And code < 5136) Or (code > 6100 And code < 6103)")

            # export of selected features into a new layer
            arcpy.conversion.FeatureClassToFeatureClass(selected_features, workspace, "lines_export")
            selected_features = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
            arcpy.AddMessage("Exported into a new layer")

            # if there are some bridges, they are selected and exported into a new layer
            selected_features = arcpy.management.SelectLayerByAttribute("lines_export", "NEW_SELECTION", "bridge = 'T'")
            if int(selected_features[1]) > 0:
                arcpy.conversion.FeatureClassToFeatureClass(selected_features, workspace, "bridges")
                arcpy.AddMessage("Bridges selected and exported.")
            else:
                arcpy.AddMessage("No bridges")

            # if there are some tunnels, they are selected and exported into a new layer
            selected_features = arcpy.management.SelectLayerByAttribute("lines_export", "NEW_SELECTION", "tunnel = 'T'")
            if int(selected_features[1]) > 0:
                arcpy.conversion.FeatureClassToFeatureClass(selected_features, workspace, "tunnels")
                arcpy.AddMessage("Tunnels selected and exported.")
            else:
                arcpy.AddMessage("No tunnels")

            selected_features = arcpy.management.SelectLayerByAttribute("lines_export", "CLEAR_SELECTION")

            # intersecting (cutting) roads/railways by "hex_gr"
            # and dissolving (merging, aggregating) roads/railways in the same hexagon, so there will be only one feature for each hexagon
            arcpy.analysis.Intersect(["lines_export", "hex_gr"], "lines_isect", "ONLY_FID")
            arcpy.management.Dissolve("lines_isect", "lines_isect_diss", "FID_hex_gr")

            # the same Intersect-Dissolve process with bridges, if there are some
            if arcpy.Exists("bridges"):
                arcpy.analysis.Intersect(["bridges", "hex_gr"], "bridges_isect", "ONLY_FID")
                arcpy.management.Dissolve("bridges_isect", "bridges_isect_diss", "FID_hex_gr")

            # the same Intersect-Dissolve process with tunnels, if there are some
            if arcpy.Exists("tunnels"):
                arcpy.analysis.Intersect(["tunnels", "hex_gr"], "tunnels_isect", "ONLY_FID")
                arcpy.management.Dissolve("tunnels_isect", "tunnels_isect_diss", "FID_hex_gr")

            arcpy.AddMessage("Intersected and dissolved")

            # joining roads/railways length to "hex_gr"
            arcpy.management.AddField("lines_isect_diss", rd_or_rlw + "_length", "DOUBLE")
            arcpy.management.CalculateField("lines_isect_diss", rd_or_rlw + "_length", '!Shape_Length!')
            arcpy.management.JoinField("hex_gr", "OBJECTID", "lines_isect_diss", "FID_hex_gr", [rd_or_rlw + "_length"])

            # calculating roads/railways density
            if rd_or_rlw == "rd":
                arcpy.management.AddField("hex_gr", "rd_density", "DOUBLE")
                arcpy.management.CalculateField("hex_gr", "rd_density", '(!rd_length!/1000)/(!Shape_Area!/1000000)')
            elif rd_or_rlw == "rlw":
                arcpy.management.AddField("hex_gr", "rlw_density", "DOUBLE")
                arcpy.management.CalculateField("hex_gr", "rlw_density", '(!rlw_length!/1000)/(!Shape_Area!/1000000)')
            elif rd_or_rlw == "rd_rlw":
                arcpy.management.AddField("hex_gr", "rd_rlw_density", "DOUBLE")
                arcpy.management.CalculateField("hex_gr", "rd_rlw_density", '(!rd_rlw_length!/1000)/(!Shape_Area!/1000000)')

            # if there are some bridges, their length is joined to "hex_gr" and their ratio is calculated
            if arcpy.Exists("bridges"):
                arcpy.management.AddField("bridges_isect_diss", rd_or_rlw + "_bridges_length", "DOUBLE")
                arcpy.management.CalculateField("bridges_isect_diss", rd_or_rlw + "_bridges_length", '!Shape_Length!')
                arcpy.management.JoinField("hex_gr", "OBJECTID", "bridges_isect_diss", "FID_hex_gr", [rd_or_rlw + "_bridges_length"])
                arcpy.management.AddField("hex_gr", "br_" + rd_or_rlw + "_ratio", "DOUBLE")

                # bridge ratio is bridges length in m per 1 km of roads/railways
                if rd_or_rlw == "rd":
                    arcpy.management.CalculateField("hex_gr", "br_rd_ratio", '!rd_bridges_length!/(!rd_length!/1000)')
                elif rd_or_rlw == "rlw":
                    arcpy.management.CalculateField("hex_gr", "br_rlw_ratio", '!rlw_bridges_length!/(!rlw_length!/1000)')
                elif rd_or_rlw == "rd_rlw":
                    arcpy.management.CalculateField("hex_gr", "br_rd_rlw_ratio", '!rd_rlw_bridges_length!/(!rd_rlw_length!/1000)')

            # if there are some tunnels, their length is joined to "hex_gr" and their ratio is calculated
            if arcpy.Exists("tunnels"):
                arcpy.management.AddField("tunnels_isect_diss", rd_or_rlw + "_tunnels_length", "DOUBLE")
                arcpy.management.CalculateField("tunnels_isect_diss", rd_or_rlw + "_tunnels_length", '!Shape_Length!')
                arcpy.management.JoinField("hex_gr", "OBJECTID", "tunnels_isect_diss", "FID_hex_gr", [rd_or_rlw + "_tunnels_length"])
                arcpy.management.AddField("hex_gr", "tu_" + rd_or_rlw + "_ratio", "DOUBLE")

                # tunnel ratio is tunnels length in m per 1 km of roads/railways
                if rd_or_rlw == "rd":
                    arcpy.management.CalculateField("hex_gr", "tu_rd_ratio", '!rd_tunnels_length!/(!rd_length!/1000)')
                elif rd_or_rlw == "rlw":
                    arcpy.management.CalculateField("hex_gr", "tu_rlw_ratio", '!rlw_tunnels_length!/(!rlw_length!/1000)')
                elif rd_or_rlw == "rd_rlw":
                    arcpy.management.CalculateField("hex_gr", "tu_rd_rlw_ratio", '!rd_rlw_tunnels_length!/(!rd_rlw_length!/1000)')

            arcpy.AddMessage("Joins successful, new fields added and calculated.")

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
                    arcpy.management.Rename("hex_gr", rd_or_rlw + "_bridge_tunnel_" + siz_uni[0] + siz_uni[1] + area_ending)
                except:
                    v += 1
                    # while some other layer with the same name exists in the geodatabase, the version number would increase by 1
                    while arcpy.Exists(rd_or_rlw + "_bridge_tunnel" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v)):
                        v += 1
                    arcpy.management.Rename("hex_gr", rd_or_rlw + "_bridge_tunnel_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))

                if v > 0:
                    arcpy.AddMessage("Name of the output: " + rd_or_rlw + "_bridge_tunnel" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))
                else:
                    arcpy.AddMessage("Name of the output: " + rd_or_rlw + "_bridge_tunnel" + "_" + siz_uni[0] + siz_uni[1] + area_ending)

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                if arcpy.Exists("bridges"):
                    arcpy.management.Delete("bridges")
                if arcpy.Exists("bridges_isect"):
                    arcpy.management.Delete("bridges_isect")
                if arcpy.Exists("bridges_isect_diss"):
                    arcpy.management.Delete("bridges_isect_diss")
                if arcpy.Exists("tunnels"):
                    arcpy.management.Delete("tunnels")
                if arcpy.Exists("tunnels_isect"):
                    arcpy.management.Delete("tunnels_isect")
                if arcpy.Exists("tunnels_isect_diss"):
                    arcpy.management.Delete("tunnels_isect_diss")
                arcpy.management.Delete(["clipped_data", "lines_export", "lines_isect", "lines_isect_diss"])
            else:
                # renaming the output layer: when exporting to shapefile, the version number is added automatically if some other layer with the same name is in the output folder
                arcpy.management.Rename("hex_gr", rd_or_rlw + "_bridge_tunnel" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                arcpy.conversion.FeatureClassToShapefile(rd_or_rlw + "_bridge_tunnel" + "_" + siz_uni[0] + siz_uni[1] + area_ending, workspace[:(workspace.rfind(chr(92)))])

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                if arcpy.Exists("bridges"):
                    arcpy.management.Delete("bridges")
                if arcpy.Exists("bridges_isect"):
                    arcpy.management.Delete("bridges_isect")
                if arcpy.Exists("bridges_isect_diss"):
                    arcpy.management.Delete("bridges_isect_diss")
                if arcpy.Exists("tunnels"):
                    arcpy.management.Delete("tunnels")
                if arcpy.Exists("tunnels_isect"):
                    arcpy.management.Delete("tunnels_isect")
                if arcpy.Exists("tunnels_isect_diss"):
                    arcpy.management.Delete("tunnels_isect_diss")
                arcpy.management.Delete(["clipped_data", "lines_export", "lines_isect", "lines_isect_diss"])
                arcpy.env.workspace = workspace[:(workspace.rfind(chr(92)))]

                # deleting the "working.gdb"
                arcpy.management.Delete("working.gdb")
                arcpy.AddMessage("Name of the output: " + rd_or_rlw + "_bridge_tunnel" + "_" + siz_uni[0] + siz_uni[1] + area_ending + ".shp")

            # deleting variables
            del data, area, size, workspace, cor_sys_string, desc, fields, i, cursor, row, control_selection, check_d, check_a, leng, ending
            del area_name, data_spref, area_spref, cor_sys, rd_or_rlw, selected_features, siz_uni, area_ending, v, hex_or_own, own_layer
            arcpy.AddMessage("Trash deleted")

            # finish! :D
            arcpy.AddMessage("The script has ended successfully!")


if __name__ == '__main__':
    main()

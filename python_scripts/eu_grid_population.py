#-------------------------------------------------------------------------------
# Name:        Bridges Tunnels OSM
#
# Purpose:     The purpose of this script is to calculate density of OpenStreetMap (OSM) road/railway network of chosen area per area and per capita.
#              It calculates two indicators:
#              rd/rlw_density (roads/railways length in km per 1 km2 of area),
#              rd/rlw_per_capita (roads/railways length in m per 1 inhabitant).
#
# Author:      Adam Tóth
#
# This script is a part of bachelor thesis "Possibilities of calculation characteristics of the transport network of states and cities"
# supervisor: doc. Ing. Zdena Dobešová, Ph.D.
# Department of Geoinformatics, Faculty of Science, Palacký University in Olomouc, Czech republic
#
# Created:     21.03.2022
#-------------------------------------------------------------------------------

# import library arcpy and allow overwriting features with the same name
import arcpy
arcpy.env.overwriteOutput = True

def main():
    arcpy.AddMessage("The script has started!")

    # getting inputs from parameters in tool's interface
    data = arcpy.GetParameterAsText(0)
    pop_data = arcpy.GetParameterAsText(1)
    area = arcpy.GetParameterAsText(2)
    hex_or_own = arcpy.GetParameterAsText(3)
    size = arcpy.GetParameterAsText(4)
    own_layer = arcpy.GetParameterAsText(5)
    workspace = arcpy.GetParameterAsText(6)
    cor_sys_string = arcpy.GetParameterAsText(7)

    area_name = area[(area.rfind(chr(92))+1):]

    # checking OSM layer, if it is a line layer, if it has a field 'code' of Short/Long type
    # and if it contains at least one road or railway
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
                        if (row[0] == 6101) or (row[0] == 6102):
                            check_d += 1
                            rd_or_rlw = "rlw"
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
        del data, area, pop_data, size, workspace, cor_sys_string, desc, area_name, hex_or_own, own_layer, check_d, fields, rd_or_rlw, i, cursor, row
        arcpy.AddError("Your data is not suitable for this script.")
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
        pop_data_spref = arcpy.Describe(pop_data).spatialReference
        if hex_or_own == "true":
            own_layer_spref = arcpy.Describe(own_layer).spatialReference

        # if user selected projected coordinate system with meter as its unit, it is set as the main coordinate system
        if (cor_sys_string[:6] == "PROJCS") and ('UNIT["Meter",1.0]' in cor_sys_string):
            cor_sys = arcpy.SpatialReference()
            cor_sys.loadFromString(cor_sys_string)
            arcpy.AddMessage(f"You selected this projected coordinate system for the output: {cor_sys.name}")
        # if user selected geographic coordinate system or projected coordinate system with different unit than meter or they selected nothing,
        # this is the order of setting the main coordinate system:
        # the coordinate system of their own output layer, the coordinate system of population grid, the system of OSM layer, the system of area, WGS84 Web Mercator (Auxiliary Sphere)
        else:
            if hex_or_own == "true":
                if (own_layer_spref.type == "Projected") and (own_layer_spref.linearUnitName == "Meter"):
                    cor_sys = own_layer_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of your output layer {cor_sys.name} will be used.")
                elif (pop_data_spref.type == "Projected") and (pop_data_spref.linearUnitName == "Meter"):
                    cor_sys = pop_data_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of population grid {cor_sys.name} will be used.")
                elif (data_spref.type == "Projected") and (data_spref.linearUnitName == "Meter"):
                    cor_sys = data_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of OSM layer {cor_sys.name} will be used.")
                elif (area_spref.type == "Projected") and (area_spref.linearUnitName == "Meter"):
                    cor_sys = area_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of area layer {cor_sys.name} will be used.")
                else:
                    cor_sys = arcpy.SpatialReference(3857)
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system and systems of input layers weren't appropriate, so {cor_sys.name} coordinate system will be used.")
            elif (pop_data_spref.type == "Projected") and (pop_data_spref.linearUnitName == "Meter"):
                cor_sys = pop_data_spref
                arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of population grid {cor_sys.name} will be used.")
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

        # if coordinate systems of population grid is different from the main coordinate system, it is reprojected into that coordinate system
        if pop_data_spref.factoryCode != cor_sys.factoryCode:
            arcpy.management.Project(pop_data, "reprj_pop_data", cor_sys)
            pop_data = workspace + chr(92) + "reprj_pop_data"
            arcpy.AddMessage(f"Population data layer was reprojected from {pop_data_spref.factoryCode} to {cor_sys.factoryCode}")

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

        # control and clipping of population grid: it has to be polygon layer, it has to contain field 'TOT_P_2018' and it has to overlap with area layer
        desc = arcpy.Describe(pop_data)
        fields = arcpy.ListFields(pop_data)
        control_selection = arcpy.management.SelectLayerByLocation(pop_data, "INTERSECT", area)
        if desc.shapeType == "Polygon":
            for i in fields:
                if (i.name == 'TOT_P_2018') and (i.type == 'Integer'):
                    if int(control_selection[2]) == 0:
                        arcpy.AddError("Your population data doesn't overlap with area layer.")
                    # if it meets the requirements, population grid is clipped by area and population inside squares is recalculated based on the area:
                    # copy of population grid is created, into this copied layer new field "area_orig" is added, the area of squares is loaded there,
                    # then the copied layer is clipped by area, into this clipped layer new field "P_2018_orig" is added and
                    # new population inside polygons is calculated as the original population divided by original area of polygons multiplied by current area of polygons/squares
                    else:
                        check_a += 1
                        arcpy.management.CopyFeatures(control_selection, "pop_data_copy")
                        control_selection = arcpy.management.SelectLayerByAttribute(pop_data, "CLEAR_SELECTION")
                        arcpy.management.AddField("pop_data_copy", "area_orig", "DOUBLE")
                        arcpy.management.CalculateField("pop_data_copy", "area_orig", '!Shape_Area!')
                        arcpy.analysis.Clip("pop_data_copy", area, "clipped_pop_data")
                        arcpy.management.AddField("clipped_pop_data", "P_2018_orig", "DOUBLE")
                        arcpy.management.CalculateField("clipped_pop_data", "P_2018_orig", '(!TOT_P_2018!/!area_orig!)*!Shape_Area!')
                        pop_data = workspace + chr(92) + "clipped_pop_data"
                        arcpy.AddMessage("Your population data layer is OK and clipped.")
                    break
        else:
            arcpy.AddError("Your population data layer is not of polygon shape type.")

        control_selection = arcpy.management.SelectLayerByAttribute(pop_data, "CLEAR_SELECTION")

        # if it doesn't meet the requirements, script is ended
        if check_a < 3:
            del data, area, pop_data, size, workspace, cor_sys_string, desc, fields, i, control_selection, check_a, leng, ending
            del area_name, data_spref, area_spref, pop_data_spref, cor_sys, hex_or_own, own_layer, rd_or_rlw, cursor, row
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

            # into the field "area_orig" is loaded current area of squares of population grid, then it's intersected by "hex_gr", new field for population is added
            # where the population is calculated proportionally to area, same principle as in clipping the population grid by area
            # and finally dissolving all polygons in one polygon/hexagon and summing the population in one polygon/hexagon
            arcpy.management.CalculateField(pop_data, "area_orig", '!Shape_Area!')
            arcpy.analysis.Intersect([pop_data, "hex_gr"], "pop_data_isect", "ALL")
            arcpy.management.AddField("pop_data_isect", "new_pop2018", "DOUBLE")
            arcpy.management.CalculateField("pop_data_isect", "new_pop2018", '(!P_2018_orig!/!area_orig!)*!Shape_Area!')
            arcpy.management.Dissolve("pop_data_isect", "pop_data_isect_diss", "FID_hex_gr", [["new_pop2018","SUM"]])
            arcpy.AddMessage("Population in each hexagon calculated from 2018 estimate")

            # selection of roads: major roads (5111-5115), minor roads (5121-5124), major road links (5131-5135)
            if rd_or_rlw == "rd":
                selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code > 5110 And code < 5136")
            # selection of railways: rails (6101) light rails (6102)
            elif rd_or_rlw == "rlw":
                selected_features = arcpy.management.SelectLayerByAttribute(data, "NEW_SELECTION", "code > 6100 And code < 6103")

            # export of selected features into a new layer
            arcpy.conversion.FeatureClassToFeatureClass(selected_features, workspace, "lines_export")
            selected_features = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
            arcpy.AddMessage("Exported into a new layer")

            # intersecting (cutting) roads/railways by "hex_gr"
            arcpy.analysis.Intersect(["lines_export", "hex_gr"], rd_or_rlw + "_isect", "ONLY_FID")
            arcpy.AddMessage("Transport infrastructure intersected")

            # dissolving (merging, aggregating) roads/railways in the same polygon/hexagon, so there will be only one feature for each polygon/hexagon
            arcpy.management.Dissolve(rd_or_rlw + "_isect", rd_or_rlw + "_isect_diss", "FID_hex_gr")
            arcpy.AddMessage("Dissolved")

            # joining population and roads/railways length to "hex_gr"
            arcpy.management.JoinField("hex_gr", "OBJECTID", "pop_data_isect_diss", "FID_hex_gr", ["SUM_new_pop2018"])
            arcpy.management.AddField(rd_or_rlw + "_isect_diss", rd_or_rlw + "_length", "DOUBLE")
            arcpy.management.CalculateField(rd_or_rlw + "_isect_diss", rd_or_rlw + "_length", '!Shape_Length!')
            arcpy.management.JoinField("hex_gr", "OBJECTID", rd_or_rlw + "_isect_diss", "FID_hex_gr", [rd_or_rlw + "_length"])
            arcpy.AddMessage("Join successful")

            # creating new fields "rd/rlw_density" and "rd/rlw_per_capita", where the indicators will be calculated
            arcpy.management.AddFields("hex_gr", [[rd_or_rlw + "_density", "DOUBLE"], [rd_or_rlw + "_per_capita", "DOUBLE"]])
            arcpy.AddMessage("New fields added")

            # calculation of new fields:
            # "rd/rlw_density" is the roads/railways length in km per 1 square km
            # "rd/rlw_per_capita" is the roads/railways length in m per 1 inhabitant
            if rd_or_rlw == "rd":
                arcpy.management.CalculateField("hex_gr", "rd_density", '(!rd_length!/1000)/(!Shape_Area!/1000000)')
                arcpy.management.CalculateField("hex_gr", "rd_per_capita", '!rd_length!/!SUM_new_pop2018!')
            elif rd_or_rlw == "rlw":
                arcpy.management.CalculateField("hex_gr", "rlw_density", '(!rlw_length!/1000)/(!Shape_Area!/1000000)')
                arcpy.management.CalculateField("hex_gr", "rlw_per_capita", '!rlw_length!/!SUM_new_pop2018!')
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
                    arcpy.management.Rename("hex_gr", rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                except:
                    v += 1
                    # while some other layer with the same name exists in the geodatabase, the version number would increase by 1
                    while arcpy.Exists(rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v)):
                        v += 1
                    arcpy.management.Rename("hex_gr", rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))

                if v > 0:
                    arcpy.AddMessage("Name of the output: " + rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))
                else:
                    arcpy.AddMessage("Name of the output: " + rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending)

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_pop_data"):
                    arcpy.management.Delete("reprj_pop_data")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["clipped_data", "pop_data_isect", "pop_data_isect_diss", "lines_export", rd_or_rlw + "_isect", rd_or_rlw + "_isect_diss", "clipped_pop_data", "pop_data_copy"])
            else:
                # renaming the output layer: when exporting to shapefile, the version number is added automatically if some other layer with the same name is in the output folder
                arcpy.management.Rename("hex_gr", rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                arcpy.conversion.FeatureClassToShapefile(rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending, workspace[:(workspace.rfind(chr(92)))])

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_pop_data"):
                    arcpy.management.Delete("reprj_pop_data")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["clipped_data", "pop_data_isect", "pop_data_isect_diss", "lines_export", rd_or_rlw + "_isect", rd_or_rlw + "_isect_diss", "clipped_pop_data", "pop_data_copy"])
                arcpy.env.workspace = workspace[:(workspace.rfind(chr(92)))]

                # deleting the "working.gdb"
                arcpy.management.Delete("working.gdb")
                arcpy.AddMessage("Name of the output: " + rd_or_rlw + "_pop_grid" + "_" + siz_uni[0] + siz_uni[1] + area_ending + ".shp")

            # deleting variables
            del data, area, pop_data, size, siz_uni, workspace, cor_sys_string, desc, fields, i, v, control_selection, check_a, leng, ending
            del area_name, data_spref, area_spref, pop_data_spref, cor_sys, area_ending, hex_or_own, own_layer, rd_or_rlw, cursor, row
            arcpy.AddMessage("Trash deleted")

            # finish! :D
            arcpy.AddMessage("The script has succesfully ended! Your result is ready :)")

if __name__ == '__main__':
    main()

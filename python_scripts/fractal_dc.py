#-------------------------------------------------------------------------------
# Name:        Fractal Dimension
#
# Purpose:     The purpose of this script is to assess a line network (roads, railways, ...) of chosen area based on fractal dimension.
#              It calculates one indicator, TP (transport provision = fractal dimension/2).
#              Values of TP can be within 0-1, the closer to 1, the more complex and dense the network is.
#
# Attributions: This script is an upgraded version of FractalDimensionCalculation script (author: Svitlana Kuznichenko, source: https://github.com/kuznichenko-s/FractalDimension).
#               Main parts of the code, especially the mathematics parts, are taken from that original script.
#
# Author:      Adam Tóth
#
# This script is a part of bachelor thesis "Possibilities of calculation characteristics of the transport network of states and cities"
# supervisor: doc. Ing. Zdena Dobešová, Ph.D.
# Department of Geoinformatics, Faculty of Science, Palacký University in Olomouc, Czech republic
#
# Created:     18.03.2022
#-------------------------------------------------------------------------------

# importing Libraries arcpy, scipy and numpy (taken from the original script) and allowing overwriting features with the same name
import arcpy
import scipy
from scipy import optimize
import numpy
from numpy import *
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

    # checking input data, if it is a line layer
    desc = arcpy.Describe(data)
    check_d = 0
    if desc.shapeType == "Polyline":
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
    if check_d < 2:
        del data, area, size, workspace, cor_sys_string, desc, area_name, hex_or_own, own_layer, check_d
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

        # if user selected projected coordinate system, it is set as the main coordinate system
        if cor_sys_string[:6] == "PROJCS":
            cor_sys = arcpy.SpatialReference()
            cor_sys.loadFromString(cor_sys_string)
            arcpy.AddMessage(f"You selected this projected coordinate system for the output: {cor_sys.name}")
        # if user selected geographic coordinate system or they selected nothing,
        # this is the order of setting the main coordinate system:
        # the coordinate system of their own output layer, the coordinate system of line data, the system of area, WGS84 Web Mercator (Auxiliary Sphere)
        else:
            if hex_or_own == "true":
                if own_layer_spref.type == "Projected":
                    cor_sys = own_layer_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of your output layer {cor_sys.name} will be used.")
                elif data_spref.type == "Projected":
                    cor_sys = data_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of line layer {cor_sys.name} will be used.")
                elif area_spref.type == "Projected":
                    cor_sys = area_spref
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of area layer {cor_sys.name} will be used.")
                else:
                    cor_sys = arcpy.SpatialReference(3857)
                    arcpy.AddMessage(f"You didn't select any appropriate coordinate system and systems of input layers weren't appropriate, so {cor_sys.name} coordinate system will be used.")
            elif data_spref.type == "Projected":
                cor_sys = data_spref
                arcpy.AddMessage(f"You didn't select any appropriate coordinate system, so coordinate system of line layer {cor_sys.name} will be used.")
            elif area_spref.type == "Projected":
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

        # control of area layer, if it is a polygon layer and if it overlaps with line data
        desc = arcpy.Describe(area)
        control_selection = arcpy.management.SelectLayerByLocation(data, "INTERSECT", area)

        if desc.shapeType == "Polygon":
            if int(control_selection[2]) == 0:
                control_selection = arcpy.management.SelectLayerByAttribute(data, "CLEAR_SELECTION")
                arcpy.AddError("Your data and area layers don't overlap.")
            # if it meets the requirements, line data is clipped by area
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
            del data, area, size, workspace, cor_sys_string, desc, control_selection, check_a, leng, ending
            del area_name, area_spref, data_spref, cor_sys, hex_or_own, own_layer
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

                # (same as in the original script)
                #arcpy.management.GenerateTessellation("hex_grid", area, "HEXAGON", size, cor_sys)
                arcpy.management.GenerateTessellation("hex_grid", area, "HEXAGON", size)
                arcpy.AddMessage("Hexagonal grid generated")
                arcpy.analysis.Clip("hex_grid", area, "hex_gr")
                arcpy.AddMessage("Clipped")

             # intersecting (cutting) lines by "hex_gr" (same as in the original script)
            arcpy.analysis.Intersect([data, "hex_gr"], "roads_isect", "ONLY_FID")
            arcpy.AddMessage("Roads intersected by hexagons")

            # dissolving (merging, aggregating) lines in the same hexagon, so there will be only one feature for each hexagon (same as in the original script)
            arcpy.management.Dissolve("roads_isect", "roads_isect_diss", "FID_hex_gr")
            arcpy.AddMessage("Dissolved")

            # creating new field TP, where the transport provision will be calculated (from this point on the code is taken from the original script with little corrections and edits)
            arcpy.management.AddField("hex_gr", "TP", "FLOAT")
            arcpy.AddMessage("New field added")

            # some maths, fitting functions to data, but I have no idea what is lambda, p, x, y
            fitfunc = lambda p, x: (p[0] + p[1] * x)
            errfunc = lambda p, x, y: (y - fitfunc(p, x))

            # "a" is the number of rows in "roads_isect_diss" feature class, it is the number of hexagons which contain some lines
            # "rows" is a cursor, it is a list of objects, list of rows in "roads_isect_diss"
            # "total" is a list of integers, values, IDs of hexagons which contain some lines
            # "count" is a number of hexagons which cover our area
            # "tp_values" is a list with calculated values of transport provision for each hexagon which contains some lines
            a = int(arcpy.management.GetCount("roads_isect_diss").getOutput(0))
            rows = arcpy.SearchCursor("roads_isect_diss")
            total = []
            for row in rows:
               total.append(row.getValue("FID_hex_gr"))
            count = int(arcpy.management.GetCount("hex_gr").getOutput(0))
            tp_values = []
            i = 1
            arcpy.AddMessage(f"Number of hexagons which intersect with roads: {a}. Total number of hexagons: {count}")

            # the final loop, it runs while "i" (starting at 1) is less than or equal to "a", in the end of each iteration "i" is increased by 1,
            # so the number of iterations will be equal to number of hexagons which contain some roads
            # (this is one major change from the original script: there the while cycle runs "while i < count", which doesn't make sense, because the calculation can be done only for the polygons/hexagons which contain some lines)
            while i <= a:
                arcpy.AddMessage(f"iteration: {i} out of {a}")
                # select the lines and select the respective hexagon where the lines are
                selected_roads = arcpy.management.SelectLayerByAttribute("roads_isect_diss", "NEW_SELECTION", "OBJECTID = %s" % i)
                selected_hex = arcpy.management.SelectLayerByAttribute("hex_gr", "NEW_SELECTION", "OBJECTID = %s" % (total[i-1]))

                # selected hexagon is exported into layer "one_hex"
                arcpy.conversion.FeatureClassToFeatureClass(selected_hex, workspace, "one_hex")

                # "aa" contains extent of this hexagon
                aa = arcpy.Describe("one_hex").extent
                xmin = aa.XMin
                ymin  = aa.YMin

                # list "squares" contains numbers of squares in fishnet, which will be generated in the next for loop
                squares = [4,16,64,256]
                # list "intersections" contains counts of squares which cover lines in the polygon/hexagon, first it is 1/1, then a/4, b/16, c/64, d/256
                intersections = [1]

                # this for loop has 4 iterations
                # during one iteration it creates fishnet over the "one_hex", clips the fishnet by "one_hex", counts the number of squares that cover lines and add these counts into the list "intersections"
                for n in range(len(squares)):
                    arcpy.management.CreateFishnet("fishnet_" + str(squares[n]), str(xmin) + ' ' + str(ymin), str(xmin) + ' ' + str(ymin+1), "0", "0", int((squares[n])**(0.5)), int((squares[n])**(0.5)), "#", "NO_LABELS", "one_hex", "POLYGON")
                    arcpy.analysis.Clip("fishnet_" + str(squares[n]), "one_hex", "fishnet_clip_" + str(squares[n]))
                    c = int(arcpy.management.GetCount(arcpy.management.SelectLayerByLocation("fishnet_clip_" + str(squares[n]), "INTERSECT", selected_roads)).getOutput(0))
                    intersections.append(c)
                    arcpy.management.Delete(["fishnet_" + str(squares[n]), "fishnet_clip_" + str(squares[n])])

                # fractal dimension and transport provision calculation (another math which I don't understand, but it works)
                edge = [1,0.5,0.25,0.125,0.0625]
                logx = log(edge)
                logy = log(intersections)
                qout, success = optimize.leastsq(errfunc, [0, 0], args = (logx, logy), maxfev = 30000)

                # adding the transport provision into the list "tp_values" and deleting layer "one_hex"
                # (in the original code, the field TP was calculated in the end of each iteration, in my version, transport provision for each polygon is saved in the list and after the while loop terminates, it is loaded into the field TP)
                tp_values.append(float(int(qout[1]*100000))/(-200000))
                arcpy.management.Delete("one_hex")
                i += 1

            # calculating field TP: if the hexagon contains some lines, it is assigned its transport provision value
            # (from this point on, the code is mine, not taken from the original script)
            i = 0
            with arcpy.da.UpdateCursor("hex_gr", ["OBJECTID", "TP"]) as cursor:
                for row in cursor:
                    if row[0] == total[i]:
                        row[1] = tp_values[i]
                        cursor.updateRow(row)
                        if i < a-1:
                            i += 1
            arcpy.AddMessage("Field TP calculated and updated")


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
                    arcpy.management.Rename("hex_gr", "fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                except:
                    v += 1
                    # while some other layer with the same name exists in the geodatabase, the version number would increase by 1
                    while arcpy.Exists("fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v)):
                        v += 1
                    arcpy.management.Rename("hex_gr", "fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))

                if v > 0:
                    arcpy.AddMessage("Name of the output: " + "fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending + "_" + str(v))
                else:
                    arcpy.AddMessage("Name of the output: " + "fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending)

                 # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["clipped_data", "roads_isect_diss", "roads_isect"])
            else:
                # renaming the output layer: when exporting to shapefile, the version number is added automatically if some other layer with the same name is in the output folder
                arcpy.management.Rename("hex_gr", "fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending)
                arcpy.conversion.FeatureClassToShapefile("fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending, workspace[:(workspace.rfind(chr(92)))])

                # deleting all layers that were created during the run of the script
                if arcpy.Exists("reprj_data"):
                    arcpy.management.Delete("reprj_data")
                if arcpy.Exists("reprj_area"):
                    arcpy.management.Delete("reprj_area")
                if arcpy.Exists("reprj_own_layer"):
                    arcpy.management.Delete("reprj_own_layer")
                if arcpy.Exists("hex_grid"):
                    arcpy.management.Delete("hex_grid")
                arcpy.management.Delete(["clipped_data", "roads_isect_diss", "roads_isect", "fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending])
                arcpy.env.workspace = workspace[:(workspace.rfind(chr(92)))]

                # deleting the "working.gdb"
                arcpy.management.Delete("working.gdb")
                arcpy.AddMessage("Name of the output: " + "fractal_tp" + "_" + siz_uni[0] + siz_uni[1] + area_ending + ".shp")

            # deleting variables
            del area, data, size, siz_uni, workspace, ending, leng, area_ending, v, data_spref, area_spref, cor_sys, cor_sys_string, desc, i, cursor, control_selection, row, check_a
            del fitfunc, errfunc, a, rows, total, count, tp_values, selected_roads, selected_hex, aa, xmin, ymin, squares, intersections, n, c, edge, logx, logy, qout, success, area_name, hex_or_own, own_layer
            arcpy.AddMessage("Trash deleted")

            # finish! :D
            arcpy.AddMessage("The script has successfully ended!")

if __name__ == '__main__':
    main()

#-------------------------------------------------------------------------------
# Name:        Summary Transport Index
#
# Purpose:     The purpose of this script is to calculate a summary transport index from indicators calculated in previous scripts in this toolbox.
#              User provides a layer where at least one indicator is calculated and sets weights (0-10) for individual indicators (deciles will be multiplied by weights).
#              If user doesn't want to include certain indicator in the calculation, they can delete it from the input layer or set its weight to 0.
#
# Author:      Adam Tóth
#
# This script is a part of bachelor thesis "Possibilities of calculation characteristics of the transport network of states and cities"
# supervisor: doc. Ing. Zdena Dobešová, Ph.D.
# Department of Geoinformatics, Faculty of Science, Palacký University in Olomouc, Czech republic
#
# Created:     25.03.2022
#-------------------------------------------------------------------------------

# import library arcpy and allow overwriting features with the same name
import arcpy
arcpy.env.overwriteOutput = True

def main():
    arcpy.AddMessage("The script has started!")

    # getting input from parameters in tool's interface: "in_layer" is input layer with already calculated indicators,
    # "dir_name" is the directory and name of the output (default value: home gdb + \ + in_layer name + "SumDecIndex"),
    # "weights" is a list of weights (integers) set by user from range 0-10
    in_layer = arcpy.GetParameterAsText(0)
    dir_name = arcpy.GetParameterAsText(1)
    weights = []

    # loading of weights
    for i in range(2,15):
        weights.append(int(arcpy.GetParameterAsText(i)))

    # control of input layer, if it contains at least one field with indicator, if it doesn't, the script will fail
    # at the same time, indicator fields from input layer will be loaded into the list "fields" and its respective weights into the list "pom"
    data_fields = arcpy.ListFields(in_layer)
    indicators = ["TP", "tia_percentage", "tia_per_capita", "rd_density", "rd_per_capita", "rlw_density", "rlw_per_capita", "hway_percentage", "hway_density", "br_rd_ratio", "tu_rd_ratio", "br_rlw_ratio", "tu_rlw_ratio"]
    fields = []
    pom = []
    check = 0
    for f in data_fields:
        for i in range(len(indicators)):
            if f.name == indicators[i]:
                fields.append(indicators[i])
                pom.append(weights[i])
                check = 1

    # if there is no indicator field in the input layer, the script ends here by the message below and by deleting variables
    if check == 0:
        arcpy.AddMessage("Input layer doesn't contain any field with indicator calculated in other tools of the 'characteristics_of_transport_network.tbx' toolbox.")
        del in_layer, dir_name, weights, i, data_fields, indicators, fields, pom, check, f
    # but if there is at least one indicator field, the script continues here
    else:
        # if the weight is set to 0, the respective indicator will not be included in the calculation of summary deciles index, so it is popped out of the list together with its 0 weight
        weights = pom
        while 0 in weights:
            fields.pop(weights.index(0))
            weights.pop(weights.index(0))

        arcpy.AddMessage(f"Summary deciles index will be calculated from these indicators: {fields}")
        arcpy.AddMessage(f"and their decile values will be multiplied by these weights, respectively: {weights}")

        # "workspace" is a path to directory for the output; if the directory is a folder, there will be created "working.gdb" and the workspace is set to this gdb
        # "name" is just a string containing the name for the output
        # "ending" is a control variable, it controls the output format, whether it is shapefile in folder or feature class in gdb
        workspace = dir_name[0:(dir_name.rfind(chr(92)))]
        name = dir_name[(dir_name.rfind(chr(92))+1):]
        ending = workspace[(len(workspace)-4):]
        if ending != ".gdb":
            arcpy.management.CreateFileGDB(workspace, "working.gdb")
            workspace = workspace + chr(92) + "working.gdb"

        # input layer is copied to the output gdb or "working.gdb"
        arcpy.management.CopyFeatures(in_layer, workspace + chr(92) + name)
        in_layer = workspace + chr(92) + name


        # the main part: calculation of the summary decile index
        # "index" is a list of 2-element's lists, first element is OBJECTID of hexagon/polygon and the second element is its summary deciles index
        index = []
        with arcpy.da.SearchCursor(in_layer, "OBJECTID") as cursor:
            for row in cursor:
                pom = [0,0]
                pom[0] = row[0]
                index.append(pom)

        # the big for loop, it goes for all the indicators entering the calculation, "f" is integer variable
        for f in range(len(fields)):
            # "values" is a list of lists, 0th element is indicator value and 1st element is OBJECTID, so it can be sorted by indicator values and their deciles assigned
            flds = ["OBJECTID", fields[f]]
            values = []

            # if there is some value in the indicator field, it will be loaded into "values"
            with arcpy.da.SearchCursor(in_layer, flds) as cursor:
                for row in cursor:
                    if row[1] != None:
                        pom = []
                        for j in range(2,0,-1):
                            pom.append(row[j-1])
                        values.append(pom)

            # "values" sorted by indicator value, "deciles" list created for decile values and "step" (size of one decile, type: float) is calculated
            values.sort()
            deciles = []
            step = len(values)/10

            # decile values are the i*step-th elements from "values", i goes from 1 to 9 (both included)
            for i in range(1,10):
                deciles.append(values[round(i*step)-1][0])

            # each value from "values" is assigned its decile, so values from 1st decile are assigned number 1, ... values from 10th decile number 10
            # if user set some other weight than 1, the decile will be multiplied by this weight, for example weight = 2, values from 1st decile are assigned number 2, ... values from 10th decile number 20
            # now "values" look like this: 0 – indicator value, 1 – OBJECTID, 2 – decile
            j = 0
            for i in values:
                if i[0] <= deciles[j]:
                    i.append((j+1)*weights[f])
                elif j < 8:
                    j += 1
                    i.append((j+1)*weights[f])
                else:
                    i.append((10)*weights[f])

            # indicator values are removed and the list is sorted by OBJECTID, now it looks like this: 0 – OBJECTID, 1 – decile
            for i in values:
                i.pop(0)
            values.sort()

            # new field "dec_" + fields[f] added, where the deciles of the current indicator will be stored; loading of deciles from "values" list to the field (matching determined by OBJECTID)
            arcpy.management.AddField(in_layer, "dec_" + fields[f], "LONG")
            i = 0
            with arcpy.da.UpdateCursor(in_layer, ["OBJECTID", "dec_" + fields[f]]) as cursor:
                for row in cursor:
                    if row[0] == values[i][0]:
                        row[1] = values[i][1]
                        cursor.updateRow(row)
                        if i < len(values)-1:
                            i += 1
            arcpy.AddMessage(f"Field dec_{fields[f]} calculated and updated")

            # deciles are added to the overall score in "index" list
            j = 0
            for i in index:
                if i[0] == values[j][0]:
                    i[1] += values[j][1]
                    if j < len(values)-1:
                        j += 1

        # new field sum_tr_index added, where the index will be stored and loading of index from "index" list to the field (matching determined by OBJECTID)
        arcpy.management.AddField(in_layer, "sum_tr_index", "LONG")
        i = 0
        with arcpy.da.UpdateCursor(in_layer, ["OBJECTID", "sum_tr_index"]) as cursor:
            for row in cursor:
                if row[0] == index[i][0]:
                    row[1] = index[i][1]
                    cursor.updateRow(row)
                    if i < len(index)-1:
                        i += 1
        arcpy.AddMessage("Field sum_tr_index calculated and updated")

        # if user selected a folder for the output, they will get a shapefile there, "working.gdb" is deleted
        if ending != ".gdb":
            workspace = workspace[:(workspace.rfind(chr(92)))]
            arcpy.conversion.FeatureClassToShapefile(in_layer, workspace)
            arcpy.management.Delete(in_layer)
            arcpy.management.Delete(workspace + chr(92) + "working.gdb")

        # all variables deleted and final messages printed
        del in_layer, dir_name, workspace, weights, i, data_fields, indicators, fields, pom, check, f, index, flds, values, j, deciles, step, name, ending
        arcpy.AddMessage("Trash deleted")
        arcpy.AddMessage("The script has succesfully ended! Your result is ready :)")

if __name__ == '__main__':
    main()

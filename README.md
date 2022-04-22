# characteristics_of_transport_network_toolbox
This repository contains toolbox for ArcGIS Pro called "characteristics_of_transport_network.tbx". You can open your ArcGIS Pro project and on the left side in the catalog pane find "Toolboxes", right-click it and click on "Add Toolbox". Then select this toolbox from where you've downloaded it.

The second part is a folder called "python_scripts". This folder contains 6 python codes written in Python 3.7. These are the source codes of individual tools in the toolbox.

The third part is a folder called "sample_data". This folder contians geodatabase with the name "sample_data.gdb" and folder with the name "urban_atlas_legend". Geodatabase can be added to ArcGIS Pro project in a similar way as toolbox, you just have to click on "Databases" right below "Toolboxes". This geodatabase contains 8 layers which you can use in the tools of the toolbox:

GEOSTAT_pop_grid_slovakia - GEOSTAT 1km2 population grid provided by Eurostat (link to download: https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/population-distribution-demography/geostat) and clipped for Slovak territory. This grid consists of squares of size 1km2 and each square contains population estimate from year 2018. This grid is an input for "Transport_network_EUPopGrid" tool.

main_SK001L1_BRATISLAVA_UA2018 - Urban Atlas LCLU 2018 v013 layer provided by Copernicus Land Monitoring Service (link to download: https://land.copernicus.eu/local/urban-atlas/urban-atlas-2018?tab=download). This layer covers Bratislava FUA and it is an input for "Transport_infrastructure_area_UA" tool.

main_SK001L1_BRATISLAVA_UA2018_Boundary - simple polygon layer defining boundaries of Bratislava FUA. Layer provided by Copernicus Land Monitoring Service together with the Urban Atlas LCLU 2018 v013 layer. This layer can be an input as area boundary for any tool of the toolbox except for "Summary_Transport_Index" tool.

main_SK001L1_BRATISLAVA_UA2018_UrbanCore - simple polygon layer defining boundaries of Bratislava city itself. Layer provided by Copernicus Land Monitoring Service together with the Urban Atlas LCLU 2018 v013 layer. This layer can be an input as area boundary for any tool of the toolbox except for "Summary_Transport_Index" tool.

OSM__railways_slovakia - railways of Slovakia provided by OpenStreetMap (link to download: http://download.geofabrik.de/europe/slovakia.html). This line layer can be an input for "Fractal_Dimension", "Transport_network_EUPopGrid" and "Bridges_Tunnels_OSM".

OSM_highways_slovakia - highways of Slovakia provided by OpenStreetMap (link to download: http://download.geofabrik.de/europe/slovakia.html). This line layer was created from OSM roads layer by exporting only lines with codes 5111 (motorway) and 5112 (trunk). It can be an input for "Fractal_Dimension", "Transport_network_EUPopGrid" and "Bridges_Tunnels_OSM".

OSM_roads_slovakia - roads of Slovakia provided by OpenStreetMap (link to download: http://download.geofabrik.de/europe/slovakia.html). This line layer was created from OSM roads layer by exporting only lines with codes 5111-5135. It can be an input for "Fractal_Dimension", "Highways_OSM", "Transport_network_EUPopGrid" and "Bridges_Tunnels_OSM".

slovakia_country_boundary - simple polygon layer defining boundaries of Slovakia provided by Geodetic and Cartographic Institute Bratislava (link to download: https://www.geoportal.sk/en/zbgis/download/). This layer can be an input for "Fractal_Dimension", "Highways_OSM", "Transport_network_EUPopGrid" and "Bridges_Tunnels_OSM".

The folder with the name "urban_atlas_legend" contains 3 files, all have the same name "Urban_Atlas_2018_Legend" but different extensions, specifically .lyr, .qml and .sld. All three files have the same purpose - symbology of Urban Atlas LCLU 2018 v013 layer is stored in them and you can use it by applying this files to the layer in gis. For ArcGIS please use .lyr file, for QGIS please use .qml or .sld file.

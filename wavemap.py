# Wavemap 1.16

# This program makes an OpenAir airspace file from a wave forecast map (downloaded png image).
# Currently supported are COSMO-D2 maps "Deutschland Nord/Kuestengebiete", "Deutschland Mitte" and "Deutschland Sued/Alpenbereich"
# as well as Meteociel WRF NMM 2 km maps "France Sud-Ouest" and "France-Est"

# (c) 2018 
# Benjamin Bachmaier (Codebase, COSMO-D2)
# Christof Maul (Meteociel)

# www.flugfieber.net

# A python distribution as well as the package "pyPNG" must be installed.

import png
import array
import math
from math import pi,sqrt,atan
import os

smooth = 4          #Smoothing factor defining how aggressive irregularities in wave contour shall be smoothed out (Default is 4)

#------------------Function: georeferencing of all available map types

def georef(px_x, px_y, maptype):
     #Returns a string containing the geo-coordinates of a pixel
     rtd = 180/pi

     if (maptype == 'meteociel_sw'):
          lat = 47.43389 - px_y * 0.00829 + px_x * 9.22527E-004 + px_y * px_y * 2.16603E-007 - px_x * px_x * 9.55649E-007 - px_y * px_x * 3.83603E-008;
          lon = -5.72284 + px_x * 0.01244 + px_y * 0.00101 - px_y * px_x * 2.29369E-006 + px_y * px_y * 8.65559E-008 - px_x * px_x * 8.46498E-008
     if (maptype == 'meteociel_se'):
          lat = 47.6133 - px_y * 0.00819 - px_x * 4.68432E-004 - px_y * px_y * 2.99144E-009 - px_x * px_x * 7.14964E-007 + px_y * px_x * 3.06157E-007;
          lon = 2.44224 + px_x * 0.01229 - px_y * 6.12007E-004 - px_y * px_x * 2.43203E-006 + px_y * px_y * 3.19494E-007 - px_x * px_x * 2.69217E-008
# ne/nw not georeferenced yet
     if (maptype == 'meteociel_ne'):
          lat = 47.43389 - px_y * 0.00829 + px_x * 9.22527E-004 + px_y * px_y * 2.16603E-007 - px_x * px_x * 9.55649E-007 - px_y * px_x * 3.83603E-008;
          lon = -5.72284 + px_x * 0.01244 + px_y * 0.00101 - px_y * px_x * 2.29369E-6 + px_y * px_y * 3.19494E-007 - px_x * px_x * 2.69217E-008
     if (maptype == 'meteociel_nw'):
          lat = 47.43389 - px_y * 0.00829 + px_x * 9.22527E-004 + px_y * px_y * 2.16603E-007 - px_x * px_x * 9.55649E-007 - px_y * px_x * 3.83603E-008;
          lon = -5.72284 + px_x * 0.01244 + px_y * 0.00101 - px_y * px_x * 2.29369E-6 + px_y * px_y * 8.65559E-008 - px_x * px_x * 8.46498E-008		  

     if (maptype == 'dsued'):
          y_NP = 3054.281690140845
          x_NP = 644.0

          dx = x_NP-px_x
          dy = y_NP+px_y
          dist = sqrt(dx*dx+dy*dy)
          lat = 0.000000331886825*dist*dist -0.013629374097183*dist+90.000000000000000

          c = atan(dx/dy)*rtd
          lon = -1.000708892761411*c+9.998175118483397

     elif maptype == 'dmitte':
          y_NP = 2759.3575757576
          x_NP = 541.0

          dx = x_NP-px_x
          dy = y_NP+px_y
          dist = sqrt(dx*dx+dy*dy)
          lat = 0.000000286854877*dist*dist-0.013435214773414*dist+90.0000000000000

          c = atan(dx/dy)*rtd
          lon = -1.005754777000518*c+9.999890059768152

     elif maptype == 'dnord':
          y_NP = 6022.10126582
          x_NP = 550.0

          dx = x_NP-px_x
          dy = y_NP+px_y
          dist = sqrt(dx*dx+dy*dy)
          lat = -0.000000943359028*dist*dist+0.000335858282526*dist+90.0000000000000-0.08

          c = atan(dx/dy)*rtd
          lon = -2.095342514979555*c+10.000000000000002
     
     #Now make formatted coordinates from the lat and lon decimal values
     
     if lon < 0:
          lonstring = " W\n"
     else:
          lonstring = " E\n"
     lon = abs(lon)

     latdeg = int(lat)
     londeg = int(lon)
     
     latmin_all = (lat-latdeg)*60
     lonmin_all = (lon-londeg)*60
     
     latmin = int(latmin_all)
     lonmin = int(lonmin_all)
     
     latsec = int((latmin_all-latmin)*60)
     lonsec = int((lonmin_all-lonmin)*60)
     
     coords = [latdeg, latmin, latsec, londeg, lonmin, lonsec]
     
     for u in range(len(coords)):
          if u != 3:
               if coords[u] < 10:
                    coords[u] = "0"+str(coords[u])
               else:
                    coords[u] = str(coords[u])
          else:
               if coords[u] < 10:
                    coords[u] = "00"+str(coords[u])
               elif coords[u] >= 10 and coords[u] < 100:
                    coords[u] = "0"+str(coords[u])
               else:
                    coords[u] = str(coords[u])
     
     geostring = "DP "+coords[0]+":"+coords[1]+":"+coords[2]+" N "+coords[3]+":"+coords[4]+":"+coords[5]+lonstring
     
     return geostring
     
#Change working directory to the directory of "wavemap.py"
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
     
#------------------Step 1: Open "cosmo.png" file and make color code of any pixel accessible
     
print("Lese Kartendaten...\n")

reader = png.Reader(filename='cosmo.png')          
w, h, pixels, metadata = reader.read_flat()

#------------------Step 2: Check whether certain pixels are white -> Find out which map type it is

#First check whether the image fits for further reading
error = 0
if len(pixels) != w*h:
     print("Fehler: Karte nicht im originalen Farbmodus (indexed)! Beende Programm...\n")
     error = 1
if len(pixels) == 589824:
     print("Meteociel-Karte erkannt\n")
     mapsource = 'meteociel'
elif len(pixels) == 750000:
     print("DWD-Karte erkannt\n")
     mapsource = 'DWD'
else:
     print("Fehler: Karte besitzt nicht die richtigen Abmessungen! Beende Programm...\n")
     error = 1

#DWD: If image is okay, see where the cities are and find out map type 
#Meteociel: See where specific grey departement boundaries (RGB 808080) are (2 points per image, color index identical and > 2)

if error != 1:

     maptype = 'none'
     
     if mapsource == 'meteociel':
         x1 = 127
         y1 = 6
         x2 = 208
         y2 = 556
         p1 = y1*w+x1
         p2 = y2*w+x2
         if (pixels[p1] == pixels[p2] and pixels[p1] > 2):
              print("Karte 'Meteociel Nordwest erkannt!")
              maptype = 'meteociel_nw'

         x1 = 29
         y1 = 3
         x2 = 606
         y2 = 483
         p1 = y1*w+x1
         p2 = y2*w+x2
         if (pixels[p1] == pixels[p2] and pixels[p1] > 2):
              print("Karte 'Meteociel Nordost' erkannt!")
              maptype = 'meteociel_ne'

         x1 = 232
         y1 = 508
         x2 = 651
         y2 = 535
         p1 = y1*w+x1
         p2 = y2*w+x2
         if (pixels[p1] == pixels[p2] and pixels[p1] > 2):
              print("Karte 'Meteociel Suedost' erkannt!")
              maptype = 'meteociel_se'

         x1 = 208
         y1 = 5
         x2 = 334
         y2 = 476
         p1 = y1*w+x1
         p2 = y2*w+x2
         if (pixels[p1] == pixels[p2] and pixels[p1] > 2):
              print("Karte 'Meteociel Suedwest' erkannt!")
              maptype = 'meteociel_sw'
    
     else:
         x1 = 277
         y1 = 460
         x2 = 785
         y2 = 654
         p1 = y1*w+x1
         p2 = y2*w+x2
         if (pixels[p1] > 246 and pixels[p1] < 256) or (pixels[p2] > 246 and pixels[p2] < 256):
              print("Karte 'Deutschland Nord' erkannt!")
              maptype = 'dnord'

         x1 = 243
         y1 = 343
         x2 = 776
         y2 = 419
         p1 = y1*w+x1
         p2 = y2*w+x2
         if (pixels[p1] > 246 and pixels[p1] < 256) or (pixels[p2] > 246 and pixels[p2] < 256):
              print("Karte 'Deutschland Mitte' erkannt!")
              maptype = 'dmitte'
              
         x1 = 220
         y1 = 186
         x2 = 704
         y2 = 170
         p1 = y1*w+x1
         p2 = y2*w+x2
         
         if (pixels[p1] > 246 and pixels[p1] < 256) or (pixels[p2] > 246 and pixels[p2] < 256):
              print("Karte 'Deutschland Sued' erkannt!")
              maptype = 'dsued'

     if maptype == 'none':
          print("Fehler: Karte wurde nicht erkannt! Beende Programm...\n")

     #Reference number of lines and columns of the actual map (indices starting at 0)
     if (maptype == 'meteociel_sw' or maptype == 'meteociel_se' or maptype == 'meteociel_ne' or maptype == 'meteociel_nw'):
          x_topleft = 0       
          y_topleft = 0       
          x_botright = 767    
          y_botright = 767    
          columns = 768       
          lines = 768         
     else:
          x_topleft = 2
          y_topleft = 2
          x_botright = 997
          y_botright = 677
          columns = 996
          lines = 676

     #------------------Step 3: Build map pixel zeromatrix and identify red shaded (climb) pixels as "1".

     #Initialize matrix
     matrix = [[0 for x in range(columns)] for y in range(lines)] 

     #matrix has maximum index [767][767]         #hcm

     #Read row by row into matrix and identify climb

     #For Meteociel maps climb colors are taken from the legend at the bottom
     #Threshhold value can be adjusted by including more (or less) lift strength categories
     if (maptype == 'meteociel_sw' or maptype == 'meteociel_se' or maptype == 'meteociel_ne' or maptype == 'meteociel_nw'):
          y = 725
          x1 = 525
          x2 = 550
          x3 = 575
          x4 = 600
          x5 = 625
          x6 = 650
          x7 = 675
          x8 = 700
          x9 = 725
          x10 = 500
          x11 = 475
          p1 = y*w+x1
          p2 = y*w+x2
          p3 = y*w+x3
          p4 = y*w+x4
          p5 = y*w+x5
          p6 = y*w+x6
          p7 = y*w+x7
          p8 = y*w+x8
          p9 = y*w+x9
          p10 = y*w+x10
          p11 = y*w+x11
          lift1 = pixels[p1]
          lift2 = pixels[p2]
          lift3 = pixels[p3]
          lift4 = pixels[p4]
          lift5 = pixels[p5]
          lift6 = pixels[p6]
          lift7 = pixels[p7]
          lift8 = pixels[p8]
          lift9 = pixels[p9]
          lift10 = pixels[p10]
          lift11 = pixels[p11]
          j = y_topleft
          while j <= y_botright:
               i = x_topleft
               while i <= x_botright:
                    n = j*w+i
                    if (pixels[n] == lift1 or pixels[n] == lift2 or pixels[n] == lift3 or pixels[n] == lift4 or pixels[n] == lift5 or pixels[n] == lift6 or pixels[n] == lift7 or pixels[n] == lift8 or pixels[n] == lift9 or pixels[n] == lift10 or pixels[n] == lift11):           
                         matrix[j-y_topleft][i-x_topleft] = 1    
                    i = i+1
               j = j+1
     else:     
          j = y_topleft
          while j <= y_botright:
               i = x_topleft
               while i <= x_botright:
                    n = j*w+i
                    if pixels[n] >= 49 and pixels[n] <= 79:           
                         matrix[j-y_topleft][i-x_topleft] = 1    
                    if pixels[n] >= 94 and pixels[n] <= 110:
                         matrix[j-y_topleft][i-x_topleft] = 9         #9 are the Question marks: the color index of very strong climb (in cores) is very similar to strong sink
                    i = i+1
               j = j+1

     #Now we have a Matrix of 1's (smoothed climb fields) and 0 (no climb).

     #------------------Step 4: Cancel out irregularities in lines and columns by unifying divided 1's that are very close together in lines and columns or divided only by 9's
     repeat = 0
     while repeat < 2:
          #Line by line
          for j in range(0,lines):
               for i in range(0,columns-smooth):
                    if matrix[j][i] == 1 and matrix[j][i+1] != 1:
                         k = 1
                         while ((k<smooth and matrix[j][i+k] == 0) or matrix[j][i+k] == 9) and i+k < columns-1:
                              k = k+1
                         if matrix[j][i+k] == 1:
                              for l in range(1,k):
                                   matrix[j][i+l] = 1

          #Column by column
          for i in range(0,columns):
               for j in range(0,lines-smooth):
                    if matrix[j][i] == 1 and matrix[j+1][i] != 1:
                         k = 1
                         while ((k<smooth and matrix[j+k][i] == 0) or matrix[j+k][i] == 9) and j+k < lines-1:
                              k = k+1
                         if matrix[j+k][i] == 1:
                              for l in range(1,k):
                                   matrix[j+l][i] = 1                      
          repeat = repeat +1
     
     #Cancel out leftover "9"s
     for j in range(0,lines):
          for i in range(0,columns):
               if matrix[j][i] == 9:
                    matrix[j][i] = 0
          
     #------------------Step 5: Line by line and column by column, assign transition from sink to climb as "2" to depict lift contours
     
     #Line by line
     for j in range(0,lines):
          for i in range(0,columns-1):
               if matrix[j][i] == 0 and matrix[j][i+1] == 1:
                    matrix[j][i+1] = 2
               if matrix[j][i] == 1 and matrix[j][i+1] == 0:
                    matrix[j][i] = 2
     
     #Column by column
     for i in range(0,columns):
          for j in range(0,lines-1):
               if matrix[j][i] == 0 and matrix[j+1][i] == 1:
                    matrix[j+1][i] = 2
               if matrix[j][i] == 1 and matrix[j+1][i] == 0:
                    matrix[j][i] = 2              
                    
     #------------------Step 6: Smooth out the contours of "2"s
     
     #Draw a line of 0's around the map to account for stability
     for i in range(0,columns):    #top and bottom
          matrix[0][i] = 0
          matrix[lines-1][i] = 0
     
     for j in range(0, lines):     #left and right
          matrix[j][0] = 0
          matrix[j][columns-1] = 0
     
     #Go around the map and change every borderline 1 to 2
     for i in range(1,columns-1):  #top and bottom
          if matrix[1][i] == 1:
               matrix[1][i] = 2
          if matrix[lines-2][i] == 1:
               matrix[lines-2][i] = 2
     
     for j in range(1, lines-1):        #left and right
          if matrix[j][1] == 1:
               matrix[j][1] = 2
          if matrix[j][columns-2] == 1:
               matrix[j][columns-2] = 2

     #Delete all 2's that have more than 4 neighbor 2's
     for j in range(0,lines):
          for i in range(0,columns):
               if matrix[j][i] == 2:
                    if matrix[j][i+1] == 1 or matrix[j+1][i+1] == 1 or matrix[j+1][i] == 1 or matrix[j+1][i-1] == 1 or matrix[j][i-1] == 1 or matrix[j-1][i-1] == 1 or matrix[j-1][i] == 1 or matrix[j-1][i+1] == 1:
                         go = 0
                    else:
                         go = 1
                    if go == 1:    
                         twos = 0
                         if matrix[j][i+1] == 2:
                              twos = twos +1
                         if matrix[j+1][i+1] == 2:
                              twos = twos +1
                         if matrix[j+1][i] == 2:
                              twos = twos +1 
                         if matrix[j+1][i-1] == 2:
                              twos = twos +1 
                         if matrix[j][i-1] == 2:
                              twos = twos +1 
                         if matrix[j-1][i-1] == 2:
                              twos = twos +1 
                         if matrix[j-1][i] == 2:
                              twos = twos +1                          
                         if matrix[j-1][i+1] == 2:
                              twos = twos +1                          
                         if twos > 4:
                              matrix[j][i] = 0
               
     #Then: Cancel out single "2"s
     repeat = 0
     while repeat <3:
          for j in range(0,lines):
               for i in range(0,columns):
                    if matrix[j][i] == 2:
                         gozero = 0
                         if (matrix[j][i+1] == 0 and matrix[j][i-1] == 0) or (matrix[j+1][i] == 0 and matrix[j-1][i] == 0):
                              if matrix[j][i+1] == 1 or matrix[j+1][i+1] == 1 or matrix[j+1][i] == 1 or matrix[j+1][i-1] == 1 or matrix[j][i-1] == 1 or matrix[j-1][i-1] == 1 or matrix[j-1][i] == 1 or matrix[j-1][i+1] == 1: 
                                   gozero = 0
                              else:
                                   gozero = 1
                         if (matrix[j+1][i+1] == 0 and matrix[j-1][i-1] == 0) or (matrix[j+1][i-1] == 0 and matrix[j-1][i+1] == 0):
                              gozero = 1
                         if gozero == 1:
                              matrix[j][i] = 0    
          repeat = repeat+1
                         
                         
     #------------------Step 7: Show a predefined part of the number matrix for debugging purposes
     #Show raw output of part of the matrix
     #f = open("matrix_raw.txt", "w")
     #j = 322
     #while j <= 416:
     #    i = 664
     #    while i <= 850:
     #        f.write(str(matrix[j][i]))
     #        i = i+1
     #    j = j+1
     #    f.write("\n")
     #f.close()     

     #------------------Step 8: Make polygon around every wave contour and write to openair format file
     
     fout = open("wavemap_openair.txt", "w")
     fout.write("*Diese experimentelle Wellenkarte wurde erstellt mit 'Wavemap'.\n")
     
     for j in range(0,lines):
          for i in range(0,columns):
               if matrix[j][i] == 2:              #A wave begins here.
                    end = 0
                    p = i          
                    q = j          #Memorize coordinates of the wave beginning.
                    k = p
                    l = q          #Memorize coordinates of the current polygon point
                    points = 1
                    geostring_initial = georef(p,q,maptype)      #Georeference the point with coordinates p, q 
                    matrix[l][k] = 3    #Point is done.
                    
                    #Search for neighboring point (starting right, going clockwise)
                    if matrix[l][k+1] == 2:
                         p = k+1
                         angle = 90
                    elif matrix[l+1][k+1] == 2:
                         q = l+1
                         p = k+1
                         angle = 135
                    elif matrix[l+1][k] == 2:
                         q = l+1
                         angle = 180
                    elif matrix[l+1][k-1] == 2:
                         q = l+1
                         p = k-1
                         angle = 225
                    elif matrix[l][k-1] == 2:
                         p = k-1
                         angle = 270
                    elif matrix[l-1][k-1] == 2:
                         q = l-1
                         p = k-1
                         angle = 315
                    elif matrix[l-1][k] == 2:
                         q = l-1
                         angle = 0
                    elif matrix[l-1][k+1] == 2:
                         q = l-1
                         p = k+1
                         angle = 45
                    else:
                         end = 1
                         angle = 0
                         
                    matrix[q][p] = 3    #Point is done.
                    angle_prev = angle
                    
                    while end != 1:
                         r = 0
                         count = 1.0
                         while abs(r) < 3 and end != 1:
                              #Search for neighboring point (starting right, going clockwise)
                              if matrix[q][p+1] == 2:
                                   p = p+1
                                   angle = 90
                              elif matrix[q+1][p+1] == 2:
                                   q = q+1
                                   p = p+1
                                   angle = 135
                              elif matrix[q+1][p] == 2:
                                   q = q+1
                                   angle = 180
                              elif matrix[q+1][p-1] == 2:
                                   q = q+1
                                   p = p-1
                                   angle = 225
                              elif matrix[q][p-1] == 2:
                                   p = p-1
                                   angle = 270
                              elif matrix[q-1][p-1] == 2:
                                   q = q-1
                                   p = p-1
                                   angle = 315
                              elif matrix[q-1][p] == 2:
                                   q = q-1
                                   angle = 0
                              elif matrix[q-1][p+1] == 2:
                                   q = q-1
                                   p = p+1
                                   angle = 45
                              else:
                                   end = 1
                                   
                              matrix[q][p] = 3    #Point is done.
                              
                              #Update the accumulated curvature "r" since the last point
                              if end != 1:                                 
                                   count = count +1
                                   angle = (angle_prev+angle)/count
                                   if angle - angle_prev > 1:
                                        r = r+1
                                   elif angle-angle_prev < 1:
                                        r = r-1
                                   angle_prev = angle
                              
                         #Exiting this loop, either the wave has ended or we need a new polygon point    
                         if end != 1:
                              #Go backwards by three points and set new polygon point there. This is annoying, but useful for contour exactness
                              matrix[q][p] = 2
                              t = 0
                              while t<2:          #Should maybe be three?
                                   if matrix[q-1][p+1] == 3:
                                        q = q-1
                                        p = p+1
                                   elif matrix[q-1][p] == 3:
                                        q = q-1
                                   elif matrix[q-1][p-1] == 3:
                                        q = q-1
                                        p = p-1
                                   elif matrix[q][p-1] == 3:
                                        p = p-1
                                   elif matrix[q+1][p-1] == 3:
                                        q = q+1
                                        p = p-1
                                   elif matrix[q+1][p] == 3:
                                        q = q+1
                                   elif matrix[q+1][p+1] == 3:
                                        q = q+1
                                        p = p+1
                                   elif matrix[q][p+1] == 3:
                                        p = p+1
                                   else:
                                        print("Etwas bei den Polygonen ist schiefgelaufen.\n")
                                   matrix[q][p] = 2
                                   t = t+1
                              
                              #Here is the new polygon point.
                              
                              #If this is the second polygon point, subsequently write the first point to the file (this kills single point airspace artefacts)
                              if points == 1:                              
                                   fout.write("AC A\nAN WELLE\nAL 0\nAH 1\n")
                                   fout.write(geostring_initial) 
                              
                              #Now write the current point
                              geostring = georef(p,q,maptype)         #Georeference the point with coordinates p, q 
                              fout.write(geostring)                   #Write these coordinates to file: 
                              matrix[q][p] = 3
                              points = points+1
                         
                    #If we ever get here, the wave has ended.
                    fout.write("\n")
     
     fout.close()
     #If we ever get here, the entire map has been solved (No '2's left over.)
     
     print("OpenAir Luftraumdatei 'wavemap_openair.txt' geschrieben.")

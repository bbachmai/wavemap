#Wavemap 1.1

#This program makes an OpenAir airspace file from a wave forecast map (downloaded png image).
#Currently supported are COSMO-DE maps "Deutschland Nord", "Deutschland Mitte", "Deutschland Sued" and "Alpen".

#(c) 2017 Benjamin Bachmaier

#www.flugfieber.net

#A python distribution as well as the package "pyPNG" must be installed.

import png
import array
import math
from math import pi,sqrt,atan
import os

smooth = 4		#Smoothing factor defining how aggressive irregularities in wave contour shall be smoothed out (Default is 4)

#------------------Function: georeferencing of all available map types

def georef(px_x, px_y, maptype):
	#Returns a string containing the geo-coordinates of a pixel
	rtd = 180/pi
	if maptype == 'alpen':	
		y_NP = 3683.76422764
		x_NP = 445.5

		dx = x_NP-px_x
		dy = y_NP+px_y
		dist = sqrt(dx*dx+dy*dy)
		lat = 0.000000209249420*dist*dist -0.011436747352329*dist+90.000010539530194

		c = atan(dx/dy)*rtd
		lon = -1.011460842672144*c+9.997416742431932

	elif maptype == 'dsued':
		y_NP = 5163.5301204819
		x_NP = 476.5

		dx = x_NP-px_x
		dy = y_NP+px_y
		dist = sqrt(dx*dx+dy*dy)
		lat = 0.000000117899841*dist*dist -0.008179191193347*dist+89.999999999999986

		c = atan(dx/dy)*rtd
		lon = -0.999522641321516*c+10.001359350792196

	elif maptype == 'dmitte':
		y_NP = 4915.56097
		x_NP = 473.5

		dx = x_NP-px_x
		dy = y_NP+px_y
		dist = sqrt(dx*dx+dy*dy)
		lat = 0.000000093867125*dist*dist -0.007971583223335*dist+90.000000000000014

		c = atan(dx/dy)*rtd
		lon = -1.011160313697560*c+9.996511362096365

	elif maptype == 'dnord':
		y_NP = 4582.90243902439
		x_NP = 474.5

		dx = x_NP-px_x
		dy = y_NP+px_y
		dist = sqrt(dx*dx+dy*dy)
		lat = 0.000000086136311*dist*dist-0.007940279894018*dist+90.000000000000014

		c = atan(dx/dy)*rtd
		lon = -1.010245500195550*c+10.004147667638424
	
	#Now make formatted coordinates from the lat and lon decimal values
	
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
	
	geostring = "DP "+coords[0]+":"+coords[1]+":"+coords[2]+" N "+coords[3]+":"+coords[4]+":"+coords[5]+" E\n"
	
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
if len(pixels) != 663000:
	print("Fehler: Karte besitzt nicht die richtigen Abmessungen! Beende Programm...\n")
	error = 1

#If image is okay, see where the cities are and find out map type
maptype = 'none'
if error != 1:

	x1 = 784
	y1 = 425
	x2 = 474
	y2 = 252
	p1 = y1*w+x1
	p2 = y2*w+x2
	if (pixels[p1] > 246 and pixels[p1] < 250) or (pixels[p2] > 246 and pixels[p2] < 250):
		print("Karte 'Deutschland Nord' erkannt!")
		maptype = 'dnord'

	x1 = 184
	y1 = 250
	x2 = 866
	y2 = 411
	p1 = y1*w+x1
	p2 = y2*w+x2
	if (pixels[p1] > 246 and pixels[p1] < 250) or (pixels[p2] > 246 and pixels[p2] < 250):
		print("Karte 'Deutschland Mitte' erkannt!")
		maptype = 'dmitte'
		
	x1 = 402
	y1 = 320
	x2 = 869
	y2 = 103
	p1 = y1*w+x1
	p2 = y2*w+x2
	if (pixels[p1] > 246 and pixels[p1] < 250) or (pixels[p2] > 246 and pixels[p2] < 250):
		print("Karte 'Deutschland Sued' erkannt!")
		maptype = 'dsued'
		
	x1 = 354
	y1 = 68
	x2 = 885
	y2 = 485
	p1 = y1*w+x1
	p2 = y2*w+x2
	if (pixels[p1] > 246 and pixels[p1] < 250) or (pixels[p2] > 246 and pixels[p2] < 250):
		print("Karte 'Alpen' erkannt!")
		maptype = 'alpen'

	if maptype == 'none':
		print("Fehler: Karte wurde nicht erkannt! Beende Programm...\n")

	#Reference number of lines and columns of the actual map (indices starting at 0)
	x_topleft = 2
	y_topleft = 2
	x_botright = 997
	y_botright = 594
	columns = 996
	lines = 593

	#------------------Step 3: Build map pixel zeromatrix and identify red shaded (climb) pixels as "1".

	#Initialize matrix
	matrix = [[0 for x in range(columns)] for y in range(lines)] 

	#matrix has maximum index [592][995]

	#Read row by row into matrix and identify climb
	j = y_topleft
	while j <= y_botright:
		i = x_topleft
		while i <= x_botright:
			n = j*w+i
			if pixels[n] >= 50 and pixels[n] <= 79:			
				matrix[j-y_topleft][i-x_topleft] = 1	
			if pixels[n] >= 94 and pixels[n] <= 110:
				matrix[j-y_topleft][i-x_topleft] = 9		#9 are the Question marks: the color index of very strong climb (in cores) is very similar to strong sink
			i = i+1
		j = j+1

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
	
	#Now we have a Matrix of 1's (smoothed climb fields) and 0 (no climb).
		
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
	for i in range(0,columns):	#top and bottom
		matrix[0][i] = 0
		matrix[lines-1][i] = 0
	
	for j in range(0, lines):	#left and right
		matrix[j][0] = 0
		matrix[j][columns-1] = 0
	
	#Go around the map and change every borderline 1 to 2
	for i in range(1,columns-1):	#top and bottom
		if matrix[1][i] == 1:
			matrix[1][i] = 2
		if matrix[lines-2][i] == 1:
			matrix[lines-2][i] = 2
	
	for j in range(1, lines-1):		#left and right
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
	# f = open("matrix_raw.txt", "w")
	# j = 404
	# while j <= 461:
		# i = 544
		# while i <= 617:
			# f.write(str(matrix[j][i])+" ")
			# i = i+1
		# j = j+1
		# f.write("\n")
	# f.close()

	#------------------Step 8: Make polygon around every wave contour and write to openair format file
	
	fout = open("wavemap_openair.txt", "w")
	fout.write("*Diese experimentelle Wellenkarte wurde erstellt mit 'Wavemap'.\n")
	
	for j in range(0,lines):
		for i in range(0,columns):
			if matrix[j][i] == 2:			#A wave begins here.
				end = 0
				p = i		
				q = j		#Memorize coordinates of the wave beginning.
				k = p
				l = q		#Memorize coordinates of the current polygon point
				fout.write("AC A\nAN WELLE\n")
				geostring = georef(p,q,maptype)		#Georeference the point with coordinates p, q 
				fout.write(geostring)				#Write these coordinates to file: 

				matrix[l][k] = 3 	#Point is done.
				
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
					
				matrix[q][p] = 3	#Point is done.
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
							
						matrix[q][p] = 3	#Point is done.
						
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
						while t<2:		#Should maybe be three?
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
						geostring = georef(p,q,maptype)		#Georeference the point with coordinates p, q 
						fout.write(geostring)				#Write these coordinates to file: 
						matrix[q][p] = 3
					
				#If we ever get here, the wave has ended.
				fout.write("\n")
	
	#If we ever get here, the entire map has been solved (No '2's left over.)
	fout.close()
	print("OpenAir Luftraumdatei 'wavemap_openair.txt' geschrieben.")
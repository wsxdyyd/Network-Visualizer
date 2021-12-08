# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.

#Thanks to Keith Peters from Coding Math youtube channel, he's a real OG


from math import sqrt, floor, pi, atan2
from random import random
from kivy.uix.scatter import Scatter
from kivy.input.providers.mouse import MouseMotionEvent


def normalize(value, minV, maxV): #returns a normalized value between 0-1
	return (value-minV) / float(maxV - minV)

def lerp(norm_value, minV, maxV): #linear interpolation for a desired range
	return  norm_value * (maxV - minV) + minV

#maps a value from range_A to range_B
def map_to_range (value, rangeA_min, RangeA_max, RangeB_min, RangeB_max):
	N_value = normalize(value, rangeA_min, RangeA_max)
	return lerp(N_value, RangeB_min, RangeB_max)
    
     #succint version: return lerp(normalize(value, rangeA_min, RangeA_max), RangeB_min, RangeB_max)

	
def clamp(value, minimum, maximum): #validate input
	return min(max(value, minimum), maximum)

def distance( p0_X, p0_Y, p1_X, p1_Y):
	dx = p1_X - p0_X
	dy = p1_Y - p0_Y
	return sqrt(dx * dx + dy * dy)

def random_range(minimum, maximum):
	return minimum + random() * (maximum - minimum)	


def random_int(minimum, maximum): #add 1 to range and floor to prevent bias with round
	return floor(round(minimum + random() * (maximum - minimum+1)))

def deg_to_rad(deg):
	return deg * pi/ 180

def rad_to_deg(rad):
	return rad * 180/pi

def round_to_places(value, places):
	mult = pow(10, places)
	return round(value * mult) / mult

def round_to_nearest(value, nearest): #use for snap to grid
	return round(value / nearest) * nearest



    
def angle_between_points(objectA_pos: tuple[float, float], objectB_pos: tuple[float, float]) -> float:

	"""
	Calculate the angle between two points.
	"""
	
	dx = objectB_pos[1] - objectA_pos[1]
	dy = objectB_pos[0] - objectA_pos[0]

	return atan2(dx,dy)



def distance_between_points(destination: tuple[float, float], source: tuple[float, float]) -> tuple[float, float, float]:

	"""
	Calculate the distance between two points.
	"""

	x_distance = destination[0] - source[0] 
	y_distance = destination[1] - source[1]

	distance = sqrt( x_distance*x_distance + y_distance*y_distance )

	return distance, x_distance, y_distance






class Icon_Scatter_Override(Scatter):

    """
    Override kivy Scatter widget to allow for scatter widget to drag/drop without bugging its position when being updated by update()
    """

    def __init__(self, **kwargs):
        super().__init__() 


    def on_motion(self, touch: MouseMotionEvent ) -> bool: 

        """
        Kivy on_motion callback. 
        """

        response =  super(Icon_Scatter_Override, self).on_motion(touch)
        if response: 
            self.parent_widget.do_layout = True

        return response

    def on_touch_down(self, touch: MouseMotionEvent ) -> bool:

        """
        Kivy on_touch_down callback. 
        """
 
        response =  super(Icon_Scatter_Override, self).on_touch_down(touch)
        if response: 
            self.parent_widget.pos = (self.center[0]-28, self.center[1]-28    )
            self.parent_widget.do_layout = False

        return response

    def on_touch_up(self, touch: MouseMotionEvent ) -> bool: 

        """
        Kivy on_touch_up callback. 
        """

        response = super(Icon_Scatter_Override, self).on_touch_up(touch)
        if response:
            self.parent_widget.pos = (self.center[0]-28, self.center[1]-28  )  
            self.parent_widget.do_layout = True

        return response




country_lat_long = { 'Unresolved': [-70, 20], 'None' : [10, 30], 'Canada': [56.130366, -106.346771], 'Guinea-Bissau': [11.803749, -15.180413], 'Saint Helena': [-24.143474, -10.030696], 'Lithuania': [55.169438, 23.881275], 'Cambodia': [12.565679, 104.990963], 'Ethiopia': [9.145, 40.489673], 'Aruba': [12.52111, -69.968338], 'Swaziland': [-26.522503, 31.465866], 'Argentina': [-38.416097, -63.616672], 'Bolivia': [-16.290154, -63.588653], 'Cameroon': [7.369722, 12.354722], 'Burkina Faso': [12.238333, -1.561593], 'Turkmenistan': [38.969719, 59.556278], 'Ghana': [7.946527, -1.023194], 'Saudi Arabia': [23.885942, 45.079162], 'Rwanda': [-1.940278, 29.873888], 'South Africa': [-30.559482, 22.937506], 'Japan': [36.204824, 138.252924], 'Cape Verde': [16.002082, -24.013197], 'Northern Mariana Islands': [17.33083, 145.38469], 'Slovenia': [46.151241, 14.995463], 'Guatemala': [15.783471, -90.230759], 'Bosnia and Herzegovina': [43.915886, 17.679076], 'Kuwait': [29.31166, 47.481766], 'Jordan': [30.585164, 36.238414], 'Dominica': [15.414999, -61.370976], 'Liberia': [6.428055, -9.429499], 'Maldives': [3.202778, 73.22068], 'Jamaica': [18.109581, -77.297508], 'Falkland Islands [Islas Malvinas]': [-51.796253, -59.523613], 'Congo [Republic]': [-0.228021, 15.827659], 'Martinique': [14.641528, -61.024174], 'S\xc3\xa3o Tom\xc3\xa9 and Pr\xc3\xadncipe': [0.18636, 6.613081], 'Albania': [41.153332, 20.168331], 'French Guiana': [3.933889, -53.125782], 'Niue': [-19.054445, -169.867233], 'Monaco': [43.750298, 7.412841], 'Wallis and Futuna': [-13.768752, -177.156097], 'New Zealand': [-40.900557, 174.885971], 'Yemen': [15.552727, 48.516388], 'Jersey': [49.214439, -2.13125], 'Bahamas': [25.03428, -77.39628], 'Greenland': [71.706936, -42.604303], 'Samoa': [-13.759029, -172.104629], 'Macau': [22.198745, 113.543873], 'Norfolk Island': [-29.040835, 167.954712], 'United Arab Emirates': [23.424076, 53.847818], "Cote D'Ivoire" :  [7.539989, -5.54708], "C\xc3\xb4te d'Ivoire": [7.539989, -5.54708], 'Kosovo': [42.602636, 20.902977], 'India': [20.593684, 78.96288], 'Azerbaijan': [40.143105, 47.576927], 'Lesotho': [-29.609988, 28.233608], 'Saint Vincent and the Grenadines': [12.984305, -61.287228], 'Kenya': [-0.023559, 37.906193], 'South Korea': [35.907757, 127.766922], 'Tajikistan': [38.861034, 71.276093], 'Guam': [13.444304, 144.793731], 'Turkey': [38.963745, 35.243322], 'Afghanistan': [33.93911, 67.709953], 'Bangladesh': [23.684994, 90.356331], 'Mauritania': [21.00789, -10.940835], 'Solomon Islands': [-9.64571, 160.156194], 'Turks and Caicos Islands': [21.694025, -71.797928], 'Saint Lucia': [13.909444, -60.978893], 'Gaza Strip': [31.354676, 34.308825], 'San Marino': [43.94236, 12.457777], 'Mongolia': [46.862496, 103.846656], 'France': [46.227638, 2.213749], 'Bermuda': [32.321384, -64.75737], 'Namibia': [-22.95764, 18.49041], 'Somalia': [5.152149, 46.199616], 'Peru': [-9.189967, -75.015152], 'Laos': [19.85627, 102.495496], 'Nauru': [-0.522778, 166.931503], 'Seychelles': [-4.679574, 55.491977], 'Norway': [60.472024, 8.468946], 'Malawi': [-13.254308, 34.301525], 'Cook Islands': [-21.236736, -159.777671], 'Benin': [9.30769, 2.315834], 'R\xc3\xa9union': [-21.115141, 55.536384], 'Libya': [26.3351, 17.228331], 'Cuba': [21.521757, -77.781167], 'Montenegro': [42.708678, 19.37439], 'Saint Kitts and Nevis': [17.357822, -62.782998], 'Togo': [8.619543, 0.824782], 'China': [35.86166, 104.195397], 'Armenia': [40.069099, 45.038189], 'Timor-Leste': [-8.874217, 125.727539], 'Dominican Republic': [18.735693, -70.162651], 'French Polynesia': [-17.679742, -149.406843], 'Ukraine': [48.379433, 31.16558], 'Bahrain': [25.930414, 50.637772], 'Tonga': [-21.178986, -175.198242], 'Indonesia': [-0.789275, 113.921327], 'Western Sahara': [24.215527, -12.885834], 'Finland': [61.92411, 25.748151], 'Central African Republic': [6.611111, 20.939444], 'New Caledonia': [-20.904305, 165.618042], 'Mauritius': [-20.348404, 57.552152], 'Liechtenstein': [47.166, 9.555373], 'Belarus': [53.709807, 27.953389], 'British Virgin Islands': [18.420695, -64.639968],'Virgin Islands, British': [18.420695, -64.639968] ,'Mali': [17.570692, -3.996166], 'Vatican City': [41.902916, 12.453389], 'Russia': [61.52401, 105.318756], 'Bulgaria': [42.733883, 25.48583], 'United States': [37.09024, -95.712891], 'Romania': [45.943161, 24.96676], 'Angola': [-11.202692, 17.873887], 'French Southern Territories': [-49.280366, 69.348557], 'Cayman Islands': [19.513469, -80.566956], 'Trinidad and Tobago': [10.691803, -61.222503], 'Tokelau': [-8.967363, -171.855881], 'Cyprus': [35.126413, 33.429859], 'South Georgia and the South Sandwich Islands': [-54.429579, -36.587909], 'Sweden': [60.128161, 18.643501], 'Qatar': [25.354826, 51.183884], 'Malaysia': [4.210484, 101.975766], 'Austria': [47.516231, 14.550072], 'Vietnam': [14.058324, 108.277199], 'Mozambique': [-18.665695, 35.529562], 'Uganda': [1.373333, 32.290275], 'Hungary': [47.162494, 19.503304], 'Niger': [17.607789, 8.081666], 'Brazil': [-14.235004, -51.92528], 'Faroe Islands': [61.892635, -6.911806], 'Guinea': [9.945587, -9.696645], 'Panama': [8.537981, -80.782127], 'Costa Rica': [9.748917, -83.753428], 'Luxembourg': [49.815273, 6.129583], 'American Samoa': [-14.270972, -170.132217], 'Andorra': [42.546245, 1.601554], 'Chad': [15.454166, 18.732207], 'Gibraltar': [36.137741, -5.345374], 'Ireland': [53.41291, -8.24389], 'Pakistan': [30.375321, 69.345116], 'Palau': [7.51498, 134.58252], 'Nigeria': [9.081999, 8.675277], 'Ecuador': [-1.831239, -78.183406], 'Czech Republic': [49.817492, 15.472962], 'Brunei': [4.535277, 114.727669], 'Brunei Darussalam': [4.535277, 114.727669] ,'Australia': [-25.274398, 133.775136], 'Iran, Islamic Republic of' : [32.427908, 53.688046] ,'Iran': [32.427908, 53.688046], 'Algeria': [28.033886, 1.659626], 'El Salvador': [13.794185, -88.89653], 'Tuvalu': [-7.109535, 177.64933], 'Pitcairn Islands': [-24.703615, -127.439308], 'Saint Pierre and Miquelon': [46.941936, -56.27111], 'Marshall Islands': [7.131474, 171.184478], 'Chile': [-35.675147, -71.542969], 'Puerto Rico': [18.220833, -66.590149], 'Belgium': [50.503887, 4.469936], 'Kiribati': [-3.370417, -168.734039], 'Haiti': [18.971187, -72.285215], 'Belize': [17.189877, -88.49765], 'Hong Kong': [22.396428, 114.109497], 'Sierra Leone': [8.460555, -11.779889], 'Georgia': [42.315407, 43.356892], 'Gambia': [13.443182, -15.310139], 'Philippines': [12.879721, 121.774017],'Moldova, Republic of': [47.411631, 28.369885],'Moldova': [47.411631, 28.369885], 'Macedonia': [41.608635, 21.745275], 'Netherlands Antilles': [12.226079, -69.060087], 'Croatia': [45.1, 15.2], 'Malta': [35.937496, 14.375416], 'Guernsey': [49.465691, -2.585278], 'Thailand': [15.870032, 100.992541], 'Switzerland': [46.818188, 8.227512], 'Grenada': [12.262776, -61.604171], 'Myanmar [Burma]': [21.913965, 95.956223], 'U.S. Virgin Islands': [18.335765, -64.896335], 'Isle of Man': [54.236107, -4.548056], 'Portugal': [39.399872, -8.224454], 'Estonia': [58.595272, 25.013607], 'Uruguay': [-32.522779, -55.765835], 'Bouvet Island': [-54.423199, 3.413194], 'Lebanon': [33.854721, 35.862285], 'Svalbard and Jan Mayen': [77.553604, 23.670272], 'Uzbekistan': [41.377491, 64.585262], 'Tunisia': [33.886917, 9.537499], 'Djibouti': [11.825138, 42.590275], 'Heard Island and McDonald Islands': [-53.08181, 73.504158], 'Antigua and Barbuda': [17.060816, -61.796428], 'Spain': [40.463667, -3.74922], 'Colombia': [4.570868, -74.297333], 'Burundi': [-3.373056, 29.918886], 'Slovakia': [48.669026, 19.699024], 'Taiwan': [23.69781, 120.960515], 'Fiji': [-16.578193, 179.414413], 'Barbados': [13.193887, -59.543198], 'Madagascar': [-18.766947, 46.869107], 'Italy': [41.87194, 12.56738], 'Bhutan': [27.514162, 90.433601], 'Sudan': [12.862807, 30.217636], 'Palestinian Territories': [31.952162, 35.233154], 'Palestinian Territory': [31.952162, 35.233154],'Nepal': [28.394857, 84.124008], 'Singapore': [1.352083, 103.819836], 'Micronesia': [7.425554, 150.550812], 'Netherlands': [52.132633, 5.291266], 'Tanzania, United Republic of': [-6.369028, 34.888822] ,'Tanzania': [-6.369028, 34.888822], 'Suriname': [3.919305, -56.027783], 'Anguilla': [18.220554, -63.068615], 'Venezuela': [6.42375, -66.58973], 'Israel': [31.046051, 34.851612], 'Oman': [21.512583, 55.923255], 'Iceland': [64.963051, -19.020835], 'Zambia': [-13.133897, 27.849332], 'Senegal': [14.497401, -14.452362], 'Papua New Guinea': [-6.314993, 143.95555], 'Zimbabwe': [-19.015438, 29.154857], 'Germany': [51.165691, 10.451526], 'Vanuatu': [-15.376706, 166.959158], 'Denmark': [56.26392, 9.501785], 'Kazakhstan': [48.019573, 66.923684], 'Poland': [51.919438, 19.145136], 'Eritrea': [15.179384, 39.782334], 'Kyrgyzstan': [41.20438, 74.766098], 'Mayotte': [-12.8275, 45.166244], 'British Indian Ocean Territory': [-6.343194, 71.876519], 'Iraq': [33.223191, 43.679291], 'Montserrat': [16.742498, -62.187366], 'Mexico': [23.634501, -102.552784], 'North Korea': [40.339852, 127.510093], 'Paraguay': [-23.442503, -58.443832], 'Latvia': [56.879635, 24.603189], 'Guyana': [4.860416, -58.93018], 'Syria': [34.802075, 38.996815], 'Guadeloupe': [16.995971, -62.067641], 'Morocco': [31.791702, -7.09262], 'Honduras': [15.199999, -86.241905], 'Equatorial Guinea': [1.650801, 10.267895], 'Egypt': [26.820553, 30.802498], 'Nicaragua': [12.865416, -85.207229], 'Cocos [Keeling] Islands': [-12.164165, 96.870956], 'Serbia': [44.016521, 21.005859], 'Congo [DRC]': [-4.038333, 21.758664], 'Congo, The Democratic Republic of the' : [-4.038333, 21.758664], 'Comoros': [-11.875001, 43.872219], 'United Kingdom': [55.378051, -3.435973], 'Antarctica': [-75.250973, -0.071389], 'Christmas Island': [-10.447525, 105.690449], 'Greece': [39.074208, 21.824312], 'Sri Lanka': [7.873054, 80.771797], 'Gabon': [-0.803689, 11.609444], 'Botswana': [-22.328474, 24.684866], 'Europe' : [54.5260, 15.2551], 'Russian Federation': [61.5240, 105.3188], 'Syrian Arab Republic': [34.8021, 38.9968], 'Korea, Republic of' : [35.9078, 127.7669], 'Anonymous Proxy': [0,0] , 'Satellite Provider': [0,0], 'Asia/Pacific Region' : [-50,130], 'Holy See (Vatican City State)': [41.9021788,12.4536007], 'Reunion' : [21.1151, 55.5364], "Lao People's Democratic Republic": [18.206296, 103.889022] }
#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import geopy
from geopy.distance import geodesic
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from math import radians
from sklearn.metrics.pairwise import haversine_distances


# In[2]:


def GetGeoDistance(points:np.array, scale:str="meters") -> np.array:
    
    '''
    This function computes the geodesic distance implemented from geopy.distance.geodesic
    
    Parameters
    ----------
    
    points: numpy array of shape (n_points, 2)
        Numpy array containing the latitude and longitute of the points in this order
    
    scale: str,string
        String indicating of the distance will be meters, kilometers, etc
    
    Return
    ------
    
    '''
    
    shape = points.shape[0]
    matrix_distance = np.zeros((shape, shape))

    for i, point_a in enumerate(points):
        for j, point_b in enumerate(points):
            if i < j:
                
                dist = geodesic(point_a, point_b)
                dist = getattr(dist, scale)
                
                matrix_distance[i,j] = dist
                matrix_distance[j,i] = dist
            
        print(f"Iteration {i + 1} of {shape}", end="\r")

    return matrix_distance


# In[3]:


def GetClosestPoint(ref_points:np.array, matrix_distance:np.array) -> pd.DataFrame:
    
    '''
    This function gets the two closest points based on a matrix distance
    
    Parameters
    ----------
    
        ref_points: numpy array of shape (n_points, 2).
            Numpy array containing the latitude and longitute of the points compared
            where the matrix_distance came
            
        matrix_distance: numpy array of shape (n_point, n_points)
            Quadratic matrix containing the distances among each point
        
    Return
    ------
    
        pd.DataFrame
            Pandas dataframe with the shortest distance between two points
    
    '''
    
    closest_points = pd.DataFrame(columns=["point_a", "point_b",
                                        "index_a","index_b",
                                        "distance"])
    
    index_min = np.argmin(matrix_distance, axis=0)
    
    a_data = []
    b_data = []
    idx_a = []
    idx_b = []
    dist = []

    for i in range(matrix_distance.shape[0]):
    
        a_data.append((ref_points[i, 0], ref_points[i, 1]))
        b_data.append((ref_points[index_min[i], 0], ref_points[index_min[i], 1]))
    
        idx_a.append(i)
        idx_b.append(index_min[i])
    
        dist.append(matrix_distance[i, index_min[i]])
    
    closest_points["point_a"] = a_data
    closest_points["point_b"] = b_data
    closest_points["index_a"] = idx_a
    closest_points["index_b"] = idx_b
    closest_points["distance"] = dist
    
    return closest_points


# In[4]:


def ParserPointsPlotly(points_a:np.array,
                       points_b:np.array,
                       distances:np.array) -> "tuple(list, list, list)":
    
    '''
    This function gets an appropiate format to plot "marks+lines" in a plottly
    Scattermapbox object. Avoiding connect all the points among each other
    
    Parameters
    ----------
    
    points_a: numpy array of shape (n_points, 2)
        Numpy array containing the latitude and longitute of the points A in this order
    
    points_b: numpy array of shape (n_points, 2)
        Numpy array containing the latitude and longitute of the points B in this order
    
    distances: array-like
        Distances between the points A and B
        
    Return
    ------
    
    tuple(latitude, longitude, distance): Tuple containing three list with the latitude
        longitude and distance respectively
    
    '''
    
    latitude = []
    longitude = []
    distance = []
    
    for a,b,d in zip(points_a, points_b, distances):
    
        latitude.append(a[0])
        latitude.append(b[0])
        latitude.append(None)
    
        longitude.append(a[1])
        longitude.append(b[1])
        longitude.append(None)
    
        distance.append(d)
        distance.append(d)
        distance.append(None)
        
    return (latitude, longitude, distance)


# In[5]:


def PlotPlottlyMapBox(longitude, latitude, distance):
    
    fig = go.Figure(go.Scattermapbox(
                    mode = "lines+markers",
                    lon = longitude,
                    lat = latitude,
                    text = distance,
                    hovertemplate="Distance: %{text}<br>Latitude: %{lat}<br>Longitude: %{lon}<extra></extra>"))

    fig.update_layout(mapbox_style = "open-street-map")
    fig.update_layout(margin = {'l':0,'t':0,'b':0,'r':0}, 
                      mapbox={"center":{"lon":-99.0725447,
                                        "lat":19.4407305},
                              "zoom":8.5})

    fig.update_traces(marker=dict(size=8, color="black", opacity=1))

    fig.update_layout(showlegend=False)
    
    return fig


# In[6]:


class IdentifyFalsePoints():
    
    '''
    This class identify what points are describing the same element.
    The choice is based on a threshold distance (Haversine distance) in
    meters and relevance of the points
    
    Parameters
    ----------
    
    points: numpy array of shape (n_points, 2)
        Numpy array containing the latitude and longitute of the points in this order
    
    criterion: numpy array of shape (n_points, )
        Numpy array containing values related to each point. This value will be used
        to define what point should be deleted. For example, if two points (a, b) has a distance
        less than 10 meters and their criterion value are (0, 10), the point a should be
        deleted because its criterion value is the smallest
    
    distance: int|float; integer|float
        Numeric value to use as threshold to check what points are probably the same point
    
    '''
    
    def __init__(self, points, criterion, distance):
        
        self.points = points
        
        self.criterion = pd.DataFrame(criterion, columns=["criterion"])
        self.criterion.index = np.arange(0, self.criterion.shape[0], 1)
        
        self.threshold_dist = distance
        
    def havernine(self, points):
        
        # Transforming into radians
        lat_rads = [radians(lat) for lat in points[:,0]]
        lon_rads = [radians(lon) for lon in points[:,1]]
        
        lat_lon_rads = np.array([lat_rads, lon_rads]).transpose()
        
        # Havernine mutiplied by the earth radius (km) and meters
        matrix_dist = haversine_distances(lat_lon_rads) * 6378.1270 * 1000
        
        return matrix_dist
    
    def fit_transform(self):
        
        '''
        This function check what points are the same and return an index of those
        points that should be deleted
        
        Returns
        -------
        
        np.array: numpy array of shape (n_points, )
            containing the index of the points that should be deleted
        
        '''
        
        points = self.points.copy()
        
        # Defining a general index for each point rather than one depending in
        # the current distance matrix
        true_index = np.arange(0, points.shape[0], 1)
        
        self.index_drop_points = []
        
        # Iterating until there is no points with a distance less than threshold
        while points.shape[0]:
            
            # Matrix distance
            matrix_dist = self.havernine(points)

            # Using only the upper triangule to avoid repeated
            dist_upper_t = np.triu(matrix_dist)

            # Filtering according to distance. Getting the real index of the points
            mask = (dist_upper_t < self.threshold_dist) & (dist_upper_t > 0)
            current_index = np.transpose(mask.nonzero())
            true_points = true_index[current_index]
            
            # Creating a graph to look for "the weakest" node in the connected component.
            # The weakest node is the point with the smallest value according to the criterion
            g = nx.Graph()
            g.add_edges_from(true_points)
            
            current_index_drop_points = []
            for component in nx.connected_components(g):
    
                # The name of the node is equal to the index where is located the point
                node_name = list(component)
    
                # If two points has the same value in the criterion. It'll return
                # the first index of the match
                false_point_name = self.criterion.iloc[node_name].idxmin()[0]
    
                self.index_drop_points.append(false_point_name)
                current_index_drop_points.append(false_point_name)
    
            g.remove_nodes_from(current_index_drop_points)
            g.remove_nodes_from(list(nx.isolates(g)))
        
            # Updating the index of the points we'll be using in the next iteration
            true_index = np.array(g.nodes)
            points = self.points[list(true_index),:].copy()
        
        self.index_drop_points = np.unique(self.index_drop_points)
        
        return self.index_drop_points
#!/usr/bin/env python
# coding: utf-8

# # Веб-карта объектов культурного наследия Екатеринбурга 
# 

# ## 1. Импортируем необходимые библиотеки

# In[1]:


import pandas as pd
import geopandas as gpd
import folium

from shapely import geometry


# ## 2. Загружаем и подготавливаем файлы

# In[2]:


data_bounds = gpd.read_file('bounds.geojson')
data_points = gpd.read_file('points.geojson')
data_buildings = gpd.read_file('pol.geojson')
data_ans = gpd.read_file('ans.geojson')


# #### приводим всё к одной проекции 39N

# In[3]:


data_bounds = data_bounds.to_crs("EPSG:32639")
data_points = data_points.to_crs("EPSG:32639")
data_buildings = data_buildings.to_crs("EPSG:32639")
data_ans = data_ans.to_crs("EPSG:32639")
data_buildings.crs = data_points.crs
data_points.crs.name


# ## 3. Создаём сетку

# #### получение экстенда на основе точек ОКН

# In[4]:


total_bounds = data_points.total_bounds
minX, minY, maxX, maxY = total_bounds


# #### установление размера единицы сетки в метрах

# In[5]:


square_size = 400


# #### функция для построения сетки

# In[6]:


grid_cells = []
x, y = (minX, minY)
geom_array = []

while y <= maxY:
        while x <= maxX:
            geom = geometry.Polygon([(x,y), (x, y+square_size), (x+square_size, y+square_size), (x+square_size, y), (x, y)])
            geom_array.append(geom)
            x += square_size
        x = minX
        y += square_size


fishnet = gpd.GeoDataFrame(geom_array, columns=['geometry']).set_crs('EPSG:32639')
fishnet['id'] = fishnet.index


# #### соединение точек с единицами сетки и подсчёт их количества

# In[7]:


merged = gpd.sjoin(data_points, fishnet, how='left', predicate='within')
merged['n'] = 1
dissolve = merged.dissolve(by="index_right", aggfunc="count")
fishnet.loc[dissolve.index, 'n'] = dissolve.n.values


# ## 4. Создаём веб-карту

# In[8]:


data_points_4326 = data_points.to_crs('EPSG:4326')
m = folium.Map(location=[data_points_4326.centroid.y.mean(), data_points_4326.centroid.x.mean()], zoom_start=12,  tiles="cartodb positron", control_scale=True)


# #### создание картограммы на базе сетки

# In[9]:


folium.Choropleth(
    geo_data=fishnet,
    data=fishnet,
    columns=['id', 'n'],
    fill_color='BuPu',
    fill_opacity = 0.5,
    key_on='id',
    nan_fill_opacity=0,
   line_color = "#0000",
   legend_name="amount of heritage sites",
   name='Heritage Sites Concentration'
).add_to(m)


# In[10]:


#проверяем картограмму на карте
m


# ### Добавляем здания (полигоны) ОКН 

# In[11]:


folium.GeoJson(
    data_buildings,
    name="Heritage buildings",
    style_function=lambda x: {
        "fillColor": 'blue'
    },
    highlight_function=lambda x: {"fillOpacity": 0.8},
    zoom_on_click=True,
    show=False,
).add_to(m)


# In[12]:


m


# ### Добавляем административные границы города

# In[13]:


folium.GeoJson(
    data_bounds,
    name="Ekaterinburg bounds",
    style_function=lambda x: {
        "fillColor": 'blue'
    },
    highlight_function=lambda x: {"fillOpacity": 0.4},
    zoom_on_click=True,
    show=False,
).add_to(m)


# In[14]:


m


# ### Добавляем кластеризацию точек

# In[15]:


from folium.plugins import MarkerCluster
marker_cluster = MarkerCluster(name='Heritage Sites')
mc1= folium.plugins.FeatureGroupSubGroup(marker_cluster, 'Heritage Sites')
m.add_child(marker_cluster)
m.add_child(mc1)
mc1.add_child(folium.GeoJson(data_points_4326.to_json(), embed=False, show=True))
m


# ### Добавляем отдельный слой с ансамблями и достопримечательными местами

# In[16]:


folium.GeoJson(
    data_ans,
    name="Ensembles and places of interest",
    style_function=lambda x: {
        "fillColor": 'red'
    },
    highlight_function=lambda x: {"fillOpacity": 0.4},
    zoom_on_click=True,
    show=False,
).add_to(m)
m


# ### Добавляем виджеты на карту

# In[17]:


#импортируем плагины
from folium.plugins import MousePosition
from folium.plugins import Fullscreen


# In[18]:


folium.LayerControl().add_to(m)
MousePosition().add_to(m)
Fullscreen(
    position="bottomright",
    title="Expand me",
    title_cancel="Exit me",
    force_separate_button=True,
).add_to(m)
m


# ## 4. Сохраняем карту в формате index.html file и публикуем её

# In[19]:


m.save("index.html")


# In[ ]:





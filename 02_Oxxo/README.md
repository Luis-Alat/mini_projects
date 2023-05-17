# Oxxos en la Ciudad de México

Este es un proyecto dedicado a explorar principalmente la distribución de los oxxos en la Ciudad de México (cdmx) y parte del Valle de México... sólo porque sí.

## Descripción de notebooks

El proyecto consiste en cuatros partes principales (y que hacen referencia al mismo número encontrado en los notebook) descritas a continuación:

1. *Web scrapping*: Aquí se obtuvieron las coordenadas de cada de uno de los oxxos en la cdmx y parte del valle de méxico. Lo anterior a través de una búsqueda iterativa en google maps por cada código postal de la ciudad. Adicionalmente otros datos como el número de reseñas, nombre de la tienda y calificación de la sucursal fueron obtenidos.

2. *Cleaning scrapping*: Todos los resultados repetidos o inconsistencias de falsos positivos fueron eliminados en ésta parte. A su vez, éstos datos fueron cruzados con información geográfica de la cdmx como los es la población de las alcaldías y extensión territorial.

3. *Cleaning outliers*: Como parte de los trabajos de limpieza, fueron removidas sucursales "aisladas" en la cdmx y además, falsos positivos de sucursales muy cercanas las unas a las otras. Debido a errores de medición donde dos o más puntos referenciaban a la misma tienda.

4. *Exploratory data analysis*: Éste constituye el paso final de éste proyecto. Aquí se exploran la distribución y comportamiento de los oxxos en la cdmx principalmente.

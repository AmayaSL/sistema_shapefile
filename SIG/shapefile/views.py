from django.shortcuts import render, get_object_or_404, redirect
from shapefile.forms import MinasPointForm
from django.contrib.gis.geos import Point
from shapefile.models import MinasPoint
from django.http import JsonResponse
from django.core.serializers import serialize
from rest_framework.response import Response
from rest_framework import status
import shapefile
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
import os
import geopandas as gpd
import pandas as pd
import tempfile
from decimal import Decimal


# Create your views here.



def verMapa(request):
    # Obtener los puntos y serializarlos a GeoJSON
    puntos = MinasPoint.objects.all()
    geojson_data = serialize('geojson', puntos, geometry_field='geom', fields=('ocupacion', 'genero', 'lugar_deto'))

    # Verifica si la solicitud es AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(geojson_data, safe=False)

    # Si no es AJAX, renderiza la plantilla HTML
    return render(request, 'gis/mapa.html', {'geojson_data': geojson_data})

#def nuevoDepartamento(request):
#    if request.method == 'POST':
 #       formaDepartamento = DepartamentoForm(request.POST)
  #      if formaDepartamento.is_valid():
   #         formaDepartamento.save()
 #           return redirect('inicio')
  #  else:
   #     formaDepartamento = DepartamentoForm()

    #return render(request, 'departamentos/agregar_departamento.html' , {'formaDepartamento': formaDepartamento})

#def nuevoMunicipio(request):
 #   if request.method == 'POST':
  #      formaMunicipio = MunicipioForm(request.POST)
   #     if formaMunicipio.is_valid():
    #        formaMunicipio.save()
     #       return redirect('inicio')
  #  else:
   #     formaMunicipio = MunicipioForm()
#
 #   return render(request, 'municipios/agregar_municipio.html' , {'formaMunicipio': formaMunicipio})



#def nuevoMinasPoint(request):
 #   if request.method == 'POST':
  #      formaMinasPoint = MinasPointForm(request.POST)
   #     if formaMinasPoint.is_valid():
    #        # Obtener las coordenadas de X y Y
     #       x = formaMinasPoint.cleaned_data['x']
      #      y = formaMinasPoint.cleaned_data['y']
       #     point = Point(x, y, srid=4326)  # Crea un objeto Point con las coordenadas
#
 #           # Guardar la instancia de MinasPoint
  #          mina = formaMinasPoint.save(commit=False)
   #         mina.geom = point  # Asigna el objeto Point al campo geom
    #        mina.save()
#
 #           return redirect('inicio')  # Redirige a la vista de inicio
  #  else:
   #     formaMinasPoint = MinasPointForm()
#
 #   return render(request, 'minas/agregar_puntoMina.html', {'formaMinasPoint': formaMinasPoint})



def cargarArchivoVista(request):
    return render(request, 'archivo/cargar_archivo.html')  # Invoca la plantilla con el formulario


@api_view(['POST'])
def cargarArchivo(request):
    shapefile_shp = request.FILES.get('shapefile_shp')
    shapefile_shx = request.FILES.get('shapefile_shx')
    shapefile_dbf = request.FILES.get('shapefile_dbf')
    shapefile_cpg = request.FILES.get('shapefile_cpg')
    shapefile_pjr = request.FILES.get('shapefile_pjr')
    shapefile_qmd = request.FILES.get('shapefile_qmd')

    if not (shapefile_shp or shapefile_shx or shapefile_dbf or shapefile_cpg or shapefile_pjr or shapefile_qmd):
        return Response({'error': 'No se ha proporcionado ningún archivo .shp o .shx o .dbf o . cpg o .pjr o .qmd'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            shp_path = os.path.join(temp_dir, 'temp_shapefile.shp')
            with open(shp_path, 'wb') as f:
                for chunk in shapefile_shp.chunks():
                    f.write(chunk)

            if not os.path.exists(shp_path):
                return Response({'error': 'El archivo .shp no se guardó correctamente'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            shx_path = os.path.join(temp_dir, 'temp_shapefile.shx')
            with open(shx_path, 'wb') as f:
                for chunk in shapefile_shx.chunks():
                    f.write(chunk)
            
            dbf_path = os.path.join(temp_dir, 'temp_shapefile.dbf')
            with open(dbf_path, 'wb') as f:
                for chunk in shapefile_dbf.chunks():
                    f.write(chunk)

            cpg_path = os.path.join(temp_dir, 'temp_shapefile.cpg')
            with open(cpg_path, 'wb') as f:
                for chunk in shapefile_cpg.chunks():
                    f.write(chunk)

            pjr_path = os.path.join(temp_dir, 'temp_shapefile.pjr')
            with open(pjr_path, 'wb') as f:
                for chunk in shapefile_pjr.chunks():
                    f.write(chunk)

            # Leer el shapefile usando GeoPandas
            gdf = gpd.read_file(shp_path)

            print("Columnas del DataFrame:", gdf.columns)

            # Después de leer el shapefile
            gdf = gpd.read_file(shp_path)
            print(gdf.head())  # Imprime las primeras filas del DataFrame
            print(gdf.columns)  # Imprime los nombres de las columnas

            
            # Procesar cada fila en el DataFrame
            for _, row in gdf.iterrows():
    #            y = row['Y']  # Usar el valor directamente de la fila
    #            x = row['X']  # Usar el valor directamente de la fila
                y_str = str(row['Y']).replace(',', '').replace('.','').strip()  # Eliminar comas, puntos y espacios
                x_str = str(row['X']).replace(',', '').replace('.','').strip()  # Eliminar comas, puntos y espacios

                try:
                    y = float(y_str)  # Convertir a float sin redondear
                    x = float(x_str)  # Convertir a float sin redondear
                except ValueError:
                    return Response({'error': f'El valor {y_str} o {x_str} no es un número válido'}, status=status.HTTP_400_BAD_REQUEST)


                # Verificar que X e Y no sean nulos
                if pd.isnull(y) or pd.isnull(x):
                    return Response({'error': 'El shapefile contiene puntos sin coordenadas válidas'}, status=status.HTTP_400_BAD_REQUEST)

                # Si X e Y son válidos, procedemos a crear el objeto
                MinasPoint.objects.create(
                    departamen = row['Departamen'],
                    cod_dep=row['Cod_dep'],
                    municipio = row['Municipio'],
                    cod_mun=row['Cod_mun'],
                    zona = row['Zona'],
                    vereda = row['Vereda'],
                    ano=row['Ano'],
                    mes=row['Mes'],
                    edad=row['Edad'],
                    ocupacion=row['Ocupacion'],
                    genero=row['Genero'],
                    condicion=row['Condicion'],
                    y=y,  # Usar el valor directamente de la fila
                    x=x,  # Usar el valor directamente de la fila
                    lugar_deto=row['Lugar_deto'],
                    actividad=row['Actividad'],
                    y_cmt12=row['Y_CMT12'],
                    x_cmt12=row['X_CMT12'],
                    geom= Point(x, y, srid=4326)  
                )

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'status': 'Archivos cargados correctamente'}, status=status.HTTP_201_CREATED)

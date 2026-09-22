import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"

def get_distance_duration(origin: Tuple[float, float], dest: Tuple[float, float]) -> Tuple[float, float]:
    """
    Retorna (distancia en metros, duración en segundos) entre dos puntos usando OSRM.
    """
    if not origin or not dest:
        return 0.0, 0.0
    
    coords = f"{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
    url = OSRM_URL + coords
    params = {"overview": "false", "alternatives": "false"}
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data["code"] == "Ok":
            route = data["routes"][0]
            distance = route["distance"]  # metros
            duration = route["duration"]  # segundos
            return distance, duration
        else:
            print(f"OSRM error: {data.get('code')}")
            return 0.0, 0.0
    except Exception as e:
        print(f"Error en OSRM: {e}")
        return 0.0, 0.0

def optimize_route(
    invoices: List[Dict[str, Any]],
    origin_coords: Tuple[float, float],
    start_time: datetime,
    minutes_per_visit: int = 40
) -> List[Dict[str, Any]]:
    """
    Ordena las facturas usando Nearest Neighbor desde el origen.
    Cada elemento de 'invoices' debe tener:
        - id
        - customer_lat, customer_lng (float)
        - (otros campos que quieras conservar)
    Retorna una lista con el mismo diccionario pero añadiendo:
        - order_index
        - travel_time_minutes
        - distance_miles
        - suggested_arrival (datetime)
        - suggested_departure (datetime)
    """
    if not invoices:
        return []
    
    # Copia para no modificar la original
    remaining = invoices.copy()
    route = []
    
    current_coords = origin_coords
    current_time = start_time
    
    while remaining:
        # Calcular distancia/tiempo desde current_coords a cada remaining
        best_idx = None
        best_duration = None
        best_distance = None
        
        for i, inv in enumerate(remaining):
            lat = inv.get("customer_lat")
            lng = inv.get("customer_lng")
            if lat is None or lng is None:
                # Si falta coordenada, lo ponemos al final con un tiempo grande
                continue
            dist, dur = get_distance_duration(current_coords, (lat, lng))
            if best_idx is None or dur < best_duration:
                best_idx = i
                best_duration = dur
                best_distance = dist
        
        if best_idx is None:
            # Si no hay más con coordenadas, rompemos (no debería pasar)
            break
        
        # Seleccionamos la mejor
        chosen = remaining.pop(best_idx)
        
        # Calcular tiempos
        travel_min = best_duration / 60.0
        arrival_time = current_time + timedelta(seconds=best_duration)
        departure_time = arrival_time + timedelta(minutes=minutes_per_visit)
        
        chosen["order_index"] = len(route) + 1
        chosen["travel_time_minutes"] = round(travel_min, 1)
        chosen["distance_miles"] = round(best_distance / 1609.34, 1)  # metros a millas
        chosen["suggested_arrival"] = arrival_time
        chosen["suggested_departure"] = departure_time
        
        route.append(chosen)
        
        # Actualizar para la siguiente iteración
        current_coords = (chosen["customer_lat"], chosen["customer_lng"])
        current_time = departure_time
    
    return route
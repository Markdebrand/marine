from fastapi import APIRouter

router = APIRouter()


@router.get("/api/ais/test_positions")
def get_test_positions():
    """Devuelve un conjunto de posiciones de ejemplo para pruebas del frontend.

    Formato: { positions: [ { id, lat, lon, sog?, cog?, heading?, name? }, ... ] }
    """
    positions = [
        {"id": "123456789", "lat": 40.4168, "lon": -3.7038, "sog": 7.2, "cog": 85.0, "heading": 90.0, "name": "Demo Vessel A"},
        {"id": "987654321", "lat": 41.3829, "lon": 2.1774, "sog": 12.3, "cog": 210.0, "heading": 208.0, "name": "Demo Vessel B"},
        {"id": "555000111", "lat": 36.7213, "lon": -4.4214, "sog": 0.5, "cog": 10.0, "heading": 12.0, "name": "Stationary C"},
    ]
    return {"positions": positions}

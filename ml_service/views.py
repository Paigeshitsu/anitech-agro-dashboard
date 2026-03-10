import json
import hashlib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache
from pathlib import Path
from .model import load_model, predict_top_k

MODEL = None

def get_model():
    global MODEL
    if MODEL is None:
        MODEL = load_model(Path(__file__).parent / "models" / "crop_model.joblib")
    return MODEL

@csrf_exempt
@require_POST
def predict_crops(request):
    try:
        data = json.loads(request.body)
        
        # Optimization: Prediction Caching
        # Create a unique key based on the input data
        cache_key = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
        cached_result = cache.get(f"ml_pred_{cache_key}")
        
        if cached_result:
            return JsonResponse({'predictions': cached_result, 'cached': True})

        model = get_model()
        predictions = predict_top_k(model, data, k=5)
        
        # Cache results for 1 hour (3600 seconds)
        cache.set(f"ml_pred_{cache_key}", predictions, 3600)
        
        return JsonResponse({'predictions': predictions, 'cached': False})
    
    except KeyError as e:
        return JsonResponse({'error': f'Missing field: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Internal server error processing prediction'}, status=500)
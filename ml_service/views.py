import json
import hashlib
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache  # Optimization: Use Django's cache framework

# Global variable to store the model in memory (Singleton Pattern)
_MODEL_CACHE = None

def get_model():
    """
    Loads the model once and keeps it in memory. 
    This prevents slow disk reads on every API request.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        from .model import load_model
        model_path = Path(__file__).parent / "models" / "crop_model.joblib"
        try:
            _MODEL_CACHE = load_model(model_path)
            print(f"Successfully loaded ML model from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    return _MODEL_CACHE

@csrf_exempt
@require_POST
def predict_crops(request):
    """
    API Endpoint: /ml/predict/
    Returns top-k crop recommendations based on environmental data.
    Includes a caching layer to improve dashboard load times.
    """
    try:
        # 1. Parse Input
        data = json.loads(request.body)
        
        # 2. Optimization: Prediction Caching
        # We create a unique key based on the input values. 
        # If the same Location/Season/Soil data is sent twice, we return the cached result.
        cache_input = f"{data.get('location')}-{data.get('season')}-{data.get('ph')}-{data.get('rainfall')}"
        cache_key = hashlib.md5(cache_input.encode()).hexdigest()
        
        cached_prediction = cache.get(f"ml_res_{cache_key}")
        if cached_prediction:
            return JsonResponse({
                'predictions': cached_prediction, 
                'source': 'cache',
                'status': 'success'
            })

        # 3. Get Model (Loaded in RAM)
        model = get_model()
        if model is None:
            return JsonResponse({'error': 'ML Model not initialized'}, status=500)

        # 4. Perform Inference
        from .model import predict_top_k
        # k=8 matches the 8 cards shown in your dashboard screenshot
        k_value = data.get('k', 8) 
        predictions = predict_top_k(model, data, k=k_value)

        # 5. Store in cache for 1 hour (3600 seconds)
        cache.set(f"ml_res_{cache_key}", predictions, 3600)

        return JsonResponse({
            'predictions': predictions, 
            'source': 'model_inference',
            'status': 'success'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': 'An internal error occurred during prediction'}, status=500)

def clear_ml_cache(request):
    """Optional utility view to clear ML cache if models are updated."""
    if request.user.is_staff:
        cache.clear()
        return JsonResponse({'status': 'Cache cleared'})
    return JsonResponse({'status': 'Unauthorized'}, status=403)
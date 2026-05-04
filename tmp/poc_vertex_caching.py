
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models

def generate_text(project_id: str, location: str) -> str:
    """Generates content from a model with caching enabled."""

    # Initialize Vertex AI SDK
    vertexai.init(project=project_id, location=location)

    # Create a cache for the model
    # Note: The cache is created once and can be reused for multiple generate_content calls.
    # To create a cache, you must have the permission `vertexai.caches.create`.
    # To use a cache, you must have the permission `vertexai.caches.use`.
    from google.cloud import aiplatform
    from google.cloud.aiplatform_v1beta1.types import content
    from google.cloud.aiplatform_v1beta1.types import tool
    from vertexai.preview.caching import Cache

    # Create a cache instance
    # This takes about 1-2 minutes to provision
    try:
        cache = Cache.create(
            model_name="gemini-1.5-pro-001",
            display_name="my_cache_123",
            ttl_seconds=3600,  # Time-to-live for cached content
        )
        print(f"Cache created: {cache.name}")
    except Exception as e:
        # This will fail if the cache already exists, which is expected on subsequent runs.
        # A real implementation would fetch the existing cache instead.
        print(f"Cache creation failed (this is expected if it already exists): {e}")
        # For this PoC, we assume it exists and try to use it.
        # Construct the cache name manually if creation fails.
        # You'll need to replace PROJECT_ID and REGION with your actual project ID and region.
        # This is a bit of a hack for a PoC. A real app would use `Cache.get` or `Cache.list`.
        project_number = "1092797584542" # Replace with your project number if needed
        cache_id = "my_cache_123" # The display name used above
        # The resource name format is projects/PROJECT_NUMBER/locations/LOCATION/caches/CACHE_ID
        # However, the SDK expects a simplified name for the from_name method.
        # Let's try to list caches to find the right one if creation fails.
        caches = Cache.list()
        target_cache = next((c for c in caches if c.display_name == "my_cache_123"), None)
        if target_cache:
            cache = target_cache
            print(f"Found existing cache: {cache.name}")
        else:
            print("Could not find or create a cache. Exiting.")
            return

    # Load the Gemini 1.5 Pro model
    model = GenerativeModel(
        "gemini-1.5-pro-001",
        system_instruction=[
            "You are a helpful language model.",
            "Your mission is to explain complex concepts in a simple, accessible way.",
        ],
    )

    # === First Request (Cache Miss) ===
    print("
--- Sending first request (expected cache miss)... ---")
    response1 = model.generate_content(
        [
            "Why is the sky blue?",
        ],
        generation_config=generation_config,
        safety_settings=safety_settings,
        cached_content=cache.name,
    )

    print("Response 1 (Cache Miss):")
    # print(response1)
    print(f"Tokens in: {response1.usage_metadata.prompt_token_count}")
    print(f"Tokens out: {response1.usage_metadata.candidates_token_count}")


    # === Second Request (Cache Hit) ===
    print("
--- Sending second request (expected cache hit)... ---")
    response2 = model.generate_content(
        [
            "Why is the sky blue?",
        ],
        generation_config=generation_config,
        safety_settings=safety_settings,
        cached_content=cache.name,
    )

    print("
Response 2 (Cache Hit):")
    # print(response2)
    print(f"Tokens in: {response2.usage_metadata.prompt_token_count}")
    print(f"Tokens out: {response2.usage_metadata.candidates_token_count}")
    
    # Check for cache hit explicitly if the API provides it
    if hasattr(response2.usage_metadata, 'cached_content_token_count'):
        print(f"Cached content tokens: {response2.usage_metadata.cached_content_token_count}")
        if response2.usage_metadata.cached_content_token_count > 0:
            print("SUCCESS: Cache was used.")
        else:
            print("FAILURE: Cache was not used.")

    # Clean up the cache
    # print("
--- Deleting cache... ---")
    # cache.delete()
    # print("Cache deleted.")

    return "PoC script executed."


generation_config = {
    "max_output_tokens": 2048,
    "temperature": 0.2,
    "top_p": 1,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

if __name__ == "__main__":
    # You will need to replace 'your-gcp-project-id' and 'your-gcp-location' with your actual
    # Google Cloud project ID and location (e.g., 'us-central1').
    # You can get the project ID by running `gcloud config get-value project`
    # You must be authenticated with `gcloud auth application-default login`
    import os
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = "us-central1"

    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
        print("Please set it to your Google Cloud project ID.")
    else:
        generate_text(project_id, location)

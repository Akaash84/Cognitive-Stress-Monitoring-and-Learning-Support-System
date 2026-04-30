from google import genai

print("🔥 TEST FILE RUNNING 🔥")

client = genai.Client(api_key="AIzaSyBCZM46dg16wv9nynX3Bsw9VkiouN8JsQo")

response = client.models.generate_content(
    # model="https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest",
    model="models/gemini-2.0-flash",

    contents="Say hello in one line"
)

print("RESPONSE:")
print(response.text)

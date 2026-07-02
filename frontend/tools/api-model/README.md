# Generate openapi spec file

Run script from project root:

```bash
uv --project backend run ffcops openapi -f json -o frontend/tools/api-model/swagger/ffc-api-model.json

cd frontend
npm run generate:api-model
npm run format
cd ..
```
